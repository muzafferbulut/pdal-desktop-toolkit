from data.data_handler import IDataReader
from typing import Dict, Any
import pdal
import json


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
                metadata = metadata_result["metadata"]["metadata"]["readers.las"]
                bounds_data = {
                    "minx": metadata["minx"],
                    "miny": metadata["miny"],
                    "maxx": metadata["maxx"],
                    "maxy": metadata["maxy"],
                }
                return {"status": True, "bounds": bounds_data}
            except Exception as e:
                return {"status": False, "error": f"Error extracting bounds: {e}"}
        else:
            return {"status": False, "error": f"The pipeline has not been run yet."}

    def get_sample_data(self):
        if not self._pipeline:
            return {"status": False, "error": "Pipeline has not been read yet."}

        try:
            raw_data = self._pipeline.arrays[0]
            sample_data = raw_data[::100]
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
