from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QListWidgetItem,
    QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt


class MergeDialog(QDialog):

    def __init__(self, available_layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Merge Layers")
        self.resize(350, 400)
        self.available_layers = available_layers
        self.selected_files = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Select layers to merge (Ctrl+Click for multi):"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)

        for path, name in self.available_layers.items():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setText("Merge")
        layout.addWidget(self.button_box)

    def _on_accept(self):
        self.selected_files = []
        for item in self.list_widget.selectedItems():
            self.selected_files.append(item.data(Qt.UserRole))

        if len(self.selected_files) < 2:
            QMessageBox.warning(
                self, "Warning", "Please select at least 2 layers to merge."
            )
            return

        self.accept()

    def get_files(self):
        return self.selected_files
