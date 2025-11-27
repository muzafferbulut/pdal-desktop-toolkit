from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import traceback
import pdal
import json

class StatsWorker(QObject):
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, pipeline_config: list):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config

    def run(self):
        try:
            self.progress.emit(10)
            
            json_str = json.dumps(self.pipeline_config)
            pipeline = pdal.Pipeline(json_str)
            
            self.progress.emit(-1)
            count = pipeline.execute()
            self.progress.emit(80)
            metadata = pipeline.metadata
            stats_data = metadata.get("metadata", {}).get("filters.stats", {})
            
            try:
                arrays = pipeline.arrays[0]
                dims = arrays.dtype.names
                
                if "Classification" in dims:
                    cls_data = arrays["Classification"]
                    unique, counts = np.unique(cls_data, return_counts=True)
                    
                    counts_formatted = [f"{int(u)}/{c}" for u, c in zip(unique, counts)]
                    
                    if "statistic" in stats_data:
                        found = False
                        for stat in stats_data["statistic"]:
                            if stat.get("name") == "Classification":
                                stat["counts"] = counts_formatted
                                found = True
                                break
                        
                        if not found:
                            stats_data["statistic"].append({
                                "name": "Classification",
                                "counts": counts_formatted,
                                "count": count
                            })
                            
            except Exception as np_err:
                print(f"Numpy count patch warning: {np_err}")

            self.progress.emit(100)
            self.finished.emit(self.file_path, stats_data)

        except Exception as e:
            self.error.emit(f"Statistics calculation failed: {str(e)}\n{traceback.format_exc()}")