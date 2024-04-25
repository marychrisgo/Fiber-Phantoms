import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
from scipy.interpolate import splprep, splev
import nibabel as nib

def save_as_nifti(array, file_path): # for 3D Slicer visualization
    nifti_img = nib.Nifti1Image(array, affine=np.eye(4))  
    nib.save(nifti_img, file_path)

def choose_semi_axes(semi_axes_list, probabilities):
    return random.choices(semi_axes_list, weights=probabilities, k=1)[0]


def is_within_bounds_ellipsoid(center, volume, semi_axes):
    x, y, z = center
    a, b, c = semi_axes  
    return (a <= x < volume.shape[0] - a) and \
           (b <= y < volume.shape[1] - b) and \
           (c <= z < volume.shape[2] - c)


def can_place_ellipsoid(center, volume, semi_axes, allow_fusion=False, fusion_chance=0):
    a, b, c = semi_axes
    for x in range(-a, a + 1):
        for y in range(-b, b + 1):
            for z in range(-c, c + 1):
                if ((x**2) / (a**2)) + ((y**2) / (b**2)) + ((z**2) / (c**2)) <= 1:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if not is_within_bounds_ellipsoid(center, volume, semi_axes):
                        return False
                    if volume[ix, iy, iz] == 1:
                        if allow_fusion and random.random() < (fusion_chance / 100.0):
                            continue
                        return False
    return True


def add_voxel_ellipsoid_to_volume(volume, center, semi_axes):
    a, b, c = semi_axes
    for x in range(-a, a + 1):
        for y in range(-b, b + 1):
            for z in range(-c, c + 1):
                if ((x**2) / (a**2)) + ((y**2) / (b**2)) + ((z**2) / (c**2)) <= 1:
                    ix, iy, iz = center[0] + x, center[1] + y, center[2] + z
                    if is_within_bounds_ellipsoid(center, volume, semi_axes):
                        volume[ix, iy, iz] = 1



def update_volume_with_fiber(volume, fiber, semi_axes=[1,1,1]):
    for point in fiber:
        add_voxel_ellipsoid_to_volume(volume, point, semi_axes)

def plot_ellipsoid(ax, center, semi_axes=[6, 12, 6], color='b', alpha=0.2):
    x0, y0, z0 = center
    a, b, c = semi_axes
    
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    
    x = x0 + a * np.outer(np.cos(u), np.sin(v))
    y = y0 + b * np.outer(np.sin(u), np.sin(v))
    z = z0 + c * np.outer(np.ones(np.size(u)), np.cos(v))
    
    ax.plot_surface(x, y, z, color=color, alpha=alpha)

def generate_and_count_fibers(volume, random_seed, num_fibers, num_clusters, cluster_radius, min_length=50, max_length=100, 
                              semi_axes_list = [(1, 1, 1), (2, 1, 1)], probabilities = [0.5, 0.3], curve_amplitude=0.1, curve_frequency=0.1, 
                              preferred_direction=[1, 0, 0], bias=0.8, fusion_chance=0):
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    successful_fibers = 0
    fibers = []
    total_attempts = 0
    max_total_attempts = 10000
    
    colors = plt.cm.jet(np.linspace(0,1,num_fibers))
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    while successful_fibers < num_fibers and total_attempts < max_total_attempts:
        semi_axes = choose_semi_axes(semi_axes_list, probabilities)
        fiber = generate_3d_fiber_with_clustering(volume, num_clusters, cluster_radius, min_length, max_length, 
                                                  semi_axes, curve_amplitude, curve_frequency, 
                                                  preferred_direction, bias, fusion_chance)
        if fiber is not None:
            update_volume_with_fiber(volume, fiber, semi_axes)  
            for point in fiber:
                plot_ellipsoid(ax, point, semi_axes=semi_axes, color=colors[successful_fibers], alpha=0.5)
            ax.set_xlabel("X axis")
            ax.set_ylabel("Y axis")
            ax.set_zlabel("Z axis")
            fibers.append(fiber)
            successful_fibers += 1
        total_attempts += 1

    if successful_fibers < num_fibers:
        print(f"Warning: Only able to place {successful_fibers} fibers after {total_attempts} attempts.")

    # save_as_nifti(volume, f'original_volume.nii')
    plt.show()

    return successful_fibers, fibers

def generate_clusters(volume, num_clusters, cluster_radius):
    clusters = []
    attempts = 0
    max_attempts = num_clusters * 100
    while len(clusters) < num_clusters and attempts < max_attempts:
        potential_center = np.array([random.randint(cluster_radius, dim - cluster_radius - 1) for dim in volume.shape])
        if all(np.linalg.norm(potential_center - c) >= 2 * cluster_radius for c in clusters):
            clusters.append(potential_center)
        attempts += 1
    if len(clusters) != num_clusters:
        raise ValueError("Could not place all clusters within max attempts")
    return clusters

def generate_3d_fiber_with_clustering(volume, num_clusters, cluster_radius, min_length=50, max_length=100, semi_axes=[1,1,1], 
                                      curve_amplitude=0.1, curve_frequency=0.1, preferred_direction=[1, 0, 0], bias=0.8, fusion_chance=100):
    clusters = generate_clusters(volume, num_clusters, cluster_radius)
    
    cluster_center = random.choice(clusters)
    center_point = cluster_center + np.random.uniform(-cluster_radius, cluster_radius, size=3)
    center_point = np.round(center_point).astype(int)  

    attempts = 0
    max_attempts = 1000
    while attempts < max_attempts:
        center_point = np.array([random.randint(semi_axes[i], dim - semi_axes[i] - 1) for i, dim in enumerate(volume.shape)])
        if can_place_ellipsoid(center_point, volume, semi_axes, allow_fusion=True, fusion_chance=fusion_chance):
            break
        attempts += 1
    if attempts == max_attempts:
        return None

    fiber = [center_point]
    
    all_directions = [[1, 0, 0], [0, 1, 0], [0, 0, 1],
                      [-1, 0, 0], [0, -1, 0], [0, 0, -1],
                      [1, 1, 0], [1, 0, 1], [0, 1, 1],
                      [-1, -1, 0], [-1, 0, -1], [0, -1, -1],
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

    step_size = max(semi_axes) / 6  

    for step in range(max_length):
        curve = np.sin(step * curve_frequency) * curve_amplitude
        adjustment = np.array([curve if i == 0 else curve * random.uniform(-1, 1) for i in range(3)], dtype=float)
        direction += adjustment
        direction = direction / np.linalg.norm(direction)  

        next_point = center_point + direction * step_size
        next_point_int = np.round(next_point).astype(int)

        if not is_within_bounds_ellipsoid(next_point_int, volume, semi_axes) or \
        not can_place_ellipsoid(next_point_int, volume, semi_axes, allow_fusion=True, fusion_chance=fusion_chance):
            if len(fiber) >= min_length:
                break 
            else:
                return None  

        fiber.append(next_point_int)  
        center_point = next_point_int 

    return fiber

