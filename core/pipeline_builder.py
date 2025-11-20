from typing import Dict, Any, Optional
from core.layer_context import PipelineStage
from core.tools.registry import ToolRegistry

class PipelineBuilder:
    """
    Tool isimlerini yönetir, varsayılan parametreleri sağlar 
    ve PipelineStage nesneleri üretir.
    """

    @staticmethod
    def get_default_params(tool_name: str) -> Dict[str, Any]:
        try:
            tool_class = ToolRegistry.get_tool(tool_name)
            tool_instance = tool_class()
            return tool_instance.get_default_params()
        except ValueError:
            return {}

    @staticmethod
    def create_stage(tool_name: str, params: Dict[str, Any]) -> Optional[PipelineStage]:
        try:
            tool_class = ToolRegistry.get_tool(tool_name)
            tool_instance = tool_class()
            pdal_config = tool_instance.build_config(params)

            return PipelineStage(
                name = tool_name,
                params = params,
                config = pdal_config,
                is_active=True
            )
        except Exception as e:
            return None