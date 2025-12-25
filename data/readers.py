from data.data_handler import IBasicReader, IMetadataExtractor, IDataSampler
from core.render_utils import RenderUtils
from core.geo_utils import GeoUtils
from typing import Dict, Any, Union
from core.enums import Dimensions
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
                "pipeline": [{"type": "readers.las", "filename": f"{file_path}"}]
            }
            self._render_pipeline = pdal.Pipeline(json.dumps(render_config))
            count = self._render_pipeline.execute()
            return {"status": True, "count": count}
        except Exception as e:
            return {"status": False, "error": f"PDAL Pipeline Error during read: {e}"}

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
            metadata_dict = temp_pipeline.metadata
            self._analysis_pipeline = temp_pipeline
            return {"status": True, "metadata": metadata_dict}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_summary_metadata(self, full_metadata: Dict) -> Dict[str, Any]:
        try:
            readers_las = (
                full_metadata.get("metadata", {})
                .get("metadata", {})
                .get("readers.las", {})
            )
            spatial_ref = readers_las.get("spatialreference", "")
            crs_result = GeoUtils.parse_crs_info(spatial_ref)
            epsg_code = crs_result.get("epsg")
            unit_name = crs_result.get("unit", "N/A")

            minx = readers_las.get("minx")
            maxx = readers_las.get("maxx")
            miny = readers_las.get("miny")
            maxy = readers_las.get("maxy")
            minz = readers_las.get("minz")
            maxz = readers_las.get("maxz")
            x_range = (
                f"[{minx:.2f} to {maxx:.2f}]"
                if minx is not None and maxx is not None
                else "N/A"
            )
            y_range = (
                f"[{miny:.2f} to {maxy:.2f}]"
                if miny is not None and maxy is not None
                else "N/A"
            )
            z_range = (
                f"[{minz:.2f} to {maxz:.2f}]"
                if minz is not None and maxz is not None
                else "N/A"
            )

            return {
                "status": True,
                "points": readers_las.get("count", "N/A"),
                "software_id": readers_las.get("software_id", "N/A"),
                "is_compressed": readers_las.get("compressed", "N/A"),
                "crs_name": readers_las.get("srs", {})
                .get("json", {})
                .get("name", "N/A"),
                "epsg": epsg_code if epsg_code else "N/A",
                "unit": unit_name,
                "x_range": x_range,
                "y_range": y_range,
                "z_range": z_range,
            }
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_bounds(self, file_path: str) -> Dict[str, Any]:
        if not self._file_path:
            self._file_path = file_path

        meta_res = self.get_metadata(file_path)
        if not meta_res["status"]:
            return meta_res

        try:
            readers_las = meta_res["metadata"]["metadata"]["readers.las"]
            bounds = {
                "minx": readers_las.get("minx"),
                "miny": readers_las.get("miny"),
                "maxx": readers_las.get("maxx"),
                "maxy": readers_las.get("maxy"),
            }

            spatial_ref = readers_las.get("spatialreference")
            crs_result = GeoUtils.parse_crs_info(spatial_ref)
            source_epsg = crs_result.get("epsg")

            if source_epsg:
                transformed = GeoUtils.transform_bbox(bounds, source_epsg, 4326)
                return (
                    {"status": True, **transformed}
                    if transformed.get("status")
                    else transformed
                )
            return {"status": True, **bounds}

        except Exception as e:
            return {"status": False, "error": f"Bounds error: {e}"}

    def get_sample_data(self) -> Dict[str, Any]:
        if not self._render_pipeline:
            return {"status": False, "error": "Render pipeline is not initialized."}

        try:
            raw_data = self._render_pipeline.arrays[0]

            extracted_data = {
                Dimensions.X: raw_data[Dimensions.X.value],
                Dimensions.Y: raw_data[Dimensions.Y.value],
                Dimensions.Z: raw_data[Dimensions.Z.value],
                "count": len(raw_data[Dimensions.X.value]),
            }
            dims = raw_data.dtype.names

            if Dimensions.INTENSITY.value in dims:
                extracted_data[Dimensions.INTENSITY] = raw_data[
                    Dimensions.INTENSITY.value
                ]

            if (
                Dimensions.RED.value in dims
                and Dimensions.GREEN.value in dims
                and Dimensions.BLUE.value in dims
            ):
                extracted_data[Dimensions.RED] = raw_data[Dimensions.RED.value]
                extracted_data[Dimensions.GREEN] = raw_data[Dimensions.GREEN.value]
                extracted_data[Dimensions.BLUE] = raw_data[Dimensions.BLUE.value]

            if Dimensions.CLASSIFICATION.value in dims:
                extracted_data[Dimensions.CLASSIFICATION] = raw_data[
                    Dimensions.CLASSIFICATION.value
                ]

            vis_data = RenderUtils.downsample(extracted_data)
            vis_data["status"] = True
            return vis_data

        except Exception as e:
            import traceback

            return {
                "status": False,
                "error": f"Sampling Error: {str(e)}\n{traceback.format_exc()}",
            }
