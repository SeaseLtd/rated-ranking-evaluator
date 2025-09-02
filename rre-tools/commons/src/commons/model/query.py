from __future__ import annotations
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

class Query(BaseModel):
    """
    Represents a search query.
    """

    # [Optional] apply strict model config:
    # extra='forbid' - catch unexpected fields -> Raise
    # validate_assignment=True - re-validate on mutation.
    # frozen=True - immutability after creation.
    # model_config = ConfigDict(extra='forbid', validate_assignment=True, frozen=True)

    model_config = ConfigDict(extra='ignore')

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier of the query.", min_length=1)
    text: str = Field(..., description="The raw query text.", min_length=1)