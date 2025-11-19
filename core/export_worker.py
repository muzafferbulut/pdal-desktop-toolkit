from PyQt5.QtCore import QObject, pyqtSignal
from data.writers import LasWriter
import traceback

class ExportWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, pipeline_config: list):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.writer = LasWriter()

    def run(self):
        try:
            result = self.writer.write(self.file_path, self.pipeline_config)

            if result.get("status"):
                count = result.get("count")
                msg = f"Export successful!\nFile: {self.file_path}\nPoints Written: {count}"
                self.finished.emit(msg)
            else:
                self.error.emit(result.get("error"))

        except Exception as e:
            self.error.emit(f"Critical Export Error: {str(e)}\n{traceback.format_exc()}")