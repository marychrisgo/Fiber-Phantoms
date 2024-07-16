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
    def __init__(self, angle_degrees=30): # 30 degrees for kinking stage 1
        super().__init__()
        self.angle = math.radians(angle_degrees)

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        direction = direction / np.linalg.norm(direction)

        # Adjust direction based on angle
        cos_angle = math.cos(self.angle)
        sin_angle = math.sin(self.angle)

        adjusted_direction = np.array([
            direction[0] * cos_angle - direction[1] * sin_angle,
            direction[0] * sin_angle + direction[1] * cos_angle,
            direction[2]  # Z-component remains the same
        ])

        adjusted_direction /= np.linalg.norm(adjusted_direction)

        if self.grow_from_start:
            self.current_point = filament[0] - adjusted_direction * step_size
        else:
            self.current_point = filament[-1] + adjusted_direction * step_size

        return np.round(self.current_point).astype(int)


class CCurvePointGenerator(BasePointGenerator):
    def __init__(self, bend_radius=100, bend_center=250, radius=3):
        super().__init__()
        self.bend_radius = bend_radius
        self.bend_center = bend_center
        self.radius = radius

    def suggest_next_point(self, filament, direction, step_size, step=None, max_length=None):
        center_point = filament[0] if self.grow_from_start else filament[-1]
        curve_effect = (center_point[0] - self.bend_center) / self.bend_radius
        direction = np.array([1, curve_effect, 0])
        direction /= np.linalg.norm(direction)
        if self.grow_from_start:
            self.current_point = center_point - direction * self.radius
        else:
            self.current_point = center_point + direction * self.radius
        return np.round(self.current_point).astype(int)


class CurvedAmplitudeBasedPointGenerator(BasePointGenerator):
    def __init__(self, curve_amplitude=4.0):
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


# Update the NextPointGenerator to include the new mode
class NextPointGenerator:
    def __init__(self, mode='straight', **kwargs):
        self.mode = mode
        if mode == 'straight':
            self.point_generator = StraightPointGenerator(**kwargs)
        elif mode == 'c_curve':
            self.point_generator = CCurvePointGenerator(**kwargs)
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


