from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont
from typing import Dict, Any

class MetadataPanel(QWidget):

    def __init__(self, parent:QWidget = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.summary_metadata_table = self._setup_table()
        self.layout.addWidget(self.summary_metadata_table)

    def _setup_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Properties', 'Value'])
        table.horizontalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.setRowCount(1)
        return table
    
    def update_metadata(self, file_name:str, summary_metadata:Dict[str, Any]):
        points = summary_metadata.get("points", "N/A")
        is_compressed = summary_metadata.get("is_compressed")
        crs_name = summary_metadata.get("crs_name", "N/A")
        epsg = summary_metadata.get("epsg", "N/A")
        software = summary_metadata.get("software_id", "N/A")
        x_range = summary_metadata.get("x_range")
        y_range = summary_metadata.get("y_range")
        z_range = summary_metadata.get("z_range")
        unit = summary_metadata.get("unit")

        self.summary_metadata_table.setRowCount(0)

        data_to_display = [
            ("Filename", file_name),
            ("Points", points),
            ("Compressed", is_compressed),
            ("Software", software),
            ("CRS Name", crs_name),
            ("EPSG Code", epsg),
            ("Unit", unit),
            ("X Range", x_range),
            ("Y Range", y_range),
            ("Z Range", z_range)
        ]

        self.summary_metadata_table.setRowCount(len(data_to_display))
        bold_font = QFont()
        bold_font.setBold(True)

        for row, (key ,value) in enumerate(data_to_display):
            key_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(str(value))
            
            key_item.setFont(bold_font)

            self.summary_metadata_table.setItem(row, 0, key_item)
            self.summary_metadata_table.setItem(row, 1, value_item)

    def clear_metadata(self):
        self.summary_metadata_table.clearContents()
        self.summary_metadata_table.setRowCount(1)