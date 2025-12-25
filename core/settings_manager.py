from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSettings


class SettingsManager:
    """
    Uygulama ayarlarını ve UI durumunu yöneten sınıf.
    """

    ORGANIZATION_NAME = "PDALToolkit"
    APPLICATION_NAME = "DesktopApp"

    def __init__(self):
        self.settings = QSettings(self.ORGANIZATION_NAME, self.APPLICATION_NAME)

    def save_window_state(self, window: QMainWindow):
        """Pencere geometrisini ve dock yerleşimlerini kaydeder."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", window.saveGeometry())
        self.settings.setValue("state", window.saveState())
        self.settings.endGroup()

    def load_window_state(self, window: QMainWindow):
        """Pencere geometrisini ve dock yerleşimlerini geri yükler."""
        self.settings.beginGroup("MainWindow")
        geometry = self.settings.value("geometry")
        state = self.settings.value("state")

        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)
        self.settings.endGroup()

    def save_theme(self, theme_name: str):
        """Seçili temayı kaydeder."""
        self.settings.setValue("theme", theme_name)

    def load_theme(self, default="Light Theme") -> str:
        """Kayıtlı temayı döndürür, yoksa varsayılanı verir."""
        return self.settings.value("theme", default)

    def save_last_dir(self, path: str):
        self.settings.setValue("last_dir", path)

    def get_last_dir(self) -> str:
        return self.settings.value("last_dir", "")
