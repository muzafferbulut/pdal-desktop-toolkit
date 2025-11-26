from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler 
from core.layer_context import LayerContext, PipelineStage
from data.writers import PipelineWriter, MetadataWriter
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from core.pipeline_builder import PipelineBuilder
from core.filter_worker import FilterWorker
from core.export_worker import ExportWorker
from core.model_worker import ModelWorker
from core.stats_worker import StatsWorker
from core.merge_worker import MergeWorker
from core.read_worker import ReaderWorker
from typing import Dict, Any, Optional
from core.logger import Logger
import os

class ApplicationController(QObject):
    """
    Manages all application business logic, data caching, and asynchronous workflows.
    It processes requests from MainWindow and notifies the UI via signals.
    """
    
    stats_ready_signal = pyqtSignal(str, dict)

    # --- Signals from Controller to MainWindow ---
    progress_update_signal = pyqtSignal(int)
    log_error_signal = pyqtSignal(str)
    log_info_signal = pyqtSignal(str)
    ui_status_message_signal = pyqtSignal(str, int)
    
    # View Signals
    render_data_signal = pyqtSignal(dict, str, bool) # (sample_data, style_name, reset_view)
    draw_bbox_signal = pyqtSignal(dict) # (bounds)
    clear_views_signal = pyqtSignal()
    
    # Metadata Signals
    update_metadata_signal = pyqtSignal(str, dict) # (file_name, summary_metadata)
    clear_metadata_signal = pyqtSignal()
    
    # Layer/Pipeline Signals
    file_load_success_signal = pyqtSignal(str, str) # (file_path, file_name)
    file_removed_signal = pyqtSignal(str) # (file_path)
    stage_added_signal = pyqtSignal(str, str, str) # (file_path, stage_name, stage_details)
    
    # Export/Save Signals
    export_success_signal = pyqtSignal(str) # (message)

    def __init__(self, 
                 basic_reader: IBasicReader, 
                 metadata_extractor: IMetadataExtractor, 
                 data_sampler: IDataSampler, 
                 logger: Logger, 
                 parent=None):
        super().__init__(parent)

        self.basic_reader = basic_reader
        self.metadata_extractor = metadata_extractor
        self.data_sampler = data_sampler
        self.logger = logger
        self._data_cache: Dict[str, LayerContext] = {}

        self.reader_thread = None
        self.filter_thread = None
        self.export_thread = None
        self.stats_thread = None

    def start_merge_process(self, file_paths: list):
        if not file_paths:
            return
        
        virtual_name = "Merged"
        if virtual_name in self._data_cache:
            self.handle_remove_layer(virtual_name)

        self.ui_status_message_signal.emit(f"Merging {len(file_paths)} layers...", 0)
        self.progress_update_signal.emit(10)

        if hasattr(self, 'merge_thread') and self.merge_thread is not None:
            if self.merge_thread.isRunning():
                self.merge_thread.quit()
                self.merge_thread.wait()

        self.merge_thread = QThread()
        self.merge_worker = MergeWorker(file_paths, output_name=virtual_name)
        
        self.merge_worker.moveToThread(self.merge_thread)
        self.merge_thread.started.connect(self.merge_worker.run)
    
        self.merge_worker.finished.connect(self._handle_reader_success)
        
        self.merge_worker.error.connect(self._handle_worker_error)
        self.merge_worker.progress.connect(self.progress_update_signal.emit)
        
        self.merge_worker.finished.connect(self.merge_thread.quit)
        self.merge_worker.finished.connect(self.merge_worker.deleteLater)
        self.merge_thread.finished.connect(self.merge_thread.deleteLater)
        
        self.merge_thread.start()

    def _check_and_log_layer(self, file_path: str, operation: str) -> Optional[LayerContext]:
        """Helper method to check layer existence before any operation."""
        context = self._data_cache.get(file_path)
        if not context:
            file_name = os.path.basename(file_path)
            self.logger.warning(f"Operation ignored: '{file_name}' not found in cache. ({operation})")
        return context

    def _handle_worker_error(self, error_message: str):
        """Handles error signals coming from all workers."""
        self.progress_update_signal.emit(0)
        self.ui_status_message_signal.emit("Error: Operation failed.", 5000)
        self.log_error_signal.emit(error_message)

    def start_file_loading(self, file_path: str):
        """Processes file open request from MainWindow."""
        if not file_path:
            self.logger.warning("No file selected.")
            return

        file_name = os.path.basename(file_path)
        self.ui_status_message_signal.emit(f"Loading: {file_name}...", 0)
        self.progress_update_signal.emit(10)

        try:
            if hasattr(self, "reader_thread") and self.reader_thread is not None:
                if self.reader_thread.isRunning():
                    self.reader_thread.quit()
                    self.reader_thread.wait()
        except RuntimeError:
            self.logger.warning("Previous reader thread object was already deleted (RuntimeError caught).")

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
        
        self.reader_worker.finished.connect(self._handle_reader_success)
        self.reader_worker.error.connect(self._handle_worker_error)
        self.reader_worker.progress.connect(self.progress_update_signal.emit)

        self.reader_worker.finished.connect(self.reader_thread.quit)
        self.reader_worker.error.connect(self.reader_thread.quit)
        self.reader_worker.finished.connect(self.reader_worker.deleteLater)
        self.reader_thread.finished.connect(self.reader_thread.deleteLater)
        
        self.reader_thread.start()

    def _handle_reader_success(self, file_path:str, bounds:dict, full_metadata:dict, summary_metadata:dict, sample_data:dict):       
        self.progress_update_signal.emit(100)
        file_name = os.path.basename(file_path)
        self.ui_status_message_signal.emit(f"'{file_name}' loaded successfully!", 5000)
        self.logger.info(f"File '{file_name}' loaded successfully.")
        context = LayerContext(file_path, summary_metadata, full_metadata)
        context.current_render_data = sample_data
        context.bounds = bounds
        self._data_cache[file_path] = context
        self.file_load_success_signal.emit(file_path, file_name)

    def handle_single_click(self, file_path: str, file_name: str):
        context = self._check_and_log_layer(file_path, "Metadata Display")
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
        context = self._check_and_log_layer(file_path, "3D/Map Visualization")
        if not context:
            return

        bounds = context.bounds
        if bounds and bounds.get("status"):
            self.draw_bbox_signal.emit(bounds)
            self.logger.info(f"'{file_name}' bounds drawn on map.")
        else:
            self.logger.warning(f"Spatial bounds not found: {file_name}")

        sample_data = context.current_render_data
        if sample_data and "x" in sample_data:
            current_style = getattr(context, "active_style", "Elevation")
            self.render_data_signal.emit(sample_data, current_style, True)
            self.logger.info(f"'{file_name}' rendered in 3D view.")
        else:
            error_msg = sample_data.get("error", "Unknown error") if sample_data else "Data is empty"
            self.logger.error(f"3D Render Failed: '{file_name}': {error_msg}")

    def handle_style_change(self, file_path: str, style_name: str):
        context = self._check_and_log_layer(file_path, "Style Change")
        if not context or not context.current_render_data:
            return

        data = context.current_render_data
        file_name = os.path.basename(file_path)

        if style_name == "Intensity" and "intensity" not in data:
            self.logger.warning(f"'{file_name}' does not contain Intensity channel.")
            return
        if style_name == "RGB" and "red" not in data:
            self.logger.warning(f"'{file_name}' does not contain RGB channels.")
            return
        if style_name == "Classification" and "classification" not in data:
            self.logger.warning(f"'{file_name}' does not contain Classification channel.")
            return
        
        context.active_style = style_name
        self.render_data_signal.emit(data, style_name, False)
        self.logger.info(f"'{file_name}' style updated to '{style_name}'.")

    def handle_zoom_to_bbox(self, file_path: str):
        context = self._check_and_log_layer(file_path, "BBox Zoom")
        if not context:
            return
        
        bounds = context.bounds
        if not bounds or not bounds.get("status"):
            self.logger.warning(f"Spatial bounds not found: {os.path.basename(file_path)}")
            return
        
        self.draw_bbox_signal.emit(bounds)
        self.logger.info(f"Zoomed to '{os.path.basename(file_path)}' bounds.")

    def handle_remove_layer(self, file_path: str):
        file_name = os.path.basename(file_path)
        
        if file_path in self._data_cache:
            del self._data_cache[file_path]
            self.logger.info(f"File '{file_name}' removed from data cache.")
        else:
            self.logger.warning(f"File to remove '{file_name}' not found in cache.")

        self.file_removed_signal.emit(file_path) 
        self.clear_views_signal.emit() 
        self.clear_metadata_signal.emit() 
        self.logger.info(f"Views cleared and '{file_name}' removed from UI.")

    def start_filter_process(self, file_path: str, tool_name: str, user_params: Dict[str, Any]):
        context = self._check_and_log_layer(file_path, "Applying Filter")
        if not context:
            return
        
        new_stage = PipelineBuilder.create_stage(tool_name, user_params)
        
        if not new_stage:
            self.logger.error(f"Could not create stage for '{tool_name}'.")
            return
        
        base_pipeline = context.get_full_pipeline_json()
        base_pipeline.append(new_stage.config)
        self.logger.info(f"Filter Running: {new_stage.display_text}...")

        self._start_filter_worker(file_path, base_pipeline, new_stage)

    def _start_filter_worker(self, file_path: str, pipeline_config: list, stage_object: Optional[PipelineStage] = None):        
        self.progress_update_signal.emit(1)
        self.ui_status_message_signal.emit("Applying filter...", 0)
        
        if hasattr(self, 'filter_thread') and self.filter_thread is not None:
            try:
                if self.filter_thread.isRunning():
                    self.logger.warning("New process started before the previous one finished, waiting...")
                    self.filter_thread.quit()
                    self.filter_thread.wait()
            except RuntimeError:
                pass

        context = self._data_cache.get(file_path)
        input_count = 0
        if context:
            if not context.stages:
                try:
                    input_count = int(context.metadata.get("points", 0))
                except:
                    input_count = context.current_render_data.get("count", 0) if context.current_render_data else 0
            elif context.current_render_data:
                input_count = context.current_render_data.get("count", 0)

        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(file_path, pipeline_config, stage_object, input_count)
        
        self.filter_worker.moveToThread(self.filter_thread)
        self.filter_thread.started.connect(self.filter_worker.run)
        
        self.filter_worker.finished.connect(self._handle_filter_success) 
        self.filter_worker.error.connect(self._handle_worker_error)      
        self.filter_worker.progress.connect(self.progress_update_signal.emit)
        
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)
        self.filter_thread.start()

    def _handle_filter_success(self, file_path: str, result_data: dict, stage_object: Optional[PipelineStage], input_count: int):
        self.progress_update_signal.emit(100)
        self.ui_status_message_signal.emit("Operation completed.", 3000)

        if file_path not in self._data_cache:
            return
        
        context: LayerContext = self._data_cache[file_path]        
        context.current_render_data = result_data

        output_count = result_data.get("count", 0)

        if stage_object:
            context.add_stage(stage_object)
            
            clean_details = stage_object.display_text.replace(stage_object.name, "").strip().strip("()")
            
            self.stage_added_signal.emit(file_path, stage_object.name, clean_details)
            
            log_msg = (
                f"Stage added: {stage_object.name}\n"
                f"   Points: {input_count:,} -> {output_count:,}\n"
            )
            self.logger.info(log_msg)
        
        else:
            self.logger.info(f"Pipeline refreshed. Current Points: {output_count:,}")

        current_style = getattr(context, "active_style", "Elevation")
        self.render_data_signal.emit(result_data, current_style, False)

    def handle_remove_stage(self, file_path: str, stage_index: int):
        context = self._check_and_log_layer(file_path, "Removing Stage")
        if not context:
            return

        if 0 <= stage_index < len(context.stages):
            stage_name = context.stages[stage_index].name
        else:
            self.logger.warning(f"Operation failed: Stage index {stage_index} is out of bounds.")
            return
        
        context.remove_stage(stage_index)
        self.logger.info(f"Stage '{stage_name}' (index {stage_index}) removed. Recalculating pipeline...")

        new_pipeline_config = context.get_full_pipeline_json()
        self._start_filter_worker(file_path, new_pipeline_config, stage_object=None)

    def start_export_process(self, file_path: str, save_path: str):
        context = self._check_and_log_layer(file_path, "Exporting")
        if not context:
            return
        
        if not save_path:
            self.logger.warning("Export path not selected.")
            return

        file_name = os.path.basename(file_path)
        pipeline_config = context.get_full_pipeline_json()
        
        self.logger.info(f"Starting export: '{file_name}' -> '{save_path}'...")
        self._start_export_worker(save_path, pipeline_config)
    
    def _start_export_worker(self, save_path: str, pipeline_config: list):        
        self.progress_update_signal.emit(1)
        self.ui_status_message_signal.emit("Exporting layer...", 0)

        if hasattr(self, 'export_thread') and self.export_thread is not None:
            if self.export_thread.isRunning():
                self.export_thread.quit()
                self.export_thread.wait()

        self.export_thread = QThread()
        self.export_worker = ExportWorker(save_path, pipeline_config)
        
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        
        self.export_worker.finished.connect(self._handle_export_success)
        self.export_worker.error.connect(self._handle_worker_error)

        self.export_worker.progress.connect(self.progress_update_signal.emit)
        
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        
        self.export_thread.start()

    def _handle_export_success(self, message: str):
        self.progress_update_signal.emit(100)
        self.ui_status_message_signal.emit("Export completed.", 5000)
        self.logger.info("Export operation completed successfully.")

    def save_pipeline(self, file_path: str, save_path: str):
        context = self._check_and_log_layer(file_path, "Saving Pipeline")
        if not context:
            return
            
        pipeline_json = context.get_full_pipeline_json()
        writer = PipelineWriter()
        result = writer.write(save_path, pipeline_json)

        if result.get("status"):
            self.logger.info(f"Pipeline saved: {save_path}")
            self.ui_status_message_signal.emit("Pipeline configuration saved.", 3000)
        else:
            error_msg = result.get("error")
            self.logger.error(f"Pipeline save failed: {error_msg}")
            self.log_error_signal.emit(f"Could not save pipeline:\n{error_msg}")

    def save_full_metadata(self, file_path: str, save_path: str):
        context = self._check_and_log_layer(file_path, "Saving Metadata")
        if not context:
            return
        
        file_name = os.path.basename(file_path)
        metadata_to_save = getattr(context, "full_metadata", None)

        if not metadata_to_save:
            self.logger.warning(f"Full metadata not available for '{file_name}'. Saving summary.")
            metadata_to_save = context.metadata

        writer = MetadataWriter()
        result = writer.write(save_path, metadata_to_save)

        if result.get("status"):
            self.logger.info(f"Metadata saved: {save_path}")
            self.ui_status_message_signal.emit("Metadata saved successfully.", 3000)
        else:
            error_msg = result.get("error")
            self.logger.error(f"Metadata save failed: {error_msg}")
            self.log_error_signal.emit(f"Could not save metadata:\n{error_msg}")

    def start_model_process(self, file_path: str, params: dict):
        context = self._check_and_log_layer(file_path, "Generating Model")
        if not context:
            return

        save_path = params.get("filename")
        resolution = params.get("resolution")
        output_type = params.get("output_type")
        pipeline_config = context.get_full_pipeline_json()
        writer_stage = {
            "type": "writers.gdal",
            "filename": save_path,
            "resolution": resolution,
            "output_type": output_type,
            "radius": resolution * 1.414
        }

        if output_type == "idw":
            writer_stage["power"] = 2.0

        pipeline_config.append(writer_stage)

        self.ui_status_message_signal.emit("Generating Elevation Model...", 0)
        self.progress_update_signal.emit(10)
        self.logger.info(f"Starting model generation ({output_type.upper()}) -> {save_path}")

        if hasattr(self, 'model_thread') and self.model_thread is not None:
            if self.model_thread.isRunning():
                self.model_thread.quit()
                self.model_thread.wait()

        self.model_thread = QThread()
        self.model_worker = ModelWorker(pipeline_config, save_path) 
        self.model_worker.moveToThread(self.model_thread)
        self.model_thread.started.connect(self.model_worker.run)
        self.model_worker.finished.connect(self._handle_model_success) 
        self.model_worker.error.connect(self._handle_worker_error)
        self.model_worker.progress.connect(self.progress_update_signal.emit)
        self.model_worker.finished.connect(self.model_thread.quit)
        self.model_worker.finished.connect(self.model_worker.deleteLater)
        self.model_thread.finished.connect(self.model_thread.deleteLater)
        
        self.model_thread.start()

    def _handle_model_success(self, message: str, file_path: str):
        self.progress_update_signal.emit(100)
        self.ui_status_message_signal.emit(f"Model generated successfully: {os.path.basename(file_path)}", 5000)
        self.logger.info(f"{message} Saved to: {file_path}")

    def start_stats_process(self, file_path: str):
        context = self._check_and_log_layer(file_path, "Statistics")
        if not context: return

        pipeline_config = context.get_full_pipeline_json()
        pipeline_config.append({"type": "filters.stats", "enumerate": "Classification"})

        self.ui_status_message_signal.emit("Calculating statistics...", 0)
        self.progress_update_signal.emit(10)

        if hasattr(self, 'stats_thread') and self.stats_thread is not None:
            if self.stats_thread.isRunning():
                self.stats_thread.quit()
                self.stats_thread.wait()

        self.stats_thread = QThread()
        self.stats_worker = StatsWorker(file_path, pipeline_config)
        self.stats_worker.moveToThread(self.stats_thread)
        
        self.stats_thread.started.connect(self.stats_worker.run)
        self.stats_worker.finished.connect(self._handle_stats_success)
        self.stats_worker.error.connect(self._handle_worker_error)
        self.stats_worker.progress.connect(self.progress_update_signal.emit)
        
        self.stats_worker.finished.connect(self.stats_thread.quit)
        self.stats_worker.finished.connect(self.stats_worker.deleteLater)
        self.stats_thread.finished.connect(self.stats_thread.deleteLater)
        self.stats_thread.start()

    def _handle_stats_success(self, file_path: str, stats_data: dict):
        self.progress_update_signal.emit(100)
        self.ui_status_message_signal.emit("Statistics calculation completed.", 3000)
        self.stats_ready_signal.emit(file_path, stats_data)