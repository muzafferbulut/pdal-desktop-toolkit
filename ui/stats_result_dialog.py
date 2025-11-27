from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QTextEdit, QDialogButtonBox, QWidget)
from PyQt5.QtGui import QFont
import json

class StatsResultDialog(QDialog):
    
    def __init__(self, file_name, stats_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Statistics: {file_name}")
        self.resize(800, 600)
        self.stats_data = stats_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        tabs = QTabWidget()
        
        self.tab_dimensions = QWidget()
        self._setup_dimensions_tab()
        tabs.addTab(self.tab_dimensions, "Dimensions")

        if "statistic" in self.stats_data and any(d.get("name") == "Classification" for d in self.stats_data["statistic"]):
             self.tab_classes = QWidget()
             self._setup_classes_tab()
             tabs.addTab(self.tab_classes, "Classes")

        self.tab_json = QWidget()
        self._setup_json_tab()
        tabs.addTab(self.tab_json, "Raw JSON")

        layout.addWidget(tabs)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

    def _setup_dimensions_tab(self):
        layout = QVBoxLayout()
        self.tab_dimensions.setLayout(layout)

        table = QTableWidget()
        columns = ["Name", "Min", "Max", "Average", "StdDev", "Variance"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        stats_list = self.stats_data.get("statistic", [])
        table.setRowCount(len(stats_list))
        
        for row, stat in enumerate(stats_list):
            name = stat.get("name", "N/A")
            try:
                min_val = stat.get('minimum', stat.get('min', 0))
                max_val = stat.get('maximum', stat.get('max', 0))
                avg_val = stat.get('average', stat.get('mean', 0))
                std_val = stat.get('stddev', 0)
                var_val = stat.get('variance', 0)
                table.setItem(row, 0, QTableWidgetItem(str(name)))
                table.setItem(row, 1, QTableWidgetItem(f"{float(min_val):.4f}"))
                table.setItem(row, 2, QTableWidgetItem(f"{float(max_val):.4f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{float(avg_val):.4f}"))
                table.setItem(row, 4, QTableWidgetItem(f"{float(std_val):.4f}"))
                table.setItem(row, 5, QTableWidgetItem(f"{float(var_val):.4f}"))
            except Exception as e:
                print(f"Error parsing row {row}: {e}")

        layout.addWidget(table)

    def _setup_classes_tab(self):
        layout = QVBoxLayout()
        self.tab_classes.setLayout(layout)
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Class ID", "Count", "Percentage"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        stats_list = self.stats_data.get("statistic", [])
        class_stat = next((s for s in stats_list if s.get("name") == "Classification"), None)
        
        if class_stat and "counts" in class_stat:
            counts = class_stat["counts"]
            table.setRowCount(len(counts))
            total_points = class_stat.get("count", 1)

            for row, item in enumerate(counts):
                try:
                    parts = item.split("/")
                    class_id = parts[0]
                    count = int(float(parts[1]))
                    percent = (count / total_points) * 100
                    
                    table.setItem(row, 0, QTableWidgetItem(class_id))
                    table.setItem(row, 1, QTableWidgetItem(f"{count:,}"))
                    table.setItem(row, 2, QTableWidgetItem(f"%{percent:.2f}"))
                except: pass
                    
        layout.addWidget(table)

    def _setup_json_tab(self):
        layout = QVBoxLayout()
        self.tab_json.setLayout(layout)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setText(json.dumps(self.stats_data, indent=4))
        layout.addWidget(text_edit)