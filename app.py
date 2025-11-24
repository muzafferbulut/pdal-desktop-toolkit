from core.application_controller import ApplicationController
from PyQt5.QtWidgets import QApplication
from data.readers import LasLazReader
from ui.main_window import MainWindow
from core.logger import Logger
import sys

def main():
    app = QApplication(sys.argv)
    app_logger = Logger()
    reader_instance = LasLazReader() 
    app_controller = ApplicationController(
        basic_reader=reader_instance,
        metadata_extractor=reader_instance,
        data_sampler=reader_instance,
        logger=app_logger
    ) 
    main_window = MainWindow(app_logger=app_logger, controller=app_controller)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()