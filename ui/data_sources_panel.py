from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMenu
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
    remove_stage_requested = pyqtSignal(str, int)
    style_changed_requested = pyqtSignal(str, str)
    visibility_changed_requested = pyqtSignal(str, bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.data_tree = self._setup_tree_widget()
        self.layout.addWidget(self.data_tree)

        # dosya yollarını ve uygulanan filtreleri tutacak
        self.layer_items = {}

    def _setup_tree_widget(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.itemClicked.connect(self._on_single_clicked)
        tree.itemDoubleClicked.connect(self._on_double_clicked)
        tree.itemChanged.connect(self._on_item_changed)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_context_menu)
        return tree

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        if item.data(0, Qt.UserRole + 1) == "root":
            file_path = item.data(0, Qt.UserRole)
            is_visible = item.checkState(0) == Qt.Checked
            self.visibility_changed_requested.emit(file_path, is_visible)

    def get_selected_file_path(self) -> Optional[str]:
        item = self.data_tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def _show_context_menu(self, position):
        item = self.data_tree.itemAt(position)
        if not item:
            return

        item_type = item.data(0, Qt.UserRole + 1)
        file_path = item.data(0, Qt.UserRole)

        menu = QMenu()

        if item_type == "root":
            action_zoom = menu.addAction(
                QIcon("ui/resources/icons/zoom_to.png"), "Zoom to BBox"
            )
            color_menu = menu.addMenu(
                QIcon("ui/resources/icons/color_by.png"), "Color By"
            )
            act_elev = color_menu.addAction("Elevation (Z)")
            act_int = color_menu.addAction("Intensity")
            act_rgb = color_menu.addAction("RGB (True Color)")
            act_cls = color_menu.addAction("Classification")
            menu.addSeparator()
            action_export = menu.addAction(
                QIcon("ui/resources/icons/export.png"), "Export Layer"
            )
            action_save_pipe = menu.addAction(
                QIcon("ui/resources/icons/save_pipeline.png"), "Save Pipeline"
            )
            action_save_meta = menu.addAction(
                QIcon("ui/resources/icons/metadata.png"), "Save Full Metadata"
            )
            menu.addSeparator()
            action_remove = menu.addAction(
                QIcon("ui/resources/icons/remove.png"), "Remove Layer"
            )

            selected_action = menu.exec_(self.data_tree.mapToGlobal(position))

            if selected_action == action_zoom:
                self.zoom_to_bbox_requested.emit(file_path)
            elif selected_action == action_export:
                self.export_layer_requested.emit(file_path)
            elif selected_action == action_save_pipe:
                self.save_pipeline_requested.emit(file_path)
            elif selected_action == action_save_meta:
                self.save_full_metadata_requested.emit(file_path)
            elif selected_action == action_remove:
                self.remove_layer_requested.emit(file_path)
            elif selected_action == act_elev:
                self.style_changed_requested.emit(file_path, "Elevation")
            elif selected_action == act_int:
                self.style_changed_requested.emit(file_path, "Intensity")
            elif selected_action == act_rgb:
                self.style_changed_requested.emit(file_path, "RGB")
            elif selected_action == act_cls:
                self.style_changed_requested.emit(file_path, "Classification")

        elif item_type == "stage":
            action_delete_stage = menu.addAction(
                QIcon("ui/resources/icons/remove.png"), "Delete Stage"
            )
            selected_action = menu.exec_(self.data_tree.mapToGlobal(position))

            if selected_action == action_delete_stage:
                parent = item.parent()
                index = parent.indexOfChild(item)
                parent.removeChild(item)
                self.remove_stage_requested.emit(file_path, index)

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

    def add_file(self, file_path: str, file_name: str):
        if file_path in self.layer_items:
            return

        icon_path = (
            "ui/resources/icons/database.png"
            if file_path.startswith("DB://")
            else "ui/resources/icons/file.png"
        )
        file_icon = QIcon(icon_path)

        root_item = QTreeWidgetItem(self.data_tree, [file_name])
        root_item.setIcon(0, file_icon)
        root_item.setData(0, Qt.UserRole, file_path)
        root_item.setData(0, Qt.UserRole + 1, "root")
        root_item.setCheckState(0, Qt.Checked)
        self.data_tree.addTopLevelItem(root_item)

        self.layer_items[file_path] = root_item
        self.data_tree.setCurrentItem(root_item)
        self.file_single_clicked.emit(file_path, file_name)

    def add_stage_node(self, file_path: str, stage_name: str, stage_details: str):
        parent_item = self.layer_items.get(file_path)

        if not parent_item:
            return

        try:
            stage_icon = QIcon("ui/resources/icons/stage.png")
        except:
            stage_icon = QIcon()

        display_text = f"{stage_name}"
        if stage_details:
            display_text += f" ({stage_details})"

        child_item = QTreeWidgetItem(parent_item, [display_text])
        child_item.setIcon(0, stage_icon)
        child_item.setData(0, Qt.UserRole, file_path)
        child_item.setData(0, Qt.UserRole + 1, "stage")
        parent_item.setExpanded(True)

    def remove_layer(self, file_path: str):
        if file_path in self.layer_items:
            item = self.layer_items[file_path]
            root = self.data_tree.invisibleRootItem()
            root.removeChild(item)
            del self.layer_items[file_path]

    def get_loaded_layers(self) -> dict:
        layers = {}
        for path, item in self.layer_items.items():
            if item.data(0, Qt.UserRole + 1) == "root":
                layers[path] = item.text(0)
        return layers
