from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QFrame,
    QMessageBox,
)
from core.tools.registry import ToolRegistry
from PyQt5.QtCore import Qt
from typing import Dict, Any


class FilterParamsDialog(QDialog):

    def __init__(self, tool_name: str, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.result_params = {}
        self._widgets = {}

        try:
            self.tool_cls = ToolRegistry.get_tool(tool_name)
            self.tool_instance = self.tool_cls()
        except ValueError:
            QMessageBox.critical(
                self, "Error", f"Tool definition not found: {tool_name}"
            )
            self.reject()
            return

        self.default_params = self.tool_instance.get_default_params()
        self.description_text = self.tool_instance.description

        self.setWindowTitle(f"Configure {self.tool_cls.name}")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        header_layout = QHBoxLayout()
        title_content_layout = QVBoxLayout()

        title_label = QLabel(self.tool_cls.name)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

        desc_label = QLabel(self.description_text)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        desc_label.setWordWrap(True)

        title_content_layout.addWidget(title_label)
        title_content_layout.addWidget(desc_label)
        header_layout.addLayout(title_content_layout)
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

        main_layout.addWidget(button_box)

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
