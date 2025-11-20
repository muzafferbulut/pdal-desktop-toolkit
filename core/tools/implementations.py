from core.tools.registry import register_tool
from core.tools.base import BaseTool
from typing import Dict, Any

@register_tool
class OutlierFilter(BaseTool):
    name = "Outlier Filter"
    group = "Clean Data"
    description = (
        "Removes noise using statistical analysis (Mean/Stdev). "
        "Useful for cleaning up isolated points in the cloud."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {"mean_k": 8, "multiplier":2.2}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": int(params.get("mean_k", 8)),
            "multiplier": float(params.get("multiplier", 8))
        }