import math
import numpy as np
import random

class NextPointGenerator:
    def __init__(self, mode='straight', preferred_direction=[1, 0, 0], bias=0.90, bend_radius=100, bend_center=250, curve_amplitude=0.0):
        self.mode = mode
        self.preferred_direction = np.array(preferred_direction)
        self.bias = bias
        self.bend_radius = bend_radius
        self.bend_center = bend_center
        self.curve_amplitude = curve_amplitude

    def suggest_next_point_straight(self, filament, direction, grow_from_start, step_size):
        direction = direction / np.linalg.norm(direction)
        if grow_from_start:
            next_point = filament[0] - direction * step_size
        else:
            next_point = filament[-1] + direction * step_size
        return next_point

    def suggest_next_point_c_curve(self, filament, grow_from_start, radius):
        center_point = filament[0] if grow_from_start else filament[-1]
        curve_effect = (center_point[0] - self.bend_center) / self.bend_radius
        direction = np.array([1, curve_effect, 0])
        direction /= np.linalg.norm(direction)
        if grow_from_start:
            next_point = center_point - direction * radius
        else:
            next_point = center_point + direction * radius
        return next_point

    def suggest_next_point_curved_amplitude_based(self, filament, direction, grow_from_start, step_size, step, max_length):
        direction = direction / np.linalg.norm(direction)
        if grow_from_start:
            base_point = filament[0] - direction * step_size
        else:
            base_point = filament[-1] + direction * step_size

        if self.curve_amplitude > 0:
            wavelength_factor = 2.0
            angle = math.pi * step / (max_length - 1) / wavelength_factor
            offset_vector = np.cross(direction, [0, 0, 1])
            offset_vector = offset_vector / np.linalg.norm(offset_vector)
            offset_vector *= self.curve_amplitude * math.sin(angle)

            if grow_from_start:
                next_point = filament[0] - direction * step_size + offset_vector
            else:
                next_point = filament[-1] + direction * step_size + offset_vector
        else:
            next_point = base_point

        return next_point

    def suggest_next_point(self, *args):
        if self.mode == 'straight':
            return self.suggest_next_point_straight(*args)
        elif self.mode == 'c_curve':
            return self.suggest_next_point_c_curve(*args)
        elif self.mode == 'curved_amplitude_based':
            return self.suggest_next_point_curved_amplitude_based(*args)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
