from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QAction,
    QPlainTextEdit,
    QDockWidget,
    QTreeWidget,
    QTabWidget,
    QFileDialog,
    QTreeWidgetItem,
    QProgressBar,
    QApplication,
    QTextEdit
)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QTextCursor, QFont
from ui.tab_viewers import GISMapView, ThreeDView
from data.data_handler import IDataReader
from core.logger import Logger
from PyQt5.QtCore import Qt, QThread
from core.read_worker import ReaderWorker
from typing import Optional
import re
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

        # arayüz bileşenleri
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
        self.file_menu.addAction(self.action_run_pipeline)

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

        self._setup_log_panel()
        self._setup_left_panels()
        self._setup_central_widget()
        self._setup_filter_panel()
        self._create_status_bar()
        self._apply_standard_style()

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
        self.metadata_content = QTextEdit()
        self.metadata_content.setPlainText("")
        self.metadata_dock.setWidget(self.metadata_content)
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
            
    def _handle_reader_success(self, file_path:str):
        self.progressBar.hide()
        self.statusBar().showMessage(f"File '{os.path.basename(file_path)}' loaded successfully!", 5000)
        file_name = os.path.basename(file_path)
        file_icon = QIcon("ui/resources/icons/file.png")
        new_item = QTreeWidgetItem(self.data_tree, [file_name])
        new_item.setIcon(0, file_icon)
        new_item.setData(0, Qt.UserRole, file_path)
        self.data_tree.addTopLevelItem(new_item)
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
        /* ... PAYLAŞTIĞINIZ TÜM STİL KODU BURAYA GELECEK ... */
        * {
            background-color: #ffffff;
            color: #333333;
            border: none;
            outline: none;
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

        /* Dock başlıkları - mavi alt çizgi */
        QDockWidget::title {
            background-color: #f1f3f4;
            color: #333333;
            padding: 9px 12px;
            font-weight: 500;
            border-bottom: 2px solid #0078d4; /* Mavi vurgu çizgisi */
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
        
        QTextEdit, QLineEdit, QPlainTextEdit, QTreeWidget { /* QTreeWidget'ı ekledik */
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

    def _on_data_item_selected(self, item: QTreeWidgetItem, column: int):
        file_path = item.data(0, Qt.UserRole)

        if not file_path:
            self.logger.warning(
                f"No file path found for the selected item. {item.text(0)}"
            )
            return
        
        self.logger.info(f"'{item.text(0)}' selected. Getting BBox and Metadata...")

        full_metadata = self.reader.get_metadata()
        bounds_result = self.reader.get_bounds()

        if bounds_result.get("status") is True and full_metadata.get("status") is True:
            bounds = bounds_result.get("bounds")
            
            pdal_metadata = full_metadata.get("metadata", {})
            las_info = pdal_metadata.get("readers.las", {})
            point_count = las_info.get('count', 'N/A')
            crs_full_text = las_info.get('spatialreference', 'Unknown')
            crs_name_match = re.search(r'PROJCS\["([^"]+)"', crs_full_text)
            crs_display_name = crs_name_match.group(1) if crs_name_match else "Unknown"
            minx = bounds['minx']
            maxx = bounds['maxx']
            miny = bounds['miny']
            maxy = bounds['maxy']
                                    
            metadata_display = f"""
                <p style='font-size: 16px; font-weight: bold; color: #0078d4;'>{item.text(0)}</p>
                <hr style='border-top: 1px solid #dee2e6;'>
                
                <p><b><i style='color: #2196F3;'>&#x25A3;</i> İstatistikler</b></p>
                <ul style='list-style-type: none; padding-left: 15px;'>
                    <li><b>Toplam Nokta:</b> {point_count}</li>
                    <li><b>Sıkıştırma:</b> {"LAZ (Sıkıştırılmış)" if las_info.get('compressed') else "LAS (Sıkıştırılmamış)"}</li>
                    <li><b>Format Sürümü:</b> {las_info.get('major_version', 'N/A')}.{las_info.get('minor_version', 'N/A')}</li>
                </ul>
                
                <p><b><i style='color: #2196F3;'>&#x25A3;</i> Mekansal Bilgi</b></p>
                <ul style='list-style-type: none; padding-left: 15px;'>
                    <li><b>Koordinat Sistemi:</b> {crs_display_name}</li>
                    <li><b>X Min:</b> {minx}</li>
                    <li><b>Y Min:</b> {miny}</li>
                    <li><b>X Max:</b> {maxx}</li>
                    <li><b>Y Max:</b> {maxy}</li>

                </ul>
            """
            self.metadata_content.setHtml(metadata_display)

        else:
            self.logger.error(
                f"Veri çekilemedi. BBox Hatası: {bounds_result.get('error', 'N/A')}. Metadata Hatası: {full_metadata.get('error', 'N/A')}"
            )