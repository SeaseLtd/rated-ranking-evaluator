from .document import Document
from .rating import Rating

from uuid import uuid4
from pydantic import BaseModel, Field
from typing import List

class Query(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    doc_ids: List[str] =  Field(default_factory=list)
    related_ratings_ids: List[str] = Field(default_factory=list)

    # helpers de dominio opcionales
    def add_doc(self, doc: Document) -> None:
        if doc.id not in self.doc_ids:
            self.doc_ids.append(doc.id)

    def add_rating(self, rating: Rating) -> None:
        if rating.id not in self.related_ratings_ids:
            self.related_ratings_ids.append(rating.id)

