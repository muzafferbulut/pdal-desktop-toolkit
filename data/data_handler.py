from abc import ABC, abstractmethod
from typing import Dict, Any


class IBasicReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> Dict[str, Any]:
        pass


class IMetadataExtractor(ABC):

    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_summary_metadata(self, full_metadata: Dict) -> Dict[str, Any]:
        pass


class IDataSampler(ABC):

    @abstractmethod
    def get_bounds(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_sample_data(self) -> Dict[str, Any]:
        pass


class IDataWriter(ABC):

    @abstractmethod
    def write(self, file_path: str, data: Any, **kwargs) -> Dict[str, Any]:
        pass
