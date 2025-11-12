from PyQt5.QtWidgets import QWidget, QVBoxLayout

class GISMapView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        pass

class ThreeDView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        pass