from PyQt5.QtWidgets import (QMainWindow,QWidget,QAction,QPlainTextEdit,
            QDockWidget,QTabWidget,QFileDialog,QProgressBar,QMessageBox,)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QTextCursor
from core.application_controller import ApplicationController
from ui.stats_result_dialog import StatsResultDialog
from ui.data_sources_panel import DataSourcesPanel
from ui.tab_viewers import GISMapView, ThreeDView
from core.settings_manager import SettingsManager
from ui.filter_dialog import FilterParamsDialog
from ui.batch_dialog import BatchProcessDialog
from core.themes.manager import ThemeManager
from ui.metadata_panel import MetadataPanel
from ui.db_manager import DbManagerDialog
from ui.toolbox_panel import ToolboxPanel
from ui.merge_dialog import MergeDialog
from ui.model_dialog import ModelDialog
from ui.crop_dialog import CropDialog
from PyQt5.QtGui import QCloseEvent
from core.logger import Logger
from typing import Optional
from PyQt5.QtCore import Qt, QTimer
import os

class MainWindow(QMainWindow):

    def __init__(self, app_logger: Logger, controller: ApplicationController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = app_logger
        self.controller = controller
        self.setWindowTitle("Pdal Desktop Toolkit")
        self.setWindowIcon(QIcon("ui/resources/icons/app.png"))
        self.setGeometry(100, 100, 1200, 800)
        self.settings_manager = SettingsManager()
        self._setup_ui()
        self._restore_settings()

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._actual_resize_handler)

    def resize_event(self, event):
        self.resize_timer.start(200)
        super().resizeEvent(event)

    def _actual_resize_handler(self):
        if hasattr(self, 'three_d_view') and self.three_d_view.plotter:
            self.three_d_view.plotter.setUpdatesEnabled(True)
            self.three_d_view.plotter.render()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._setup_log_panel()
        self._setup_left_panels()
        self._setup_central_widget()
        self._setup_toolbox_panel()
        self._create_status_bar()
        
        ThemeManager.apply_theme("Light Theme")

        self.controller.progress_update_signal.connect(self._handle_progress)
        self.controller.log_error_signal.connect(self._handle_controller_error)
        self.controller.log_info_signal.connect(self._handle_controller_info)
        self.controller.ui_status_message_signal.connect(self.statusBar().showMessage)
        self.controller.stats_ready_signal.connect(self._show_stats_dialog)
        self.controller.file_load_success_signal.connect(self._handle_controller_file_load)
        self.controller.file_removed_signal.connect(self._handle_controller_file_remove)
        self.controller.stage_added_signal.connect(self.data_sources_panel.add_stage_node)
        self.controller.render_data_signal.connect(self._handle_render_data)
        self.controller.draw_bbox_signal.connect(self._handle_draw_bbox)
        self.controller.clear_views_signal.connect(self._handle_clear_views)
        self.controller.update_metadata_signal.connect(self.metadata_panel.update_metadata)
        self.controller.clear_metadata_signal.connect(self.metadata_panel.clear_metadata)
        self.controller.export_success_signal.connect(self._handle_export_success)
        self.controller.zoom_map_only_signal.connect(self.map_view.zoom_only)
        self.controller.focus_3d_mesh_signal.connect(self.three_d_view.zoom_to_mesh)
        
        self.action_open_file = QAction(QIcon("ui/resources/icons/open.png"), "Open File", self)
        self.action_open_file.setShortcut("Ctrl+O")
        self.action_open_file.setStatusTip("Open point cloud file (Ctrl+O).")
        self.action_open_file.triggered.connect(self._open_file_dialog)

        self.action_export_layer = QAction(QIcon("ui/resources/icons/export.png"), "Export Layer", self)
        self.action_export_layer.setShortcut("Ctrl+E")
        self.action_export_layer.setStatusTip("Export selected layer to LAS/LAZ.")
        self.action_export_layer.triggered.connect(self._on_toolbar_export_layer)

        self.action_save_pipeline = QAction(QIcon("ui/resources/icons/save_pipeline.png"), "Save Pipeline...", self)
        self.action_save_pipeline.setShortcut("Ctrl+P")
        self.action_save_pipeline.setStatusTip("Save active pipeline (Ctrl+P).")
        self.action_save_pipeline.triggered.connect(self._on_toolbar_save_pipeline)

        self.action_save_metadata = QAction(QIcon("ui/resources/icons/metadata.png"), "Save Full Metadata", self)
        self.action_save_metadata.setStatusTip("Save metadata to JSON.")
        self.action_save_metadata.triggered.connect(self._on_toolbar_save_metadata)

        self.action_batch_process = QAction(QIcon("ui/resources/icons/batch.png"), "Batch Process", self)
        self.action_batch_process.setStatusTip("Run multiple tools in sequence.")
        self.action_batch_process.triggered.connect(self._open_batch_dialog)
        
        self.action_about = QAction(QIcon("ui/resources/icons/about.png"), "About", self)
        self.action_about.setStatusTip("About")
        self.action_about.triggered.connect(self._open_about)

        self.file_toolbar = self.addToolBar("Toolbar")
        self.file_toolbar.setObjectName("MainToolbar")
        self.file_toolbar.setMovable(False)
        self.file_toolbar.addAction(self.action_open_file)
        self.file_toolbar.addSeparator()
        self.file_toolbar.addAction(self.action_export_layer)
        self.file_toolbar.addAction(self.action_save_pipeline)
        self.file_toolbar.addAction(self.action_save_metadata)
        self.file_toolbar.addSeparator()
        self.file_toolbar.addAction(self.action_batch_process)

        menu_bar = self.menuBar()

        # File Menu
        self.file_menu = menu_bar.addMenu("File")
        self.file_menu.addAction(self.action_open_file)
        self.file_menu.addAction(self.action_export_layer)
        self.file_menu.addAction(self.action_save_pipeline)
        self.file_menu.addAction(self.action_save_metadata)

        # View Menu
        self.view_menu = menu_bar.addMenu("View")
        self.themes_menu = self.view_menu.addMenu("Themes")
        self._populate_themes_menu()
        
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.file_toolbar.toggleViewAction())
        
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.data_sources_dock.toggleViewAction())
        self.view_menu.addAction(self.metadata_dock.toggleViewAction())
        self.view_menu.addAction(self.toolbox_dock.toggleViewAction())
        self.view_menu.addAction(self.log_dock.toggleViewAction())
        
        self.view_menu.addSeparator()
        self.action_reset_layout = QAction("Restore Default", self)
        self.action_reset_layout.triggered.connect(self._reset_layout)
        self.view_menu.addAction(self.action_reset_layout)

        # Help Menu
        self.help_menu = menu_bar.addMenu("Help")
        self.help_menu.addAction(self.action_about)

        self.action_db_manager = QAction(QIcon("ui/resources/icons/database.png"), "DB Manager", self)
        self.action_db_manager.setToolTip("Manage Database Connections")
        self.action_db_manager.triggered.connect(self._open_db_manager)
        self.file_toolbar.addAction(self.action_db_manager)

    def _open_db_manager(self):
        dlg = DbManagerDialog(self.controller.data_controller, self) 
        dlg.exec_()

    def _get_active_layer_path(self) -> Optional[str]:
        path = self.data_sources_panel.get_selected_file_path()
        if not path:
            self.logger.warning("Operation ignored: No layer selected.")
            return None
        return path

    def _on_toolbar_export_layer(self):
        file_path = self._get_active_layer_path()
        if file_path:
            self._ask_save_export(file_path)

    def _on_toolbar_save_pipeline(self):
        file_path = self._get_active_layer_path()
        if file_path:
            self._ask_save_pipeline(file_path)

    def _on_toolbar_save_metadata(self):
        file_path = self._get_active_layer_path()
        if file_path:
            self._ask_save_full_metadata(file_path)
    
    def _ask_save_export(self, file_path: str):
        file_name = os.path.basename(file_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Layer", 
            f"export_{file_name}",
            "LAS Files (*.las);;LAZ Files (*.laz)"
        )
        if save_path:
            self.progressBar.show()
            self.controller.start_export_process(file_path, save_path)
        
    def _ask_save_pipeline(self, file_path: str):
        file_name = os.path.basename(file_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Pipeline Configuration", 
            f"pipeline_{file_name}.json", 
            "JSON Files (*.json)"
        )
        if save_path:
            self.controller.save_pipeline(file_path, save_path)
    
    def _ask_save_full_metadata(self, file_path: str):
        file_name = os.path.basename(file_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Metadata", 
            f"metadata_{file_name}.json", 
            "JSON Files (*.json)"
        )
        if save_path:
            self.controller.save_full_metadata(file_path, save_path)

    def _populate_themes_menu(self):
        for name in ThemeManager.get_theme_names():
            action = QAction(name, self)
            action.triggered.connect(lambda checked=False, n=name: self._change_theme(n))
            self.themes_menu.addAction(action)

    def _change_theme(self, theme_name: str, verbose:bool = True):
        if verbose:
            self.logger.info(f"Changing theme: {theme_name}")

        ThemeManager.apply_theme(theme_name)
        
        if hasattr(self, 'settings_manager'):
            self.settings_manager.save_theme(theme_name)

    def _setup_log_panel(self):
        self.log_dock = QDockWidget("Log", self)
        self.log_dock.setObjectName("LogDock")
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_dock.setWidget(self.log_text_edit)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.logger.log_signal.connect(self._append_log)

    def _setup_left_panels(self):
        self.data_sources_panel = DataSourcesPanel()
        self.data_sources_panel.file_single_clicked.connect(self._on_file_single_clicked)
        self.data_sources_panel.file_double_clicked.connect(self._on_file_double_clicked)
        self.data_sources_panel.zoom_to_bbox_requested.connect(self._on_zoom_to_bbox_requested)
        self.data_sources_panel.export_layer_requested.connect(self._on_toolbar_export_layer) 
        self.data_sources_panel.save_pipeline_requested.connect(self._ask_save_pipeline)
        self.data_sources_panel.save_full_metadata_requested.connect(self._ask_save_full_metadata)
        self.data_sources_panel.remove_layer_requested.connect(self.controller.handle_remove_layer)
        self.data_sources_panel.remove_stage_requested.connect(self.controller.handle_remove_stage)
        self.data_sources_panel.style_changed_requested.connect(self.controller.handle_style_change)
        self.data_sources_panel.visibility_changed_requested.connect(self._handle_layer_visibility)

        self.data_sources_dock = QDockWidget("Data Sources", self)
        self.data_sources_dock.setObjectName("DataSourcesDock")
        self.data_sources_dock.setWidget(self.data_sources_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_sources_dock)

        self.metadata_dock = QDockWidget("Metadata", self)
        self.metadata_dock.setObjectName("MetadataDock")
        self.metadata_panel = MetadataPanel()
        self.metadata_dock.setWidget(self.metadata_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.metadata_dock)
    
    def _handle_layer_visibility(self, file_path: str, is_visible: bool):
        self.controller.handle_visibility_change(file_path, is_visible)
        self.three_d_view.set_layer_visibility(file_path, is_visible)

        if is_visible:
            context = self.controller.data_controller.get_layer(file_path)
            if context and context.bounds and context.bounds.get("status"):
                self.map_view.draw_bbox(file_path, context.bounds)
        else:
            self.map_view.clear_bbox(file_path)
            
        self.logger.info(f"Layer visibility changed: {os.path.basename(file_path)} -> {is_visible}")

    def _handle_tool_selection(self, tool_name:str):
        current_file = self.data_sources_panel.get_selected_file_path()

        if not current_file:
            self.logger.warning("Please select a layer from Data Sources first.")
            return
        
        if tool_name == "Crop (BBox)":
            self._on_toolbar_crop()
            return

        if tool_name == "Merge":
            self._on_toolbar_merge()
            return
        
        if tool_name == "Elevation Model":
            self._on_toolbar_model()
            return
        
        if tool_name == "Statistics":
            self._on_toolbar_statistics()
            return
        
        dialog = FilterParamsDialog(tool_name, self)
        
        if dialog.exec_():
            user_params = dialog.get_params()
            self.progressBar.show()
            self.controller.start_filter_process(current_file, tool_name, user_params)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a file", "", "LAS/LAZ Files (*.las *.laz)"
        )

        if file_path:
            self.progressBar.show()
            self.controller.start_file_loading(file_path)
        else:
            self.logger.warning("No file selected.")

    def _handle_controller_file_load(self, file_path: str, file_name: str):
        self.progressBar.hide()
        self.data_sources_panel.add_file(file_path, file_name)

    def _handle_controller_file_remove(self, file_path: str):
        self.data_sources_panel.remove_layer(file_path)
        self.three_d_view.remove_layer_actor(file_path)
        self.map_view.clear_bbox(file_path)
        self.metadata_panel.clear_metadata()
        self.statusBar().showMessage("Layer removed.", 3000)

    def _on_file_single_clicked(self, file_path: str):
        self.controller.handle_layer_selection(file_path)
    
    def _on_zoom_to_bbox_requested(self, file_path: str):
        active_index = self.tab_widget.currentIndex()
        self.controller.handle_zoom_to_bbox(file_path, active_index)

    def _on_file_double_clicked(self, file_path: str, file_name: str):
        self.controller.handle_double_click(file_path, file_name)

    def _handle_render_data(self, file_path: str, style_name: str, reset_view: bool):
        sample_data = self.controller.get_layer_data(file_path)
        
        if sample_data is None:
            self.logger.warning(f"Render data is NULL: {file_path}")
            return
        
        if not sample_data.get("status", True):
             self.logger.error(f"Render data ERROR: {sample_data.get('error')}")
             return

        self.three_d_view.render_point_cloud(
            file_path, 
            sample_data, 
            color_by=style_name, 
            reset_view=reset_view
        )

    def _handle_draw_bbox(self, bounds: dict):
        active_path = self.controller.data_controller.active_layer_path
        if active_path:
            self.map_view.draw_bbox(active_path, bounds)

    def _handle_clear_views(self):
        if self.three_d_view.plotter:
            self.three_d_view.layer_actors.clear()
            self.three_d_view.plotter.clear()
        self.map_view.draw_bbox({})
        self.map_view.clear_bbox()

    def _handle_export_success(self, message: str):
        self.progressBar.hide()
        self.statusBar().showMessage("Export completed.", 5000)
        self.logger.info("Export operation completed successfully.")

    def _handle_controller_error(self, error_message: str):
        self.progressBar.hide()
        self.logger.error(error_message)
    
    def _handle_controller_info(self, message: str):
        """Controller'dan gelen bilgi mesajlarını log paneline yazar."""
        self.logger.info(message)
        
    def _create_status_bar(self):
        self.statusBar()
        self.progressBar = QProgressBar(self.statusBar())
        self.progressBar.setRange(0, 100)
        self.progressBar.setTextVisible(True)
        self.progressBar.setValue(0)
        self.progressBar.setFixedWidth(150)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

    def _handle_progress(self, value:int):
        is_active = value != 0 and value != 100
        if is_active:
            self.progressBar.show()
            if value == -1:
                self.progressBar.setRange(0, 0) 
                self.progressBar.setTextVisible(False)
            else:
                if self.progressBar.maximum() == 0:
                    self.progressBar.setRange(0, 100)
                    self.progressBar.setTextVisible(True)
                self.progressBar.setValue(value)
        else:
            self.progressBar.hide()
    
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
            
    def _append_log(self, level: str, message: str):
        char_format = QTextCharFormat()
        if level == "ERROR":
            char_format.setForeground(QColor("red"))
        elif level == "WARNING":
            char_format.setForeground(QColor("darkorange"))

        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setCharFormat(char_format)
        cursor.insertText(message + "\n")
        self.log_text_edit.setTextCursor(cursor)
        self.log_text_edit.ensureCursorVisible()

    def _setup_central_widget(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.map_view = GISMapView()
        self.three_d_view = ThreeDView()

        self.tab_widget.addTab(self.map_view, QIcon("ui/resources/icons/map_view.png"), "Map View")
        self.tab_widget.addTab(self.three_d_view, QIcon("ui/resources/icons/3d_view.png"), "3D View")

        ThemeManager.add_observer(self.three_d_view.on_theme_change)
        ThemeManager.add_observer(self.map_view.on_theme_change)

    def _setup_toolbox_panel(self): 
        self.toolbox_dock = QDockWidget("Toolbox", self)
        self.toolbox_dock.setObjectName("ToolboxDock")
        self.toolbox_panel = ToolboxPanel()
        self.toolbox_dock.setWidget(self.toolbox_panel)

        self.toolbox_panel.tool_selected.connect(self._handle_tool_selection)

        self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox_dock)

    def _on_toolbar_crop(self):
        """Crop işlemini başlatır."""
        current_file = self._get_active_layer_path()
        if not current_file:
            return

        self.crop_dialog = CropDialog(self)
        
        self.crop_dialog.draw_requested.connect(self._activate_crop_drawing)
        self.crop_dialog.finished.connect(self._on_crop_dialog_finished)
        
        if self.crop_dialog.exec_():
            params = self.crop_dialog.get_params()
            if params.get("bounds"):
                self.progressBar.show()
                self.controller.start_filter_process(current_file, "Crop (BBox)", params)
        
        self.three_d_view.disable_crop_gizmo()

    def _activate_crop_drawing(self):
        """Dialog'dan çizim isteği geldiğinde çalışır."""
        self.tab_widget.setCurrentWidget(self.three_d_view)
        
        def on_box_change(box):
            self.crop_dialog.update_bounds_from_gizmo(box.bounds)

        self.three_d_view.enable_crop_gizmo(callback=on_box_change)
        
    def _on_crop_dialog_finished(self, result):
        self.three_d_view.disable_crop_gizmo()

    def _on_toolbar_crop(self):
        current_file = self._get_active_layer_path()
        if not current_file:
            return

        self.crop_dialog = CropDialog(self)
        self.crop_dialog.setModal(False)
        self.crop_dialog.draw_requested.connect(self._activate_crop_drawing)
        self.crop_dialog.finished.connect(self._on_crop_dialog_finished)
        self.crop_dialog.accepted.connect(lambda: self._start_crop_operation(current_file))
        self.crop_dialog.show()

    def _start_crop_operation(self, file_path):
        params = self.crop_dialog.get_params()
        
        if params.get("bounds"):
            self.progressBar.show()
            self.controller.start_filter_process(file_path, "Crop (BBox)", params)

    def _on_toolbar_merge(self):
        layers = self.data_sources_panel.get_loaded_layers()
        
        if len(layers) < 2:
            self.logger.warning("Not enough layers to merge. Load at least 2 files.")
            return

        dialog = MergeDialog(layers, self)
        if dialog.exec_():
            selected_files = dialog.get_files()
            self.progressBar.show()
            self.controller.start_merge_process(selected_files)

    def _on_toolbar_model(self):
        """Yükseklik modeli (DEM/DSM) oluşturma penceresini açar."""
        file_path = self._get_active_layer_path()
        if not file_path:
            return

        dialog = ModelDialog(self)
        if dialog.exec_():
            params = dialog.get_params()
            self.progressBar.show()
            self.controller.start_model_process(file_path, params)

    def _on_toolbar_statistics(self):
        file_path = self._get_active_layer_path()
        if file_path:
            self.progressBar.show()
            self.controller.start_stats_process(file_path)

    def _show_stats_dialog(self, file_path: str, stats_data: dict):
        self.progressBar.hide()
        file_name = os.path.basename(file_path)
        dialog = StatsResultDialog(file_name, stats_data, self)
        dialog.exec_()

    def _open_batch_dialog(self):
        file_path = self._get_active_layer_path()
        if not file_path:
            return

        dialog = BatchProcessDialog(self.controller, self) 
        
        if dialog.exec_():
            stages = dialog.get_pipeline_stages()
            if stages:
                self.progressBar.show()
                self.controller.start_batch_process(file_path, stages)

    def _restore_settings(self):
        """Uygulama açılışında ayarları ve temayı yükler."""
        saved_theme = self.settings_manager.load_theme()
        for action in self.themes_menu.actions():
            if action.text() == saved_theme:
                action.setChecked(True)
        
        self._change_theme(saved_theme, verbose=False)
        self.settings_manager.load_window_state(self)

    def closeEvent(self, event: QCloseEvent):
        """Uygulama kapanırken tetiklenir."""
        self.settings_manager.save_window_state(self)
        super().closeEvent(event)