from data.data_handler import IDataReader
from core.render_utils import RenderUtils
from core.geo_utils import GeoUtils
from typing import Dict, Any
import pdal
import json


class LasLazReader(IDataReader):

    def __init__(self, sample_step: int = 10):
        self._analysis_pipeline = None
        self._render_pipeline = None
        self._sample_step = sample_step
        self._file_path = None

    def read(self, file_path: str) -> Dict[str, Any]:
        """
        Render pipeline'ı hazırlar ve çalıştırır. Dosya yolunu saklar.
        """
        self._file_path = file_path
        try:
            render_config = {
                "pipeline": [
                    {"type": "readers.las", "filename": f"{file_path}"},
                    {"type": "filters.decimation", "step":self._sample_step} 
                ]
            }
            self._render_pipeline = pdal.Pipeline(json.dumps(render_config))
            count = self._render_pipeline.execute()           
            return {"status":True, "count": count}
        except Exception as e:
            return {"status":False, "error": f"PDAL Pipeline Error during read: {e}"}

    def get_metadata(self):       
        if not self._file_path:
            return {"status": False, "error": "File path is not set for metadata extraction."}
        
        analysis_config = {
            "pipeline": [
                {"type": "readers.las", "filename": f"{self._file_path}"}
            ]
        }

        try:
            temp_pipeline = pdal.Pipeline(json.dumps(analysis_config))
            temp_pipeline.execute() 
            metadata_dict  = temp_pipeline.metadata
            self._analysis_pipeline = temp_pipeline
            return {"status": True, "metadata": metadata_dict}
        except json.JSONDecodeError as e:
            return {"status": False, "error": f"Metadata JSON parse error. {e}"}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_bounds(self):
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

            if any(v is None for v in bounds_data_raw.values()):
                return {"status": False, "error": "Bounding box data is missing in metadata."}
            
            spatial_ref = readers_las.get("spatialreference")
            crs_result = GeoUtils.parse_crs_info(spatial_ref)
            source_epsg = crs_result.get("epsg")

            if source_epsg is None:
                return {"status": False, "error": "EPSG code not found for transformation."}

            transformed_result = GeoUtils.transform_bbox(
                bounds=bounds_data_raw,
                from_epsg = source_epsg,
                to_epsg=4326
            )

            if transformed_result.get("status") is None:
                return {"status": True, **transformed_result}
            else:
                return transformed_result
            
        except Exception as e:
            return {"status": False, "error": f"Error extracting bounds: {e}"}

    def get_sample_data(self):
        if not self._render_pipeline:
            return {"status": False, "error": "Render pipeline has not been read yet."}

        try:
            raw_data = self._render_pipeline.arrays[0]
            raw_x = raw_data["X"]
            raw_y = raw_data["Y"]
            raw_z = raw_data["Z"]
            
            vis_x, vis_y, vis_z = RenderUtils.downsample(raw_x, raw_y, raw_z)
            
            return {
                "status": True,
                "x": vis_x,
                "y": vis_y,
                "z": vis_z,
                "count": len(raw_x),
            }
        except Exception as e:
            return {"status": False, "error": f"Error during data sampling : {e}"}

    def get_summary_metadata(self, full_metadata:Dict):
        try:
            readers_las = full_metadata.get("metadata", {}).get("metadata", {}).get("readers.las", {})
            is_compressed = readers_las.get("compressed", "None")
            points = readers_las.get("count", "None")
            software_id = readers_las.get("software_id", "None")
            x_range = f"{readers_las.get('minx')}-{readers_las.get('maxx')}"
            y_range = f"{readers_las.get('miny')}-{readers_las.get('maxy')}"
            z_range = f"{readers_las.get('minz')}-{readers_las.get('maxz')}"
            crs_name = readers_las.get("srs", {}).get("json", {}).get("name")
            spatial_ref = readers_las.get("spatialreference")

            crs_result = GeoUtils.parse_crs_info(spatial_ref)
            epsg_code = crs_result.get("epsg")
            unit_name = crs_result.get("unit")

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