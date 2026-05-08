from __future__ import annotations
from typing import Dict, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

# Provenance label used to prioritize which queries make it into the per-run budget.
# It's a *runtime* label that reflects how the query was asserted in the current run, not
# a property of the persisted data. The datastore JSON cache must not include it: anything
# loaded from disk should be treated as 'cached' until promoted by a fresh add this run.
QuerySource = Literal["user", "category", "llm", "cached"]

# Lower number = higher priority for budgeting. user/category share priority 0 because
# both represent explicit user intent for this run; llm-generated comes next; cached last.
SOURCE_PRIORITY: Dict[str, int] = {
    "user": 0,
    "category": 0,
    "llm": 1,
    "cached": 2,
}


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
    # Excluded from model_dump so it's never written to the datastore JSON cache;
    # on load every query falls back to the default 'cached' label.
    source: QuerySource = Field(default="cached", exclude=True)
