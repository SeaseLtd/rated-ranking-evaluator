import uuid
from typing import Dict


class QueryRatingContext:
    """
    QueryRatingContext holds
    generated unique id,
    query,
    doc id → rating  dict (doc_id_to_rating)
    """

    DOC_NOT_RATED: int = -1  # doc is not yet rated

    def __init__(self, query: str, doc_id: str):
        self.id: str = str(uuid.uuid4())
        self.query: str = query
        self.doc_id_to_rating: Dict[str, int] = {doc_id: self.DOC_NOT_RATED}

    def add_doc(self, doc_id: str) -> None:
        if doc_id not in self.doc_id_to_rating:
            self.doc_id_to_rating[doc_id] = self.DOC_NOT_RATED

    def add_rating_for_query(self, doc_id: str, rating: int) -> None:
        self.doc_id_to_rating[doc_id] = rating

    def has_rating_for_query(self, doc_id: str) -> bool:
        return self.doc_id_to_rating[doc_id] != self.DOC_NOT_RATED
