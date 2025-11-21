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
            * {
                background-color: %(background)s;
                color: %(text)s;
                border: none;
                outline: none;
                font-family: 'Segoe UI', sans-serif;
            }

            /* --- Buttons --- */
            QPushButton {
                background-color: %(button_bg)s;
                border: 1px solid %(border)s;
                padding: 5px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: %(button_hover)s;
                border: 1px solid %(primary)s;
            }
            QPushButton:pressed {
                background-color: %(button_pressed)s;
            }

            /* --- Main Structure --- */
            QMainWindow {
                background-color: %(background_alt)s;
            }
            QDockWidget {
                border: 1px solid %(border)s;
            }
            QDockWidget::title {
                background-color: %(header_bg)s;
                color: %(header_text)s;
                padding: 6px;
                border-bottom: 2px solid %(primary)s;
                font-weight: bold;
            }
            
            /* --- Input Fields --- */
            QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
                background-color: %(input_bg)s;
                border: 1px solid %(border)s;
                border-radius: 3px;
                padding: 4px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid %(primary)s;
            }

            /* --- Lists & Trees --- */
            QTreeWidget, QListWidget, QTableWidget {
                background-color: %(input_bg)s;
                border: 1px solid %(border)s;
                alternate-background-color: %(background_alt)s;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: %(selection_bg)s;
                color: %(selection_text)s;
            }
            QHeaderView::section {
                background-color: %(header_bg)s;
                border: 1px solid %(border)s;
                padding: 4px;
            }

            /* --- Tabs --- */
            QTabWidget::pane {
                border: 1px solid %(border)s;
            }
            QTabBar::tab {
                background-color: %(background_alt)s;
                border: 1px solid %(border)s;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: %(background)s;
                border-bottom: 2px solid %(primary)s;
                color: %(primary)s;
                font-weight: bold;
            }

            /* --- Menus --- */
            QMenuBar {
                background-color: %(header_bg)s;
                border-bottom: 1px solid %(border)s;
            }
            QMenuBar::item:selected {
                background-color: %(selection_bg)s;
                color: %(selection_text)s;
            }
            QMenu {
                background-color: %(background)s;
                border: 1px solid %(border)s;
            }
            QMenu::item:selected {
                background-color: %(selection_bg)s;
                color: %(selection_text)s;
            }
            
            /* --- Misc --- */
            QProgressBar {
                border: 1px solid %(border)s;
                background-color: %(background_alt)s;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: %(primary)s;
            }
            QFrame[frameShape="4"] { /* HLine */
                color: %(border)s;
            }
        """
        return base_css % colors