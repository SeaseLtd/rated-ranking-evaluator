from __future__ import annotations
from uuid import uuid4
from pydantic import BaseModel, Field, NonNegativeInt
import logging

log = logging.getLogger(__name__)

class Rating(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str
    query_id: str
    score: NonNegativeInt