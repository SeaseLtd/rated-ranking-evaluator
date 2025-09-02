from abc import ABC, abstractmethod
from pathlib import Path
from src.data_store import DataStore
from src.model import WriterConfig

class AbstractWriter(ABC):
    """
    Abstract base class for writers.
    """

    def __init__(self, config: WriterConfig) -> None:
        self.config = config
        pass

    @abstractmethod
    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """Writes the data from the datastore to a file."""
        raise NotImplementedError