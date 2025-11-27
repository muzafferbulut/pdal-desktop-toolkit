from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QVBoxLayout, QFrame
from pyvistaqt import QtInteractor
from PyQt5.QtCore import QUrl
import pyvista as pv
import numpy as np
import os

class GISMapView(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        map_file_path = os.path.join(current_dir, "resources" , "map_template.html")
        map_url = QUrl.fromLocalFile(map_file_path)
        self.setUrl(map_url)
        self.map_is_loaded = False
        self.loadFinished.connect(lambda: setattr(self, "map_is_loaded", True))
    
    def draw_bbox(self, bounds:dict):

        if not self.map_is_loaded:
            return
        
        minx = bounds.get('minx')
        miny = bounds.get('miny')
        maxx = bounds.get('maxx')
        maxy = bounds.get('maxy')

        js_command = f"window.drawBBoxJS({minx}, {miny}, {maxx}, {maxy});"
        self.page().runJavaScript(js_command)

    def clear_bbox(self):
        if not self.map_is_loaded:
            return
        js_command = "window.clearBBoxJS();"
        self.page().runJavaScript(js_command)

    def on_theme_change(self, theme):
        map_style = theme.map_style

        js_command = f"window.setMapTileLayer('{map_style}');"
        
        if self.map_is_loaded:
            self.page().runJavaScript(js_command)

class ThreeDView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.plotter = QtInteractor(self)
        self.layout.addWidget(self.plotter)

        self.point_actor = None
        self.current_mesh = None

        self.plotter.set_background("#42535C", top="#BBE2F1")

        self.plotter.camera_position = "iso"
        self.plotter.show_axes()

    def render_point_cloud(self, data_dict: dict, color_by: str = "Elevation", reset_view: bool = True):
        """
        data_dict: {x, y, z, intensity, red, green...}
        color_by: 'Elevation', 'Intensity', 'RGB', 'Classification'
        """
        x = data_dict.get("x")
        y = data_dict.get("y")
        z = data_dict.get("z")

        if x is None: return

        points = np.column_stack((x, y, z))
        point_cloud = pv.PolyData(points)

        point_cloud["Elevation"] = z

        scalars = "Elevation"
        rgb = False
        cmap = "viridis"

        if color_by == "Intensity" and "intensity" in data_dict:
            point_cloud["Intensity"] = data_dict["intensity"]
            scalars = "Intensity"
            cmap = "gray"
        
        elif color_by == "Classification" and "classification" in data_dict:
            point_cloud["Classification"] = data_dict["classification"]
            scalars = "Classification"
            cmap = "tab10"

        elif color_by == "RGB" and "red" in data_dict:
            r = data_dict["red"]
            g = data_dict["green"]
            b = data_dict["blue"]
            
            max_val = max(r.max(), g.max(), b.max())
            
            if max_val > 255:
                scale = 255.0 / max_val
                r = (r * scale).astype(np.uint8)
                g = (g * scale).astype(np.uint8)
                b = (b * scale).astype(np.uint8)
            else:
                r = r.astype(np.uint8)
                g = g.astype(np.uint8)
                b = b.astype(np.uint8)
            
            rgb_array = np.column_stack((r, g, b))
            point_cloud.point_data["RGB"] = rgb_array
            scalars = "RGB"
            rgb = True

        self.plotter.clear()
        self.plotter.add_axes()

        scalar_bar_args={
            "title": None,
            "vertical": True,
            "position_x": 0.95,
            "position_y": 0.06,
            "height": 0.25,       
            "width": 0.03,   
            "label_font_size": 11
        }

        try:
            self.point_actor = self.plotter.add_mesh(
                point_cloud,
                scalars=scalars,
                rgba=rgb, 
                render_points_as_spheres=True,
                point_size=3,
                cmap=cmap if not rgb else None,
                scalar_bar_args=scalar_bar_args if not rgb else None
            )
            
            if rgb:
                self.plotter.remove_scalar_bar()

            self.current_mesh = point_cloud

            if reset_view:
                self.plotter.reset_camera()
            
            self.plotter.render()
            
        except Exception as e:
            print(f"Render error: {e}")
        
    def on_theme_change(self, theme):
        colors = theme.three_d_background

        if self.plotter:
            self.plotter.set_background(
                colors = colors['bottom'],
                top = colors['top']
            )

    def enable_crop_gizmo(self, bounds=None, callback=None):
        if not self.plotter:
            return

        self.plotter.clear_box_widgets()
        
        if bounds is None and self.current_mesh:
            bounds = self.current_mesh.bounds

        if bounds:
            self.plotter.add_box_widget(
                callback=callback,
                bounds=bounds,
                color="orange",
                rotation_enabled=False 
            )
    
    def disable_crop_gizmo(self):
        if self.plotter:
            self.plotter.clear_box_widgets()