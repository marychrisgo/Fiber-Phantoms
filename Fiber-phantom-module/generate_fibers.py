import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib

def save_as_nifti(array, file_path): # for 3D Slicer visualization
    nifti_img = nib.Nifti1Image(array, affine=np.eye(4))  
    nib.save(nifti_img, file_path)

# Sphere and with fiber curving
# time for 100 fibers (2min:47s)
# curved fibers maximum = 25 only :(

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

def update_volume_with_fiber(volume, fiber, radius=1, pipe_radius=50):
    for point in fiber:
        add_voxel_sphere_to_volume(volume, point, radius, pipe_radius)

def generate_and_count_fibers(volume, num_fibers, mode ='straight', pipe_radius=50, min_length=300, max_length=400, radius=3):

    successful_fibers = 0
    fibers = []
    total_attempts = 0
    max_total_attempts = 10000 
    
    while successful_fibers < num_fibers and total_attempts < max_total_attempts:
        if mode =='straight':
            fiber = generate_3d_fiber(volume, min_length, max_length, radius, pipe_radius)
        elif  mode == 'curve':
            fiber = generate_3d_fiber_curved(volume, min_length, max_length, radius, pipe_radius)
        if fiber is not None:
            update_volume_with_fiber(volume, fiber, radius, pipe_radius)
            fibers.append(fiber)
            successful_fibers += 1
        total_attempts += 1

    if successful_fibers < num_fibers:
        print(f"Warning: Only able to place {successful_fibers} fibers after {total_attempts} attempts.")

    plot_fibers(volume, fibers, num_fibers)

    return successful_fibers, fibers

def plot_fibers(volume, fibers, num_fibers):
    colors = plt.cm.jet(np.linspace(0, 1, num_fibers))
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for idx, fiber in enumerate(fibers):
        plot_fiber(ax, fiber, color=colors[idx]) 
    
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    ax.set_zlabel("Z axis")
    plt.show()

def plot_fiber(ax, fiber, color='b'):
    for point in fiber:
        x, y, z = point
        ax.scatter(x, y, z, color=color, alpha=0.5)

def generate_3d_fiber(volume, min_length=300, max_length=400, radius=3, pipe_radius=50,
                      curve_amplitude=0.0, curve_frequency=0.0, preferred_direction=[1, 0, 0], bias=0.90):
    
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

    fiber = [center_point]


    all_directions = [[1, 0, 0],
                      [1, 1, 0], [1, 0, 1], [0, 1, 1],
                      [-1, -1, 0],
                      [1, -1, 0], [1, 0, -1], [0, 1, -1],
                      [-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
    all_directions = [np.array(d) for d in all_directions if d != preferred_direction]

    num_biased = int(bias * 100)
    num_other = 100 - num_biased
    num_other = min(num_other, len(all_directions)) 

    biased_direction_choices = [np.array(preferred_direction)] * num_biased
    
    biased_direction_choices.extend(random.sample(all_directions, k=num_other))

    direction = random.choice(biased_direction_choices).astype(float)

    # randomness, sinusoidal adjustment, predefined direction with bias

    step_size = 1 
    for step in range(max_length):
        curve = np.sin(step * curve_frequency) * curve_amplitude
        adjustment = np.array([curve if i == 0 else curve * random.uniform(-1, 1) for i in range(3)], dtype=float)
        direction += adjustment


        direction = direction / np.linalg.norm(direction)

        next_point = center_point + direction * step_size
        next_point_int = np.round(next_point).astype(int)

        if not is_within_bounds(next_point_int, volume.shape, radius) or not is_within_pipe(next_point_int, center_y, center_z, pipe_radius) or not can_place_sphere(next_point_int, volume, radius, pipe_radius):
            if len(fiber) >= min_length:
                break
            else:
                return None

        fiber.append(next_point_int)
        center_point = next_point_int

    if len(fiber) < min_length:
        return None

    return fiber


def generate_3d_fiber_curved(volume, min_length=300, max_length=400, radius=3, pipe_radius=50, bend_radius=100, bend_center=250):
    attempts = 0
    max_attempts = 1000
    center_point = np.array([np.random.randint(radius, dim - radius - 1) for dim in volume.shape])
    
    center_y, center_z = volume.shape[1] // 2, volume.shape[2] // 2
    while attempts < max_attempts:
        if is_within_bounds(center_point, volume.shape, radius) and is_within_pipe(center_point, center_y, center_z, pipe_radius):
            break
        center_point = np.array([np.random.randint(radius, dim - radius - 1) for dim in volume.shape])
        attempts += 1
    if attempts == max_attempts:
        return None

    fiber = [center_point.copy()]
    direction = np.array([1, 0, 0], dtype=float)  # Initial direction along x-axis

    for step in range(max_length):
        curve_effect = (center_point[0] - bend_center) / bend_radius
        direction = np.array([1, curve_effect, 0])
        direction /= np.linalg.norm(direction)  # Normalize direction

        next_point = center_point + direction * radius
        next_point_int = np.round(next_point).astype(int)
        
        if not is_within_bounds(next_point_int, volume.shape, radius) or not is_within_pipe(next_point_int, center_y, center_z, pipe_radius) or not can_place_sphere(next_point_int, volume, radius, pipe_radius):
            if len(fiber) >= min_length:
                break
            else:
                return None
        
        fiber.append(next_point_int.copy())
        center_point = next_point_int

    if len(fiber) < min_length:
        return None

    return fiber


