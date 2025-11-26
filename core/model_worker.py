from PyQt5.QtCore import QObject, pyqtSignal
import pdal
import json
import traceback

class ModelWorker(QObject):
    finished = pyqtSignal(str, str) 
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, pipeline_config: list, output_path: str):
        super().__init__()
        self.pipeline_config = pipeline_config
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(10)
            json_str = json.dumps(self.pipeline_config)
            pipeline = pdal.Pipeline(json_str)
            self.progress.emit(-1)
            count = pipeline.execute()
            self.progress.emit(100)
            msg = f"Elevation Model generated successfully.\nProcessed {count} points."
            self.finished.emit(msg, self.output_path) 

        except Exception as e:
            self.error.emit(f"Model generation failed: {str(e)}\n{traceback.format_exc()}")