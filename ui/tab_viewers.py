from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import (
    pyqtSlot,
    QObject,
    pyqtSignal,
    QUrl,
)
from PyQt5.QtWidgets import QVBoxLayout, QFrame
from core.render_utils import RenderUtils
from pyvistaqt import QtInteractor
from core.enums import Dimensions
import pyvista as pv
import numpy as np
import json
import os


class MapBridge(QObject):
    area_drawn = pyqtSignal(float, float, float, float)

    @pyqtSlot(float, float, float, float)
    def areaSelected(self, minx, miny, maxx, maxy):
        self.area_drawn.emit(minx, miny, maxx, maxy)


class GISMapView(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.bridge = MapBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("handler", self.bridge)
        self.page().setWebChannel(self.channel)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        map_file_path = os.path.join(current_dir, "resources", "map_template.html")
        map_url = QUrl.fromLocalFile(map_file_path)
        self.setUrl(map_url)

        self.map_is_loaded = False
        self.pending_style = None

        self.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self):
        self.map_is_loaded = True

        if self.pending_style:
            self._apply_map_style(self.pending_style)

    def on_theme_change(self, theme):
        map_style = theme.map_style
        self.pending_style = map_style

        if self.map_is_loaded:
            self._apply_map_style(map_style)

    def _apply_map_style(self, style_name):
        js_command = f"window.setMapTileLayer('{style_name}');"
        self.page().runJavaScript(js_command)

    def draw_bbox(self, layer_id: str, bounds: dict):
        if not self.map_is_loaded:
            return
        minx, miny, maxx, maxy = (
            bounds.get("minx"),
            bounds.get("miny"),
            bounds.get("maxx"),
            bounds.get("maxy"),
        )
        if None in [minx, miny, maxx, maxy]:
            return

        js_command = f"window.drawBBoxJS({json.dumps(layer_id)}, {minx}, {miny}, {maxx}, {maxy});"
        self.page().runJavaScript(js_command)

    def clear_bbox(self, layer_id: str = None):
        if not self.map_is_loaded:
            return
        js_id = json.dumps(layer_id) if layer_id else "null"
        js_command = f"window.clearBBoxJS({js_id});"
        self.page().runJavaScript(js_command)

    def zoom_only(self, bounds: dict):
        if not self.map_is_loaded:
            return
        js_command = f"window.zoomOnlyJS({bounds['minx']}, {bounds['miny']}, {bounds['maxx']}, {bounds['maxy']});"
        self.page().runJavaScript(js_command)


class ThreeDView(QFrame):

    right_click_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.plotter = QtInteractor(self)
        self.layout.addWidget(self.plotter)

        self.layer_actors = {}
        self.current_mesh = None

        self.plotter.set_background("#42535C", top="#BBE2F1")

        self.plotter.camera_position = "iso"
        self.plotter.show_axes()

        self.plotter.iren.add_observer("RightButtonPressEvent", self._on_right_click)

    def render_point_cloud(
        self,
        file_path: str,
        data_dict: dict,
        color_by: str = "Elevation",
        reset_view: bool = True,
    ):
        x = data_dict.get(Dimensions.X)
        y = data_dict.get(Dimensions.Y)
        z = data_dict.get(Dimensions.Z)

        if x is None:
            return

        points = np.column_stack((x, y, z))
        point_cloud = pv.PolyData(points)

        point_cloud["Elevation"] = z

        scalars = "Elevation"
        rgb = False
        cmap = "viridis"

        annotations = {}

        if color_by == Dimensions.INTENSITY and Dimensions.INTENSITY in data_dict:
            point_cloud["Intensity"] = data_dict[Dimensions.INTENSITY]
            scalars = "Intensity"
            cmap = "gray"

        elif (
            color_by == Dimensions.CLASSIFICATION
            and Dimensions.CLASSIFICATION in data_dict
        ):
            cls_data = data_dict[Dimensions.CLASSIFICATION]
            point_cloud["Classification"] = cls_data
            scalars = "Classification"
            cmap = "tab10"

            unique_classes = np.unique(cls_data)
            for c in unique_classes:
                annotations[float(c)] = RenderUtils.get_label(c)

        elif color_by == Dimensions.RGB and Dimensions.RED in data_dict:
            r = data_dict[Dimensions.RED]
            g = data_dict[Dimensions.GREEN]
            b = data_dict[Dimensions.BLUE]

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

        self.plotter.add_axes()
        if file_path in self.layer_actors:
            self.plotter.remove_actor(self.layer_actors[file_path])

        scalar_bar_args = {
            "title": None,
            "vertical": True,
            "position_x": 0.95,
            "position_y": 0.06,
            "height": 0.25,
            "width": 0.03,
            "label_font_size": 11,
        }

        try:
            new_actor = self.plotter.add_mesh(
                point_cloud,
                scalars=scalars,
                rgba=rgb,
                render_points_as_spheres=False,
                point_size=1,
                cmap=cmap if not rgb else None,
                name=file_path,
                scalar_bar_args=scalar_bar_args if not rgb else None,
                categories=bool(annotations),
                show_scalar_bar=not rgb,
                annotations=annotations if annotations else None,
            )
            self.layer_actors[file_path] = new_actor

            if rgb:
                self.plotter.remove_scalar_bar()

            self.current_mesh = point_cloud

            if reset_view:
                self.plotter.reset_camera()

            self.plotter.render()

        except Exception as e:
            print(f"Render error: {e}")

    def zoom_to_mesh(self, file_path: str):
        if hasattr(self, "layer_actors") and file_path in self.layer_actors:
            actor = self.layer_actors[file_path]
            if actor:
                self.plotter.reset_camera(render=True, bounds=actor.GetBounds())

    def set_layer_visibility(self, file_path: str, is_visible: bool):
        if self.layer_actors is None or file_path not in self.layer_actors:
            return

        actor = self.layer_actors[file_path]
        if actor:
            actor.SetVisibility(is_visible)
            self.plotter.render()

    def on_theme_change(self, theme):
        colors = theme.three_d_background

        if self.plotter:
            self.plotter.set_background(colors=colors["bottom"], top=colors["top"])

    def enable_crop_gizmo(self, bounds=None, callback=None):
        if not self.plotter:
            return

        self.plotter.clear_box_widgets()

        if bounds is None and self.current_mesh:
            bounds = self.current_mesh.bounds

        if bounds:
            self.plotter.add_box_widget(
                callback=callback, bounds=bounds, color="orange", rotation_enabled=False
            )

    def disable_crop_gizmo(self):
        if self.plotter:
            self.plotter.clear_box_widgets()

    def resizeEvent(self, event):
        if self.plotter:
            self.plotter.setUpdatesEnabled(False)

        super().resizeEvent(event)

    def remove_layer_actor(self, file_path: str):
        if file_path in self.layer_actors:
            self.plotter.remove_actor(self.layer_actors[file_path])
            del self.layer_actors[file_path]
            self.plotter.render()

    def _on_right_click(self, obj, event):
        self.right_click_signal.emit()
