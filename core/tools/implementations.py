from core.tools.registry import register_tool
from core.tools.base import BaseTool
from typing import Dict, Any

@register_tool
class OutlierFilter(BaseTool):
    name = "Outliers"
    group = "Noise/Outlier"
    description = (
        "Classify noise using statistical analysis (Mean/Stdev). "
        "Useful for cleaning up isolated points in the cloud."
    )
    supports_batch = True

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
    group = "Data Manipulation"
    description = (
        "Keeps points that fall within specific criteria. "
        "Use 'Classification![7:7]' to remove noise, or 'Z[0:100]' for elevation."
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
class DecimationFilter(BaseTool):
    name = "Decimation Sampling"
    group = "Sampling"
    description = (
        "Keeps every Nth point from the cloud, effectively downsampling it."
        "Use this for quick visualization of large datasets."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {"step": 10}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.decimation",
            "step": int(params.get("step", 1))
        }
    
@register_tool
class SmrfFilter(BaseTool):
    name = "SMRF (Ground)"
    group = "Classification"
    description = (
        "Simple Morphological Filter. "
        "It classifies ground points by comparing elevations against an interpolated surface."
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
    name = "PMF (Ground)"
    group = "Classification" 
    description = (
        "Progressive Morphological Filter."
        "It classifies ground points using a progressive window size and threshold."
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
class DbscanFilter(BaseTool):
    name = "DBSCAN Clustering"
    group = "Segmentation"
    description = (
        "DBSCAN Clustering. Extracts and labels clusters based on point density "
        "using Euclidean distance. Highly effective for segmenting individual objects."
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
class CsfFilter(BaseTool):
    name = "CSF (Ground)"
    group = "Classification" 
    description = (
        "Cloth Simulation Filter (Zhang et al., 2016). Highly accurate "
        "ground classification using a simulated cloth to model the terrain."
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
class IqrFilter(BaseTool):
    name = "IQR (Noise)"
    group = "Noise/Outlier"
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
class VoxelDownsizeFilter(BaseTool):
    name = "Voxel Downsize"
    group = "Sampling" 
    description = (
        "Reduces the point cloud density using a Voxel Grid. "
        "It selects the first point within each 3D cell (voxel), "
        "resulting in a uniformly distributed point cloud."
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
class NormalFilter(BaseTool):
    name = "Normal Calculation"
    group = "Feature Extraction"
    description = (
        "Calculates the normal vector (NormalX, NormalY, NormalZ) for each point "
        "based on its k-nearest neighbors. Essential for surface analysis and modeling."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "knn": 10
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.normal",
            "knn": int(params.get("knn", 10)),
        }
    
@register_tool
class EigenvaluesFilter(BaseTool):
    name = "Eigenvalues Calculation"
    group = "Feature Extraction" 
    description = (
        "Calculates the eigenvalues (Lambda1, Lambda2, Lambda3) of the covariance "
        "matrix based on k-nearest neighbors. Used to determine local geometry features."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "knn": 10
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.eigenvalues",
            "knn": int(params.get("knn", 10)),
        }

@register_tool
class ExpressionFilter(BaseTool):
    name = "Expression Filter"
    group = "Data Manipulation"
    description = (
        "Passes only points that satisfy a mathematical/logical expression (e.g., "
        "'Z > 100' or 'Classification == 2'). Offers maximum flexibility."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "expression": "Z > 100"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.expression",
            "expression": str(params.get("expression", "Z > 100"))
        }
    
@register_tool
class SetCRSFilter(BaseTool):
    name = "Set CRS"
    group = "Geo-Processing"
    description = (
        "Manually sets the Coordinate Reference System (CRS) for unreferenced data. "
        "This tool only adds the CRS metadata (in_srs) to the points, no coordinate transformation is performed."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "in_srs": "EPSG:3857"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.reprojection",
            "in_srs": params.get("in_srs", 3857),
            "out_srs": params.get("in_srs", 3857)
        }

@register_tool
class ReprojectionFilter(BaseTool):
    name = "Reprojection"
    group = "Geo-Processing"
    description = (
        "Transforms point cloud data from one Coordinate Reference System (CRS) "
        "to another, typically defined by an EPSG code (e.g., EPSG:4326)."
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
class SupervoxelFilter(BaseTool):
    name = "Supervoxel Segmentation"
    group = "Segmentation"
    description = (
        "Segments the point cloud into perceptually homogeneous 'supervoxels'. "
        "Useful for advanced object segmentation and scene understanding."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "Params": "First filters.normal should work",
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.supervoxel",
        }
    
@register_tool
class FarthestPointSamplingFilter(BaseTool):
    name = "FPS Filter (Sampling)"
    group = "Sampling"
    description = (
        "Farthest Point Sampling (FPS). Selects a subset of points that "
        "maximizes the distance between selected points, ensuring a uniform "
        "and representative sampling of the whole cloud. Requires a sample size."
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
class FerryFilter(BaseTool):
    name = "Ferry Filter (Copy Dim)"
    group = "Data Manipulation"
    description = (
        "Copies data from a source dimension to a target dimension. "
        "Useful for persisting intermediate results or transferring attributes (e.g., 'ClusterID => Classification')."
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
    name = "Assign"
    group = "Data Manipulation"
    description = (
        "Assigns a single value to a dimension or dimension range defined by a formula (e.g., "
        "'Classification[0:2]=1' to set Class 0 and 1 to 1, or 'Z=Z*2.0' to scale Z)."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "value": "Classification[0:2]=1" 
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.assign",
            "value": str(params.get("value", "Classification[0:2]=1"))
        }
    
@register_tool
class LofFilter(BaseTool):
    name = "LOF Filter"
    group = "Noise/Outlier"
    description = (
        "Local Outlier Factor (LOF) filter. Detects local outliers by comparing "
        "the local density of a point with the local densities of its neighbors. "
        "Effective for varying-density point clouds."
    )
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
class ClusterFilter(BaseTool):
    name = "Cluster (Euclidean)"
    group = "Segmentation"
    description = (
        "Performs Euclidean distance clustering. Assigns a unique ClusterID to "
        "groups of points that are within the specified distance tolerance."
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
class HeadFilter(BaseTool):
    name = "Head Filter (First N)"
    group = "Sampling"
    description = (
        "Returns the first N points from the beginning of the point cloud stream. "
        "Useful for quick file inspection and debugging."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "count": 1000
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.head",
            "count": int(params.get("count", 1000))
        }

@register_tool
class TailFilter(BaseTool):
    name = "Tail Filter (Last N)"
    group = "Sampling"
    description = (
        "Returns the last N points from the end of the point cloud stream. "
        "Useful for inspecting the end of large data files."
    )
    supports_batch = True

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "count": 1000
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.tail",
            "count": int(params.get("count", 1000))
        }
    
@register_tool
class CropFilter(BaseTool):
    name = "Crop (BBox)"
    group = "Geo-Processing"
    description = "Crops the point cloud using a bounding box."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "bounds": "([0, 100], [0, 100])"
        }

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.crop",
            "bounds": str(params.get("bounds"))
        }
    
@register_tool
class MergeFilter(BaseTool):
    name = "Merge"
    group = "Geo-Processing"
    description = "Merges multiple input files into a single point cloud."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.merge"
        }
    
@register_tool
class ElevationModel(BaseTool):
    name = "Elevation Model"
    group = "Geo-Processing"
    description = "Generate elevation model from a file."
    supports_batch = False

    def get_default_params(self) -> Dict[str, Any]:
        return {}

    def build_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "filters.dem"
        }
    
@register_tool
class StatsFilter(BaseTool):
    name = "Statistics"
    group = "Geo-Processing"
    description = "Calculates statistical information (min, max, mean, etc.) for dimensions."
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
        
        if dims:
            config["dimensions"] = dims
        if enums:
            config["enumerate"] = enums
            
        return config