from PyQt5.QtCore import QObject, pyqtSignal
import pdal
import json
import traceback

class StatsWorker(QObject):
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, pipeline_config: list):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config

    def run(self):
        try:
            self.progress.emit(10)
            json_str = json.dumps(self.pipeline_config)
            pipeline = pdal.Pipeline(json_str)
            
            self.progress.emit(-1)
            pipeline.execute()
            
            self.progress.emit(90)
            metadata = pipeline.metadata
            stats_data = metadata.get("metadata", {}).get("filters.stats", {})
            
            self.progress.emit(100)
            self.finished.emit(self.file_path, stats_data)

        except Exception as e:
            self.error.emit(f"Statistics calculation failed: {str(e)}\n{traceback.format_exc()}")