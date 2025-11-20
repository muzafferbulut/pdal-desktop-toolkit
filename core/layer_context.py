from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class PipelineStage:
    """
    Tek bir pipeline adımını temsil eder.
    """

    name:str
    params:dict
    config:dict
    is_active:bool = True

    @property
    def display_text(self) -> str:
        """
        Treewidgetta görünecek ux metni.
        """

        params_str = ", ".join([f"{k}:{v}" for k, v in self.params.items()])

        return f"{self.name} ({params_str})" if params_str else self.name
    
class LayerContext:
    """
    Bir katman üzerine eklenen tüm stage'lerin
    tutulduğu sınıf.
    """

    def __init__(self, file_path:str, initial_metadata:Dict, full_metadata: Dict = None):
        self.file_path = file_path
        self.metadata = initial_metadata
        self.full_metadata = full_metadata

        # stage list
        self.stages: List[PipelineStage] = []

        self.current_render_data: Optional[Dict] = None

    def add_stage(self, stage:PipelineStage):
        self.stages.append(stage)

    def get_full_pipeline_json(self) -> List[Dict[str, Any]]:
        pipeline = [{"type": "readers.las", "filename": self.file_path}]

        for stage in self.stages:
            if stage.is_active:
                pipeline.append(stage.config)
        
        return pipeline
    
    def remove_stage(self, index:int):
        if 0 <= index < len(self.stages):
            del self.stages[index]