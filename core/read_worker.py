from PyQt5.QtCore import QObject, pyqtSignal
from data.data_handler import IDataReader
from core.logger import Logger

class ReaderWorker(QObject):

    finished = pyqtSignal(str, dict, dict, dict, dict)
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
                self.progress.emit(25)
                self.bounds = self.reader.get_bounds()
                self.progress.emit(47)
                self.full_metadata = self.reader.get_metadata()
                self.progress.emit(60)
                self.summary_metadata = self.reader.get_summary_metadata(self.full_metadata)
                self.progress.emit(75)
                self.sample_data = self.reader.get_sample_data()
                self.progress.emit(100)
                self.finished.emit(self.file_path, self.bounds, self.full_metadata, self.summary_metadata, self.sample_data)
            else:
                error_message = result.get("error", "Unknown reader error."),
                self.progress.emit(0)
                self.error.emit(error_message)
        except Exception as e:
            import traceback
            error_details = f"Worker thread critical error: {e}\n{traceback.format_exc()}"
            self.progress.emit(0)
            self.error.emit(f"{error_details}")