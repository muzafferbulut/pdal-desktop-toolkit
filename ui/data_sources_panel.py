from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QDockWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional

class DataSourcesPanel(QWidget):

    file_single_clicked = pyqtSignal(str, str)
    file_double_clicked = pyqtSignal(str, str)

    def __init__(self, parent:Optional[QWidget] = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.data_tree = self._setup_tree_widget()
        self.layout.addWidget(self.data_tree)

    def _setup_tree_widget(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.itemClicked.connect(self._on_single_clicked)
        tree.itemDoubleClicked.connect(self._on_double_clicked)
        return tree
    
    def _on_single_clicked(self, item: QTreeWidgetItem):
        file_path = item.data(0, Qt.UserRole)
        file_name = item.text(0)

        if file_path:
            self.file_single_clicked.emit(file_path, file_name)

    def _on_double_clicked(self, item: QTreeWidgetItem, column: int):
        file_path = item.data(0, Qt.UserRole)
        file_name = item.text(0)

        if file_path:
            self.file_double_clicked.emit(file_path, file_name)

    def add_file(self, file_path:str, file_name:str):
        file_icon = QIcon("ui/resources/icons/file.png")
        new_item = QTreeWidgetItem(self.data_tree, [file_name])
        new_item.setIcon(0, file_icon)
        new_item.setData(0, Qt.UserRole, file_path)
        self.data_tree.addTopLevelItem(new_item)
        self.data_tree.setCurrentItem(new_item)
        self.file_single_clicked.emit(file_path, file_name)