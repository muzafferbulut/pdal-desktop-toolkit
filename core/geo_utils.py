from pyproj import CRS, Transformer
from typing import Dict, Any
import re


class GeoUtils:
    """
    CRS ayrıştırma ve koordinat dönüşüm işlemlerini
    yöneten yardımcı sınıf.
    """

    @staticmethod
    def transform_bbox(bounds: dict, from_epsg: int, to_epsg: int = 4326) -> Dict:
        """
        Bbox koordinatlarını (minx, miny, maxx, maxy) bir EPSG'den
        başka bir EPSG'ye dönüştürür (Varsayılan olarak 4326'ya).
        """
        try:
            transformer = Transformer.from_crs(
                f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True
            )
            x_coords = [bounds.get("minx"), bounds.get("maxx")]
            y_coords = [bounds.get("miny"), bounds.get("maxy")]

            transformed_x, transformed_y = transformer.transform(x_coords, y_coords)

            return {
                "status": True,
                "minx": transformed_x[0],
                "maxx": transformed_x[1],
                "miny": transformed_y[0],
                "maxy": transformed_y[1],
            }

        except Exception as e:
            return {"status": False, "error": f"CRS transformation failed. {e}"}

    @staticmethod
    def parse_crs_info(spatial_ref: str) -> Dict[str, Any]:
        """
        PDAL'dan gelen WKT stringini ayrıştırarak EPSG kodu
        ve birim bilgisini (Unit) döndürür.
        """

        try:
            crs = CRS.from_wkt(spatial_ref)

            epsg_code = crs.to_epsg()

            if epsg_code is None:
                epsg_match = re.findall(r'AUTHORITY\["EPSG","(\d+)"\]', spatial_ref)
                epsg_code = epsg_match[-1] if epsg_match else None

            unit_name = crs.axis_info[0].unit_name if crs.axis_info else None
            if unit_name is None:
                unit_match = re.search(r'UNIT\["([^"]+)",', spatial_ref)
                unit_name = unit_match.group(1) if unit_match else None

            return {"epsg": epsg_code, "unit": unit_name, "crs": crs}
        except Exception as e:
            return {"epsg": None, "unit": "N/A", "crs": None}
