from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def group(self) -> str:
        pass

    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        pass

    def build_config(self, params:Dict[str, Any]) -> Dict[str, Any]:
        pass