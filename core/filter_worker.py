from PyQt5.QtCore import QObject, pyqtSignal
from core.render_utils import RenderUtils
from core.enums import Dimensions
import traceback
import pdal
import json

class FilterWorker(QObject):
    finished = pyqtSignal(str, dict, dict, object, int) 
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, pipeline_config: list, stage: object, input_count: int):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.stage = stage
        self.input_count = input_count

    def run(self):
        try:
            self.progress.emit(10)
            json_str = json.dumps(self.pipeline_config, indent=2)
            pipeline = pdal.Pipeline(json_str)
            self.progress.emit(-1)         
            count = pipeline.execute()
            self.progress.emit(80)

            metadata = pipeline.metadata
            
            arrays = pipeline.arrays[0]

            extracted_data = {
                Dimensions.X: arrays[Dimensions.X.value],
                Dimensions.Y: arrays[Dimensions.Y.value],
                Dimensions.Z: arrays[Dimensions.Z.value],
                "count": count
            }

            dims = arrays.dtype.names
            if Dimensions.INTENSITY.value in dims:
                extracted_data[Dimensions.INTENSITY] = arrays[Dimensions.INTENSITY.value]
            
            if Dimensions.RED.value in dims and Dimensions.GREEN.value in dims and Dimensions.BLUE.value in dims:
                extracted_data[Dimensions.RED] = arrays[Dimensions.RED.value]
                extracted_data[Dimensions.GREEN] = arrays[Dimensions.GREEN.value]
                extracted_data[Dimensions.BLUE] = arrays[Dimensions.BLUE.value]
                
            if Dimensions.CLASSIFICATION.value in dims:
                extracted_data[Dimensions.CLASSIFICATION] = arrays[Dimensions.CLASSIFICATION.value]

            vis_data = RenderUtils.downsample(extracted_data)
            self.progress.emit(100)
            self.finished.emit(self.file_path, vis_data, metadata, self.stage, self.input_count)
        except Exception as e:
            error_details = f"Worker error : {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_details)