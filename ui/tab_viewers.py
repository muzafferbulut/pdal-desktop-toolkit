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

    def render_point_cloud(self, x, y, z):
        if not len(x) or not len(y) or not len(z):
            return

        points = np.column_stack((x, y, z))
        point_cloud = pv.PolyData(points)
        point_cloud["elevation"] = z

        if self.point_actor:
            try:
                self.plotter.remove_actor(self.point_actor)
            except Exception:
                self.plotter.clear()
            self.point_actor = None

        self.plotter.clear()
        self.plotter.add_axes()
        self.plotter.enable_anti_aliasing()

        try:

            self.point_actor = self.plotter.add_mesh(
                point_cloud,
                scalars="elevation",
                render_points_as_spheres=True,
                point_size=2,
                cmap="viridis",
                scalar_bar_args={
                    "title":None,
                    "vertical": True,
                    "position_x": 0.95,
                    "position_y": 0.06,
                    "height": 0.25,       
                    "width": 0.03,   
                    "label_font_size": 11
                }
            )

            self.current_mesh = point_cloud

        except Exception as e:
            return

        try:
            self.plotter.reset_camera()
            self.plotter.render()
        except Exception as e:
            return
        
    def on_theme_change(self, theme):
        colors = theme.three_d_background

        if self.plotter:
            self.plotter.set_background(
                colors = colors['bottom'],
                top = colors['top']
            )
        text_color = "white" if "Dark" in theme.name or "Contrast" in theme.name else "black"
