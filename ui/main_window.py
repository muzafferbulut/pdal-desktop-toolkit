from PyQt5.QtWidgets import (QMainWindow,QWidget,QAction,QPlainTextEdit,QDockWidget,
    QTabWidget,QFileDialog,QProgressBar,QApplication,QMessageBox,)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QTextCursor, QFont
from core.layer_context import LayerContext, PipelineStage
from ui.data_sources_panel import DataSourcesPanel
from core.pipeline_builder import PipelineBuilder
from ui.tab_viewers import GISMapView, ThreeDView
from ui.filter_dialog import FilterParamsDialog
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

    def __init__(
        self, app_logger: Logger, reader: IDataReader, parent: Optional[QWidget] = None
    ):
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
        self._apply_standard_style()

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

        self.data_sources_dock = QDockWidget("Data Sources", self)
        self.data_sources_dock.setWidget(self.data_sources_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_sources_dock)

        self.metadata_dock = QDockWidget("Metadata", self)
        
        self.metadata_panel = MetadataPanel()
        self.metadata_dock.setWidget(self.metadata_panel)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.metadata_dock)

    def _handle_zoom_to_bbox(self, file_path: str):
        file_name = os.path.basename(file_path)
        cached_data = self._data_cache.get(file_path)

        if not cached_data:
            self.logger.error(f"Cannot zoom, data not found in cache: {file_name}")
            return
        
        self.map_view.draw_bbox(cached_data.bounds)
        self.logger.info(f"Zoomed Map View to BBox of '{file_name}'.")

    def _handle_export_layer(self, file_path: str):
        file_name = os.path.basename(file_path)
        self.logger.info(f"Context Menu: Export Layer requested for '{file_name}'. (Not implemented yet)")

    def _handle_save_pipeline(self, file_path: str):
        file_name = os.path.basename(file_path)
        self.logger.info(f"Context Menu: Save Pipeline requested for '{file_name}'. (Not implemented yet)")

    def _handle_save_full_metadata(self, file_path: str):
        file_name = os.path.basename(file_path)
        cached_data = self._data_cache.get(file_path)
        
        if not cached_data:
            self.logger.error(f"Cannot save metadata, data not found in cache: {file_name}")
            return

        self.logger.info(f"Context Menu: Save Full Metadata requested for '{file_name}'. (Not implemented yet)")

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

        self.tab_widget.addTab(self.map_view, "Map View")
        self.tab_widget.addTab(self.three_d_view, "3D View")

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
        self.progressBar.setValue(value)
            
    def _handle_reader_success(self, file_path:str, bounds:dict, full_metadata:dict, summary_metadata:dict, sample_data):
        self.progressBar.hide()
        self.statusBar().showMessage(f"File '{os.path.basename(file_path)}' loaded successfully!", 5000)
        file_name = os.path.basename(file_path)
        
        context = LayerContext(file_path, summary_metadata)
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

        default_params = PipelineBuilder.get_default_params(tool_name)

        dialog = FilterParamsDialog(tool_name, default_params, self)
        
        if dialog.exec_():
            user_params = dialog.get_params()

            new_stage = PipelineBuilder.create_stage(tool_name, user_params)

            if not new_stage:
                self.logger.error(f"Could not build stage for {tool_name}")
                return
            
            base_pipeline = context.get_full_pipeline_json()
            base_pipeline.append(new_stage.config)

            self.logger.info(f"Running filter: {new_stage.display_text}...")
            
            vis_pipeline = copy.deepcopy(base_pipeline)
            vis_pipeline.append({
                "type": "filters.decimation",
                "step": 10
            })
            self._start_filter_worker(current_file, vis_pipeline, new_stage)
    
    def _start_filter_worker(self, file_path, pipeline_config, stage_object):        
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

        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(file_path, pipeline_config, stage_object)
        
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

    def _handle_filter_success(self, file_path, result_data, stage_object:PipelineStage):
        self.progressBar.hide()
        self.statusBar().showMessage("Filter applied successfully.", 3000)

        if file_path not in self._data_cache:
            return
        
        context: LayerContext = self._data_cache[file_path]
        context.add_stage(stage_object)
        context.current_render_data = result_data

        self.data_sources_panel.add_stage_node(
            file_path=file_path,
            stage_name=stage_object.name,
            stage_details=stage_object.display_text.replace(stage_object.name, "").strip("()")
        )

        self.three_d_view.render_point_cloud(
            result_data["x"], 
            result_data["y"], 
            result_data["z"]
        )

        self.logger.info(f"Stage added: {stage_object.display_text}. Points: {result_data['count']}")

    def _create_status_bar(self):
        self.statusBar()
        self.progressBar = QProgressBar(self.statusBar())
        self.progressBar.setRange(0, 100)
        self.progressBar.setTextVisible(True)
        self.progressBar.setValue(0)
        self.progressBar.setFixedWidth(150)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

    def _apply_standard_style(self):

        minimal_stylesheet = """
        * {
            background-color: #ffffff;
            color: #333333;
            border: none;
            outline: none;
        }

        QPushButton {
            background-color: #f2f2f2;
            border: 1px solid #ccc;
            padding: 5px 14px;
            border-radius: 4px;
            font-family: Segoe UI, sans-serif;
            font-size: 9pt;
        }
        
        QPushButton:hover {
            background-color: #e6e6e6;
        }
        
        QPushButton:pressed {
            background-color: #d9d9d9;
        }
            
        QMainWindow {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
        }
        
        QDockWidget {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            margin: 2px;
        }

        QDockWidget::title {
            background-color: #f1f3f4;
            color: #333333;
            padding: 9px 12px;
            font-weight: 500;
            border-bottom: 2px solid #0078d4; 
        }

        QTabWidget::pane {
            border: 1px solid #dee2e6;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f8f9fa;
            color: #666666;
            padding: 8px 16px;
            margin-right: 1px;
            border: 1px solid #dee2e6;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #333333;
            border-bottom: 2px solid #0078d4;
        }
        
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #dee2e6;
            spacing: 6px;
            padding: 6px;
        }
        
        QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 6px;
            border-radius: 4px;
        }
        
        QToolButton:hover {
            background-color: #e9ecef;
            border: 1px solid #dee2e6;
        }

        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #dee2e6;
        }
        
        QMenuBar::item {
            padding: 8px 12px;
            background-color: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #e9ecef;
        }
        
        QMenu {
            border: 1px solid #dee2e6;
            background-color: #ffffff;
        }
        
        QMenu::item:selected {
            background-color: #e9ecef;
        }
        
        QTextEdit, QLineEdit, QPlainTextEdit, QTreeWidget {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            padding: 6px 8px;
            selection-background-color: #e9ecef;
        }
        
        QLabel {
            color: #333333;
            background: transparent;
        }
        
        QStatusBar {
            background-color: #ffffff;
            color: #666666;
            border-top: 1px solid #dee2e6;
        }

        QProgressBar {
            border: 1px solid #0078d4;
            border-radius: 4px;
            text-align: center;
            height: 18px;
            background-color: #f1f3f4;
        }
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(minimal_stylesheet)
        app_font = QFont("Segoe UI", 9)
        QApplication.setFont(app_font)

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
            self.logger.warning(f"Double click ignored: No file path for {file_name}")
            return
        
        cached_data = self._data_cache.get(file_path)

        if not cached_data:
            self.logger.warning(f"Cannot render views, data not found in cache: {file_path}")
            return
        
        self.map_view.draw_bbox(cached_data.bounds)

        sample_data = cached_data.current_render_data

        if sample_data and "x" in sample_data:
            x = sample_data.get("x")
            y = sample_data.get("y")
            z = sample_data.get("z")
            self.three_d_view.render_point_cloud(x, y, z)
        else:
            self.logger.warning(f"Data sampling failed, cannot render 3D view for '{file_name}'.")
            return