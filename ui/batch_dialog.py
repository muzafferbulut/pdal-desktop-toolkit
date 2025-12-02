from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QComboBox, QLabel, QStyle, QFrame, 
                             QFileDialog, QMessageBox)
from core.pipeline_builder import PipelineBuilder
from ui.filter_dialog import FilterParamsDialog
from core.tools.registry import ToolRegistry
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

class BatchProcessDialog(QDialog):

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Batch Processor")
        self.resize(400, 500)
        self.queued_stages = [] 
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        btn_load = self._create_icon_button(
            "Load Preset", 
            self.style().standardIcon(QStyle.SP_DialogOpenButton), 
            self._on_load_preset
        )

        btn_save = self._create_icon_button(
            "Save Preset", 
            self.style().standardIcon(QStyle.SP_DialogSaveButton), 
            self._on_save_preset
        )

        toolbar_layout.addWidget(btn_load)
        toolbar_layout.addWidget(btn_save)

        self._add_separator(toolbar_layout)

        btn_up = self._create_icon_button(
            "Move Up", 
            QIcon("ui/resources/icons/up.png"), 
            self._move_up
        )

        btn_down = self._create_icon_button(
            "Move Down", 
            QIcon("ui/resources/icons/down.png"), 
            self._move_down
        )

        btn_remove = self._create_icon_button(
            "Remove Selected", 
            QIcon("ui/resources/icons/remove.png"), 
            self._remove_item
        )

        toolbar_layout.addWidget(btn_up)
        toolbar_layout.addWidget(btn_down)
        toolbar_layout.addWidget(btn_remove)

        btn_run = self._create_icon_button(
            "Run Batch", 
            QIcon("ui/resources/icons/run.png"), 
            self.accept
        )

        toolbar_layout.addWidget(btn_run)
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        h_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(h_line)

        tool_select_layout = QHBoxLayout()
        tool_select_layout.setContentsMargins(0, 0, 0, 0)
        tool_select_layout.setSpacing(10)

        self.cb_tools = QComboBox()
        self.cb_tools.setFixedHeight(32)
        self.cb_tools.setStyleSheet("""
            QComboBox { padding-left: 5px; }
            QComboBox QAbstractItemView::item { 
                min-height: 30px; 
                padding: 4px; 
            }
        """)

        tools = ToolRegistry.get_all_tools()
        for name, tool_cls in tools.items():
            if tool_cls.supports_batch:
                self.cb_tools.addItem(name)

        btn_add = self._create_icon_button(
            "Add Tool to Queue", 
            QIcon("ui/resources/icons/add.png"), 
            self._on_add_tool_clicked
        )

        btn_add.setFixedSize(32, 32)
        btn_add.setIconSize(QSize(24, 24))

        tool_select_layout.addWidget(QLabel("Select Tool:"), 0, Qt.AlignVCenter)
        tool_select_layout.addWidget(self.cb_tools, 1, Qt.AlignVCenter)
        tool_select_layout.addWidget(btn_add, 0, Qt.AlignVCenter)

        layout.addLayout(tool_select_layout)
        layout.addWidget(QLabel("Execution Queue:"))
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget::item { 
                padding: 5px; 
                border-bottom: 1px solid #eee; 
            }
        """)
        layout.addWidget(self.list_widget)

    def _create_icon_button(self, tooltip, icon, slot):
        btn = QPushButton()
        btn.setIcon(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(36, 36)
        btn.setIconSize(QSize(20, 20))
        btn.clicked.connect(slot)

        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: transparent;
            }
            QPushButton:pressed {
                padding-left: 1px;
                padding-top: 1px;
            }
        """)

        return btn

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    def _on_add_tool_clicked(self):
        tool_name = self.cb_tools.currentText()
        if not tool_name:
            return

        dialog = FilterParamsDialog(tool_name, self)
        if dialog.exec_():
            params = dialog.get_params()
            stage = PipelineBuilder.create_stage(tool_name, params)
            if stage:
                self.queued_stages.append(stage)
                self._update_list()

    def _update_list(self):
        self.list_widget.clear()
        for i, stage in enumerate(self.queued_stages):
            self.list_widget.addItem(f"{i+1}. {stage.display_text}")

    def _remove_item(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            del self.queued_stages[row]
            self._update_list()

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.queued_stages[row], self.queued_stages[row-1] = \
                self.queued_stages[row-1], self.queued_stages[row]
            self._update_list()
            self.list_widget.setCurrentRow(row-1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row < len(self.queued_stages) - 1:
            self.queued_stages[row], self.queued_stages[row+1] = \
                self.queued_stages[row+1], self.queued_stages[row]
            self._update_list()
            self.list_widget.setCurrentRow(row+1)

    def _on_save_preset(self):
        if not self.queued_stages:
            QMessageBox.warning(self, "Empty Queue", "There are no stages to save.")
            return

        export_data = []
        for stage in self.queued_stages:
            export_data.append({
                "tool_name": stage.name,
                "params": stage.params
            })

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Batch Preset", "", "JSON Files (*.json)"
        )

        if file_path:
            self.controller.io_controller.save_batch_config(file_path, export_data)

    def _on_load_preset(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Batch Preset", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        data = self.controller.io_controller.load_batch_config(file_path)
        if not data:
            return

        self.queued_stages.clear()
        self.list_widget.clear()

        for item in data:
            tool_name = item.get("tool_name")
            params = item.get("params")
            stage = PipelineBuilder.create_stage(tool_name, params)
            if stage:
                self.queued_stages.append(stage)
            else:
                print(f"Warning: Could not restore tool '{tool_name}'")

        self._update_list()

    def get_pipeline_stages(self):
        return self.queued_stages