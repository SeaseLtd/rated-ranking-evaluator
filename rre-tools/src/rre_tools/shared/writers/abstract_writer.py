from abc import ABC, abstractmethod
from pathlib import Path
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.writers.writer_config import WriterConfig

class AbstractWriter(ABC):
    """
    Abstract base class for writers.
    """

    def __init__(self, writer_config: WriterConfig) -> None:
        self.writer_config = writer_config
        pass

    @abstractmethod
    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """Writes the data from the datastore to a file."""
        raise NotImplementedError