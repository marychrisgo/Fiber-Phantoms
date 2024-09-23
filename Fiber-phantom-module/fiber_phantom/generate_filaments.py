import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib



# Define the attenuation coefficients
ATTENUATION_AIR = 0.0
ATTENUATION_RESIN = 0.1
ATTENUATION_FIBER = 1.0

# Slicer reads .nii
def save_as_nifti(array, file_path):
    nifti_img = nib.Nifti1Image(array, affine=np.eye(4))  
    nib.save(nifti_img, file_path)

def is_within_bounds(point, dimensions, radius):
    x, y, z = point
    return (radius <= x < dimensions[0] - radius and
            radius <= y < dimensions[1] - radius and
            radius <= z < dimensions[2] - radius)

def is_within_pipe(point, center_y, center_z, pipe_radius):
    y, z = point[1], point[2]
    return ((y - center_y)**2 + (z - center_z)**2) <= pipe_radius**2

def can_place_sphere(center, volume, radius=1, pipe_radius=50):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if not is_within_pipe((ix, iy, iz), center_y, center_z, pipe_radius) or volume[ix, iy, iz] == ATTENUATION_FIBER:
                        return False
    return True

def add_voxel_sphere_to_volume(volume, center, radius=1, pipe_radius=50, intensity=ATTENUATION_FIBER):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2 and is_within_pipe((center[0]+x, center[1]+y, center[2]+z), center_y, center_z, pipe_radius):
                    volume[center[0]+x, center[1]+y, center[2]+z] = intensity

def update_volume_with_filament(volume, filament, radius=1, pipe_radius=50, intensity=ATTENUATION_FIBER):
    for point in filament:
        add_voxel_sphere_to_volume(volume, point, radius, pipe_radius, intensity)



############################################################

def fill_pipe_with_resin(volume, pipe_radius=50):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(volume.shape[0]):
        for y in range(volume.shape[1]):
            for z in range(volume.shape[2]):
                if volume[x, y, z] == 0.0:  # unfilled spaces
                    if is_within_pipe((x, y, z), center_y, center_z, pipe_radius):
                        volume[x, y, z] = ATTENUATION_RESIN  # Fill with resin


def generate_and_count_filaments(volume, num_filaments, generator, defect_generator, pipe_radius=50, min_length=512, max_length=512, radius=5, bias=0.90, preferred_direction=[1, 0, 0], cluster_centers=None, cluster_radii=None, cluster_percentages=None):
    cluster_centers = [
        [120, 120, 120],  # Cluster 1
        [180, 180, 180],  # Cluster 2
        [50, 50, 50]      # Cluster 3
    ]
    cluster_radii = [
        10,  # Radius for Cluster 1
        20,  # Radius for Cluster 2
        15   # Radius for Cluster 3
    ]
    cluster_percentages = [
        20,  
        50,  
        30   
    ]    

    successful_filaments = 0
    filaments = []
    total_attempts = 0
    max_total_attempts = 100000

    if cluster_centers is None or cluster_radii is None or cluster_percentages is None:
        raise ValueError("You must provide cluster centers, radii, and percentages")

    if len(cluster_centers) != len(cluster_radii) or len(cluster_centers) != len(cluster_percentages):
        raise ValueError("The number of cluster centers, radii, and percentages must be the same")

    # calculate the number of filaments per cluster based on percentages
    filaments_per_cluster = [int((p / 100) * num_filaments) for p in cluster_percentages]

    current_cluster_idx = 0
    filaments_in_cluster = 0

    while successful_filaments < num_filaments and total_attempts < max_total_attempts:
        if current_cluster_idx < len(cluster_centers):
            if filaments_in_cluster < filaments_per_cluster[current_cluster_idx]:
                # generate filament in the current cluster
                generator.cluster_center = cluster_centers[current_cluster_idx]
                generator.cluster_radius = cluster_radii[current_cluster_idx]
                filaments_in_cluster += 1
            else:
                current_cluster_idx += 1
                filaments_in_cluster = 0
        else:
            # sll clusters are exhausted, place filaments randomly
            generator.cluster_center = None
            generator.cluster_radius = None

        # generate the filament
        filament = generate_3d_filament(volume, generator, min_length, max_length, radius, pipe_radius, bias, preferred_direction)

        if filament is not None:
            update_volume_with_filament(volume, filament, radius, pipe_radius, ATTENUATION_FIBER)
            filaments.append(filament)
            successful_filaments += 1

        total_attempts += 1

    if successful_filaments < num_filaments:
        print(f"Warning: Only able to place {successful_filaments} filaments after {total_attempts} attempts.")

    fill_pipe_with_resin(volume, pipe_radius)

    num_voids = 100  
    add_many_small_resin_voids(volume, num_voids, void_radius=1)

    volume = defect_generator.apply(volume)
    return successful_filaments, filaments


def generate_3d_filament(volume, generator, min_length=512, max_length=512, radius=6, pipe_radius=50, bias=0.90, preferred_direction=[1, 0, 0]):
    # starting point without validation
    starting_point = generator.initialize_starting_point(volume.shape, radius)

    # validation: within pipe? within bounds?
    if not (is_within_bounds(starting_point, volume.shape, radius) and 
            is_within_pipe(starting_point, volume.shape[1] // 2, volume.shape[2] // 2, pipe_radius)):
        return None

    filament = [starting_point.copy()]

    all_directions = [[1, 0, 0], [1, 1, 0], [1, 0, 1], [0, 1, 1], [-1, -1, 0], [1, -1, 0], [1, 0, -1], [0, 1, -1], [-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
    all_directions = [np.array(d) for d in all_directions if not np.array_equal(d, preferred_direction)]

    num_biased = int(bias * 100)
    num_other = 100 - num_biased
    num_other = min(num_other, len(all_directions))

    biased_direction_choices = [np.array(preferred_direction)] * num_biased
    biased_direction_choices.extend(random.sample(all_directions, k=num_other))

    step_size = 1
    direction = np.array(preferred_direction).astype(float)

    num_steps = max_length * 10
    for step in range(num_steps):
        next_point = generator.suggest_next_point(filament, direction, step_size, step, max_length)

        if not (is_within_bounds(next_point, volume.shape, radius) and 
                is_within_pipe(next_point, volume.shape[1] // 2, volume.shape[2] // 2, pipe_radius) and 
                can_place_sphere(next_point, volume, radius, pipe_radius)):
            if len(filament) >= min_length:
                break
            else:
                return None

        if generator.point_generator.grow_from_start:
            filament.insert(0, next_point)
        else:
            filament.append(next_point)

        generator.toggle_growth_direction()
        direction = random.choice(biased_direction_choices).astype(float)

    if len(filament) < min_length:
        return None

    return filament

def add_many_small_resin_voids(volume, num_voids, void_radius=1, pipe_radius=125):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    voids_added = 0
    attempts = 0
    max_attempts = 100000

    # location of resin
    resin_positions = np.argwhere(volume == ATTENUATION_RESIN)

    if len(resin_positions) == 0:
        print("No resin areas")
        return voids_added

    while voids_added < num_voids and attempts < max_attempts:
        random_index = random.randint(0, len(resin_positions) - 1)
        x, y, z = resin_positions[random_index]

        for i in range(-void_radius, void_radius + 1):
            for j in range(-void_radius, void_radius + 1):
                for k in range(-void_radius, void_radius + 1):
                    if i**2 + j**2 + k**2 <= void_radius**2:
                        xi, yj, zk = x + i, y + j, z + k
                        if (0 <= xi < volume.shape[0] and
                            0 <= yj < volume.shape[1] and
                            0 <= zk < volume.shape[2] and
                            is_within_pipe((xi, yj, zk), center_y, center_z, pipe_radius)):
                            volume[xi, yj, zk] = 0.0  # Set void intensity back to 'air' 

        voids_added += 1
        attempts += 1

    if voids_added < num_voids:
        print(f"Warning: Only able to add {voids_added} small resin voids after {attempts} attempts.")
    else:
        print(f"Successfully added {voids_added} small resin voids.")

    return voids_added