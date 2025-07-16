from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid

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
            raise ValueError('The fields dictionary cannot be empty.')
        if any(not key for key in v.keys()):
            raise ValueError('Field keys cannot be empty strings.')
        return v

class Score(BaseModel):
    """
    Represents the relevance score of a document for a given query.
    """
    doc_id: str = Field(..., description="The unique identifier of the document.")
    value: int = Field(-1, description="The relevance score. -1 indicates not scored.")


class Query(BaseModel):
    """
    Represents a query with its text, a unique identifier, and associated scores.
    """
    id: str = Field(default_factory=lambda: f"q-{uuid.uuid4()}", description="Unique identifier for the query.")
    text: str = Field(..., description="The query text.")
    scores: Dict[str, Score] = Field(..., description="A dictionary of scores for documents, indexed by doc_id.")


from .llm_response import LLMRequest, LLMResponse