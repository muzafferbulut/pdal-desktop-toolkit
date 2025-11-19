from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDialogButtonBox,
    QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox, QGroupBox,
    QFrame
)
from PyQt5.QtCore import Qt
from typing import Dict, Any

class FilterParamsDialog(QDialog):
    
    TOOL_DESCRIPTIONS = {
        # Data Management
        "Merge": "Combines multiple point cloud datasets into a single file.",
        "Splitter": "Splits the point cloud into multiple parts based on a spatial grid or capacity.",

        # Pre-processing & Cleaning
        "Crop": "Removes points falling outside a defined bounding box or polygon.",
        "Decimation": "Reduces point density by keeping every Nth point to optimize performance.",
        "Outlier": "Removes noise using statistical analysis (Mean/Stdev) or radius search.",
        "ELM": "Extended Local Minimum: Identifies low noise points below the estimated surface.",
        "Range": "Keeps only points that fall within a specific range for a given dimension (e.g., Z, Intensity).",

        # Classification & Analysis
        "CSF": "Cloth Simulation Filter: Classifies ground points by simulating a cloth dropping on the terrain.",
        "SMRF": "Simple Morphological Filter: Segments ground and non-ground points using morphological operations.",
        "HAG": "Height Above Ground: Normalizes Z values by calculating the height relative to the ground surface.",
        "Normal": "Computes surface normals and curvature estimates for each point.",
        "Cluster": "Groups spatially close points into clusters using Euclidean distance (DBSCAN).",

        # Georeferencing & Transforms
        "Reprojection": "Reprojects data from one Coordinate Reference System (CRS) to another.",
        "Transformation": "Applies a 4x4 affine transformation matrix to scale, rotate, or translate data.",

        # Rasterization
        "DSM": "Digital Surface Model: Generates a raster grid representing the highest surface elevation.",
        "DTM": "Digital Terrain Model: Generates a raster grid representing the bare earth elevation."
    }

    def __init__(self, tool_name: str, default_params: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.default_params = default_params
        self.result_params = {}
        self._widgets = {}
        
        self.setWindowTitle(f"Configure {tool_name}")
        self.setMinimumWidth(400)
        
        self._apply_stylesheet()
        self._setup_ui()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
                font-family: 'Segoe UI';
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                selection-background-color: #0078d4;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #0078d4;
                background-color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 20px;
                font-weight: bold;
                color: #555;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #f1f1f1;
                border: 1px solid #d1d1d1;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e1e1e1;
            }
            QPushButton[text="OK"] {
                background-color: #0078d4;
                color: white;
                border: 1px solid #0067b5;
            }
            QPushButton[text="OK"]:hover {
                background-color: #0067b5;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        header_layout = QHBoxLayout()
        
        try:
            icon_label = QLabel()
            header_layout.addWidget(icon_label)
        except:
            pass

        title_content_layout = QVBoxLayout()
        title_label = QLabel(self.tool_name)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        
        desc_text = self.TOOL_DESCRIPTIONS.get(self.tool_name, "Configure parameters for this tool.")
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        desc_label.setWordWrap(True)

        title_content_layout.addWidget(title_label)
        title_content_layout.addWidget(desc_label)
        header_layout.addLayout(title_content_layout)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)

        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(line)

        param_group = QGroupBox("Parameters")
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setVerticalSpacing(12)
        form_layout.setContentsMargins(15, 20, 15, 15)

        for key, value in self.default_params.items():
            label_text = key.replace("_", " ").title()
            label_widget = QLabel(label_text)
            label_widget.setStyleSheet("font-weight: 500;")
            
            widget = self._create_widget_for_value(value)
            self._widgets[key] = widget
            form_layout.addRow(label_widget, widget)

        param_group.setLayout(form_layout)
        main_layout.addWidget(param_group)

        main_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        button_box.button(QDialogButtonBox.Ok).setText("Apply")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancel")
        
        main_layout.addWidget(button_box)

    def _create_widget_for_value(self, value):
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            widget.setStyleSheet("margin-left: 5px;")
            return widget
            
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(3)
            widget.setValue(value)
            widget.setButtonSymbols(QDoubleSpinBox.NoButtons)
            return widget
            
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(value)
            widget.setButtonSymbols(QSpinBox.NoButtons)
            return widget
            
        else:
            widget = QLineEdit(str(value))
            return widget

    def _on_accept(self):
        for key, widget in self._widgets.items():
            if isinstance(widget, QCheckBox):
                self.result_params[key] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                self.result_params[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                self.result_params[key] = widget.text()
        
        self.accept()

    def get_params(self) -> Dict[str, Any]:
        return self.result_params