from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from core.layer_context import LayerContext
from core.read_worker import ReaderWorker
from core.merge_worker import MergeWorker
from typing import Dict, Optional, List
from core.logger import Logger
import os

class DataController(QObject):
    """
    Veri yükleme, saklama (cache), silme ve birleştirme işlemlerini yönetir.
    """
    file_loaded = pyqtSignal(str, str) # file_path, file_name
    file_removed = pyqtSignal(str)     # file_path
    progress_update = pyqtSignal(int)
    status_message = pyqtSignal(str, int)
    log_message = pyqtSignal(str, str) # level, message

    def __init__(self, reader: IBasicReader, extractor: IMetadataExtractor, sampler: IDataSampler, logger: Logger):
        super().__init__()
        self.basic_reader = reader
        self.metadata_extractor = extractor
        self.data_sampler = sampler
        self.logger = logger
        
        self._data_cache: Dict[str, LayerContext] = {}
        
        self.reader_thread = None
        self.merge_thread = None

    def get_layer(self, file_path: str) -> Optional[LayerContext]:
        return self._data_cache.get(file_path)

    def load_file(self, file_path: str):
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        self.status_message.emit(f"Loading: {file_name}...", 0)
        self.progress_update.emit(10)

        if self.reader_thread is not None:
            try:
                if self.reader_thread.isRunning():
                    self.reader_thread.quit()
                    self.reader_thread.wait()
            except RuntimeError:
                self.reader_thread = None

        self.reader_thread = QThread()
        self.reader_worker = ReaderWorker(
            file_path=file_path,
            basic_reader=self.basic_reader,
            metadata_extractor=self.metadata_extractor,
            data_sampler=self.data_sampler,
            logger=self.logger
        )
        self.reader_worker.moveToThread(self.reader_thread)
        
        self.reader_thread.started.connect(self.reader_worker.run)
        self.reader_worker.finished.connect(self._on_load_finished)
        self.reader_worker.error.connect(self._on_worker_error)
        self.reader_worker.progress.connect(self.progress_update.emit)
        
        self.reader_worker.finished.connect(self.reader_thread.quit)
        self.reader_worker.finished.connect(self.reader_worker.deleteLater)
        self.reader_thread.finished.connect(self.reader_thread.deleteLater)
        self.reader_thread.finished.connect(self._cleanup_reader_thread)
        self.reader_thread.start()

    def merge_layers(self, file_paths: List[str], output_name="Merged"):
        """
        Seçilen katmanları birleştirmek için MergeWorker'ı başlatır.
        """
        if not file_paths:
            return
        
        if output_name in self._data_cache:
            self.remove_layer(output_name)

        self.status_message.emit(f"Merging {len(file_paths)} layers...", 0)
        self.progress_update.emit(10)

        if self.merge_thread is not None:
            try:
                if self.merge_thread.isRunning():
                    self.merge_thread.quit()
                    self.merge_thread.wait()
            except RuntimeError:
                pass

        self.merge_thread = QThread()
        self.merge_worker = MergeWorker(file_paths, output_name=output_name)
        
        self.merge_worker.moveToThread(self.merge_thread)
        self.merge_thread.started.connect(self.merge_worker.run)
        self.merge_worker.finished.connect(self._on_load_finished)
        self.merge_worker.error.connect(self._on_worker_error)
        self.merge_worker.progress.connect(self.progress_update.emit)
        
        # Temizlik
        self.merge_worker.finished.connect(self.merge_thread.quit)
        self.merge_worker.finished.connect(self.merge_worker.deleteLater)
        self.merge_thread.finished.connect(self.merge_thread.deleteLater)
        self.merge_thread.finished.connect(self._cleanup_merge_thread)
        self.merge_thread.start()

    def _on_load_finished(self, file_path: str, bounds: dict, full_meta: dict, summary_meta: dict, sample_data: dict):
        """
        Hem ReaderWorker hem de MergeWorker başarıyla tamamlandığında çağrılır.
        """
        file_name = os.path.basename(file_path)
        
        context = LayerContext(file_path, summary_meta, full_meta)
        context.current_render_data = sample_data
        context.bounds = bounds
        self._data_cache[file_path] = context

        if file_path == "Merged":
             self.status_message.emit("Layers merged successfully!", 5000)
             self.log_message.emit("INFO", "Layers merged into 'Merged' successfully.")
        else:
             self.status_message.emit(f"'{file_name}' loaded successfully!", 5000)
             self.log_message.emit("INFO", f"File '{file_name}' loaded successfully.")
        
        self.file_loaded.emit(file_path, file_name)
        self.progress_update.emit(100)

    def remove_layer(self, file_path: str):
        if file_path in self._data_cache:
            del self._data_cache[file_path]
            file_name = os.path.basename(file_path)
            self.log_message.emit("INFO", f"File '{file_name}' removed from cache.")
            self.file_removed.emit(file_path)
        else:
            self.log_message.emit("WARNING", f"File not found in cache: {file_path}")

    def _on_worker_error(self, error_msg: str):
        self.progress_update.emit(0)
        self.status_message.emit("Error: Operation failed.", 5000)
        self.log_message.emit("ERROR", error_msg)

    def _cleanup_reader_thread(self):
        self.reader_thread = None

    def _cleanup_merge_thread(self):
        self.merge_thread = None