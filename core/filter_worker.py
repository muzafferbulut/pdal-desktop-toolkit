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
    stage_progress = pyqtSignal(int, str, int, int) 

    def __init__(self, file_path: str, pipeline_config: list, stage: object, input_count: int):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.stage = stage
        self.input_count = input_count
        self.is_interrupted = False

    def run(self):
        try:
            self.progress.emit(10)
            
            current_arrays = []
            current_count = self.input_count
            total_stages = len(self.pipeline_config)
            last_pipeline = None 

            for i, stage_conf in enumerate(self.pipeline_config):
                if self.is_interrupted:
                    break

                if i == 0:
                    pipeline = pdal.Pipeline(json.dumps([stage_conf]))
                else:
                    pipeline = pdal.Pipeline(json.dumps([stage_conf]), arrays=current_arrays)

                pipeline.execute()
                
                current_arrays = pipeline.arrays
                last_pipeline = pipeline
                
                new_count = 0
                if current_arrays:
                    new_count = len(current_arrays[0])

                percent = int((i + 1) / total_stages * 80) + 10
                self.progress.emit(percent)

                tag = stage_conf.get("tag")
                if tag:
                    self.stage_progress.emit(i, tag, current_count, new_count)
                
                current_count = new_count

            if not last_pipeline or not last_pipeline.arrays:
                raise Exception("Pipeline produced no data.")

            arrays = last_pipeline.arrays[0]
            metadata = last_pipeline.metadata

            extracted_data = {
                Dimensions.X: arrays[Dimensions.X.value],
                Dimensions.Y: arrays[Dimensions.Y.value],
                Dimensions.Z: arrays[Dimensions.Z.value],
                "count": current_count
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