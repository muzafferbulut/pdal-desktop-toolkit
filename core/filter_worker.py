from PyQt5.QtCore import QObject, pyqtSignal
from core.render_utils import RenderUtils
import traceback
import pdal
import json

class FilterWorker(QObject):
    finished = pyqtSignal(str, dict, object) 
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, pipeline_config: list, stage: object):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.stage = stage

    def run(self):
        try:
            self.progress.emit(10)
            json_str = json.dumps(self.pipeline_config, indent=2)
            pipeline = pdal.Pipeline(json_str)            
            count = pipeline.execute()
            self.progress.emit(80)
            arrays = pipeline.arrays[0]

            extracted_data = {
                "x": arrays["X"],
                "y": arrays["Y"],
                "z": arrays["Z"],
                "count": count
            }

            dims = arrays.dtype.names
            if "Intensity" in dims:
                extracted_data["intensity"] = arrays["Intensity"]
            if "Red" in dims and "Green" in dims and "Blue" in dims:
                extracted_data["red"] = arrays["Red"]
                extracted_data["green"] = arrays["Green"]
                extracted_data["blue"] = arrays["Blue"]
            if "Classification" in dims:
                extracted_data["classification"] = arrays["Classification"]


            vis_data = RenderUtils.downsample(extracted_data)
            self.progress.emit(100)
            self.finished.emit(self.file_path, vis_data, self.stage)

        except Exception as e:
            error_details = f"Worker error : {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_details)