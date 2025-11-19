from typing import Dict, Any, Optional
from core.layer_context import PipelineStage

class PipelineBuilder:
    """
    Tool isimlerini yönetir, varsayılan parametreleri sağlar 
    ve PipelineStage nesneleri üretir.
    """

    @staticmethod
    def get_default_params(tool_name:str) -> Dict[str, Any]:
        """
        Dialog penceresi açıldığında inputların içinde varsayılan 
        olarak ne yazacağını belirler.
        """

        if tool_name == "VoxelGrid":
            return {"leaf_x": 1.0, "leaf_y": 1.0, "leaf_z": 1.0}
        elif tool_name in ["Outlier", "Statistical"]:
            return {"mean_k": 8, "multiplier": 3.0}
        
        elif tool_name == "Decimation":
            return {"step": 10}
            
        elif tool_name == "Crop":
            return {"bounds": "([0,100],[0,100])"}

        return {}
    
    @staticmethod
    def create_stage(tool_name: str, params: Dict[str, Any]) -> Optional[PipelineStage]:
        """
        Kullanıcının girdiği parametreleri alır ve geçerli bir 
        PipelineStage nesnesi üretir.
        """
        pdal_config = {}

        if tool_name == "VoxelGrid":
            pdal_config = {
                "type": "filters.voxelgrid",
                "leaf_x": float(params.get("leaf_x", 1.0)),
                "leaf_y": float(params.get("leaf_y", 1.0)),
                "leaf_z": float(params.get("leaf_z", 1.0))
            }
            
        elif tool_name in ["Outlier", "Statistical"]:
            pdal_config = {
                "type": "filters.outlier",
                "method": "statistical",
                "mean_k": int(params.get("mean_k", 8)),
                "multiplier": float(params.get("multiplier", 3.0))
            }
        
        elif tool_name in ["Sample", "Decimation"]:
             pdal_config = {
                "type": "filters.decimation",
                "step": int(params.get("step", 1))
            }

        if not pdal_config:
            return None

        return PipelineStage(
            name=tool_name,
            params=params,
            config=pdal_config
        )