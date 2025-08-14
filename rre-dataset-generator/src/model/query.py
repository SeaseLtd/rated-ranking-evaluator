from __future__ import annotations
from uuid import uuid4
from typing import Optional
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

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier of the query.", min_length=1)
    text: str = Field(..., description="The raw query text.", min_length=1)
    # Reference to the document ID that generated this query (used by Pipeline for query generation tracking)
    generated_from_doc_id: Optional[str] = Field(default=None, description="ID of the document that generated this query, if applicable.")
