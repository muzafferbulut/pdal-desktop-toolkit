import numpy as np

class RenderUtils:
    
    # Görüntülenecek maksimum nokta sayısı (1 Milyon)
    MAX_VISIBLE_POINTS = 1_000_000 

    @staticmethod
    def downsample(data_dict: dict):
        if "x" not in data_dict:
            return data_dict

        x_data = data_dict["x"]
        total_points = len(x_data)

        if total_points <= RenderUtils.MAX_VISIBLE_POINTS:
            return data_dict
        
        step = total_points // RenderUtils.MAX_VISIBLE_POINTS
        
        if step <= 1:
            return data_dict

        result_dict = {}
        
        for key, value in data_dict.items():
            if isinstance(value, np.ndarray) and len(value) == total_points:
                result_dict[key] = value[::step].copy()
            else:
                result_dict[key] = value
        
        return result_dict