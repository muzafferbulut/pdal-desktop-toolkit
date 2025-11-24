from core.tools.registry import register_tool
from core.tools.base import BaseTool
from typing import Dict, Any

@register_tool
class OutlierFilter(BaseTool):
    name = "Outlier Filter"
    group = "Data Cleaning"
    description = (
        "Removes noise using statistical analysis (Mean/Stdev). "
        "Useful for cleaning up isolated points in the cloud."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {"mean_k": 8, "multiplier":2}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": int(params.get("mean_k", 8)),
            "multiplier": float(params.get("multiplier", 2))
        }
    
@register_tool
class RangeFilter(BaseTool):
    name = "Range Filter"
    group = "Data Cleaning"
    description = (
        "Keeps points that fall within specific criteria. "
        "Use 'Classification![7:7]' to remove noise, or 'Z[0:100]' for elevation."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {"limits": "Classification![7:7]"}
    
    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.range",
            "limits": str(params.get("limits", "Classification![7:7]"))
        }
    
@register_tool
class DecimationFilter(BaseTool):
    name = "Decimation Filter"
    group = "Sampling"
    description = (
        "Keeps every Nth point from the cloud, effectively downsampling it."
        "Use this for quick visualization of large datasets."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {"step": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.decimation",
            "step": int(params.get("step", 1)) # step değeri int olmalıdır
        }
    
@register_tool
class SmrfFilter(BaseTool):
    name = "SMRF Filter (Ground)"
    group = "Classification"
    description = (
        "Simple Morphological Filter (Pingel et al., 2013). "
        "It classifies ground points by comparing elevations against an interpolated surface."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "slope": 0.2,       # Maksimum zemin eğimi (derece değil)
            "threshold": 0.15,  # Toprak yüzeyinden maksimum dikey mesafe
            "window": 18.0      # Filtre pencere boyutu (yaklaşık nesne boyutu)
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.smrf",
            "slope": float(params.get("slope", 0.2)),
            "threshold": float(params.get("threshold", 0.15)),
            "window": float(params.get("window", 18.0))
        }