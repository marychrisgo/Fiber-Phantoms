import math
import numpy as np
import random


class BasePointGenerator:
    def __init__(self):
        self.current_point = None
        self.grow_from_start = True

    def initialize_starting_point(self, volume_shape, radius):
        x = random.randint(radius, volume_shape[0] - radius - 1)
        y = random.randint(radius, volume_shape[1] - radius - 1)
        z = random.randint(0, volume_shape[2] - 1)
        self.current_point = np.array([x,y,z])
        return self.current_point


class StraightPointGenerator(BasePointGenerator):
    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        direction = direction / np.linalg.norm(direction)
        if self.grow_from_start:
            self.current_point = filament[0] - direction * step_size
        else:
            self.current_point = filament[-1] + direction * step_size
        return np.round(self.current_point).astype(int)


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


class SCurvePointGenerator(BasePointGenerator):
    def __init__(self, bend_center=250, transition_range=20, return_center=270, return_transition_range=20, radius=3, jaggedness_factor=0.1):
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
            # Interpolate angle between 0 and 45 degrees within the transition range
            fraction = (distance_from_bend + self.transition_range) / (2 * self.transition_range)
            turn_angle = fraction * 45
        elif abs(distance_from_return) <= self.return_transition_range:
            # Interpolate it back from 45 to 0 degrees
            fraction = (distance_from_return + self.return_transition_range) / (2 * self.return_transition_range)
            turn_angle = 45 - (fraction * 45)
        else:
            turn_angle = 45 if distance_from_bend > 0 and abs(distance_from_bend) > self.transition_range else 0
        
        # conversion to radians
        angle_radians = np.radians(turn_angle)
        direction_x = np.cos(angle_radians)
        direction_y = np.sin(angle_radians)

        # direction vector
        direction = np.array([direction_x, direction_y, 0])

        # random perturbation to the direction
        jaggedness = self.jaggedness_factor * np.random.randn(*direction.shape)
        direction += jaggedness

        direction /= np.linalg.norm(direction)

        # Update the current point based on the direction and radius
        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius

        return np.round(self.current_point).astype(int)


class KinkPointGenerator(BasePointGenerator):
    def __init__(self, bend_center=250, kink_range=10, radius=4, jaggedness_factor=0.1):
        super().__init__()
        self.bend_center = bend_center
        self.kink_range = kink_range 
        self.radius = radius
        self.jaggedness_factor = jaggedness_factor 

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        
        distance_from_center = center_point[0] - self.bend_center

        # the angle based on proximity to the bend center
        if -self.kink_range <= distance_from_center <= self.kink_range:
            turn_angle = 45
        else:
            turn_angle = 0
        
        # Conversion
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



# probably delete this?? 
class CurvedAmplitudeBasedPointGenerator(BasePointGenerator):
    def __init__(self, curve_amplitude=2.0):
        super().__init__()
        self.curve_amplitude = curve_amplitude

    def suggest_next_point(self, filament, direction, step_size, step, max_length):
        direction = direction / np.linalg.norm(direction)
        base_point = filament[0] - direction * step_size if self.grow_from_start else filament[-1] + direction * step_size
        if self.curve_amplitude > 0:
            wavelength_factor = 2.0
            angle = math.pi * step / (max_length - 1) / wavelength_factor
            offset_vector = np.cross(direction, [0, 0, 1])
            offset_vector = offset_vector / np.linalg.norm(offset_vector)
            offset_vector *= self.curve_amplitude * math.sin(angle)
            self.current_point = base_point + offset_vector
        else:
            self.current_point = base_point
        return np.round(self.current_point).astype(int)


class NextPointGenerator:
    def __init__(self, mode='straight', **kwargs):
        self.mode = mode
        if mode == 'straight':
            self.point_generator = StraightPointGenerator(**kwargs)
        elif mode == 'c_curve':
            self.point_generator = CCurvePointGenerator(**kwargs)
        elif mode == 's_curve':
            self.point_generator = SCurvePointGenerator(**kwargs)
        elif mode == 'kink_curve':
            self.point_generator = KinkPointGenerator(**kwargs)
        elif mode == 'curved_amplitude_based':
            self.point_generator = CurvedAmplitudeBasedPointGenerator(**kwargs)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def initialize_starting_point(self, volume_shape, radius):
        return self.point_generator.initialize_starting_point(volume_shape, radius)

    def suggest_next_point(self, filament, direction, step_size, step, max_length):
        return self.point_generator.suggest_next_point(filament, direction, step_size, step, max_length)

    def toggle_growth_direction(self):
        self.point_generator.grow_from_start = not self.point_generator.grow_from_start