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
        self.logger.info(f"Worker thread started reading: {self.file_path}")
        result = self.reader.read(self.file_path)

        if result.get("status"):
            self.finished.emit(self.file_path)

        else:
            error_message = result.get("error", "Unknown reader error.")
            self.error.emit(error_message)

        self.logger.info(f"Worker thread finished for: {self.file_path}")