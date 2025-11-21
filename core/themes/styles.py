from core.themes.base import BaseTheme

class LightTheme(BaseTheme):
    name = "Light Theme"

    @property
    def palette(self):
        return {
            'background': '#ffffff',
            'background_alt': '#f8f9fa',
            'text': '#333333',
            'primary': '#0078d4',
            'border': '#dee2e6',
            'input_bg': '#ffffff',
            
            'button_bg': '#f8f9fa',
            'button_hover': '#e2e6ea',
            'button_pressed': '#dae0e5',
            
            'header_bg': '#f1f3f4',
            'header_text': '#333333',
            
            'selection_bg': '#e8f0fe',
            'selection_text': '#0078d4'
        }
    
    @property
    def three_d_background(self):
        return {'top': '#BBE2F1', 'bottom': '#42535C'}

    @property
    def map_style(self):
        return 'osm'

class DarkTheme(BaseTheme):
    name = "Dark Modern"
    
    @property
    def palette(self):
        return {
            'background': '#2b2b2b',
            'background_alt': '#3c3f41',
            'text': '#e0e0e0',
            'primary': '#4cc2ff',
            'border': '#555555',
            'input_bg': '#3c3f41',
            
            'button_bg': '#3c3f41',
            'button_hover': '#4e5254',
            'button_pressed': '#5a5e61',
            
            'header_bg': '#323232',
            'header_text': '#ffffff',
            
            'selection_bg': '#094771',
            'selection_text': '#ffffff'
        }
    
    @property
    def three_d_background(self):
        return {'top': '#1e1e1e', 'bottom': '#000000'}

    @property
    def map_style(self):
        return 'carto_dark'

class HighContrastTheme(BaseTheme):
    name = "High Contrast"
    
    @property
    def palette(self):
        return {
            'background': '#000000',
            'background_alt': '#000000',
            'text': '#ffffff',
            'primary': '#ffff00',
            'border': '#ffffff',
            'input_bg': '#000000',
            
            'button_bg': '#000000',
            'button_hover': '#333333',
            'button_pressed': '#666666',
            
            'header_bg': '#000000',
            'header_text': '#ffff00',
            
            'selection_bg': '#ffff00',
            'selection_text': '#000000'
        }
    
    @property
    def three_d_background(self):
        return {'top': '#000000', 'bottom': '#000000'}

    @property
    def map_style(self):
        return 'carto_dark'