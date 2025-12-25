from data.data_handler import IDataWriter
from typing import Any, Dict
import json
import pdal


class PipelineWriter(IDataWriter):

    def write(self, file_path: str, data: list, **kwargs) -> Dict[str, Any]:
        try:
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            return {"status": True, "path": file_path}

        except Exception as e:
            return {"status": False, "error": str(e)}


class LasWriter(IDataWriter):

    def write(self, file_path: str, data: list, **kwargs) -> Dict[str, Any]:
        try:
            pipeline_config = data.copy()
            pipeline_config.append(
                {"type": "writers.las", "filename": file_path, "extra_dims": "all"}
            )

            pipeline = pdal.Pipeline(json.dumps(pipeline_config))
            count = pipeline.execute()
            return {"status": True, "count": count, "path": file_path}

        except Exception as e:
            return {"status": False, "error": f"Export failed: {str(e)}"}


class MetadataWriter(PipelineWriter):
    pass
