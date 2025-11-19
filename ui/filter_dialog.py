from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, 
    QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt
from typing import Dict, Any

class FilterParamsDialog(QDialog):

    def __init__(self, tool_name:str, default_params:Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure {tool_name}")
        self.setMinimumWidth(300)

        self.default_params = default_params
        self.result_params = {}
        self._widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        layout.addLayout(form_layout)

        for key, value in self.default_params.items():
            label_text = key.replace("_", " ").title()
            widget = self._create_widget_for_value(value)
            self._widgets[key] = widget
            form_layout.addRow(f"{label_text}:", widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_widget_for_value(self, value):
        
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            return widget
        
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(3)
            widget.setValue(value)
            return widget
        
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(value)
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