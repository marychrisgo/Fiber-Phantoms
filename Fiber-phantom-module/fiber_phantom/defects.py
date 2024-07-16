import numpy as np

class Defect:
    def apply(self, volume):
        raise NotImplementedError("Subclasses should implement this method.")

class Hole(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            center = param['hole_center']
            radius = param['hole_radius']

            for x in range(volume.shape[0]):
                for y in range(volume.shape[1]): 
                    for z in range(volume.shape[2]):
                        if (x - center[0])**2 + (y - center[1])**2 <= radius**2:
                            volume[x, y, z] = 0

        return volume

class SquareNotch(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            square_notch_center = param['square_notch_center']
            square_notch_wh = param["square_notch_wh"]  # half-width of the square notch

            x_center, y_center = square_notch_center  
            half_width = square_notch_wh

            for x in range(volume.shape[0]):
                if abs(x - x_center) <= half_width:
                    for y in range(volume.shape[1]):
                        if abs(y - y_center) <= half_width:
                            for z in range(volume.shape[2]):
                                volume[x, y, z] = 0

        return volume

class DoubleSquareNotch(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            square_notch_center = param['square_notch_center']
            square_notch_wh = param["square_notch_wh"]  # half-width of the square notch

            x_center, y_center = square_notch_center 
            half_width = square_notch_wh

            # 1st notch
            for x in range(volume.shape[0]):
                if abs(x - x_center) <= half_width:
                    for y in range(volume.shape[1]):
                        if abs(y - y_center) <= half_width:
                            for z in range(volume.shape[2]):
                                volume[x, y, z] = 0

            # calculate opposite side's center
            x_opposite_center = volume.shape[0] - x_center - 1
            y_opposite_center = volume.shape[1] - y_center - 1

            # apply 2nd notch
            for x in range(volume.shape[0]):
                if abs(x - x_opposite_center) <= half_width:
                    for y in range(volume.shape[1]):
                        if abs(y - y_opposite_center) <= half_width:
                            for z in range(volume.shape[2]):
                                volume[x, y, z] = 0

        return volume

class VNotch(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            v_notch_center = param['v_notch_center']
            v_notch_height = param["v_notch_height"] 
            v_notch_width = param["v_notch_width"]  

            x_center, y_center = v_notch_center 
            height = v_notch_height
            half_width = v_notch_width / 2

            for x in range(volume.shape[0]):
                for y in range(volume.shape[1]):
                    if abs(x - x_center) <= height and abs(y - y_center) <= half_width * (1 - abs(x - x_center) / height):
                        for z in range(volume.shape[2]):
                            volume[x, y, z] = 0

        return volume

class DoubleVNotch(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            v_notch_center = param['v_notch_center']
            v_notch_height = param["v_notch_height"] 
            v_notch_width = param["v_notch_width"] 

            x_center, y_center = v_notch_center 
            height = v_notch_height
            half_width = v_notch_width / 2

            # 1st notch
            for x in range(volume.shape[0]):
                for y in range(volume.shape[1]):
                    if abs(x - x_center) <= height and abs(y - y_center) <= half_width * (1 - abs(x - x_center) / height):
                        for z in range(volume.shape[2]):
                            volume[x, y, z] = 0

            # calculate opposite side's
            x_opposite_center = volume.shape[0] - x_center - 1
            y_opposite_center = volume.shape[1] - y_center - 1

            # 2nd notch
            for x in range(volume.shape[0]):
                for y in range(volume.shape[1]):
                    if abs(x - x_opposite_center) <= height and abs(y - y_opposite_center) <= half_width * (1 - abs(x - x_opposite_center) / height):
                        for z in range(volume.shape[2]):
                            volume[x, y, z] = 0

        return volume

class Reduced(Defect):
    def __init__(self, params):
        self.params = params

    def apply(self, volume):
        for param in self.params:
            center = param['reduced_center']
            reduced_radius = param['reduced_radius']
            slice_thickness = param['reduced_slice_thickness']
            middle_slice = volume.shape[0] // 2

            # range of slices to be 0
            start_slice = middle_slice - slice_thickness // 2
            end_slice = middle_slice + slice_thickness // 2 + 1

            # iterate for the chosen slice
            for x in range(start_slice, end_slice):
                for y in range(volume.shape[1]):
                    for z in range(volume.shape[2]):
                        # 0 the volume, not the ones in the circle with reduced_radius
                        if (y - center[0])**2 + (z - center[1])**2 > reduced_radius**2:
                            volume[x, y, z] = 0

        return volume

class NoDefect(Defect):
    def apply(self, volume):
        return volume

class DefectGenerator:
    def __init__(self, defect_type='hole', **kwargs):
        self.defect_type = defect_type
        params = kwargs.get('params', {})
        if defect_type == 'hole':
            self.defect = Hole(params)
        elif defect_type == 'square_notch':
            self.defect = SquareNotch(params)
        elif defect_type == 'double_square_notch':
            self.defect = DoubleSquareNotch(params)
        elif defect_type == 'v_notch':
            self.defect = VNotch(params)
        elif defect_type == 'double_v_notch':
            self.defect = DoubleVNotch(params)
        elif defect_type == 'reduced':
            self.defect = Reduced(params)
        elif defect_type == 'none':
            self.defect = NoDefect()
        else:
            raise ValueError(f"Unknown type: {self.defect_type}")

    def apply(self, volume):
        return self.defect.apply(volume)