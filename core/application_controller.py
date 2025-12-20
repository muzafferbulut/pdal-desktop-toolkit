from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from core.controllers.process_controller import ProcessController
from core.controllers.data_controller import DataController
from core.controllers.io_controller import IOController
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional
from core.enums import Dimensions
from core.logger import Logger
import os

class ApplicationController(QObject):
    # statistics
    stats_ready_signal = pyqtSignal(str, dict)

    # UI Güncellemeleri
    progress_update_signal = pyqtSignal(int)
    log_error_signal = pyqtSignal(str)
    log_info_signal = pyqtSignal(str)
    ui_status_message_signal = pyqtSignal(str, int)
    
    # Görünüm Sinyalleri
    render_data_signal = pyqtSignal(str, str, bool) # (filepath, style_name, reset_view)
    draw_bbox_signal = pyqtSignal(dict) # (bounds)
    clear_views_signal = pyqtSignal()
    
    # Metadata Sinyalleri
    update_metadata_signal = pyqtSignal(str, dict) 
    clear_metadata_signal = pyqtSignal()
    
    # Katman Sinyalleri
    file_load_success_signal = pyqtSignal(str, str) 
    file_removed_signal = pyqtSignal(str) 
    stage_added_signal = pyqtSignal(str, str, str) 
    
    # Export Sinyalleri
    export_success_signal = pyqtSignal(str) 

    def __init__(self, 
                 basic_reader: IBasicReader, 
                 metadata_extractor: IMetadataExtractor, 
                 data_sampler: IDataSampler, 
                 logger: Logger, 
                 parent=None):
        
        super().__init__(parent)
        self.logger = logger
        self.data_controller = DataController(basic_reader, metadata_extractor, data_sampler, logger)
        self.process_controller = ProcessController(self.data_controller, logger)
        self.io_controller = IOController(self.data_controller, logger)

        self._connect_signals()

    def _connect_signals(self):
        # --- DataController Sinyalleri ---
        self.data_controller.file_loaded.connect(self._on_file_loaded)
        self.data_controller.file_removed.connect(self._on_layer_removed) 
        self.data_controller.progress_update.connect(self.progress_update_signal)
        self.data_controller.status_message.connect(self.ui_status_message_signal)
        
        # --- ProcessController Sinyalleri ---
        self.process_controller.layer_updated.connect(self._refresh_layer_view) 
        self.process_controller.stage_added.connect(self.stage_added_signal)
        self.process_controller.stats_ready.connect(self.stats_ready_signal)
        self.process_controller.progress_update.connect(self.progress_update_signal)
        self.process_controller.status_message.connect(self.ui_status_message_signal)
        
        # --- IOController Sinyalleri ---
        self.io_controller.export_success.connect(self.export_success_signal)
        self.io_controller.progress_update.connect(self.progress_update_signal)
        self.io_controller.status_message.connect(self.ui_status_message_signal)

        # --- Loglama Sinyalleri ---
        for controller in [self.data_controller, self.process_controller, self.io_controller]:
            controller.log_message.connect(self._handle_log_message)

    def _handle_log_message(self, level: str, message: str):
        if level == "ERROR":
            self.log_error_signal.emit(message)
        else:
            self.log_info_signal.emit(message)

    def start_file_loading(self, file_path: str):
        self.data_controller.load_file(file_path)

    def start_merge_process(self, file_paths: list):
        self.data_controller.merge_layers(file_paths)

    def handle_remove_layer(self, file_path: str):
        self.data_controller.remove_layer(file_path)

    def start_filter_process(self, file_path: str, tool_name: str, user_params: Dict[str, Any]):
        self.process_controller.apply_filter(file_path, tool_name, user_params)

    def handle_remove_stage(self, file_path: str, stage_index: int):
        self.process_controller.remove_stage(file_path, stage_index)

    def start_stats_process(self, file_path: str):
        self.process_controller.calculate_statistics(file_path)

    def start_model_process(self, file_path: str, params: dict):
        self.process_controller.generate_model(file_path, params)

    def start_export_process(self, file_path: str, save_path: str):
        self.io_controller.export_layer(file_path, save_path)

    def save_pipeline(self, file_path: str, save_path: str):
        self.io_controller.save_pipeline(file_path, save_path)

    def save_full_metadata(self, file_path: str, save_path: str):
        self.io_controller.save_metadata(file_path, save_path)

    def get_layer_data(self, file_path: str) -> Optional[Any]:
        context = self.data_controller.get_layer(file_path)
        return context.current_render_data if context else None

    def handle_single_click(self, file_path: str, file_name: str):
        context = self.data_controller.get_layer(file_path)
        if not context:
            self.clear_metadata_signal.emit()
            return

        summary_metadata = context.metadata
        if summary_metadata.get("status"):
            self.update_metadata_signal.emit(file_name, summary_metadata)
        else:
            self.logger.error(f"Metadata read error: {file_name}")
            self.clear_metadata_signal.emit()

    def handle_double_click(self, file_path: str, file_name: str):
        context = self.data_controller.get_layer(file_path)
        if not context: return

        bounds = context.bounds
        if bounds and bounds.get("status"):
            self.draw_bbox_signal.emit(bounds)
            self.logger.info(f"'{file_name}' bounds drawn on map.")

        if context.current_render_data is not None:
            current_style = getattr(context, "active_style", Dimensions.Z)
            self.render_data_signal.emit(file_path, current_style, True) 
            self.logger.info(f"'{file_name}' rendered in 3D view.")

    def handle_style_change(self, file_path: str, style_name: str):
        context = self.data_controller.get_layer(file_path)
        
        if not context or context.current_render_data is None: return

        data = context.current_render_data
        file_name = os.path.basename(file_path)

        if style_name == Dimensions.INTENSITY and Dimensions.INTENSITY not in data:
            self.logger.warning(f"'{file_name}' does not contain Intensity channel.")
            return
        
        context.active_style = style_name
        self.render_data_signal.emit(file_path, style_name, False) 
        self.logger.info(f"'{file_name}' style updated to '{style_name}'.")

    def handle_zoom_to_bbox(self, file_path: str):
        context = self.data_controller.get_layer(file_path)
        if context and context.bounds and context.bounds.get("status"):
            self.draw_bbox_signal.emit(context.bounds)
            self.logger.info(f"Zoomed to '{os.path.basename(file_path)}' bounds.")

    def _on_layer_removed(self, file_path: str):
        self.file_removed_signal.emit(file_path)
        self.clear_views_signal.emit()
        self.clear_metadata_signal.emit()
        self.ui_status_message_signal.emit("Layer removed.", 3000)

    def _refresh_layer_view(self, file_path: str):
        context = self.data_controller.get_layer(file_path)
        if context:
            current_style = getattr(context, "active_style", Dimensions.Z)
            self.render_data_signal.emit(file_path, current_style, False)

    def start_batch_process(self, file_path: str, stages: list):
        self.process_controller.apply_batch_process(file_path, stages)

    def _on_file_loaded(self, file_path:str, file_name:str):
        self.file_load_success_signal.emit(file_path, file_name)
        self.handle_double_click(file_path, file_name)