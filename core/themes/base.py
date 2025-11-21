from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTheme(ABC):

    @property
    @abstractmethod 
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def palette(self) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def three_d_background(self) -> Dict[str, str]:
        pass

    @property
    @abstractmethod
    def map_style(self) -> str:
        pass

    def get_stylesheet(self) -> str:
        colors = self.palette
        
        base_css = """
        QWidget {
            background-color: %(background)s;
            color: %(text)s;
            font-family: 'Segoe UI', sans-serif;
            font-size: 9pt;
            selection-background-color: %(selection_bg)s;
            selection-color: %(selection_text)s;
            outline: none;
        }
        QPushButton {
            background-color: %(button_bg)s;
            border: 1px solid %(border)s;
            border-radius: 4px;
            padding: 6px 16px;
            min-height: 20px;
            margin: 2px; 
        }
        QPushButton:hover {
            background-color: %(button_hover)s;
            border: 1px solid %(primary)s;
        }
        QPushButton:pressed {
            background-color: %(button_pressed)s;
        }
        QPushButton:disabled {
            color: #888888;
            background-color: %(background_alt)s;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
            background-color: %(input_bg)s;
            border: 1px solid %(border)s;
            border-radius: 4px;
            padding: 5px 8px;
            min-height: 20px;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid %(primary)s;
        }
        QComboBox {
            border: 1px solid %(border)s;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: %(input_bg)s;
            min-height: 20px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 0px;
        }
        QDockWidget {
            border: 1px solid %(border)s;
        }
        QDockWidget::title {
            background-color: %(header_bg)s;
            color: %(header_text)s;
            padding: 8px 12px;
            border-bottom: 2px solid %(primary)s;
            font-weight: 600;
        }
        QDockWidget > QWidget { 
            border: 1px solid %(border)s;
        }
        QToolBar {
            background-color: %(header_bg)s;
            border-bottom: 1px solid %(border)s;
            padding: 5px; 
            spacing: 10px;
        }
        QToolButton {
            background-color: transparent;
            border-radius: 4px;
            padding: 6px; 
        }
        QToolButton:hover {
            background-color: %(button_hover)s;
        }
        QTreeWidget, QListWidget, QTableWidget {
            background-color: %(input_bg)s;
            border: 1px solid %(border)s;
            alternate-background-color: %(background_alt)s;
        }
        QTreeWidget::item, QListWidget::item, QTableWidget::item {
            padding: 2px 2px; 
            margin: 0px;
        }
        QHeaderView::section {
            background-color: %(header_bg)s;
            color: %(header_text)s;
            border: none;
            border-right: 1px solid %(border)s;
            border-bottom: 1px solid %(border)s;
            padding: 6px 10px;
            font-weight: bold;
        }
        QGroupBox {
            border: 1px solid %(border)s;
            border-radius: 6px;
            margin-top: 24px; 
            padding-top: 10px; 
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 5px;
            color: %(primary)s;
            font-weight: bold;
        }
        QTabWidget::pane {
            border: 1px solid %(border)s;
            background-color: %(background)s;
            top: -1px;
        }
        
        QTabBar::tab {
            background-color: %(background_alt)s;
            border: 1px solid %(border)s;
            padding: 8px 24px; 
            min-width: 60px;
        }
        
        QTabBar::tab:selected {
            background-color: %(background)s;
            border-bottom: 2px solid %(primary)s; 
            padding-bottom: 6px; 
            color: %(primary)s;
            font-weight: bold;
        }
        
        QTabBar::tab:!selected:hover {
            background-color: %(button_hover)s;
            margin-top: 2px; 
            padding-bottom: 6px;
        }
        QMenuBar {
            background-color: %(header_bg)s;
            padding: 4px;
            border-bottom: 1px solid %(border)s;
        }
        QMenuBar::item {
            padding: 6px 12px;
            margin-right: 4px;
            border-radius: 4px;
        }
        QMenuBar::item:selected {
            background-color: %(button_hover)s;
        }
        QMenu {
            border: 1px solid %(border)s;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 24px 6px 10px; /* Sağ tarafa ikon payı bırak */
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: %(selection_bg)s;
            color: %(selection_text)s;
        }
        QProgressBar {
            text-align: center;
            border: 1px solid %(border)s;
            border-radius: 4px;
            background-color: %(background_alt)s;
            height: 18px;
        }
        QProgressBar::chunk {
            background-color: %(primary)s;
            border-radius: 3px;
        }
        """
        return base_css % colors