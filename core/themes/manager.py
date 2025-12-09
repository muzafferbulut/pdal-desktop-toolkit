from PyQt5.QtWidgets import QApplication
from typing import Dict, Type
from .base import BaseTheme
from .styles import LightTheme, DarkTheme, HighContrastTheme, OceanicTheme, ForestTheme, MidnightTheme, SolarTheme

class ThemeManager:
    _themes: Dict[str, Type[BaseTheme]] = {}
    _observers = []
    _themes[LightTheme.name] = LightTheme
    _themes[DarkTheme.name] = DarkTheme
    _themes[HighContrastTheme.name] = HighContrastTheme
    _themes[OceanicTheme.name] = OceanicTheme
    _themes[ForestTheme.name] = ForestTheme
    _themes[MidnightTheme.name] = MidnightTheme
    _themes[SolarTheme.name] = SolarTheme

    @classmethod
    def get_theme_names(cls):
        return list(cls._themes.keys())
    
    @classmethod
    def add_observer(cls, callback_func):
        cls._observers.append(callback_func)

    @classmethod
    def apply_theme(cls, theme_name: str):
        theme_cls = cls._themes.get(theme_name)
        if not theme_cls:
            return
        
        theme_instance = theme_cls()
        stylesheet = theme_instance.get_stylesheet()
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)

        for observer in cls._observers:
            try:
                observer(theme_instance)
            except Exception as e:
                pass