from __future__ import annotations
from uuid import uuid4
from pydantic import BaseModel, Field, NonNegativeInt, field_validator
from typing import List, Dict, Any
import logging

log = logging.getLogger(__name__)

class Document(BaseModel):
    """
    Represents a document with a unique identifier, and fields.
    """
    id: str = Field(
        ...,
        description="Unique identifier of the document.",
        min_length=1
    )
    fields: Dict[str, Any] = Field(
        ...,
        description="Fields of the document."
    )
    @field_validator('fields')
    @classmethod
    def check_no_empty_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the fields dictionary is not empty and its keys are not empty."""
        if not v:
            log.error('The fields dictionary cannot be empty.')
            raise ValueError('The fields dictionary cannot be empty.')
        if any(not key for key in v.keys()):
            log.error('Field keys cannot be empty strings.')
            raise ValueError('Field keys cannot be empty strings.')
        return v

class Rating(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str
    query_id: str
    score: NonNegativeInt



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

