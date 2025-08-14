from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

log = logging.getLogger(__name__)

class Document(BaseModel):
    """
    Represents a document with a unique identifier, and fields.
    """

    # [Optional] apply strict model config:
    # extra='forbid' - catch unexpected fields -> Raise
    # validate_assignment=True - re-validate on mutation.
    # frozen=True - immutability after creation.
    # model_config = ConfigDict(extra='forbid', validate_assignment=True, frozen=True)

    model_config = ConfigDict(extra='ignore')

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
    def validate_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the fields dictionary and its keys are not empty and that all values are JSON-serializable."""
        if not v:
            raise ValueError('The fields dictionary cannot be empty.')
        if any(not key for key in v.keys()):
            raise ValueError('Field keys cannot be empty strings.')

        def is_jsonable(value: Any) -> bool:
            if isinstance(value, (str, int, float, bool)) or value is None:
                return True
            if isinstance(value, list):
                return all(is_jsonable(item) for item in value)
            if isinstance(value, dict):
                return all(isinstance(k, str) and is_jsonable(val) for k, val in value.items())
            return False

        if not is_jsonable(v):
            raise ValueError('Field values must be JSON-serializable (primitives, lists, or dicts).')
        return v

