from enum import Enum

class Dimensions(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"
    INTENSITY = "Intensity"
    CLASSIFICATION = "Classification"
    RED = "Red"
    GREEN = "Green"
    BLUE = "Blue"

class ToolNames(str, Enum):
    CROP = "Crop (BBox)"
    MERGE = "Merge"
    MODEL = "Elevation Model"
    STATS = "Statistics"