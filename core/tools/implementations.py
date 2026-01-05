from core.tools.registry import register_tool
from core.tools.base import BaseTool
from typing import Dict, Any

@register_tool
class OutlierFilter(BaseTool):
    name = "Outliers (Statistical)"
    group = "Cleaning & Noise"
    description = (
        "Classify noise using statistical analysis (Mean/Stdev). "
        "Useful for cleaning up isolated points in the cloud."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"mean_k": 8, "multiplier": 2.0}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": int(params.get("mean_k", 8)),
            "multiplier": float(params.get("multiplier", 2.0))
        }

@register_tool
class IqrFilter(BaseTool):
    name = "IQR (Box Plot)"
    group = "Cleaning & Noise"
    description = (
        "Removes outliers using the Interquartile Range (IQR) method. "
        "It is more robust to extreme outliers than standard deviation methods."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "dimension": "Z",
            "k": 1.5
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.iqr",
            "dimension": str(params.get("dimension", "Z")),
            "k": float(params.get("k", 1.5))
        }

@register_tool
class LofFilter(BaseTool):
    name = "LOF (Local Density)"
    group = "Cleaning & Noise"
    description = (
        "Local Outlier Factor (LOF) filter. Detects local outliers by comparing "
        "the local density of a point with the local densities of its neighbors."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"minpts": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.lof",
            "minpts": int(params.get("minpts", 10))
        }

@register_tool
class DecimationFilter(BaseTool):
    name = "Decimation (Step)"
    group = "Sampling"
    description = (
        "Keeps every Nth point from the cloud. "
        "Fastest way to downsample large datasets."
    )
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
    description = (
        "Reduces density using a Voxel Grid. "
        "Selects one point per 3D cell, creating a uniform distribution."
    )
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
    description = (
        "Selects a subset of points that maximizes the distance between them. "
        "Ensures high spatial coverage but is slower than others."
    )
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
    description = "Returns the first N points from the beginning of the stream."
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
    description = "Returns the last N points from the end of the stream."
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
        "Classifies ground points by comparing elevations against an interpolated surface."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "slope": 0.2,
            "threshold": 0.15,
            "window": 18.0
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
    name = "PMF (Progressive Morph.)"
    group = "Ground Classification" 
    description = (
        "Progressive Morphological Filter. "
        "Iteratively processes the cloud with increasing window sizes."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "max_window_size": 33, 
            "slope": 1.0, 
            "max_distance": 2.0 
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.pmf",
            "max_window_size": int(params.get("max_window_size", 33)), 
            "slope": float(params.get("slope", 1.0)),
            "max_distance": float(params.get("max_distance", 2.0))
        }

@register_tool
class CsfFilter(BaseTool):
    name = "CSF (Cloth Simulation)"
    group = "Ground Classification" 
    description = (
        "Cloth Simulation Filter. "
        "Models terrain by inverting the cloud and simulating a cloth dropping on it."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "resolution": 1.0,
            "threshold": 0.5,
            "rigidness": 2
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.csf",
            "resolution": float(params.get("resolution", 1.0)),
            "threshold": float(params.get("threshold", 0.5)),
            "rigidness": int(params.get("rigidness", 2))
        }

@register_tool
class DbscanFilter(BaseTool):
    name = "DBSCAN (Density)"
    group = "Segmentation"
    description = (
        "Density-Based Clustering. "
        "Extracts clusters based on point density. Good for object detection."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "min_points": 5, 
            "eps": 0.5 
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.dbscan",
            "min_points": int(params.get("min_points", 5)),
            "eps": float(params.get("eps", 0.5))
        }
    
@register_tool
class ClusterFilter(BaseTool):
    name = "Euclidean Cluster"
    group = "Segmentation"
    description = (
        "Simple Euclidean Clustering. "
        "Groups points that are within a specified distance tolerance."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "tolerance": 1.0, 
            "min_points": 10 
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.cluster",
            "tolerance": float(params.get("tolerance", 1.0)),
            "min_points": int(params.get("min_points", 10))
        }

@register_tool
class SupervoxelFilter(BaseTool):
    name = "Supervoxel"
    group = "Segmentation"
    description = (
        "Segments the point cloud into perceptually homogeneous 'supervoxels'. "
        "Requires Normal Calculation beforehand."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "Info": "Ensure Normals are computed first.",
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.supervoxel",
        }

@register_tool
class RangeFilter(BaseTool):
    name = "Range Filter"
    group = "Attributes & Values"
    description = (
        "Keeps points that fall within specific criteria. "
        "Ex: 'Classification![7:7]' (Remove Noise) or 'Z[0:100]'."
    )
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
    description = (
        "Passes points satisfying a custom formula. "
        "Ex: 'Z > 100' or 'Intensity > 4000'."
    )
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
    description = (
        "Copies data from a source dimension to a target dimension. "
        "Ex: Copy 'Z' to 'Height' to backup original values."
    )
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
    description = (
        "Assigns values based on conditions. "
        "Ex: 'Classification[0:2]=1' sets unclassified points to 1."
    )
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
    description = (
        "Assigns a Coordinate Reference System to unreferenced data. "
        "Does NOT transform coordinates, only tags metadata."
    )
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
    description = (
        "Transforms point coordinates from one CRS to another. "
        "Ex: WGS84 (4326) to Web Mercator (3857)."
    )
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
    description = "Crops the point cloud using a 2D or 3D bounding box."
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
    description = "Merges multiple input files into a single point cloud layer."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "filters.merge"}
    
@register_tool
class ElevationModel(BaseTool):
    name = "Elevation Model (DEM)"
    group = "Spatial Tools"
    description = "Generates a Raster DEM/DSM from the point cloud."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "filters.dem"}

@register_tool
class StatsFilter(BaseTool):
    name = "Statistics"
    group = "Analysis & Features"
    description = "Calculates statistical info (min, max, mean) for dimensions."
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
    description = (
        "Calculates surface normal vectors (NormalX, NormalY, NormalZ). "
        "Required for advanced shading and segmentation."
    )
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
    description = (
        "Calculates covariance eigenvalues. "
        "Used to analyze local geometry (Linearity, Planarity, Scattering)."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"knn": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.eigenvalues",
            "knn": int(params.get("knn", 10)),
        }