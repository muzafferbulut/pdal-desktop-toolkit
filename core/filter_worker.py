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

            # ham data
            raw_x = arrays["X"]
            raw_y = arrays["Y"]
            raw_z = arrays["Z"]

            vis_x, vis_y, vis_z = RenderUtils.downsample(raw_x, raw_y, raw_z)

            result_data = {
                "x": vis_x,
                "y": vis_y,
                "z": vis_z,
                "count": count
            }
            self.progress.emit(100)
            self.finished.emit(self.file_path, result_data, self.stage)

        except Exception as e:
            error_details = f"Worker error : {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_details)