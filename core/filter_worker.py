from PyQt5.QtCore import QObject, pyqtSignal
from core.enums import Dimensions
import numpy as np
import traceback
import pdal
import json


class FilterWorker(QObject):
    finished = pyqtSignal(str, dict, dict, object, int)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    stage_progress = pyqtSignal(int, str, int, int)

    def __init__(
        self,
        file_path: str,
        pipeline_config: list,
        stage: object,
        input_count: int,
        input_data: dict = None,
    ):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.stage = stage
        self.input_count = input_count
        self.input_data = input_data
        self.is_interrupted = False

    def _dict_to_structured_array(self, data_dict: dict):
        if not data_dict:
            return None

        count = data_dict.get("count", 0)
        if count == 0 and Dimensions.X in data_dict:
            count = len(data_dict[Dimensions.X])

        if count == 0:
            return None

        dtype_specs = []
        
        possible_fields = [
            (Dimensions.X, "X", "f8"),
            (Dimensions.Y, "Y", "f8"),
            (Dimensions.Z, "Z", "f8"),
            (Dimensions.INTENSITY, "Intensity", "u2"),
            (Dimensions.CLASSIFICATION, "Classification", "u1"),
            (Dimensions.RED, "Red", "u2"),
            (Dimensions.GREEN, "Green", "u2"),
            (Dimensions.BLUE, "Blue", "u2"),
        ]

        valid_fields = []
        for key, name, fmt in possible_fields:
            if key in data_dict and len(data_dict[key]) == count:
                dtype_specs.append((name, fmt))
                valid_fields.append((key, name))

        if not dtype_specs:
            return None

        structured_arr = np.zeros(count, dtype=dtype_specs)

        for key, name in valid_fields:
            structured_arr[name] = data_dict[key]

        return structured_arr

    def run(self):
        try:
            self.progress.emit(10)

            current_arrays = []

            if self.input_data:
                struct_arr = self._dict_to_structured_array(self.input_data)
                if struct_arr is not None:
                    current_arrays = [struct_arr]
            
            current_count = self.input_count
            total_stages = len(self.pipeline_config)
            last_pipeline = None

            for i, stage_conf in enumerate(self.pipeline_config):
                if self.is_interrupted:
                    break

                if isinstance(stage_conf, list):
                    payload = json.dumps(stage_conf)
                else:
                    payload = json.dumps([stage_conf])

                if current_arrays:
                    pipeline = pdal.Pipeline(payload, arrays=current_arrays)
                else:
                    pipeline = pdal.Pipeline(payload)

                pipeline.execute()

                current_arrays = pipeline.arrays
                last_pipeline = pipeline

                new_count = (
                    sum(len(arr) for arr in current_arrays) if current_arrays else 0
                )

                percent = int((i + 1) / total_stages * 80) + 10
                self.progress.emit(percent)

                tag = stage_conf.get("tag")
                if tag:
                    self.stage_progress.emit(i, tag, current_count, new_count)

                current_count = new_count

            if not last_pipeline or not last_pipeline.arrays:
                raise Exception("Pipeline produced no data.")

            arrays = np.concatenate(last_pipeline.arrays)
            metadata = last_pipeline.metadata

            extracted_data = {
                Dimensions.X: arrays[Dimensions.X.value],
                Dimensions.Y: arrays[Dimensions.Y.value],
                Dimensions.Z: arrays[Dimensions.Z.value],
                "count": len(arrays),
            }

            dims = arrays.dtype.names
            if Dimensions.INTENSITY.value in dims:
                extracted_data[Dimensions.INTENSITY] = arrays[Dimensions.INTENSITY.value]

            if (Dimensions.RED.value in dims and 
                Dimensions.GREEN.value in dims and 
                Dimensions.BLUE.value in dims):
                extracted_data[Dimensions.RED] = arrays[Dimensions.RED.value]
                extracted_data[Dimensions.GREEN] = arrays[Dimensions.GREEN.value]
                extracted_data[Dimensions.BLUE] = arrays[Dimensions.BLUE.value]

            if Dimensions.CLASSIFICATION.value in dims:
                extracted_data[Dimensions.CLASSIFICATION] = arrays[Dimensions.CLASSIFICATION.value]
            
            extracted_data["status"] = True
            
            self.progress.emit(100)
            self.finished.emit(
                self.file_path, extracted_data, metadata, self.stage, self.input_count
            )

        except Exception as e:
            import traceback
            error_details = f"Worker error : {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_details)