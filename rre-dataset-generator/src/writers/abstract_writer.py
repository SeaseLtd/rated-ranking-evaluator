from abc import ABC, abstractmethod
from pathlib import Path
from src.data_store import DataStore

class AbstractWriter(ABC):
    """
    Abstract base class for writers.
    """

    def __init__(self) -> None:
        pass

    @abstractmethod
    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """Writes the data from the datastore to a file."""
        raise NotImplementedError