import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib


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
                    if not is_within_pipe((ix, iy, iz), center_y, center_z, pipe_radius) or volume[ix, iy, iz] == 1:
                        return False
    return True

def add_voxel_sphere_to_volume(volume, center, radius=1, pipe_radius=50):
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2 and is_within_pipe((center[0]+x, center[1]+y, center[2]+z), center_y, center_z, pipe_radius):
                    volume[center[0]+x, center[1]+y, center[2]+z] = 1

def update_volume_with_filament(volume, filament, radius=1, pipe_radius=50):
    for point in filament:
        add_voxel_sphere_to_volume(volume, point, radius, pipe_radius)

############################################################

def create_void(volume, center, radius):
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x**2 + y**2 + z**2 <= radius**2:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if is_within_bounds((ix, iy, iz), volume.shape, 0):
                        volume[ix, iy, iz] = 0

def generate_random_voids(volume, number_of_voids, min_void_radius=5, max_void_radius=8):
    for _ in range(number_of_voids):
        void_center = (
            random.randint(0, volume.shape[0] - 1),
            random.randint(0, volume.shape[1] - 1),
            random.randint(0, volume.shape[2] - 1)
        )
        void_radius = random.randint(min_void_radius, max_void_radius)
        create_void(volume, void_center, void_radius)
    
    return volume


############################################################

def generate_and_count_filaments(volume, num_filaments, generator, defect_generator, pipe_radius=50, min_length=512, max_length=700, radius=3, bias=0.90, preferred_direction=[1,0,0]):
    successful_filaments = 0
    filaments = []
    total_attempts = 0
    max_total_attempts = 10000

    while successful_filaments < num_filaments and total_attempts < max_total_attempts:
        filament = generate_3d_filament(volume, generator, min_length, max_length, radius, pipe_radius, bias, preferred_direction)
        if filament is not None:
            update_volume_with_filament(volume, filament, radius, pipe_radius)
            filaments.append(filament)
            successful_filaments += 1
        total_attempts += 1

    if successful_filaments < num_filaments:
        print(f"Warning: Only able to place {successful_filaments} filaments after {total_attempts} attempts.")

    volume = defect_generator.apply(volume)
    generate_random_voids(volume, 300)
    return successful_filaments, filaments

def generate_3d_filament(volume, generator, min_length=512, max_length=700, radius=3, pipe_radius=50, bias=0.90, preferred_direction=[1, 0, 0]):
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
