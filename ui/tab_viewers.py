from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

class GISMapView(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body {
                    margin: 0;
                    padding: 0;
                    height: 100%;
                }
                #mapid {
                    height: 100vh;
                    width: 100%;
                }

                .leaflet-control-layers {
                    background: rgba(255, 255, 255, 0.85);
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 13px;
                }

                .leaflet-control-layers label {
                    cursor: pointer;
                    padding: 2px 6px;
                    border-radius: 4px;
                    transition: background 0.2s;
                }

                .leaflet-control-layers label:hover {
                    background: rgba(0, 123, 255, 0.1);
                }

                .leaflet-control-layers-separator {
                    border-top: 1px solid rgba(0,0,0,0.1);
                    margin: 4px 0;
                }
            </style>
        </head>
        <body>
            <div id="mapid"></div>
            <script>
                var map = L.map('mapid').setView([39, 35], 6);

                var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                });

                var esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/' +
                                    'World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    maxZoom: 19,
                    attribution: 'Tiles © Esri, Maxar, Earthstar Geographics'
                });

                var hybrid = L.layerGroup([
                    esri,
                    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/' +
                                'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
                        maxZoom: 19,
                        attribution: '© Esri'
                    })
                ]);

                osm.addTo(map);

                var baseMaps = {
                    "OpenStreetMap": osm,
                    "Esri Satellite": esri,
                    "Hybrid": hybrid
                };

                L.control.layers(baseMaps, null, { collapsed: true }).addTo(map);

                var boundsLayer = L.layerGroup().addTo(map);

                window.drawBBoxJS = function(minx, miny, maxx, maxy) {
                    boundsLayer.clearLayers();
                    var bounds = L.latLngBounds([[miny, minx], [maxy, maxx]]);
                    L.rectangle(bounds, {color: "#ff7800", weight: 3, fillOpacity: 0.2}).addTo(boundsLayer);
                    map.fitBounds(bounds, {padding: [20, 20]});
                };
            </script>
        </body>
        </html>
        """
        self.setHtml(self.map_template)
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


class ThreeDView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        pass