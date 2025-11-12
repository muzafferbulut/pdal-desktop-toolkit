from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import sys

class Logger(QObject):

    log_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__()

    def _emit_log(self, level:str, message:str):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        formatted_message = f"{timestamp} [{level}] > {message}"
        self.log_signal.emit(level, formatted_message)

    def info(self, message:str):
        self._emit_log("INFO", message)

    def error(self, message:str):
        self._emit_log("ERROR", message)

    def warning(self, message:str):
        self._emit_log("WARNING", message)