from abc import ABC, abstractmethod
from typing import Dict, Any

class IDataReader(ABC):

    @abstractmethod
    def read(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_bounds(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_sample_data(self) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def get_summary_metadata(self, full_metadata:Dict) -> Dict[str, Any]:
        pass