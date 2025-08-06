from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Rating(BaseModel):
    """
    Represents a rating score for a document with an optional explanation.
    """
    score: int = Field(..., description="Relevance score of the document.")
    explanation: Optional[str] = Field(None, description="LLM-generated explanation for the score.")

    @field_validator("explanation")
    @classmethod
    def non_empty_explanation(cls, explanation):
        if explanation is not None and not explanation.strip():
            raise ValueError("Explanation must not be empty if provided.")
        return explanation


