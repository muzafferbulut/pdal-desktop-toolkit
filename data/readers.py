from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from core.render_utils import RenderUtils 
from core.geo_utils import GeoUtils
from typing import Dict, Any, Union
import numpy as np  
import traceback
import pdal
import json

class LasLazReader(IBasicReader, IMetadataExtractor, IDataSampler):

    def __init__(self, sample_step: int = 10):
        self._analysis_pipeline: Union[pdal.Pipeline, None] = None
        self._render_pipeline: Union[pdal.Pipeline, None] = None
        self._sample_step = sample_step
        self._file_path: Union[str, None] = None 

    def read(self, file_path: str) -> Dict[str, Any]:
        self._file_path = file_path
        try:
            render_config = {
                "pipeline": [
                    {"type": "readers.las", "filename": f"{file_path}"}
                ]
            }
            self._render_pipeline = pdal.Pipeline(json.dumps(render_config))
            count = self._render_pipeline.execute()           
            return {"status":True, "count": count}
        except Exception as e:
            return {"status":False, "error": f"PDAL Pipeline Error during read: {e}"}

    def get_metadata(self, file_path: str) -> Dict[str, Any]: 
        if not self._file_path:
            self._file_path = file_path
        
        analysis_config = {
            "pipeline": [
                {"type": "readers.las", "filename": f"{self._file_path}", "count": 10}
            ]
        }
        try:
            temp_pipeline = pdal.Pipeline(json.dumps(analysis_config))
            temp_pipeline.execute() 
            metadata_dict  = temp_pipeline.metadata
            self._analysis_pipeline = temp_pipeline
            return {"status": True, "metadata": metadata_dict}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_summary_metadata(self, full_metadata:Dict) -> Dict[str, Any]:
        try:
            readers_las = full_metadata.get("metadata", {}).get("metadata", {}).get("readers.las", {})
            return {
                "status": True,
                "points" : readers_las.get("count", "None"),
                "software_id": readers_las.get("software_id", "None"),
                "crs_name": readers_las.get("srs", {}).get("json", {}).get("name"),
                "is_compressed": readers_las.get("compressed", "None")
            }
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_bounds(self, file_path: str) -> Dict[str, Any]: 
        if not self._file_path:
            self._file_path = file_path
            
        meta_res = self.get_metadata(file_path)
        if not meta_res["status"]: return meta_res
        
        try:
            readers_las = meta_res["metadata"]["metadata"]["readers.las"]
            bounds = {
                "minx": readers_las.get('minx'), "miny": readers_las.get('miny'),
                "maxx": readers_las.get('maxx'), "maxy": readers_las.get('maxy')
            }
            
            spatial_ref = readers_las.get("spatialreference")
            crs_result = GeoUtils.parse_crs_info(spatial_ref)
            source_epsg = crs_result.get("epsg")

            if source_epsg:
                transformed = GeoUtils.transform_bbox(bounds, source_epsg, 4326)
                return {"status": True, **transformed} if transformed.get("status") else transformed
            return {"status": True, **bounds} 
            
        except Exception as e:
            return {"status": False, "error": f"Bounds error: {e}"}

    def get_sample_data(self) -> Dict[str, Any]:
        if not self._render_pipeline:
            return {"status": False, "error": "Render pipeline is not initialized."}

        try:
            raw_data = self._render_pipeline.arrays[0]
            
            extracted_data = {
                "x": raw_data["X"],
                "y": raw_data["Y"],
                "z": raw_data["Z"],
                "count": len(raw_data["X"])
            }

            dims = raw_data.dtype.names
            if "Intensity" in dims:
                extracted_data["intensity"] = raw_data["Intensity"]
            if "Red" in dims and "Green" in dims and "Blue" in dims:
                extracted_data["red"] = raw_data["Red"]
                extracted_data["green"] = raw_data["Green"]
                extracted_data["blue"] = raw_data["Blue"]
            if "Classification" in dims:
                extracted_data["classification"] = raw_data["Classification"]

            vis_data = RenderUtils.downsample(extracted_data)
            vis_data["status"] = True
            return vis_data

        except Exception as e:
            import traceback
            return {"status": False, "error": f"Sampling Error: {str(e)}\n{traceback.format_exc()}"}