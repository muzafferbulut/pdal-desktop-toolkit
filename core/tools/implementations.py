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
    
@register_tool
class PmfFilter(BaseTool):
    name = "PMF Filter (Ground)"
    group = "Classification" 
    description = (
        "Progressive Morphological Filter (Zhang et al., 2016). "
        "It classifies ground points using a progressive window size and threshold."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "max_window_size": 33,  # Maksimum pencere boyutu (tek sayı olmalı)
            "slope": 1.0,           # Maksimum zemin eğimi
            "max_distance": 2.0     # Maksimum dikey mesafe
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.pmf",
            "max_window_size": int(params.get("max_window_size", 33)), 
            "slope": float(params.get("slope", 1.0)),
            "max_distance": float(params.get("max_distance", 2.0))
        }
    
@register_tool
class DbscanFilter(BaseTool):
    name = "DBSCAN Clustering"
    group = "Segmentation"
    description = (
        "DBSCAN Clustering. Extracts and labels clusters based on point density "
        "using Euclidean distance. Highly effective for segmenting individual objects."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "min_points": 5,      # Bir küme oluşturmak için gereken minimum nokta sayısı (int)
            "eps": 0.5            # Komşuluk için maksimum mesafe (float, metre cinsinden)
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.dbscan",
            "min_points": int(params.get("min_points", 5)),
            "eps": float(params.get("eps", 0.5))
        }
    
@register_tool
class CsfFilter(BaseTool):
    name = "CSF Filter (Ground)"
    group = "Classification" 
    description = (
        "Cloth Simulation Filter (Zhang et al., 2016). Highly accurate "
        "ground classification using a simulated cloth to model the terrain."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "resolution": 1.0,           # Kumaşın ızgara çözünürlüğü (float)
            "class_threshold": 0.5,      # Sınıflandırma eşiği (float)
            "cloth_resolution": 0.5,     # Kumaş simülasyonu hassasiyeti (float)
            "time_step": 0.65            # Simülasyon zaman adımı (float)
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.csf",
            "resolution": float(params.get("resolution", 1.0)),
            "class_threshold": float(params.get("class_threshold", 0.5)),
            "cloth_resolution": float(params.get("cloth_resolution", 0.5)),
            "time_step": float(params.get("time_step", 0.65))
        }

@register_tool
class IqrFilter(BaseTool):
    name = "IQR Filter (Noise)"
    group = "Noise/Outlier"
    description = (
        "Removes outliers using the Interquartile Range (IQR) method. "
        "It is more robust to extreme outliers than standard deviation methods."
    )

    def get_default_params(self) -> Dict[str, Any]:
        """
        IQR filtresi için varsayılan parametreler: Z boyutunda 1.5 çarpanı.
        """
        return {
            "dimension": "Z",  # Hangi boyutta uygulanacağı
            "k": 1.5           # IQR çarpanı (genellikle 1.5 kullanılır)
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.iqr",
            "dimension": str(params.get("dimension", "Z")),
            "k": float(params.get("k", 1.5))
        }
    
@register_tool
class VoxelDownsizeFilter(BaseTool):
    name = "Voxel Downsize Filter"
    group = "Sampling" 
    description = (
        "Reduces the point cloud density using a Voxel Grid. "
        "It selects the first point within each 3D cell (voxel), "
        "resulting in a uniformly distributed point cloud."
    )

    def get_default_params(self) -> Dict[str, Any]:
        return {"cell_size": 0.5}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.voxeldownsize",
            # PDAL'da bu parametre 'cell' olarak geçer.
            "cell": float(params.get("cell_size", 0.5)) 
        }
    