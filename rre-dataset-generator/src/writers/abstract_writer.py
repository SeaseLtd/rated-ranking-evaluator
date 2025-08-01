from abc import ABC, abstractmethod
from typing import List, Tuple
from pathlib import Path

from src.model.query_rating_context import QueryRatingContext
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
        for query_ctx in self.datastore.get_queries():
            query_text = query_ctx.get_query_text()
            for doc_id in query_ctx.get_doc_ids():
                if query_ctx.has_rating_score(doc_id):
                    rating = query_ctx.get_rating_score(doc_id)
                    result.append((query_text, doc_id, rating))
        return result
