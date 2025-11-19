from typing import Dict, Any, Optional
from core.layer_context import PipelineStage

class PipelineBuilder:
    """
    Tool isimlerini yönetir, varsayılan parametreleri sağlar 
    ve PipelineStage nesneleri üretir.
    """

    @staticmethod
    def get_default_params(tool_name: str) -> Dict[str, Any]:
        """
        Dialog penceresi açıldığında inputların içinde varsayılan 
        olarak ne yazacağını belirler.
        """
        if tool_name == "Splitter":
            return {"length": 1000.0}

        elif tool_name == "Crop":
            return {"bounds": "([0,100],[0,100])"} 
            
        elif tool_name in ["Sample", "Decimation"]:
            return {"step": 10}
            
        elif tool_name in ["Outlier", "Statistical"]:
            return {"mean_k": 8, "multiplier": 3.0}
            
        elif tool_name == "ELM":
            return {"cell": 20.0, "threshold": 1.0}
            
        elif tool_name == "Range":
            return {"limits": "Z[0:100]"}

        elif tool_name == "CSF":
            return {"resolution": 1.0, "threshold": 0.5, "rigidness": 2}
            
        elif tool_name == "SMRF":
            return {"cell": 1.0, "slope": 0.15, "window": 18.0, "threshold": 0.5}
            
        elif tool_name == "HAG":
            return {}
            
        elif tool_name == "Normal":
            return {"knn": 8}
            
        elif tool_name == "Cluster":
            return {"min_points": 10, "tolerance": 1.0}

        elif tool_name == "Reprojection":
            return {"out_srs": "EPSG:3857"}
            
        elif tool_name == "Transformation":
            return {"matrix": "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"}

        return {}

    @staticmethod
    def create_stage(tool_name: str, params: Dict[str, Any]) -> Optional[PipelineStage]:
        """
        Kullanıcının girdiği parametreleri alır ve geçerli bir 
        PipelineStage nesnesi üretir.
        """
        pdal_config = {}

        if tool_name == "Splitter":
            pdal_config = {
                "type": "filters.splitter",
                "length": float(params.get("length", 1000.0))
            }

        elif tool_name == "VoxelGrid":
             pdal_config = {
                "type": "filters.voxelgrid",
                "leaf_x": float(params.get("leaf_x", 1.0)),
                "leaf_y": float(params.get("leaf_y", 1.0)),
                "leaf_z": float(params.get("leaf_z", 1.0))
            }

        elif tool_name == "Crop":
            pdal_config = {
                "type": "filters.crop",
                "bounds": str(params.get("bounds", ""))
            }
            
        elif tool_name in ["Sample", "Decimation"]:
             pdal_config = {
                "type": "filters.decimation",
                "step": int(params.get("step", 10))
            }

        elif tool_name in ["Outlier", "Statistical"]:
            pdal_config = {
                "type": "filters.outlier",
                "method": "statistical",
                "mean_k": int(params.get("mean_k", 8)),
                "multiplier": float(params.get("multiplier", 3.0))
            }
            
        elif tool_name == "ELM":
            pdal_config = {
                "type": "filters.elm",
                "cell": float(params.get("cell", 20.0)),
                "class": 7,
                "threshold": float(params.get("threshold", 1.0))
            }
            
        elif tool_name == "Range":
            pdal_config = {
                "type": "filters.range",
                "limits": str(params.get("limits", "Z[0:100]"))
            }

        elif tool_name == "CSF":
            pdal_config = {
                "type": "filters.csf",
                "resolution": float(params.get("resolution", 1.0)),
                "threshold": float(params.get("threshold", 0.5)),
                "rigidness": int(params.get("rigidness", 2)),
                "ignore": "Classification[7:7]"
            }
            
        elif tool_name == "SMRF":
            pdal_config = {
                "type": "filters.smrf",
                "cell": float(params.get("cell", 1.0)),
                "slope": float(params.get("slope", 0.15)),
                "window": float(params.get("window", 18.0)),
                "threshold": float(params.get("threshold", 0.5)),
                "ignore": "Classification[7:7]"
            }
            
        elif tool_name == "HAG":
            pdal_config = {
                "type": "filters.hag_delaunay"
            }
            
        elif tool_name == "Normal":
            pdal_config = {
                "type": "filters.normal",
                "knn": int(params.get("knn", 8))
            }
            
        elif tool_name == "Cluster":
            pdal_config = {
                "type": "filters.cluster",
                "min_points": int(params.get("min_points", 10)),
                "tolerance": float(params.get("tolerance", 1.0))
            }

        elif tool_name == "Reprojection":
            pdal_config = {
                "type": "filters.reprojection",
                "out_srs": str(params.get("out_srs", "EPSG:3857"))
            }
            
        elif tool_name == "Transformation":
            pdal_config = {
                "type": "filters.transformation",
                "matrix": str(params.get("matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"))
            }

        if not pdal_config:
            return None

        return PipelineStage(
            name=tool_name,
            params=params,
            config=pdal_config,
            is_active=True
        )