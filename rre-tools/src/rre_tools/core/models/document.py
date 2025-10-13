from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging
from rre_tools.core.utils import is_json_serializable

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
    is_used_to_generate_queries: bool = Field(default=False,
                                                description="Whether the document is used to generate queries.")

    @field_validator('fields')
    @classmethod
    def validate_fields(cls, field_values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the fields dictionary and its keys are not empty and that all values are JSON-serializable."""
        if not field_values:
            raise ValueError('The fields dictionary cannot be empty.')
        if any(not key for key in field_values.keys()):
            raise ValueError('Field keys cannot be empty strings.')

        if not is_json_serializable(field_values):
            raise ValueError('Field values must be JSON-serializable (primitives, lists, or dicts).')
        return field_values
