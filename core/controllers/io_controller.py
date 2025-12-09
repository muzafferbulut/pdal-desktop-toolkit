from core.controllers.data_controller import DataController
from data.writers import PipelineWriter, MetadataWriter
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from core.database.repository import Repository
from core.export_worker import ExportWorker
from core.logger import Logger
import json
import os

class IOController(QObject):
    export_success = pyqtSignal(str) # message
    progress_update = pyqtSignal(int)
    status_message = pyqtSignal(str, int)
    log_message = pyqtSignal(str, str) # level, message

    def __init__(self, data_controller: DataController, logger: Logger):
        super().__init__()
        self.data_controller = data_controller
        self.logger = logger
        self.export_thread = None
        self.repository = Repository()

    def export_layer(self, file_path: str, save_path: str):
        context = self.data_controller.get_layer(file_path)
        if not context:
            self.log_message.emit("WARNING", f"Export failed: Layer not found {file_path}")
            return

        if not save_path:
            self.log_message.emit("WARNING", "Export path not selected.")
            return

        file_name = os.path.basename(file_path)
        pipeline_config = context.get_full_pipeline_json()
        
        self.log_message.emit("INFO", f"Starting export: '{file_name}' -> '{save_path}'...")
        self._start_export_worker(save_path, pipeline_config)

    def save_pipeline(self, file_path: str, save_path: str):
        context = self.data_controller.get_layer(file_path)
        if not context: return
            
        pipeline_json = context.get_full_pipeline_json()
        writer = PipelineWriter()
        result = writer.write(save_path, pipeline_json)

        if result.get("status"):
            self.log_message.emit("INFO", f"Pipeline saved: {save_path}")
            self.status_message.emit("Pipeline configuration saved.", 3000)
        else:
            error_msg = result.get("error")
            self.log_message.emit("ERROR", f"Pipeline save failed: {error_msg}")

    def save_metadata(self, file_path: str, save_path: str):
        context = self.data_controller.get_layer(file_path)
        if not context: return
        
        file_name = os.path.basename(file_path)
        metadata_to_save = context.full_metadata if context.full_metadata else context.metadata

        if not getattr(context, "full_metadata", None):
             self.log_message.emit("WARNING", f"Full metadata not available for '{file_name}'. Saving summary.")

        writer = MetadataWriter()
        result = writer.write(save_path, metadata_to_save)

        if result.get("status"):
            self.log_message.emit("INFO", f"Metadata saved: {save_path}")
            self.status_message.emit("Metadata saved successfully.", 3000)
        else:
            error_msg = result.get("error")
            self.log_message.emit("ERROR", f"Metadata save failed: {error_msg}")

    def _start_export_worker(self, save_path: str, pipeline_config: list):
        self.progress_update.emit(1)
        self.status_message.emit("Exporting layer...", 0)

        if self.export_thread is not None and self.export_thread.isRunning():
            try:
                self.export_thread.quit()
                self.export_thread.wait()
            except RuntimeError:
                pass

        self.export_thread = QThread()
        self.export_worker = ExportWorker(save_path, pipeline_config)
        self.export_worker.moveToThread(self.export_thread)
        
        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_worker_error)
        self.export_worker.progress.connect(self.progress_update.emit)
        
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        
        self.export_thread.start()

    def _on_export_finished(self, message: str):
        self.progress_update.emit(100)
        self.status_message.emit("Export completed.", 5000)
        self.log_message.emit("INFO", "Export operation completed successfully.")
        self.export_success.emit(message)

    def _on_worker_error(self, error_msg: str):
        self.progress_update.emit(0)
        self.status_message.emit("Error: Export failed.", 5000)
        self.log_message.emit("ERROR", error_msg)

    def save_batch_config(self, file_path: str, config_data: list):
        try:
            if not file_path.lower().endswith(".json"):
                file_path += ".json"
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
                
            self.log_message.emit("INFO", f"Batch configuration saved: {file_path}")
            self.status_message.emit("Batch config saved.", 3000)
            return True
        except Exception as e:
            self.log_message.emit("ERROR", f"Failed to save batch config: {e}")
            return False
        
    def load_batch_config(self, file_path: str) -> list:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.log_message.emit("INFO", f"Batch configuration loaded: {file_path}")
            return data
        except Exception as e:
            self.log_message.emit("ERROR", f"Failed to load batch config: {e}")
            return []
        
    def save_batch_to_db(self, name: str, config_data: list, description: str = ""):
        success = self.repository.save_batch_preset(name, config_data, description)

        if success:
            self.log_message.emit("INFO", f"Batch preset saved to DB: '{name}'")
            self.status_message.emit("Preset saved.", 3000)
        else:
            self.log_message.emit("ERROR", "Failed to save preset to database.")

    def get_batch_presets_from_db(self):
        return self.repository.get_all_presets()

    def delete_batch_preset(self, preset_id: int):
        success = self.repository.delete_preset(preset_id)
        if success:
            self.log_message.emit("INFO", "Preset deleted.")
        else:
            self.log_message.emit("ERROR", "Failed to delete preset.")