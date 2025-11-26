from PyQt5.QtCore import QObject, pyqtSignal
from core.render_utils import RenderUtils
import numpy as np
import traceback
import pdal
import json

class MergeWorker(QObject):
    finished = pyqtSignal(str, dict, dict, dict, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_paths, output_name="Merged"):
        super().__init__()
        self.file_paths = file_paths
        self.output_name = output_name

    def run(self):
        try:
            self.progress.emit(10)
            pipeline_config = list(self.file_paths)
            pipeline_config.append({"type": "filters.merge"})
            
            self.progress.emit(20)
            
            json_str = json.dumps(pipeline_config)
            pipeline = pdal.Pipeline(json_str)
            
            self.progress.emit(-1)
            count = pipeline.execute()
            
            self.progress.emit(70)
            arrays = pipeline.arrays[0]
            extracted_data = {
                "x": arrays["X"], "y": arrays["Y"], "z": arrays["Z"], "count": count
            }
            dims = arrays.dtype.names
            if "Intensity" in dims: extracted_data["intensity"] = arrays["Intensity"]
            if "Red" in dims: 
                extracted_data["red"] = arrays["Red"]
                extracted_data["green"] = arrays["Green"]
                extracted_data["blue"] = arrays["Blue"]
            if "Classification" in dims: extracted_data["classification"] = arrays["Classification"]

            vis_data = RenderUtils.downsample(extracted_data)
            vis_data["status"] = True
            minx, maxx = np.min(arrays["X"]), np.max(arrays["X"])
            miny, maxy = np.min(arrays["Y"]), np.max(arrays["Y"])
            minz, maxz = np.min(arrays["Z"]), np.max(arrays["Z"])
            
            bounds = {
                "minx": minx, "maxx": maxx, 
                "miny": miny, "maxy": maxy, 
                "status": True
            }
            
            summary_metadata = {
                "points": count,
                "is_compressed": "N/A",
                "crs_name": "Merged CRS", 
                "epsg": "N/A",
                "software_id": "PDAL Merge",
                "x_range": f"[{minx:.2f} to {maxx:.2f}]",
                "y_range": f"[{miny:.2f} to {maxy:.2f}]",
                "z_range": f"[{minz:.2f} to {maxz:.2f}]",
                "unit": "N/A"
            }
            
            full_metadata = {"metadata": pipeline.metadata}
            self.progress.emit(100)
            self.finished.emit(self.output_name, bounds, full_metadata, summary_metadata, vis_data)

        except Exception as e:
            self.error.emit(f"Merge operation failed: {str(e)}\n{traceback.format_exc()}")