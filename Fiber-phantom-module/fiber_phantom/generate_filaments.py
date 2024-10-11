import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib

# Define the attenuation coefficients
ATTENUATION_AIR = 0.0
ATTENUATION_RESIN = 100.0
ATTENUATION_FIBER = 255.0

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

def can_place_sphere(center, volume, radius, pipe_radius=50):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if not is_within_bounds((ix, iy, iz), volume.shape, 0):
                        return False
                    if not is_within_pipe((ix, iy, iz), center_y, center_z, pipe_radius) or volume[ix, iy, iz] == ATTENUATION_FIBER:
                        return False
    return True

def add_voxel_sphere_to_volume(volume, center, radius, pipe_radius=50, intensity=ATTENUATION_FIBER):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if is_within_bounds((ix, iy, iz), volume.shape, 0) and is_within_pipe((ix, iy, iz), center_y, center_z, pipe_radius):
                        volume[ix, iy, iz] = intensity

def update_volume_with_filament(volume, filament, radius, pipe_radius=50, intensity=ATTENUATION_FIBER):
    for point in filament:
        add_voxel_sphere_to_volume(volume, point, radius, pipe_radius, intensity)

def fill_pipe_with_resin(volume, pipe_radius=50):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(volume.shape[0]):
        for y in range(volume.shape[1]):
            for z in range(volume.shape[2]):
                if volume[x, y, z] == 0.0 and is_within_pipe((x, y, z), center_y, center_z, pipe_radius):
                    volume[x, y, z] = ATTENUATION_RESIN

def generate_radius_normal(radius_range, mean, std_dev):
    radius = np.random.normal(loc=mean, scale=std_dev)
    # Clamp the value between the min and max of the range
    radius = max(radius_range[0], min(radius_range[1], radius))
    return int(radius)


def generate_and_count_filaments(volume, num_filaments, generator, defect_generator, pipe_radius=50, min_length=512, max_length=512, radius_range=(1, 6), bias=0.90, preferred_direction=[1, 0, 0], cluster_centers=None, cluster_radii=None, cluster_percentages=None):
    cluster_centers = cluster_centers or [
        [120, 120, 120],
        [180, 180, 180],
        [50, 50, 50]
    ]
    cluster_radii = cluster_radii or [10, 20, 15]
    cluster_percentages = cluster_percentages or [20, 50, 30]

    if len(cluster_centers) != len(cluster_radii) or len(cluster_centers) != len(cluster_percentages):
        raise ValueError("The number of cluster centers, radii, and percentages must be the same")

    filaments_per_cluster = [int((p / 100) * num_filaments) for p in cluster_percentages]
    
    successful_filaments = 0
    filaments = []
    total_attempts = 0
    max_total_attempts = 10000

    current_cluster_idx = 0
    filaments_in_cluster = 0

    while successful_filaments < num_filaments and total_attempts < max_total_attempts:
        if current_cluster_idx < len(cluster_centers):
            if filaments_in_cluster < filaments_per_cluster[current_cluster_idx]:
                generator.cluster_center = cluster_centers[current_cluster_idx]
                generator.cluster_radius = cluster_radii[current_cluster_idx]
                filaments_in_cluster += 1
            else:
                current_cluster_idx += 1
                filaments_in_cluster = 0
        else:
            generator.cluster_center = None
            generator.cluster_radius = None
        
        # uniform distribution
        # filament_radius = random.randint(radius_range[0], radius_range[1])

        # normal distribution
        mean = (radius_range[0] + radius_range[1]) / 2
        filament_radius = generate_radius_normal(radius_range, mean=mean, std_dev=0.5)

        filament = generate_3d_filament(volume, generator, min_length, max_length, filament_radius, pipe_radius, bias, preferred_direction)

        if filament is not None:
            update_volume_with_filament(volume, filament, filament_radius, pipe_radius, ATTENUATION_FIBER)
            filaments.append(filament)
            successful_filaments += 1

        total_attempts += 1

    if successful_filaments < num_filaments:
        print(f"Warning: Only able to place {successful_filaments} filaments after {total_attempts} attempts.")

    fill_pipe_with_resin(volume, pipe_radius)

    volume = defect_generator.apply(volume)

    num_voids = 100  
    add_many_small_resin_voids(volume, num_voids, pipe_radius, void_radius=1)
    return successful_filaments, filaments

def generate_3d_filament(volume, generator, min_length=512, max_length=512, filament_radius=3, pipe_radius=50, bias=0.50, preferred_direction=[1, 0, 0]):
    starting_point = generator.initialize_starting_point(volume.shape, filament_radius)

    if not (is_within_bounds(starting_point, volume.shape, filament_radius) and 
            is_within_pipe(starting_point, volume.shape[1] // 2, volume.shape[2] // 2, pipe_radius) and
            can_place_sphere(starting_point, volume, filament_radius, pipe_radius)):
        return None

    filament = [starting_point]

    all_directions = [
        [1, 0, 0], [1, 1, 0], [1, 0, 1], [0, 1, 1], [-1, -1, 0], [1, -1, 0],
        [1, 0, -1], [0, 1, -1], [-1, 1, 0], [-1, 0, 1], [0, -1, 1]
    ]
    all_directions = [np.array(d) for d in all_directions if not np.array_equal(d, preferred_direction)]

    num_biased = int(bias * 100)
    num_other = min(100 - num_biased, len(all_directions))

    biased_direction_choices = [np.array(preferred_direction)] * num_biased + random.sample(all_directions, k=num_other)

    step_size = 1
    direction = np.array(preferred_direction).astype(float)

    for _ in range(max_length * 10):
        next_point = generator.suggest_next_point(filament, direction, step_size, len(filament), max_length)

        if not (is_within_bounds(next_point, volume.shape, filament_radius) and 
                is_within_pipe(next_point, volume.shape[1] // 2, volume.shape[2] // 2, pipe_radius) and 
                can_place_sphere(next_point, volume, filament_radius, pipe_radius)):
            break

        if generator.point_generator.grow_from_start:
            filament.insert(0, next_point)
        else:
            filament.append(next_point)

        if len(filament) >= max_length:
            break

        generator.toggle_growth_direction()
        direction = random.choice(biased_direction_choices).astype(float)

    if len(filament) < min_length:
        return None

    return filament

def add_many_small_resin_voids(volume, num_voids, pipe_radius, void_radius=1):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    voids_added = 0
    attempts = 0
    max_attempts = 1000000

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
                            volume[xi, yj, zk] = ATTENUATION_AIR

        voids_added += 1
        attempts += 1

    if voids_added < num_voids:
        print(f"Warning: Only able to add {voids_added} small resin voids after {attempts} attempts.")
    else:
        print(f"Successfully added {voids_added} small resin voids.")

    return voids_added