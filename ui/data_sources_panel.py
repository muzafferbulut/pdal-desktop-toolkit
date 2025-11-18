from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMenu, QTreeWidgetItemIterator
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional

class DataSourcesPanel(QWidget):

    file_single_clicked = pyqtSignal(str, str)
    file_double_clicked = pyqtSignal(str, str)
    zoom_to_bbox_requested = pyqtSignal(str)
    export_layer_requested = pyqtSignal(str)
    save_pipeline_requested = pyqtSignal(str)
    save_full_metadata_requested = pyqtSignal(str)
    remove_layer_requested = pyqtSignal(str)

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
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_context_menu)
        return tree
    
    def _show_context_menu(self, position):
        item = self.data_tree.itemAt(position)
        if item and item.data(0, Qt.UserRole):
            file_path = item.data(0, Qt.UserRole)
            
            menu = QMenu()
            
            action_zoom_to_bbox = menu.addAction(QIcon("ui/resources/icons/zoom_to.png"), "Zoom to BBox")
            menu.addSeparator()
            action_export_layer = menu.addAction(QIcon("ui/resources/icons/export.png"), "Export Layer")
            action_save_pipeline = menu.addAction(QIcon("ui/resources/icons/save_pipeline.png"), "Save Pipeline")
            action_save_metadata = menu.addAction(QIcon("ui/resources/icons/metadata.png"), "Save Full Metadata")
            menu.addSeparator()
            action_remove = menu.addAction(QIcon("ui/resources/icons/remove.png"), "Remove Layer")
            
            selected_action = menu.exec_(self.data_tree.mapToGlobal(position))
            
            if selected_action == action_zoom_to_bbox:
                self.zoom_to_bbox_requested.emit(file_path)
            elif selected_action == action_export_layer:
                self.export_layer_requested.emit(file_path)
            elif selected_action == action_save_pipeline:
                self.save_pipeline_requested.emit(file_path)
            elif selected_action == action_save_metadata:
                self.save_full_metadata_requested.emit(file_path)
            elif selected_action == action_remove:
                self.remove_layer_requested.emit(file_path)

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

    def remove_layer(self, file_path:str):
        iterator = QTreeWidgetItemIterator(self.data_tree)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) == file_path:
                root = item.parent() or self.data_tree.invisibleRootItem()
                root.removeChild(item)
                del item
                break
            iterator +=1