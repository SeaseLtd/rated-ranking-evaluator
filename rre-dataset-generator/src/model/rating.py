from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Rating(BaseModel):
    """
    Represents a rating score for a document with an optional reasoning.
    """
    score: int = Field(..., description="Relevance score of the document.")
    reasoning: Optional[str] = Field(None, description="LLM-generated explanation for the score.")

    @field_validator("reasoning")
    @classmethod
    def non_empty_reasoning(cls, reasoning):
        if reasoning is not None and not reasoning.strip():
            raise ValueError("Reasoning must not be empty if provided.")
        return reasoning


