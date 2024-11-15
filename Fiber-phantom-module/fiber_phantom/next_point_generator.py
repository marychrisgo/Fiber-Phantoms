import math
import numpy as np
import random


class BasePointGenerator:
    def __init__(self):
        self.current_point = None
        self.grow_from_start = True

    def initialize_starting_point(self, volume_shape, radius, cluster_center=None, cluster_radius=None):
        if cluster_center is not None and cluster_radius is not None:
            # Calculate the bounds for x, y, and z
            lower_bound_x = max(cluster_center[0] - cluster_radius, radius)
            upper_bound_x = min(cluster_center[0] + cluster_radius, volume_shape[0] - radius - 1)

            lower_bound_y = max(cluster_center[1] - cluster_radius, radius)
            upper_bound_y = min(cluster_center[1] + cluster_radius, volume_shape[1] - radius - 1)

            # Add checks for valid ranges
            if lower_bound_x > upper_bound_x:
                lower_bound_x, upper_bound_x = upper_bound_x, lower_bound_x
            if lower_bound_y > upper_bound_y:
                lower_bound_y, upper_bound_y = upper_bound_y, lower_bound_y

            # Avoid empty ranges by ensuring bounds are valid
            x = lower_bound_x if lower_bound_x == upper_bound_x else random.randint(lower_bound_x, upper_bound_x)
            y = lower_bound_y if lower_bound_y == upper_bound_y else random.randint(lower_bound_y, upper_bound_y)
            z = random.randint(0, volume_shape[2] - 1)  # No need to change z unless there are similar issues

        else:
            # Default random point generation
            x = random.randint(radius, volume_shape[0] - radius - 1)
            y = random.randint(radius, volume_shape[1] - radius - 1)
            z = random.randint(0, volume_shape[2] - 1)

        self.current_point = np.array([x, y, z])
        return self.current_point



class CCurvePointGenerator(BasePointGenerator):
    def __init__(self, bend_radius=100, bend_center=250, radius=3, jaggedness_factor=0.1):
        super().__init__()
        self.bend_radius = bend_radius
        self.bend_center = bend_center
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor  

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        curve_effect = (center_point[0] - self.bend_center) / self.bend_radius
        direction = np.array([1, curve_effect, 0])

        # random perturbation added to each direction component
        jaggedness = self.jaggedness_factor * np.random.randn(*direction.shape)
        direction += jaggedness

        direction /= np.linalg.norm(direction)

        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius
        return np.round(self.current_point).astype(int)


class KinkCurvePointGenerator(BasePointGenerator):
    def __init__(self, bend_center=125, transition_range=20, return_center=150, return_transition_range=20, radius=3, jaggedness_factor=0.01):
        super().__init__()
        self.bend_center = bend_center
        self.transition_range = transition_range
        self.return_center = return_center
        self.return_transition_range = return_transition_range
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor  

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        
        distance_from_bend = center_point[0] - self.bend_center
        distance_from_return = center_point[0] - self.return_center

        if abs(distance_from_bend) <= self.transition_range:
            # interpolate angle between 0 and 45 degrees 
            fraction = (distance_from_bend + self.transition_range) / (2 * self.transition_range)
            turn_angle = fraction * 45
        elif abs(distance_from_return) <= self.return_transition_range:
            #  back to 0 degrees
            fraction = (distance_from_return + self.return_transition_range) / (2 * self.return_transition_range)
            turn_angle = 45 - (fraction * 45)
        else:
            turn_angle = 0  
        
        # conversion to radians
        angle_radians = np.radians(turn_angle)
        direction_x = np.cos(angle_radians)
        direction_y = np.sin(angle_radians)

        direction = np.array([direction_x, direction_y, 0])

        # random perturbations
        jaggedness = self.jaggedness_factor * np.random.randn(*direction.shape)
        direction += jaggedness

        direction /= np.linalg.norm(direction)


        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius

        return np.round(self.current_point).astype(int)

class StraightFiberPointGenerator(BasePointGenerator):
    def __init__(self, volume_shape, radius=3, jaggedness_factor=0.0):
        super().__init__()
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor
        self.volume_shape = volume_shape  
        
    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        # Set the starting point at x = 0
        if len(filament) == 0:
            self.current_point = np.array([0, self.volume_shape[1] // 2, self.volume_shape[2] // 2])
            filament.append(self.current_point)
        
        center_point = filament[-1]

        direction = np.array([1.0, 0.0, 0.0]) 

        jaggedness = self.jaggedness_factor * np.random.randn(3)
        direction[1:] += jaggedness[1:] 

        direction = direction / np.linalg.norm(direction)

        self.current_point = center_point + direction * self.radius

        if self.current_point[0] >= self.volume_shape[0]:
            self.current_point[0] = self.volume_shape[0]  
            return None  

        return np.round(self.current_point).astype(int)


class FullWaveCurvePointGenerator(BasePointGenerator):
    def __init__(self, wave_center=125, wave_range=100, wave_amplitude=20, wave_frequency=3, radius=3, jaggedness_factor=0.0): 
        super().__init__()
        self.wave_center = wave_center
        self.wave_range = wave_range
        self.wave_amplitude = wave_amplitude
        self.wave_frequency = wave_frequency
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor  

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        
        distance_from_wave = center_point[0] - self.wave_center

        if abs(distance_from_wave) <= self.wave_range:
            fraction = (distance_from_wave + self.wave_range) / (2 * self.wave_range) #normalized position along the wave's range
            turn_angle = self.wave_amplitude * np.sin(self.wave_frequency * fraction * np.pi)  # Full wave
        else:
            turn_angle = 0  
        
        angle_radians = np.radians(turn_angle)
        direction_x = np.cos(angle_radians)
        direction_y = np.sin(angle_radians)

        direction = np.array([direction_x, direction_y, 0])

        jaggedness = self.jaggedness_factor * np.random.randn(*direction.shape)
        direction += jaggedness

        direction /= np.linalg.norm(direction)

        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius

        return np.round(self.current_point).astype(int)

class HalfWaveCurvePointGenerator(BasePointGenerator):
    def __init__(self, wave_center=125, wave_range=100, wave_amplitude=20, wave_frequency=2, radius=3, jaggedness_factor=0.0): 
        super().__init__()
        self.wave_center = wave_center
        self.wave_range = wave_range
        self.wave_amplitude = wave_amplitude
        self.wave_frequency = wave_frequency
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor  

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        
        distance_from_wave = center_point[0] - self.wave_center

        if abs(distance_from_wave) <= self.wave_range:
            fraction = (distance_from_wave + self.wave_range) / (2 * self.wave_range) 
            turn_angle = self.wave_amplitude * np.sin(self.wave_frequency * fraction * np.pi)  
        else:
            turn_angle = 0  
        
        angle_radians = np.radians(turn_angle)
        direction_x = np.cos(angle_radians)
        direction_y = np.sin(angle_radians)

        direction = np.array([direction_x, direction_y, 0])

        jaggedness = self.jaggedness_factor * np.random.randn(*direction.shape)
        direction += jaggedness

        direction /= np.linalg.norm(direction)

        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius

        return np.round(self.current_point).astype(int)

class NextPointGenerator:
    def __init__(self, mode='straight', cluster_center=None, cluster_radius=None, **kwargs):
        self.mode = mode
        self.cluster_center = cluster_center
        self.cluster_radius = cluster_radius

        if mode == 'c_curve':
            self.point_generator = CCurvePointGenerator(**kwargs)
        elif mode == 'kink_curve':
            self.point_generator = KinkCurvePointGenerator(**kwargs)
        elif mode == 'straight':
            self.point_generator = StraightFiberPointGenerator(**kwargs)
        elif mode == 'full_wave_curve':
            self.point_generator = FullWaveCurvePointGenerator(**kwargs)
        elif mode == 'half_wave_curve':
            self.point_generator = HalfWaveCurvePointGenerator(**kwargs)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def initialize_starting_point(self, volume_shape, radius):
        # Pass clustering parameters to the point generator
        return self.point_generator.initialize_starting_point(volume_shape, radius, self.cluster_center, self.cluster_radius)

    def suggest_next_point(self, filament, direction, step_size, step, max_length):
        return self.point_generator.suggest_next_point(filament, direction, step_size, step, max_length)

    def toggle_growth_direction(self):
        self.point_generator.grow_from_start = not self.point_generator.grow_from_start
