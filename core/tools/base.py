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

    @property
    @abstractmethod
    def description(self) -> str:
        return "No description available for this tool."

    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        pass

    def build_config(self, params:Dict[str, Any]) -> Dict[str, Any]:
        pass