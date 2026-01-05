from core.controllers.data_controller import DataController
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from core.pipeline_builder import PipelineBuilder
from core.layer_context import PipelineStage
from core.filter_worker import FilterWorker
from core.model_worker import ModelWorker
from core.stats_worker import StatsWorker
from typing import Dict, Any, Optional
from core.logger import Logger
import os

class ProcessController(QObject):
    """
    Filtreleme, istatistik hesaplama ve model oluşturma gibi
    veri işleme süreçlerini yönetir.
    """
    layer_updated = pyqtSignal(str) # file_path
    stage_added = pyqtSignal(str, str, str) # file_path, stage_name, details
    stats_ready = pyqtSignal(str, dict) # file_path, stats_data
    progress_update = pyqtSignal(int)
    status_message = pyqtSignal(str, int)
    log_message = pyqtSignal(str, str) # level, message

    def __init__(self, data_controller:DataController, logger:Logger):
        super().__init__()
        self.data_controller = data_controller
        self.logger = logger
        self.filter_thread = None
        self.stats_thread = None
        self.model_thread = None

    def apply_filter(self, file_path:str, tool_name:str, user_params:Dict[str, Any]):
        context = self.data_controller.get_layer(file_path)
        if not context:
            self.log_message.emit("WARNING", f"Layer not found: {file_path}")
            return
        
        new_stage = PipelineBuilder.create_stage(tool_name, user_params)
        if not new_stage:
            self.log_message.emit("ERROR", f"Could not create stage for '{tool_name}'.")
            return
        
        previous_data = context.get_latest_data()
        
        pipeline_config = []
        input_data = None
        
        if previous_data is not None:
            self.log_message.emit("INFO", f"Filter Running (Cached): {new_stage.display_text}...")
            
            if isinstance(new_stage.config, list):
                pipeline_config = new_stage.config
            else:
                pipeline_config = [new_stage.config]

            input_data = previous_data
        else:
            self.log_message.emit("INFO", f"Filter Running (Full): {new_stage.display_text}...")
            
            pipeline_config = context.get_full_pipeline_json()
            if isinstance(new_stage.config, list):
                pipeline_config.extend(new_stage.config)
            else:
                pipeline_config.append(new_stage.config)
                
            input_data = None

        self._start_filter_worker(file_path, pipeline_config, new_stage, input_data=input_data)
        
    def remove_stage(self, file_path:str, stage_index:int):
        context = self.data_controller.get_layer(file_path)
        if not context:
            return
        
        if 0 <= stage_index < len(context.stages):
            stage_name = context.stages[stage_index].name
            context.remove_stage(stage_index)

            for stage in context.stages:
                stage.cached_data = None
            
            self.log_message.emit("INFO", f"Stage '{stage_name}' removed. Recalculating pipeline...")
            new_pipeline = context.get_full_pipeline_json()
            self._start_filter_worker(file_path, new_pipeline, stage_object=None)
        else:
            self.log_message.emit("WARNING", "Stage index out of bounds.")

    def calculate_statistics(self, file_path:str):
        context = self.data_controller.get_layer(file_path)
        if not context: return

        pipeline_config = context.get_full_pipeline_json()
        pipeline_config.append({
            "type":"filters.stats",
            "enumerate": "Classification"
        })
        self.status_message.emit("Calculating statistics...", 0)
        self.progress_update.emit(10)

        if self.stats_thread is not None:
            try:
                if self.stats_thread.isRunning():
                    self.stats_thread.quit()
                    self.stats_thread.wait()
            except RuntimeError:
                self.stats_thread = None

        self.stats_thread = QThread()
        self.stats_worker = StatsWorker(file_path, pipeline_config)
        self.stats_worker.moveToThread(self.stats_thread)
        
        self.stats_thread.started.connect(self.stats_worker.run)
        self.stats_worker.finished.connect(self._on_stats_finished)
        self.stats_worker.error.connect(self._on_worker_error)
        self.stats_worker.progress.connect(self.progress_update.emit)
        
        self.stats_worker.finished.connect(self.stats_thread.quit)
        self.stats_worker.finished.connect(self.stats_worker.deleteLater)
        self.stats_thread.finished.connect(self.stats_thread.deleteLater)
        self.stats_thread.finished.connect(lambda: setattr(self, 'stats_thread', None))
        self.stats_thread.start()

    def generate_model(self, file_path:str, params:dict):
        context = self.data_controller.get_layer(file_path)
        if not context: return

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

        self.status_message.emit("Generating Elevation Model...", 0)
        self.progress_update.emit(10)
        self.log_message.emit("INFO", f"Starting model generation ({output_type}) -> {save_path}")

        if self.model_thread is not None and self.model_thread.isRunning():
            self.model_thread.quit()
            self.model_thread.wait()

        self.model_thread = QThread()
        self.model_worker = ModelWorker(pipeline_config, save_path)
        self.model_worker.moveToThread(self.model_thread)
        
        self.model_thread.started.connect(self.model_worker.run)
        self.model_worker.finished.connect(self._on_model_finished)
        self.model_worker.error.connect(self._on_worker_error)
        self.model_worker.progress.connect(self.progress_update.emit)
        
        self.model_worker.finished.connect(self.model_thread.quit)
        self.model_worker.finished.connect(self.model_worker.deleteLater)
        self.model_thread.finished.connect(self.model_thread.deleteLater)
        
        self.model_thread.start()

    def apply_batch_process(self, file_path: str, stages: list):
        context = self.data_controller.get_layer(file_path)
        if not context:
            return

        if not stages:
            self.log_message.emit("WARNING", "Batch queue is empty.")
            return

        full_pipeline_config = context.get_full_pipeline_json()

        stage_names = []
        for i, stage in enumerate(stages):
            tagged_config = stage.config.copy()
            tagged_config["tag"] = f"batch_stage_{i}" 
            
            full_pipeline_config.append(tagged_config)
            stage_names.append(stage.name)
        
        self.log_message.emit("INFO", "=== Batch Process Started ===")
        self.log_message.emit("INFO", f"Queue: {' -> '.join(stage_names)}")
        
        self._start_filter_worker(file_path, full_pipeline_config, stage_object=stages)

    def _start_filter_worker(self, file_path: str, pipeline_config: list, stage_object: Optional[PipelineStage], input_data: dict = None):
        self.progress_update.emit(1)
        self.status_message.emit("Applying filter...", 0)

        if self.filter_thread is not None:
            try:
                if self.filter_thread.isRunning():
                    self.log_message.emit("WARNING", "Waiting for previous process...")
                    self.filter_thread.quit()
                    self.filter_thread.wait()
            except RuntimeError:
                self.filter_thread = None

        context = self.data_controller.get_layer(file_path)
        input_count = 0
        
        if input_data:
            input_count = input_data.get("count", 0)
        elif context is not None and context.current_render_data is not None:
            if isinstance(context.current_render_data, dict):
                input_count = context.current_render_data.get("count", 0)
            else:
                input_count = len(context.current_render_data)

        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(file_path, pipeline_config, stage_object, input_count, input_data=input_data)
        self.filter_worker.moveToThread(self.filter_thread)
        
        self.filter_thread.started.connect(self.filter_worker.run)
        self.filter_worker.finished.connect(self._on_filter_finished)
        self.filter_worker.error.connect(self._on_worker_error)
        self.filter_worker.progress.connect(self.progress_update.emit)
        self.filter_worker.stage_progress.connect(self._handle_stage_progress)
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)
        self.filter_thread.finished.connect(self._cleanup_filter_thread_ref)
        
        self.filter_thread.start()

    def _handle_stage_progress(self, index, tag, in_count, out_count):
        try:
            tag_parts = tag.split("_")
            if tag_parts[-1].isdigit():
                stage_idx = int(tag_parts[-1])
            else:
                stage_idx = index

            stages = self.filter_worker.stage 
            
            if isinstance(stages, list) and 0 <= stage_idx < len(stages):
                current_stage = stages[stage_idx]
                stage_name = current_stage.name
                details = current_stage.display_text.replace(stage_name, "").strip()
                
                msg = f"Stage {stage_idx + 1}: {stage_name} {details} | In: {in_count:,} -> Out: {out_count:,}"
                self.log_message.emit("INFO", msg)
                
        except Exception as e:
            print(f"Log parsing error: {e}")

    def _cleanup_filter_thread_ref(self):
        self.filter_thread = None

    def _on_filter_finished(self, file_path: str, result_data: dict, metadata: dict, stage_object: Any, input_count: int):
        self.progress_update.emit(100)
        self.status_message.emit("Operation completed.", 3000)

        context = self.data_controller.get_layer(file_path)
        if not context: return

        context.current_render_data = result_data
        
        if isinstance(stage_object, list):
            for stage in stage_object:
                context.add_stage(stage)
                self.stage_added.emit(file_path, stage.name, stage.display_text)

            self.log_message.emit("INFO", "=== Batch Process Completed ===")

        elif stage_object:
            stage_object.cached_data = result_data
            
            context.add_stage(stage_object)
            output_count = result_data.get("count", 0)
            
            clean_details = stage_object.display_text.replace(stage_object.name, "").strip().strip("()")
            
            log_msg = f"Filter Applied: {stage_object.name} {clean_details} | In: {input_count:,} -> Out: {output_count:,}"
            self.log_message.emit("INFO", log_msg)
            
            self.stage_added.emit(file_path, stage_object.name, clean_details)
        
        else:
            output_count = result_data.get("count", 0)
            self.log_message.emit("INFO", f"Pipeline refreshed. Current Points: {output_count:,}")

        self.layer_updated.emit(file_path)

    def _on_stats_finished(self, file_path: str, stats_data: dict):
        self.progress_update.emit(100)
        self.status_message.emit("Statistics ready.", 3000)
        self.stats_ready.emit(file_path, stats_data)

    def _on_model_finished(self, message: str, file_path: str):
        self.progress_update.emit(100)
        file_name = os.path.basename(file_path)
        self.status_message.emit(f"Model generated: {file_name}", 5000)
        self.log_message.emit("INFO", message)

    def _on_worker_error(self, error_msg: str):
        self.progress_update.emit(0)
        self.status_message.emit("Error: Process failed.", 5000)
        self.log_message.emit("ERROR", error_msg)