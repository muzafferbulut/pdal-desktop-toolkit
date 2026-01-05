from core.tools.registry import register_tool
from core.tools.base import BaseTool
from typing import Dict, Any, List, Union

@register_tool
class OutlierFilter(BaseTool):
    name = "Outliers (Statistical)"
    group = "Cleaning & Noise"
    description = (
        "Classify or remove noise using statistical analysis (Mean/Stdev). "
        "Use 'Clean Data' mode to directly delete noise points."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "mean_k": 8, 
            "multiplier": 2.0,
            "mode": ["Classify Only", "Clean Data"]
        }

    def build_config(self, params: Dict[str, Any]) -> Union[Dict, List]:
        mode = params.get("mode", "Classify Only")
        
        outlier_stage = {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": int(params.get("mean_k", 8)),
            "multiplier": float(params.get("multiplier", 2.0)),
            "class": 7
        }

        if mode == "Clean Data":
            range_stage = {
                "type": "filters.range",
                "limits": "Classification![7:7]"
            }
            return [outlier_stage, range_stage]
        
        return outlier_stage

@register_tool
class IqrFilter(BaseTool):
    name = "IQR (Box Plot)"
    group = "Cleaning & Noise"
    description = (
        "Removes outliers using the Interquartile Range (IQR) method. "
        "More robust to extreme outliers than standard deviation."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "dimension": "Z",
            "k": 1.5,
        }

    def build_config(self, params: Dict[str, Any]) -> Union[Dict, List]:
        iqr_stage = {
            "type": "filters.iqr",
            "dimension": str(params.get("dimension", "Z")),
            "k": float(params.get("k", 1.5))
        }
        return iqr_stage

@register_tool
class LofFilter(BaseTool):
    name = "LOF (Local Density)"
    group = "Cleaning & Noise"
    description = "Local Outlier Factor (LOF). Detects local outliers based on density."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "minpts": 10
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.lof",
            "minpts": int(params.get("minpts", 10))
        }

@register_tool
class DecimationFilter(BaseTool):
    name = "Decimation (Step)"
    group = "Sampling"
    description = "Keeps every Nth point. Fast downsampling."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"step": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.decimation",
            "step": int(params.get("step", 10))
        }

@register_tool
class VoxelDownsizeFilter(BaseTool):
    name = "Voxel Grid"
    group = "Sampling" 
    description = "Reduces density using a Voxel Grid (Uniform distribution)."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"cell_size": 0.5}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.voxeldownsize",
            "cell": float(params.get("cell_size", 0.5)) 
        }

@register_tool
class FarthestPointSamplingFilter(BaseTool):
    name = "Farthest Point (FPS)"
    group = "Sampling"
    description = "Selects points maximizing distance between them (High quality, Slow)."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"sample_size": 10000}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.fps",
            "count": int(params.get("sample_size", 10000)) 
        }

@register_tool
class HeadFilter(BaseTool):
    name = "Head (First N)"
    group = "Sampling"
    description = "Returns the first N points."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"count": 1000}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.head",
            "count": int(params.get("count", 1000))
        }

@register_tool
class TailFilter(BaseTool):
    name = "Tail (Last N)"
    group = "Sampling"
    description = "Returns the last N points."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"count": 1000}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.tail",
            "count": int(params.get("count", 1000))
        }

@register_tool
class SmrfFilter(BaseTool):
    name = "SMRF (Simple Morph.)"
    group = "Ground Classification"
    description = (
        "Simple Morphological Filter. "
        "Classifies ground (Class 2). Use 'Extract Ground' to keep only ground points."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "slope": 0.2,
            "threshold": 0.15,
            "window": 18.0,
            "action": ["Classify Only", "Extract Ground"]
        }

    def build_config(self, params: Dict[str, Any]) -> Union[Dict, List]:
        action = params.get("action", "Classify Only")
        
        smrf_stage = {
            "type": "filters.smrf",
            "slope": float(params.get("slope", 0.2)),
            "threshold": float(params.get("threshold", 0.15)),
            "window": float(params.get("window", 18.0))
        }

        if action == "Extract Ground":
            range_stage = {
                "type": "filters.range",
                "limits": "Classification[2:2]" 
            }
            return [smrf_stage, range_stage]

        return smrf_stage
    
@register_tool
class PmfFilter(BaseTool):
    name = "PMF (Progressive Morph.)"
    group = "Ground Classification" 
    description = "Progressive Morphological Filter."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "max_window_size": 33, 
            "slope": 1.0, 
            "max_distance": 2.0,
            "action": ["Classify Only", "Extract Ground"]
        }

    def build_config(self, params: Dict[str, Any]) -> Union[Dict, List]:
        action = params.get("action", "Classify Only")

        pmf_stage = {
            "type": "filters.pmf",
            "max_window_size": int(params.get("max_window_size", 33)), 
            "slope": float(params.get("slope", 1.0)),
            "max_distance": float(params.get("max_distance", 2.0))
        }

        if action == "Extract Ground":
            range_stage = {
                "type": "filters.range",
                "limits": "Classification[2:2]" 
            }
            return [pmf_stage, range_stage]

        return pmf_stage

@register_tool
class CsfFilter(BaseTool):
    name = "CSF (Cloth Simulation)"
    group = "Ground Classification" 
    description = "Cloth Simulation Filter. Very robust for terrain extraction."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "resolution": 1.0,
            "threshold": 0.5,
            "rigidness": 2,
            "action": ["Classify Only", "Extract Ground"]
        }

    def build_config(self, params: Dict[str, Any]) -> Union[Dict, List]:
        action = params.get("action", "Classify Only")

        csf_stage = {
            "type": "filters.csf",
            "resolution": float(params.get("resolution", 1.0)),
            "threshold": float(params.get("threshold", 0.5)),
            "rigidness": int(params.get("rigidness", 2))
        }

        if action == "Extract Ground":
            range_stage = {
                "type": "filters.range",
                "limits": "Classification[2:2]" 
            }
            return [csf_stage, range_stage]

        return csf_stage

@register_tool
class DbscanFilter(BaseTool):
    name = "DBSCAN (Density)"
    group = "Segmentation"
    description = "Density-Based Clustering. Extracts clusters based on density."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "min_points": 5, 
            "eps": 0.5,
            "dimensions": "X,Y,Z"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.dbscan",
            "min_points": int(params.get("min_points", 5)),
            "eps": float(params.get("eps", 0.5)),
            "dimensions": str(params.get("dimensions", "X,Y,Z"))
        }
    
@register_tool
class ClusterFilter(BaseTool):
    name = "Euclidean Cluster"
    group = "Segmentation"
    description = "Groups points within a distance tolerance."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "tolerance": 1.0, 
            "min_points": 10,
            "dimensions": "X,Y,Z"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.cluster",
            "tolerance": float(params.get("tolerance", 1.0)),
            "min_points": int(params.get("min_points", 10)),
            "dimensions": str(params.get("dimensions", "X,Y,Z"))
        }

@register_tool
class SupervoxelFilter(BaseTool):
    name = "Supervoxel"
    group = "Segmentation"
    description = "Segments cloud into perceptually homogeneous supervoxels."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "Info": "Requires Normals first.",
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.supervoxel",
        }

@register_tool
class RangeFilter(BaseTool):
    name = "Range Filter"
    group = "Attributes & Values"
    description = "Keeps points satisfying criteria. Ex: 'Classification![7:7]'"
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"limits": "Classification![7:7]"}
    
    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.range",
            "limits": str(params.get("limits", "Classification![7:7]"))
        }

@register_tool
class ExpressionFilter(BaseTool):
    name = "Expression (Math)"
    group = "Attributes & Values"
    description = "Passes points satisfying a formula. Ex: 'Z > 100'"
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"expression": "Z > 100"}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.expression",
            "expression": str(params.get("expression", "Z > 100"))
        }

@register_tool
class FerryFilter(BaseTool):
    name = "Ferry (Copy Dim)"
    group = "Attributes & Values"
    description = "Copies data from source to target dimension. Ex: Z => Z_ORIG"
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "source_dimension": "Z",    
            "target_dimension": "Z_COPY"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        source = str(params.get("source_dimension", "Z"))
        target = str(params.get("target_dimension", "Z_COPY"))
        ferry_string = f"{source} => {target}"

        return {
            "type": "filters.ferry",
            "dimensions": ferry_string
        }
        
@register_tool
class AssignFilter(BaseTool):
    name = "Assign Value"
    group = "Attributes & Values"
    description = "Assigns values based on conditions. Ex: 'Classification[0:2]=1'"
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"value": "Classification[0:2]=1"}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.assign",
            "value": str(params.get("value", "Classification[0:2]=1"))
        }

@register_tool
class SetCRSFilter(BaseTool):
    name = "Set CRS (Metadata)"
    group = "Coordinates"
    description = "Tags data with a CRS (No transformation). Default: EPSG:3857"
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"in_srs": "EPSG:3857"}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.reprojection",
            "in_srs": params.get("in_srs", "EPSG:3857"),
            "out_srs": params.get("in_srs", "EPSG:3857")
        }

@register_tool
class ReprojectionFilter(BaseTool):
    name = "Reprojection (Transform)"
    group = "Coordinates"
    description = "Transforms coordinates. Ex: WGS84 (4326) -> Web Mercator (3857)."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "in_srs": "EPSG:4326",
            "out_srs": "EPSG:3857"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.reprojection",
            "in_srs": params.get("in_srs", "EPSG:4326"),
            "out_srs": params.get("out_srs", "EPSG:3857")
        }

@register_tool
class CropFilter(BaseTool):
    name = "Crop (BBox)"
    group = "Spatial Tools"
    description = "Crops the point cloud using a bounding box."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {"bounds": "([0, 100], [0, 100])"}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.crop",
            "bounds": str(params.get("bounds"))
        }
    
@register_tool
class MergeFilter(BaseTool):
    name = "Merge Layers"
    group = "Spatial Tools"
    description = "Merges multiple input files into a single layer."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "filters.merge"}
    
@register_tool
class ElevationModel(BaseTool):
    name = "Elevation Model (DEM)"
    group = "Spatial Tools"
    description = "Generates a Raster DEM/DSM."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "filters.dem"}

@register_tool
class StatsFilter(BaseTool):
    name = "Statistics"
    group = "Analysis & Features"
    description = "Calculates statistical info (min, max, mean)."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "dimensions": "", 
            "enumerate": "Classification" 
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        config = {"type": "filters.stats"}
        dims = str(params.get("dimensions", "")).strip()
        enums = str(params.get("enumerate", "Classification")).strip()
        
        if dims: config["dimensions"] = dims
        if enums: config["enumerate"] = enums
            
        return config

@register_tool
class NormalFilter(BaseTool):
    name = "Calculate Normals"
    group = "Analysis & Features"
    description = "Calculates surface normal vectors (NormalX, NormalY, NormalZ)."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"knn": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.normal",
            "knn": int(params.get("knn", 10)),
        }
    
@register_tool
class EigenvaluesFilter(BaseTool):
    name = "Calculate Eigenvalues"
    group = "Analysis & Features" 
    description = "Calculates covariance eigenvalues (Linearity, Planarity)."
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"knn": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.eigenvalues",
            "knn": int(params.get("knn", 10)),
        }