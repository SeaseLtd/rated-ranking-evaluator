from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationError
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
