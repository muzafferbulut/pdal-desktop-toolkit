from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
    QLineEdit,
    QToolButton,
    QDialogButtonBox,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtGui import QIcon


class ModelDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Elevation Model")
        self.resize(400, 180)
        self.result_params = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        form.setSpacing(10)
        self.sb_resolution = QDoubleSpinBox()
        self.sb_resolution.setRange(0.01, 1000.0)
        self.sb_resolution.setValue(1.0)
        self.sb_resolution.setSuffix(" m")
        self.sb_resolution.setToolTip("Size of each pixel in the output raster.")
        form.addRow("Grid Resolution:", self.sb_resolution)
        self.cb_type = QComboBox()
        self.cb_type.addItems(["max", "min", "mean", "idw", "count", "stdev"])
        self.cb_type.setToolTip("Select 'max' for DSM, 'min' for DTM.")
        form.addRow("Algorithm:", self.cb_type)
        file_layout = QHBoxLayout()
        self.le_output = QLineEdit()
        self.le_output.setPlaceholderText("Select output file (*.tif)...")

        self.btn_browse = QToolButton()
        try:
            self.btn_browse.setIcon(QIcon("ui/resources/icons/open.png"))
        except:
            self.btn_browse.setText("...")
        self.btn_browse.clicked.connect(self._browse_file)

        file_layout.addWidget(self.le_output)
        file_layout.addWidget(self.btn_browse)

        form.addRow("Output GeoTIFF:", file_layout)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Elevation Model", "", "GeoTIFF Files (*.tif)"
        )
        if path:
            if not path.lower().endswith(".tif"):
                path += ".tif"
            self.le_output.setText(path)

    def _on_accept(self):
        if not self.le_output.text():
            QMessageBox.warning(self, "Missing Input", "Please specify an output file.")
            return

        self.result_params = {
            "resolution": self.sb_resolution.value(),
            "output_type": self.cb_type.currentText(),
            "filename": self.le_output.text(),
        }
        self.accept()

    def get_params(self):
        return self.result_params
