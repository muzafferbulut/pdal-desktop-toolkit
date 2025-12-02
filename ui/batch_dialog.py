from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QComboBox, QLabel, QStyle)
from core.pipeline_builder import PipelineBuilder
from ui.filter_dialog import FilterParamsDialog
from core.tools.registry import ToolRegistry
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

class BatchProcessDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processor")
        self.resize(350, 450)
        self.queued_stages = [] 
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        tool_layout = QHBoxLayout()        
        self.cb_tools = QComboBox()
        
        tools = ToolRegistry.get_all_tools()

        for name, tool_cls in tools.items():
            if tool_cls.supports_batch:
                self.cb_tools.addItem(name)
            
        btn_add = QPushButton()
        btn_add.setIcon(QIcon("ui/resources/icons/add.png")) 
        btn_add.setToolTip("Add to Queue")
        btn_add.setFixedSize(30, 30)
        btn_add.clicked.connect(self._on_add_tool_clicked)
        
        tool_layout.addWidget(QLabel("Select Tool:"))
        tool_layout.addWidget(self.cb_tools, 1)
        tool_layout.addWidget(btn_add)
        
        layout.addLayout(tool_layout)
        
        layout.addWidget(QLabel("Processing Queue (Execution Order):"))
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget::item { padding: 5px; }")
        layout.addWidget(self.list_widget)

        control_layout = QHBoxLayout()
        
        btn_up = QPushButton()
        btn_up.setIcon(QIcon("ui/resources/icons/up.png"))
        btn_up.setToolTip("Move Up")
        
        btn_down = QPushButton()
        btn_down.setIcon(QIcon("ui/resources/icons/down.png"))
        btn_down.setToolTip("Move Down")
        
        btn_remove_item = QPushButton()
        btn_remove_item.setIcon(QIcon("ui/resources/icons/remove.png"))
        btn_remove_item.setToolTip("Remove Selected Item")
        
        btn_run = QPushButton()
        btn_run.setIcon(QIcon("ui/resources/icons/run.png"))
        btn_run.setToolTip("Run Batch Process")
        
        btn_cancel = QPushButton()
        btn_cancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        btn_cancel.setToolTip("Cancel")

        for btn in [btn_up, btn_down, btn_remove_item, btn_run, btn_cancel]:
            btn.setFixedSize(40, 40)
            btn.setIconSize(QSize(20, 20))

        btn_up.clicked.connect(self._move_up)
        btn_down.clicked.connect(self._move_down)
        btn_remove_item.clicked.connect(self._remove_item)
        btn_run.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        control_layout.addWidget(btn_up)
        control_layout.addWidget(btn_down)
        control_layout.addWidget(btn_remove_item)
        
        control_layout.addStretch()
        
        control_layout.addWidget(btn_run)
        control_layout.addWidget(btn_cancel)
        
        layout.addLayout(control_layout)

    def _on_add_tool_clicked(self):
        tool_name = self.cb_tools.currentText()
        if not tool_name: return

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
            self.queued_stages[row], self.queued_stages[row-1] = self.queued_stages[row-1], self.queued_stages[row]
            self._update_list()
            self.list_widget.setCurrentRow(row-1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row < len(self.queued_stages) - 1:
            self.queued_stages[row], self.queued_stages[row+1] = self.queued_stages[row+1], self.queued_stages[row]
            self._update_list()
            self.list_widget.setCurrentRow(row+1)

    def get_pipeline_stages(self):
        return self.queued_stages