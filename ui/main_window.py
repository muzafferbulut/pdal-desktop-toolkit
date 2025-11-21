from PyQt5.QtWidgets import (QMainWindow,QWidget,QAction,QPlainTextEdit,QDockWidget,
    QTabWidget,QFileDialog,QProgressBar,QMessageBox,)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QTextCursor
from core.layer_context import LayerContext, PipelineStage
from data.writers import PipelineWriter, MetadataWriter
from ui.data_sources_panel import DataSourcesPanel
from core.pipeline_builder import PipelineBuilder
from ui.tab_viewers import GISMapView, ThreeDView
from ui.filter_dialog import FilterParamsDialog
from core.themes.manager import ThemeManager
from core.export_worker import ExportWorker
from core.filter_worker import FilterWorker
from ui.metadata_panel import MetadataPanel
from ui.toolbox_panel import ToolboxPanel
from data.data_handler import IDataReader
from core.read_worker import ReaderWorker
from PyQt5.QtCore import Qt, QThread
from core.logger import Logger
from typing import Optional
import copy
import os

class MainWindow(QMainWindow):

    def __init__(self, app_logger: Logger, reader: IDataReader, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = app_logger
        self.reader = reader
        self.logger.info("Ana pencere başlatılıyor.")
        self.setWindowTitle("Pdal Desktop Toolkit")
        self.setWindowIcon(QIcon("ui/resources/icons/app.png"))
        self.setGeometry(100, 100, 1200, 800)

        self._data_cache = {}

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._setup_log_panel()
        self._setup_left_panels()
        self._setup_central_widget()
        self._setup_toolbox_panel()
        self._create_status_bar()
        
        ThemeManager.apply_theme("Light Theme")

        menu_bar = self.menuBar()

        # file menu actions
        self.file_menu = menu_bar.addMenu("File")

        self.action_open_file = QAction(QIcon("ui/resources/icons/open.png"), "Open File", self)
        self.action_open_file.setShortcut("Ctrl+O")
        self.action_open_file.setStatusTip("Open point cloud file (Ctrl+O).")
        self.action_open_file.triggered.connect(self._open_file_dialog)
        self.file_menu.addAction(self.action_open_file)

        self.action_save_as = QAction(QIcon("ui/resources/icons/save.png"), "Save As...", self)
        self.action_save_as.setShortcut("Ctrl+S")
        self.action_save_as.setStatusTip("Save selected layer (Ctrl+S).")
        self.file_menu.addAction(self.action_save_as)

        self.action_save_pipeline = QAction(QIcon("ui/resources/icons/save_pipeline.png"), "Save Pipeline...", self)
        self.action_save_pipeline.setShortcut("Ctrl+P")
        self.action_save_pipeline.setStatusTip("Save active pipeline (Ctrl+P).")
        self.file_menu.addAction(self.action_save_pipeline)

        # view menü actions
        self.view_menu = menu_bar.addMenu("View")

        self.themes_menu = self.view_menu.addMenu("Themes")
        self._populate_themes_menu()

        self.view_menu.addSeparator()

        self.view_menu.addAction(self.data_sources_dock.toggleViewAction())
        self.view_menu.addAction(self.metadata_dock.toggleViewAction())
        self.view_menu.addAction(self.toolbox_dock.toggleViewAction())
        self.view_menu.addAction(self.log_dock.toggleViewAction())

        self.view_menu.addSeparator()

        self.action_reset_layout = QAction("Restore Default", self)
        self.action_reset_layout.triggered.connect(self._reset_layout)
        self.view_menu.addAction(self.action_reset_layout)

        # help menu actions
        self.help_menu = menu_bar.addMenu("Help")

        self.action_about = QAction(QIcon("ui/resources/icons/about.png"), "About", self)
        self.action_about.setStatusTip("About")
        self.action_about.triggered.connect(self._open_about)
        self.help_menu.addAction(self.action_about)

        # toolbar actions
        self.file_toolbar = self.addToolBar("File Operations")
        self.file_toolbar.setMovable(False)

        self.file_toolbar.addAction(self.action_open_file)
        self.file_toolbar.addAction(self.action_save_as)
        self.file_toolbar.addAction(self.action_save_pipeline)
        self.file_toolbar.addSeparator()

    def _populate_themes_menu(self):
        for name in ThemeManager.get_theme_names():
            action = QAction(name, self)
            action.triggered.connect(lambda checked=False, n=name: self._change_theme(n))
            self.themes_menu.addAction(action)

    def _change_theme(self, theme_name: str):
        self.logger.info(f"Changing theme to: {theme_name}")
        ThemeManager.apply_theme(theme_name)

    def _reset_layout(self):

        for dock in [self.data_sources_dock, self.metadata_dock, 
                     self.toolbox_dock, self.log_dock]:
            self.removeDockWidget(dock)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_sources_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.metadata_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox_dock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)  

        self.data_sources_dock.show()
        self.metadata_dock.show()
        self.toolbox_dock.show()
        self.log_dock.show()

    def _open_about(self):
        try:
            about_text = (
                "<div style='font-family:Segoe UI, sans-serif; font-size:10pt; color:#333;'>"
                "<h3 style='margin-bottom:4px;'>PDAL Desktop Toolkit</h3>"
                "<p style='margin:0; font-size:9pt;'>"
                "Version: 0.7.0<br>"
                "Developer: Muzaffer Bulut<br>"
                "Contact: bulutmuzafferr@gmail.com<br><br>"
                "Designed for simple, fast and sustainable geospatial solutions."
                "</p>"
                "<p style='margin-top:10px; font-size:8pt; color:#777;'>"
                "© 2025 Muzaffer Bulut — All rights reserved."
                "</p>"
                "</div>"
            )

            msg = QMessageBox(self)
            msg.setWindowTitle("About")
            msg.setTextFormat(1)
            msg.setIcon(QMessageBox.Information)
            msg.setText(about_text)
            msg.addButton("Close", QMessageBox.AcceptRole)
            msg.exec_()

        except Exception as e:
            self.logger.error(f"An error occured : {e}")

    def _setup_log_panel(self):
        self.log_dock = QDockWidget("Log", self)
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_dock.setWidget(self.log_text_edit)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.logger.log_signal.connect(self._append_log)

    def _append_log(self, level: str, message: str):
        char_format = QTextCharFormat()
        if level == "ERROR":
            char_format.setForeground(QColor("red"))
        elif level == "WARNING":
            char_format.setForeground(QColor("darkorange"))
        else:
            char_format.setForeground(QColor("black"))

        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.mergeCharFormat(char_format)
        cursor.insertText(message + "\n")

    def _setup_left_panels(self):
        self.data_sources_panel = DataSourcesPanel()
        self.data_sources_panel.file_single_clicked.connect(self._on_file_single_clicked)
        self.data_sources_panel.file_double_clicked.connect(self._on_file_double_clicked)
        self.data_sources_panel.zoom_to_bbox_requested.connect(self._handle_zoom_to_bbox)
        self.data_sources_panel.export_layer_requested.connect(self._handle_export_layer)
        self.data_sources_panel.save_pipeline_requested.connect(self._handle_save_pipeline)
        self.data_sources_panel.save_full_metadata_requested.connect(self._handle_save_full_metadata)
        self.data_sources_panel.remove_layer_requested.connect(self._handle_remove_layer)
        self.data_sources_panel.remove_stage_requested.connect(self._handle_remove_stage)
        self.data_sources_panel.style_changed_requested.connect(self._handle_style_change)

        self.data_sources_dock = QDockWidget("Data Sources", self)
        self.data_sources_dock.setWidget(self.data_sources_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_sources_dock)

        self.metadata_dock = QDockWidget("Metadata", self)
        
        self.metadata_panel = MetadataPanel()
        self.metadata_dock.setWidget(self.metadata_panel)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.metadata_dock)

    def _handle_style_change(self, file_path: str, style_name:str):
        context = self._data_cache.get(file_path)
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
        
        self.three_d_view.render_point_cloud(data, color_by=style_name, reset_view=False)
        self.logger.info(f"Updated style for '{file_name}' to {style_name}.")

    def _handle_remove_stage(self, file_path: str, stage_index: int):
        if file_path not in self._data_cache:
            return

        context = self._data_cache[file_path]

        context.remove_stage(stage_index)
        self.logger.info(f"Stage at index {stage_index} removed. Re-calculating pipeline...")

        new_pipeline_config = context.get_full_pipeline_json()

        vis_pipeline = copy.deepcopy(new_pipeline_config)
        vis_pipeline.append({
            "type": "filters.decimation",
            "step": 10
        })

        self._start_filter_worker(file_path, vis_pipeline, stage_object=None)

    def _handle_zoom_to_bbox(self, file_path: str):
        context = self._data_cache.get(file_path)

        if not context:
            self.logger.error(f"Can not zoom, data not found: {file_path}")
            return
        
        bounds = context.bounds

        if not bounds or not bounds.get("status"):
            QMessageBox.warning(self, "Warning", "Spatial bounds not found for this layer.")
            return
        
        file_name = os.path.basename(file_path)
        self.map_view.draw_bbox(bounds)

        self.logger.info(f"Zoomed to bounds of '{file_name}'.")
        self.tab_widget.setCurrentWidget(self.map_view)

    def _handle_export_layer(self, file_path: str):
        context = self._data_cache.get(file_path)
        if not context:
            return
            
        file_name = os.path.basename(file_path)

        pipeline_config = context.get_full_pipeline_json()

        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Layer", 
            f"export_{file_name}",
            "LAS Files (*.las);;LAZ Files (*.laz)"
        )

        if not save_path:
            return
        
        self.logger.info(f"Starting export for '{file_name}' to '{save_path}'...")
        self._start_export_worker(save_path, pipeline_config)

    def _start_export_worker(self, save_path, pipeline_config):        
        self.progressBar.show()
        self.statusBar().showMessage("Exporting layer... Please wait.", 0)

        if hasattr(self, 'export_thread') and self.export_thread is not None:
            if self.export_thread.isRunning():
                self.export_thread.quit()
                self.export_thread.wait()

        self.export_thread = QThread()
        self.export_worker = ExportWorker(save_path, pipeline_config)
        
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        
        self.export_worker.finished.connect(self._handle_export_success)
        self.export_worker.error.connect(self._handle_reader_error)

        self.export_worker.progress.connect(self._handle_progress)
        
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        
        self.export_thread.start()

    def _handle_export_success(self, message: str):
        self.progressBar.hide()
        self.statusBar().showMessage("Export completed.", 5000)
        self.logger.info("Export operation finished successfully.")

    def _handle_save_pipeline(self, file_path: str):
        context = self._data_cache.get(file_path)
        if not context:
            return
            
        file_name = os.path.basename(file_path)
        
        pipeline_json = context.get_full_pipeline_json()

        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Pipeline Configuration", 
            f"pipeline_{file_name}.json", 
            "JSON Files (*.json)"
        )

        if not save_path:
            return
        
        writer = PipelineWriter()
        result = writer.write(save_path, pipeline_json)

        if result.get("status"):
            self.logger.info(f"Pipeline saved to: {save_path}")
            self.statusBar().showMessage("Pipeline configuration saved.", 3000)
        else:
            error_msg = result.get("error")
            self.logger.error(f"Failed to save pipeline: {error_msg}")
            QMessageBox.critical(self, "Error", f"Could not save pipeline:\n{error_msg}")

    def _handle_save_full_metadata(self, file_path: str):
        file_name = os.path.basename(file_path)
        cached_data = self._data_cache.get(file_path)
        
        if not cached_data:
            self.logger.error(f"Cannot save metadata, data not found in cache: {file_name}")
            return
        
        metadata_to_save = getattr(cached_data, "full_metadata", None)

        if not metadata_to_save:
            self.logger.warning(f"Full metadata not available for {file_name}. Saving summary instead.")
            metadata_to_save = cached_data.metadata


        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Metadata", 
            f"metadata_{file_name}.json", 
            "JSON Files (*.json)"
        )

        if not save_path:
            return
        
        writer = MetadataWriter()
        result = writer.write(save_path, metadata_to_save)

        if result.get("status"):
            self.logger.info(f"Metadata saved to: {save_path}")
            self.statusBar().showMessage("Metadata saved successfully.", 3000)
        else:
            error_msg = result.get("error")
            self.logger.error(f"Metadata save failed: {error_msg}")
            QMessageBox.critical(self, "Error", f"Could not save metadata:\n{error_msg}")

    def _handle_remove_layer(self, file_path: str):
        file_name = os.path.basename(file_path)
        
        if file_path in self._data_cache:
            del self._data_cache[file_path]
            self.logger.info(f"File '{file_name}' removed from data cache.")
            self.data_sources_panel.remove_layer(file_path)
            self.logger.info(f"File '{file_name}' removed from Data Sources Panel.")
            self.metadata_panel.clear_metadata()            
            self.map_view.draw_bbox({})
            self.three_d_view.plotter.clear()
            self.map_view.clear_bbox()
            self.logger.info(f"Views cleared after removing '{file_name}'.")
        else:
            self.logger.warning(f"File '{file_name}' not found in cache for removal. Checking UI only.")
            self.data_sources_panel.remove_layer(file_path)
            self.metadata_panel.clear_metadata()
            self.logger.info(f"File '{file_name}' removed from UI.")

    def _setup_central_widget(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.map_view = GISMapView()
        self.three_d_view = ThreeDView()

        self.tab_widget.addTab(self.map_view, QIcon("ui/resources/icons/map_view.png"), "Map View")
        self.tab_widget.addTab(self.three_d_view, QIcon("ui/resources/icons/3d_view.png"), "3D View")

        ThemeManager.add_observer(self.three_d_view.on_theme_change)
        ThemeManager.add_observer(self.map_view.on_theme_change)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a file", "", "LAS/LAZ Files (*.las *.laz)"
        )

        if file_path:
            self.statusBar().showMessage(f"Loading {os.path.basename(file_path)}...", 0)
            self.progressBar.show() 

            self.worker_thread = QThread()
            self.worker = ReaderWorker(
                file_path=file_path, 
                reader=self.reader, 
                logger=self.logger
            ) 
            self.worker.moveToThread(self.worker_thread) 
            self.worker_thread.started.connect(self.worker.run) 
            
            self.worker.finished.connect(self._handle_reader_success)
            self.worker.error.connect(self._handle_reader_error)
            self.worker.progress.connect(self._handle_progress)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.error.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.start()

        else:
            self.logger.warning("File not selected.")

    def _handle_progress(self, value:int):
        if value == -1:
            self.progressBar.setRange(0, 0) 
            self.progressBar.setTextVisible(False)        
        else:
            if self.progressBar.maximum() == 0:
                self.progressBar.setRange(0, 100)
                self.progressBar.setTextVisible(True)
            
            self.progressBar.setValue(value)
            
    def _handle_reader_success(self, file_path:str, bounds:dict, full_metadata:dict, summary_metadata:dict, sample_data):
        self.progressBar.hide()
        self.statusBar().showMessage(f"File '{os.path.basename(file_path)}' loaded successfully!", 5000)
        file_name = os.path.basename(file_path)
        
        context = LayerContext(file_path, summary_metadata, full_metadata)
        context.current_render_data = sample_data
        context.bounds = bounds
        
        self._data_cache[file_path] = context

        self.data_sources_panel.add_file(file_path, file_name)
        
        self.logger.info(f"File '{file_name}' successfully added to data sources.")

    def _handle_reader_error(self, error_message: str):
        self.progressBar.hide()
        self.statusBar().showMessage("Error: The process failed.", 5000)
        self.logger.error(error_message)

    def _setup_toolbox_panel(self): 
        self.toolbox_dock = QDockWidget("Toolbox", self)
        self.toolbox_panel = ToolboxPanel()
        self.toolbox_dock.setWidget(self.toolbox_panel)

        self.toolbox_panel.tool_selected.connect(self._handle_tool_selection)

        self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox_dock)

    def _handle_tool_selection(self, tool_name:str):
        current_file = self.data_sources_panel.get_selected_file_path()

        if not current_file or current_file not in self._data_cache:
            self.logger.warning("Please select a layer from data sources first.")
            return
        
        context: LayerContext = self._data_cache[current_file]
        dialog = FilterParamsDialog(tool_name, self)
        
        if dialog.exec_():
            user_params = dialog.get_params()

            new_stage = PipelineBuilder.create_stage(tool_name, user_params)

            if not new_stage:
                self.logger.error(f"Could not build stage for {tool_name}")
                return
            
            base_pipeline = context.get_full_pipeline_json()
            base_pipeline.append(new_stage.config)
            self.logger.info(f"Running filter: {new_stage.display_text}...")
            self._start_filter_worker(current_file, base_pipeline, new_stage)
    
    def _start_filter_worker(self, file_path, pipeline_config, stage_object:Optional[PipelineStage] = None):        
        self.progressBar.show()
        self.statusBar().showMessage("The filter is applied...", 0)
        
        if hasattr(self, 'filter_thread') and self.filter_thread is not None:
            try:
                if self.filter_thread.isRunning():
                    self.logger.warning("The new one was started before the previous process was finished, waiting...")
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
        
        # sinyalleri bağla
        self.filter_worker.finished.connect(self._handle_filter_success) 
        self.filter_worker.error.connect(self._handle_reader_error)      
        self.filter_worker.progress.connect(self._handle_progress)
        
        # temizle
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)
        self.filter_thread.start()

    def _handle_filter_success(self, file_path, result_data, stage_object: Optional[PipelineStage], input_count: int):
        self.progressBar.hide()
        self.statusBar().showMessage("Process completed.", 3000)

        if file_path not in self._data_cache:
            return
        
        context: LayerContext = self._data_cache[file_path]        
        context.current_render_data = result_data
    
        output_count = result_data.get("count", 0)

        if stage_object:
            context.add_stage(stage_object)
            
            clean_details = stage_object.display_text.replace(stage_object.name, "").strip().strip("()")
            
            self.data_sources_panel.add_stage_node(
                file_path=file_path,
                stage_name=stage_object.name,
                stage_details=clean_details
            )
            
            log_msg = (
                f"Stage added: {stage_object.name}\n"
                f"   Points: {input_count:,} -> {output_count:,}\n"
            )
            self.logger.info(log_msg)
        
        else:
            self.logger.info(f"Pipeline refreshed. Current Points: {output_count:,}")

        self.three_d_view.render_point_cloud(result_data)

    def _create_status_bar(self):
        self.statusBar()
        self.progressBar = QProgressBar(self.statusBar())
        self.progressBar.setRange(0, 100)
        self.progressBar.setTextVisible(True)
        self.progressBar.setValue(0)
        self.progressBar.setFixedWidth(150)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

    def _on_file_single_clicked(self, file_path: str, file_name: str):
        if not file_path:
            self.logger.warning(f"No file path found for the selected item: {file_name}")
            return
        
        cached_data = self._data_cache.get(file_path)

        if not cached_data:
            self.logger.error(f"Data not found in cache: {file_path}")
            self.metadata_panel.clear_metadata() 
            return
        
        summary_metadata = cached_data.metadata

        if summary_metadata.get("status"):
            self.metadata_panel.update_metadata(file_name, summary_metadata)
        else:
            self.logger.error(f"Metadata reading error.")
            self.metadata_panel.clear_metadata()

    def _on_file_double_clicked(self, file_path: str, file_name:str):
        if not file_path:
            return
        
        cached_data = self._data_cache.get(file_path)
        if not cached_data:
            self.logger.warning(f"Data not found in cache: {file_path}")
            return

        if cached_data.bounds and cached_data.bounds.get("status"):
             self.map_view.draw_bbox(cached_data.bounds)

        sample_data = cached_data.current_render_data

        if sample_data and "x" in sample_data:
            self.three_d_view.render_point_cloud(sample_data)
        else:
            error_msg = sample_data.get("error", "Unknown error") if sample_data else "Data is None"
            self.logger.error(f"3D Render Failed for '{file_name}': {error_msg}")
            QMessageBox.warning(self, "Render Error", f"Could not render 3D view:\n{error_msg}")