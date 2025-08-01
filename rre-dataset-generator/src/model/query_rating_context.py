import uuid
from typing import Dict, List, Any


class QueryRatingContext:
    """
    QueryRatingContext holds
    generated unique id,
    query,
    doc id → rating score (dict)
    """

    DOC_NOT_RATED: int = -1  # doc is not yet rated

    def __init__(self, query: str, doc_id: str | None = None, query_id:str = None):
        self._id: str = str(uuid.uuid4()) if query_id is None else query_id
        self._query: str = query
        self._doc_id_to_rating_score: Dict[str, int] = {}
        # HANDLING NONEs - threw error in some tests
        if doc_id is not None:
            self._doc_id_to_rating_score[doc_id] = self.DOC_NOT_RATED

    def get_query_id(self) -> str:
        """Return the unique identifier for this query context."""
        return self._id

    def get_query_text(self) -> str:
        """Return the original query string."""
        return self._query

    def get_doc_ids(self) -> List[str]:
        """Return all doc ids currently tracked for this query context"""
        return list(self._doc_id_to_rating_score.keys())

    def add_doc_id(self, doc_id: str) -> None:
        if doc_id not in self._doc_id_to_rating_score:
            self._doc_id_to_rating_score[doc_id] = self.DOC_NOT_RATED

    def add_rating_score(self, doc_id: str, rating_score: int) -> None:
        self._doc_id_to_rating_score[doc_id] = rating_score

    def has_rating_score(self, doc_id: str) -> bool:
        return doc_id in self._doc_id_to_rating_score and self._doc_id_to_rating_score[doc_id] != self.DOC_NOT_RATED

    def get_rating_score(self, doc_id: str) -> int:
        return self._doc_id_to_rating_score[doc_id]


    @classmethod
    def from_dict(cls, context_as_dict: Dict[str, Any]) -> "QueryRatingContext":
        query_id = context_as_dict.get("id", None)
        query_text = context_as_dict.get("query", "")
        doc_ratings = context_as_dict.get("doc_ratings", {})

        context = cls(query=query_text, query_id=query_id)
        for doc_id, rating in doc_ratings.items():
            context.add_doc_id(doc_id)
            context.add_rating_score(doc_id, rating)

        return context

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the QueryRatingContext to a JSON-serializable dictionary.
        """
        return {
            "id": self._id,
            "query": self._query,
            "doc_ratings": self._doc_id_to_rating_score
        }
