from data.data_handler import IDataReader
from typing import Dict, Any
from pyproj import CRS, Transformer
import pdal
import json
import re


class LasLazReader(IDataReader):

    def __init__(self):
        self._pipeline = None

    def read(self, file_path: str) -> Dict[str, Any]:
        json_config = {
            "pipeline": [{"type": "readers.las", "filename": f"{file_path}"}]
        }

        try:
            self._pipeline = pdal.Pipeline(json.dumps(json_config))
            count = self._pipeline.execute()
            return {"status": True, "count": count}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_metadata(self):
        if not self._pipeline:
            return {"status": False, "error": "Pipeline has not been yet."}
        try:
            metadata_dict = self._pipeline.metadata
            return {"status": True, "metadata": metadata_dict}

        except json.JSONDecodeError as e:
            return {"status": False, "error": f"Metadata JSON parse error. {e}"}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_bounds(self):
        if self._pipeline:
            metadata_result = self.get_metadata()

            if metadata_result.get("status") is False:
                return metadata_result

            try:
                readers_las = metadata_result["metadata"]["metadata"]["readers.las"]
                bounds_data_raw = {
                    "minx": readers_las.get('minx'),
                    "miny": readers_las.get('miny'),
                    "maxx": readers_las.get('maxx'),
                    "maxy": readers_las.get('maxy')
                }

                spatial_ref = readers_las.get("spatialreference")
                crs = CRS.from_wkt(spatial_ref)
                source_epsg = crs.to_epsg()

                if source_epsg is None:
                    epsg_match = re.findall(r'AUTHORITY\["EPSG","(\d+)"\]', spatial_ref)
                    source_epsg = epsg_match[-1] if epsg_match else None

                transformed_result = self._transform_bbox(
                    bounds=bounds_data_raw,
                    from_epsg = source_epsg,
                    to_epsg=4326
                )

                if transformed_result.get("status"):
                    return {"status": True, "bounds": transformed_result}
                else:
                    return transformed_result
                
            except Exception as e:
                return {"status": False, "error": f"Error extracting bounds: {e}"}
        else:
            return {"status": False, "error": f"The pipeline has not been run yet."}

    def get_sample_data(self):
        if not self._pipeline:
            return {"status": False, "error": "Pipeline has not been read yet."}

        try:
            raw_data = self._pipeline.arrays[0]
            sample_data = raw_data[::10]
            x = sample_data["X"]
            y = sample_data["Y"]
            z = sample_data["Z"]
            return {
                "status": True,
                "x": x.tolist(),
                "y": y.tolist(),
                "z": z.tolist(),
                "count": len(x),
            }

        except Exception as e:
            return {"status": False, "error": f"Error during data sampling : {e}"}

    def get_summary_metadata(self, full_metadata:Dict):
        try:
            readers_las = full_metadata.get("metadata", {}).get("metadata", {}).get("readers.las", {})
            is_compressed = readers_las.get("compressed", "None")
            points = readers_las.get("count", "None")
            software_id = readers_las.get("software_id", "None")
            x_range = f"{readers_las.get('minx')}-{readers_las.get('maxz')}"
            y_range = f"{readers_las.get('miny')}-{readers_las.get('maxy')}"
            z_range = f"{readers_las.get('minz')}-{readers_las.get('maxz')}"
            crs_name = readers_las.get("srs", {}).get("json", {}).get("name")
            spatial_ref = readers_las.get("spatialreference")
            crs = CRS.from_wkt(spatial_ref)
            epsg_code = crs.to_epsg()
            unit_name = crs.axis_info[0].unit_name

            if epsg_code is None:
                epsg_match = re.findall(r'AUTHORITY\["EPSG","(\d+)"\]', spatial_ref)
                epsg_code = epsg_match[-1] if epsg_match else None

            if unit_name is None:
                unit_match = re.search(r'UNIT\["([^"]+)",', spatial_ref)
                unit_name = unit_match.group(1) if unit_match else None

            return {
                "status": True,
                "is_compressed": is_compressed,
                "points" : points,
                "software_id": software_id,
                "x_range": x_range,
                "y_range": y_range,
                "z_range": z_range,
                "crs_name": crs_name,
                "epsg": epsg_code,
                "unit": unit_name
            }

        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }
        
    def _transform_bbox(self,bounds:dict,from_epsg:int, to_epsg:int = 4326) -> Dict:

        try:
            transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
            x_coords = [bounds.get("minx"), bounds.get("maxx")]
            y_coords = [bounds.get("miny"), bounds.get("maxy")]

            transformed_x, transformed_y = transformer.transform(x_coords, y_coords)

            return {
                "minx": transformed_x[0], 
                "maxx": transformed_x[1], 
                "miny": transformed_y[0], 
                "maxy": transformed_y[1]
            }
        
        except Exception as e:
            return {
                "status":False,
                "error": f"CRS transformation failed. {e}"
            }