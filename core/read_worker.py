from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from PyQt5.QtCore import QObject, pyqtSignal
from core.logger import Logger
from typing import Union
import traceback


class ReaderWorker(QObject):

    finished = pyqtSignal(str, dict, dict, dict, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(
        self,
        file_path: str,
        basic_reader: IBasicReader,
        metadata_extractor: IMetadataExtractor,
        data_sampler: IDataSampler,
        logger: Logger,
    ):

        super().__init__()
        self.file_path = file_path
        self.basic_reader = basic_reader
        self.metadata_extractor = metadata_extractor
        self.data_sampler = data_sampler
        self.logger = logger

    def run(self):
        try:
            self.progress.emit(10)
            self.progress.emit(-1)
            result = self.basic_reader.read(self.file_path)
            if result.get("status"):
                self.progress.emit(25)
                self.bounds = self.data_sampler.get_bounds(self.file_path)
                self.progress.emit(47)
                self.full_metadata = self.metadata_extractor.get_metadata(
                    self.file_path
                )
                self.progress.emit(60)
                self.summary_metadata = self.metadata_extractor.get_summary_metadata(
                    self.full_metadata
                )
                self.progress.emit(75)
                self.sample_data = self.data_sampler.get_sample_data()
                self.progress.emit(100)
                self.finished.emit(
                    self.file_path,
                    self.bounds,
                    self.full_metadata,
                    self.summary_metadata,
                    self.sample_data,
                )
            else:
                error_message = result.get("error", "Unknown reader error.")
                self.progress.emit(0)
                self.error.emit(error_message)
        except Exception as e:
            import traceback

            error_details = (
                f"Worker thread critical error: {e}\n{traceback.format_exc()}"
            )
            self.progress.emit(0)
            self.error.emit(f"{error_details}")
