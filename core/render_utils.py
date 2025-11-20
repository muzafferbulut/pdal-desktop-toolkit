import numpy as np

class RenderUtils:

    MAX_VISIBLE_POINTS = 1_000_000

    @staticmethod
    def downsample(x,y,z):

        total_points = len(x)

        if total_points <= RenderUtils.MAX_VISIBLE_POINTS:
            return x,y,z
        
        step = total_points // RenderUtils.MAX_VISIBLE_POINTS
        return x[::step], y[::step], z[::step]