import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib
import math 
from next_point_generator import NextPointGenerator

def save_as_nifti(array, file_path): # for 3D Slicer visualization
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

def plot_filaments(volume, filaments, num_filaments):
    colors = plt.cm.jet(np.linspace(0, 1, num_filaments))
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for idx, filament in enumerate(filaments):
        plot_filament(ax, filament, color=colors[idx]) 
    
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    ax.set_zlabel("Z axis")
    plt.show()

def plot_filament(ax, filament, color='b'):
    for point in filament:
        x, y, z = point
        ax.scatter(x, y, z, color=color, alpha=0.5)


def generate_and_count_filaments(volume, num_filaments, pipe_radius=50, min_length=300, max_length=400, radius=3):
    successful_filaments = 0
    filaments = []
    total_attempts = 0
    max_total_attempts = 10000
    
    generator = NextPointGenerator(mode='combined')  # 'straight' or 'curve' or 'combined'

    while successful_filaments < num_filaments and total_attempts < max_total_attempts:
        filament = generate_3d_filament(volume, generator, min_length, max_length, radius, pipe_radius)
        if filament is not None:
            update_volume_with_filament(volume, filament, radius, pipe_radius)
            filaments.append(filament)
            successful_filaments += 1
        total_attempts += 1

    if successful_filaments < num_filaments:
        print(f"Warning: Only able to place {successful_filaments} filaments after {total_attempts} attempts.")

    return successful_filaments, filaments

def generate_3d_filament(volume, generator, min_length=300, max_length=400, radius=3, pipe_radius=50):
    attempts = 0
    max_attempts = 1000
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2

    while attempts < max_attempts:
        center_point = np.array([random.randint(radius, dim - radius - 1) for dim in volume.shape])
        if is_within_bounds(center_point, volume.shape, radius) and is_within_pipe(center_point, center_y, center_z, pipe_radius):
            break
        attempts += 1

    if attempts == max_attempts:
        return None

    filament = [center_point.copy()]

    all_directions = [[1, 0, 0], [1, 1, 0], [1, 0, 1], [0, 1, 1], [-1, -1, 0], [1, -1, 0], [1, 0, -1], [0, 1, -1], [-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
    all_directions = [np.array(d) for d in all_directions if d != generator.preferred_direction.tolist()]

    num_biased = int(generator.bias * 100)
    num_other = 100 - num_biased
    num_other = min(num_other, len(all_directions))

    biased_direction_choices = [np.array(generator.preferred_direction)] * num_biased
    biased_direction_choices.extend(random.sample(all_directions, k=num_other))

    step_size = 1
    direction = np.array(generator.preferred_direction).astype(float)

    grow_from_start = True  # alternate to both ends

    num_steps = max_length * 10
    for step in range(num_steps):
        if generator.mode == 'straight':
            next_point = generator.suggest_next_point_straight(filament, direction, grow_from_start, step_size)
        elif generator.mode == 'curve':
            next_point = generator.suggest_next_point_curve(center_point, direction, step, max_length, radius)
        elif generator.mode == 'combined':
            next_point = generator.suggest_next_point_combined(filament, direction, grow_from_start, step_size, step, max_length)

        next_point_int = np.round(next_point).astype(int)

        if not is_within_bounds(next_point_int, volume.shape, radius) or not is_within_pipe(next_point_int, center_y, center_z, pipe_radius) or not can_place_sphere(next_point_int, volume, radius, pipe_radius):
            if len(filament) >= min_length:
                break
            else:
                return None

        if grow_from_start:
            filament.insert(0, next_point_int)
        else:
            filament.append(next_point_int)

        center_point = next_point_int
        grow_from_start = not grow_from_start  

        direction = random.choice(biased_direction_choices).astype(float)

    if len(filament) < min_length:
        return None

    return filament