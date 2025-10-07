from typing import Optional, Literal
from pydantic import BaseModel, Field


class BinaryScore(BaseModel):
    """Returns a binary relevance score."""
    score: Literal[0, 1] = Field(..., description="0 = not relevant, 1 = relevant")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")


class GradedScore(BaseModel):
    """Returns a graded relevance score."""
    score: Literal[0, 1, 2] = Field(..., description="0 = not relevant, 1 = maybe, 2 = is the answer")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")
