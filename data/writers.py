from data.data_handler import IDataWriter
from typing import Any, Dict
import json
import os

class PipelineWriter(IDataWriter):
     
    def write(self, file_path:str, data:list, **kwargs) -> Dict[str, Any]:
        try:
            if not file_path.lower().endswith(".json"):
                file_path +=".json"
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            return {"status": True, "path":file_path}
        
        except Exception as e: 
            return {"status":False, "error":str(e)}

class LasWriter(IDataWriter):
    
    def write(self, file_path:str, data:list, **kwargs) -> Dict[str, Any]:
        pass