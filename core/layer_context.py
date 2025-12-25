from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PipelineStage:
    name: str
    params: dict
    config: dict
    is_active: bool = True

    @property
    def display_text(self) -> str:
        params_str = ", ".join([f"{k}:{v}" for k, v in self.params.items()])
        return f"{self.name} ({params_str})" if params_str else self.name


class LayerContext:

    def __init__(
        self,
        file_path: str,
        initial_metadata: Dict,
        full_metadata: Dict = None,
        reader_config: Dict = None,
    ):
        self.file_path = file_path
        self.metadata = initial_metadata
        self.full_metadata = full_metadata

        self.reader_config = reader_config or {
            "type": "readers.las",
            "filename": self.file_path,
        }

        self.stages: List[PipelineStage] = []
        self.active_style: str = "Elevation"

        self.current_render_data: Optional[Any] = None
        self.is_visible: bool = True
        self.bounds: Optional[Dict] = None
        self.is_database: bool = (
            False 
        )

    def add_stage(self, stage: PipelineStage):
        self.stages.append(stage)

    def get_full_pipeline_json(self) -> List[Dict[str, Any]]:
        pipeline = [self.reader_config]

        for stage in self.stages:
            if stage.is_active:
                if isinstance(stage.config, list):
                    pipeline.extend(stage.config)
                else:
                    pipeline.append(stage.config)

        return pipeline

    def remove_stage(self, index: int):
        if 0 <= index < len(self.stages):
            del self.stages[index]
