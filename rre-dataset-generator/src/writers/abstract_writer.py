from abc import ABC, abstractmethod
from typing import List, Tuple
from pathlib import Path

from src.search_engine.data_store import DataStore


class AbstractWriter(ABC):
    """
    Abstract base class for writers.

    The writer has to read the data structure and export it to a format (e.g., quepid, rre..)
    """

    def __init__(self, datastore: DataStore):
        self.datastore = datastore

    @abstractmethod
    def write(self, output_path: str | Path) -> None:
        """Writes the data from the datastore to a file."""
        pass

    def _get_queries_with_ratings(self) -> List[Tuple[str, str, int]]:
        """
        Helper method to extract (query_text, doc_id, rating) tuples from the datastore.
        This can be used by subclasses to get the data in a consistent format.
        """
        result = []
        # DataStore now returns `Query` pydantic models. Iterate accordingly.
        for query in self.datastore.get_queries():
            query_text = query.text
            # Depending on revision the query object may expose the list of
            # associated documents under either `related_docs_ids` (legacy)
            # or `doc_ids` (current). Support both for compatibility.
            doc_ids = (
                getattr(query, "related_docs_ids", None)
                or getattr(query, "doc_ids", [])
            )
            for doc_id in doc_ids:
                rating = self.datastore.get_rating_score(query.id, doc_id)
                if rating is not None:
                    result.append((query_text, doc_id, rating))
        return result
