from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, NonNegativeInt

class Rating(BaseModel):
    """
    Represents a rating assigned to a document for a given query.
    """

    # [Optional] apply strict model config:
    # extra='forbid' - catch unexpected fields -> Raise
    # validate_assignment=True - re-validate on mutation.
    # frozen=True - immutability after creation.
    # model_config = ConfigDict(extra='forbid', validate_assignment=True, frozen=True)

    model_config = ConfigDict(extra='ignore')
    
    doc_id: str = Field(..., description="ID of the rated document.", min_length=1)
    query_id: str = Field(..., description="ID of the query associated with the rating.", min_length=1)
    score: NonNegativeInt = Field(..., description="Non-negative rating score.")
    explanation: Optional[str] = Field(default=None, description="Optional explanation for the rating score provided by LLM.")
