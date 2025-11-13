from PyQt5.QtWidgets import (
    QMainWindow,QWidget,QAction,QPlainTextEdit,QDockWidget,QTreeWidget,
    QTabWidget,QFileDialog,QTreeWidgetItem,QProgressBar,QApplication,
    QTextEdit,QTableWidget,QTableWidgetItem, QHeaderView, QMessageBox,

)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QTextCursor, QFont
from ui.tab_viewers import GISMapView, ThreeDView
from data.data_handler import IDataReader
from core.logger import Logger
from PyQt5.QtCore import Qt, QThread
from core.read_worker import ReaderWorker
from typing import Optional
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

        # create menus
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("File")
        self.view_menu = menu_bar.addMenu("View")
        self.help_menu = menu_bar.addMenu("Help")

        # create actions
        self.action_open_file = QAction(QIcon("ui/resources/icons/open.png"), "Open File", self)
        self.action_open_file.setShortcut("Ctrl+O")
        self.action_open_file.setStatusTip("Open point cloud file (Ctrl+O).")
        self.action_open_file.triggered.connect(self._open_file_dialog)
        self.file_menu.addAction(self.action_open_file)

        self.action_run_pipeline = QAction(QIcon("ui/resources/icons/run.png"), "Run Pipeline", self)
        self.action_run_pipeline.setShortcut("Ctrl+R")
        self.action_run_pipeline.setStatusTip("Run pipeline (Ctrl+R).")

        self.action_save_as = QAction(QIcon("ui/resources/icons/save.png"), "Save As...", self)
        self.action_save_as.setShortcut("Ctrl+S")
        self.action_save_as.setStatusTip("Save selected layer (Ctrl+S).")
        self.file_menu.addAction(self.action_save_as)

        self.file_menu.addAction(self.action_save_as)
        self.action_save_pipeline = QAction(QIcon("ui/resources/icons/save_pipeline.png"), "Save Pipeline...", self)
        self.action_save_pipeline.setShortcut("Ctrl+P")
        self.action_save_pipeline.setStatusTip("Save active pipeline (Ctrl+P).")
        self.file_menu.addAction(self.action_save_pipeline)

        self.file_toolbar = self.addToolBar("File Operations")
        self.file_toolbar.setMovable(False)

        self.file_toolbar.addAction(self.action_open_file)
        self.file_toolbar.addAction(self.action_run_pipeline)
        self.file_toolbar.addAction(self.action_save_as)
        self.file_toolbar.addAction(self.action_save_pipeline)
        self.file_toolbar.addSeparator()

        self.action_about = QAction(QIcon("ui/resources/icons/about.png"), "About", self)
        self.action_about.setStatusTip("About")
        self.action_about.triggered.connect(self._open_about)

        self.help_menu.addAction(self.action_about)

        self._setup_log_panel()
        self._setup_left_panels()
        self._setup_central_widget()
        self._setup_filter_panel()
        self._create_status_bar()
        self._apply_standard_style()

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
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderHidden(True)
        self.data_tree.itemClicked.connect(self._on_data_item_selected)

        self.data_sources_dock = QDockWidget("Data Sources", self)
        self.data_sources_dock.setWidget(self.data_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_sources_dock)

        self.metadata_dock = QDockWidget("Metadata", self)
        
        self.summary_metadata_table = QTableWidget() 
        self.summary_metadata_table.setColumnCount(2)
        self.summary_metadata_table.setHorizontalHeaderLabels(["Özellik", "Değer"])
        self.summary_metadata_table.horizontalHeader().setVisible(False)
        self.summary_metadata_table.setEditTriggers(QTableWidget.NoEditTriggers) 
        self.summary_metadata_table.setSelectionMode(QTableWidget.NoSelection)
        self.summary_metadata_table.verticalHeader().setVisible(False) 

        self.summary_metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        self.summary_metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) 
        
        self.summary_metadata_table.setRowCount(1)

        self.metadata_dock.setWidget(self.summary_metadata_table)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.metadata_dock)

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
        file_icon = QIcon("ui/resources/icons/file.png")

        self._data_cache[file_path] = {
            "bounds":bounds,
            "full_metadata": full_metadata,
            "summary_metadata": summary_metadata,
            "sample_data": sample_data
        }

        new_item = QTreeWidgetItem(self.data_tree, [file_name])
        new_item.setIcon(0, file_icon)
        new_item.setData(0, Qt.UserRole, file_path)
        self.data_tree.addTopLevelItem(new_item)
        self.data_tree.setCurrentItem(new_item)
        self._on_data_item_selected(new_item)
        self.logger.info(f"File '{file_name}' successfully added to data sources.")

    def _handle_reader_error(self, error_message: str):
        self.progressBar.hide()
        self.statusBar().showMessage("ERROR: File reading failed.", 5000)
        self.logger.error(error_message)

    def _setup_filter_panel(self):
        self.filters_dock = QDockWidget("Filters", self)
        filters_content = QTextEdit()
        filters_content.setPlainText("")
        self.filters_dock.setWidget(filters_content)
        self.addDockWidget(Qt.RightDockWidgetArea, self.filters_dock)

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

    def _update_metadata_panel(self, file_name: str, summary_metadata: dict):
        points = summary_metadata.get("points", "N/A")
        is_compressed = summary_metadata.get("is_compressed")
        crs_name = summary_metadata.get("crs_name", "N/A")
        epsg = summary_metadata.get("epsg", "N/A")
        software = summary_metadata.get("software_id", "N/A")
        x_range = summary_metadata.get("x_range")
        y_range = summary_metadata.get("y_range")
        z_range = summary_metadata.get("z_range")
        unit = summary_metadata.get("unit")

        self.summary_metadata_table.setRowCount(0)

        data_to_display = [
            ("Filename", file_name),
            ("Points", points),
            ("Compressed", is_compressed),
            ("Software", software),
            ("CRS Name", crs_name),
            ("EPSG Code", epsg),
            ("Unit", unit),
            ("X Range", x_range),
            ("Y Range", y_range),
            ("Z Range", z_range)
        ]

        self.summary_metadata_table.setRowCount(len(data_to_display))

        for row, (key ,value) in enumerate(data_to_display):
            key_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(str(value))
            
            font = QFont()
            font.setBold(True)
            key_item.setFont(font)

            self.summary_metadata_table.setItem(row, 0, key_item)
            self.summary_metadata_table.setItem(row, 1, value_item)

    def _on_data_item_selected(self, item: QTreeWidgetItem):
        file_path = item.data(0, Qt.UserRole)
        file_name = item.text(0)

        if not file_path:
            self.logger.warning(f"No file path found for the selected item: {file_name}")
            return
        
        cached_data = self._data_cache.get(file_path)
        
        if not cached_data:
            self.logger.error(f"Veri cache'te bulunamadı: {file_path}")
            self.summary_metadata_table.clearContents()
            self.summary_metadata_table.setRowCount(1)
            self.summary_metadata_table.setItem(0, 0, QTableWidgetItem("HATA: Cache boş"))
            return
            
        summary_metadata = cached_data["summary_metadata"]

        if summary_metadata.get("status"):
            self._update_metadata_panel(file_name, summary_metadata)
        else:
            self.logger.error(f"Metadata okuma hatası: {summary_metadata.get('error', 'Bilinmeyen Hata')}")
            self.summary_metadata_table.clearContents()
            self.summary_metadata_table.setRowCount(1)
            self.summary_metadata_table.setItem(0, 0, QTableWidgetItem("HATA: Veri okunamadı."))
            self.summary_metadata_table.setItem(0, 1, QTableWidgetItem(summary_metadata.get('error', '')))