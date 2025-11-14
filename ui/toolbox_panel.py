from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import Optional

class ToolboxPanel(QWidget):
    
    tool_selected = pyqtSignal(str) 

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self._setup_toolbox_ui()
    
    def _setup_toolbox_ui(self):        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIconSize(QSize(18,18))
        self._populate_tree()
        self.layout.addWidget(self.tree)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)

    def _populate_tree(self):
        try:
            cat_icon = QIcon("ui/resources/icons/toolbox.png")
            tool_icon = QIcon("ui/resources/icons/tool.png")
        except:
            cat_icon = QIcon()
            tool_icon = QIcon()

        categories = {
            "Noise": ["Outlier", "Statistical"],
            "Manipulation": ["VoxelGrid", "Sample", "Crop"],
            "Engineering": ["Ground", "Mesh", "ApproximateDensity"]
        }

        for cat, tools in categories.items():
            cat_item = QTreeWidgetItem([cat])
            cat_item.setIcon(0, cat_icon)
            cat_item.setData(0, Qt.UserRole, "category")
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True) 
            for t in tools:
                tool_item = QTreeWidgetItem([t])
                tool_item.setIcon(0, tool_icon)
                tool_item.setData(0, Qt.UserRole, "tool") 
                tool_item.setData(0, Qt.UserRole + 1, f"filters.{t.lower()}") 
                cat_item.addChild(tool_item)

    def _on_tree_item_clicked(self, item, column):
        if item.data(0, Qt.UserRole) == "category":
            item.setExpanded(not item.isExpanded())
        else:  
            tool_name = item.text(0)
            self.tool_selected.emit(tool_name)
            pass