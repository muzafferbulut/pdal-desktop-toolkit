from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,QToolButton, QDialogButtonBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

class CropDialog(QDialog):
    
    draw_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Point Cloud")
        self.resize(500, 80)
        self.final_bounds_str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)
        
        self.le_bounds = QLineEdit()
        self.le_bounds.setPlaceholderText("([minx, maxx], [miny, maxy], [minz, maxz])")
        self.le_bounds.setToolTip("Enter bounds in PDAL format or use the buttons.")

        self.btn_draw = QToolButton()
        self.btn_draw.setIcon(QIcon("ui/resources/icons/crop.png"))
        self.btn_draw.setToolTip("Draw BBox on 3D View (Right click on screen to finish)")
        self.btn_draw.clicked.connect(self._on_start_draw)
        
        h_layout.addWidget(self.le_bounds)
        h_layout.addWidget(self.btn_draw)
        
        layout.addLayout(h_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setText("Apply")
        
        layout.addWidget(self.button_box)

    def _on_start_draw(self):
        self.draw_requested.emit()

    def update_bounds_from_gizmo(self, bounds):
        try:
            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            bounds_str = f"([{xmin:.3f}, {xmax:.3f}], [{ymin:.3f}, {ymax:.3f}], [{zmin:.3f}, {zmax:.3f}])"
            self.le_bounds.setText(bounds_str)
        except Exception as e:
            print(f"Bounds format error: {e}")

    def _on_accept(self):
        self.final_bounds_str = self.le_bounds.text()
        self.accept()

    def get_params(self):
        return {"bounds": self.final_bounds_str}