from PyQt5.QtWidgets import QApplication
from data.readers import LasLazReader
from ui.main_window import MainWindow
from core.logger import Logger
import sys

def main():
    app = QApplication(sys.argv)
    app_logger = Logger()

    reader = LasLazReader()

    main_window = MainWindow(app_logger=app_logger, reader=reader)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
