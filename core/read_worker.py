from PyQt5.QtCore import QObject, pyqtSignal
from data.data_handler import IDataReader
from core.logger import Logger
from typing import Dict, Any

class ReaderWorker(QObject):

    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path:str, reader:IDataReader, logger:Logger):
        super().__init__()
        self.file_path = file_path
        self.reader = reader
        self.logger = logger

    def run(self):
        try:
            self.progress.emit(10)
            result = self.reader.read(self.file_path)

            if result.get("status"):
                self.progress.emit(100)
                self.finished.emit(self.file_path)
            else:
                error_message = result.get("error", "Unknown reader error."),
                self.progress.emit(0)
                self.error.emit(error_message)
        except Exception as e:
            import traceback
            error_details = f"Worker thread critical error: {e}\n{traceback.format_exc()}"
            self.progress.emit(0)
            self.error.emit(f"{error_details}")