from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from core.database.workers import DbImportWorker, DbLoadWorker
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from core.layer_context import LayerContext
from core.read_worker import ReaderWorker
from core.merge_worker import MergeWorker
from typing import Dict, Optional, List
from core.logger import Logger
import numpy as np
import json
import os

class DataController(QObject):
    
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
        self.active_layer_path: Optional[str] = None
        
        # Thread referansları
        self.reader_thread = None
        self.merge_thread = None
        self.db_import_thread = None
        self.db_load_thread = None

    def get_layer(self, file_path: str) -> Optional[LayerContext]:
        return self._data_cache.get(file_path)

    def load_file(self, file_path: str):
        if not file_path: return

        file_name = os.path.basename(file_path)
        self.status_message.emit(f"Loading: {file_name}...", 0)
        self.progress_update.emit(-1)

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
        self.reader_thread.start()

    def _on_load_finished(self, file_path: str, bounds: dict, full_meta: dict, summary_meta: dict, sample_data: dict):
        file_name = os.path.basename(file_path)
        context = LayerContext(file_path, summary_meta, full_meta)
        context.current_render_data = sample_data
        context.bounds = bounds
        self._data_cache[file_path] = context
        self.active_layer_path = file_path

        self.status_message.emit(f"'{file_name}' loaded successfully!", 5000)
        self.file_loaded.emit(file_path, file_name)
        self.progress_update.emit(100)

    def _detect_srid(self, layer: LayerContext) -> str:
        if not layer or not layer.full_metadata:
            return "4326"

        meta_str = json.dumps(layer.full_metadata).upper()
        
        if "3857" in meta_str or "GOOGLE" in meta_str or "PSEUDO-MERCATOR" in meta_str:
            return "3857"
        elif "4326" in meta_str or "WGS 84" in meta_str:
            return "4326"
            
        return "4326"

    def export_active_layer_to_db(self, conn_info, schema, table):
        if not self.active_layer_path: return

        layer = self._data_cache.get(self.active_layer_path)

        if not layer or layer.current_render_data is None: return

        target_srid = self._detect_srid(layer)

        raw_data = layer.current_render_data
        data_to_write = None

        if isinstance(raw_data, dict):
            valid_items = []
            for k, v in raw_data.items():
                if hasattr(v, 'dtype'):
                    name = k.value if hasattr(k, 'value') else str(k)
                    valid_items.append((name, v))
            
            if not valid_items: return
            dtype = [(name, v.dtype) for name, v in valid_items]
            data_to_write = np.empty(len(valid_items[0][1]), dtype=dtype)
            for name, v in valid_items:
                data_to_write[name] = v
        else:
            if hasattr(raw_data, "to_records"):
                 data_to_write = raw_data.to_records(index=False)
            else:
                 return

        source_name = os.path.basename(self.active_layer_path)
        self.logger.info(f"Exporting '{source_name}' to DB with SRID: {target_srid}")

        self.db_import_thread = DbImportWorker(
            data_to_write, conn_info, schema, table, source_name, 
            is_array=True, srid=target_srid
        )
        self._connect_db_signals(self.db_import_thread)
        self.db_import_thread.start()

    def import_layer_to_db(self, source_path, conn_info, schema, table):
        source_name = os.path.basename(source_path)
        
        layer = self._data_cache.get(source_path)
        detected_srid = self._detect_srid(layer) if layer else "4326"

        self.logger.info(f"Importing file '{source_name}' to DB with detected SRID: {detected_srid}")
        
        self.db_import_thread = DbImportWorker(
            source_path, conn_info, schema, table, source_name, 
            is_array=False, srid=detected_srid
        )
        self._connect_db_signals(self.db_import_thread)
        self.db_import_thread.start()

    def load_from_database(self, conn_info, schema, table, where=""):
        self.db_load_thread = DbLoadWorker(conn_info, schema, table, where)
        self.db_load_thread.signals.progress.connect(self.progress_update.emit)
        self.db_load_thread.signals.finished.connect(self._on_db_load_finished)
        self.db_load_thread.signals.error.connect(self._on_worker_error)
        self.db_load_thread.start()

    def _on_db_load_finished(self, payload):
        unique_id = f"DB://{payload['conn']['host']}/{payload['table_info']}"
        if payload.get('query_filter'): 
            unique_id += f"?{payload['query_filter']}"

        table_parts = payload['table_info'].split('.')
        schema = table_parts[0] if len(table_parts) > 1 else "public"
        table = table_parts[-1]

        db_reader_config = {
            "type": "readers.pgpointcloud",
            "connection": f"host={payload['conn']['host']} port={payload['conn']['port']} "
                          f"dbname={payload['conn']['dbname']} user={payload['conn']['user']} "
                          f"password={payload['conn']['password']}",
            "schema": schema,
            "table": table,
            "column": "patch",
            "where": payload.get('query_filter', "")
        }
        summary_metadata = payload.get("summary_metadata", {})
        raw_metadata = payload.get("raw_metadata", {})

        context = LayerContext(
            unique_id, 
            summary_metadata,
            raw_metadata,
            reader_config=db_reader_config
        )

        context.current_render_data = payload['data']
        context.bounds = payload['bounds']
        context.is_database = True

        self._data_cache[unique_id] = context
        self.active_layer_path = unique_id
        
        self.file_loaded.emit(unique_id, payload['table_info'])
        self.status_message.emit("Layer loaded from Database.", 3000)
        self.progress_update.emit(100)

    def merge_layers(self, file_paths: List[str], output_name="Merged"):
        if not file_paths: return
        self.status_message.emit(f"Merging {len(file_paths)} layers...", 0)
        self.progress_update.emit(-1)

        self.merge_thread = QThread()
        self.merge_worker = MergeWorker(file_paths, output_name=output_name)
        self.merge_worker.moveToThread(self.merge_thread)
        
        self.merge_thread.started.connect(self.merge_worker.run)
        self.merge_worker.finished.connect(self._on_load_finished)
        self.merge_worker.error.connect(self._on_worker_error)
        self.merge_worker.progress.connect(self.progress_update.emit)
        
        self.merge_worker.finished.connect(self.merge_thread.quit)
        self.merge_worker.finished.connect(self.merge_worker.deleteLater)
        self.merge_thread.finished.connect(self.merge_thread.deleteLater)
        self.merge_thread.start()

    def remove_layer(self, file_path: str):
        if file_path in self._data_cache:
            del self._data_cache[file_path]
            if self.active_layer_path == file_path:
                self.active_layer_path = None
            self.file_removed.emit(file_path)

    def _connect_db_signals(self, worker):
        worker.signals.progress.connect(self.progress_update.emit)
        worker.signals.error.connect(self._on_worker_error)
        worker.signals.finished.connect(lambda msg: self.status_message.emit(msg, 5000))

    def _on_worker_error(self, error_msg: str):
        self.progress_update.emit(0)
        self.log_message.emit("ERROR", f"Data operation failed: {error_msg}") 
        self.status_message.emit("Operation failed. Check logs for details.", 5000)