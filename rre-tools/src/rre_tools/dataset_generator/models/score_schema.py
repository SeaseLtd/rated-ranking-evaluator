from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class BinaryScore(BaseModel):
    """Returns a binary relevance score."""
    score: Literal[0, 1] = Field(..., description="0 = not relevant, 1 = relevant")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")


class GradedScore(BaseModel):
    """Returns a graded relevance score."""
    score: Literal[0, 1, 2] = Field(..., description="0 = not relevant, 1 = maybe, 2 = is the answer")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")


# Batch schemas — used when `llm_micro_batch_size > 1`. Each *Item carries an
# explicit `doc_id` because structured-output providers do not guarantee that
# list-of-objects responses preserve input order; the service keys by `doc_id`
# rather than by index. See `LLMService.generate_scores_batch` and the
# response-id contract documented there (every asked id present exactly once,
# no unasked ids).
class BinaryBatchItem(BaseModel):
    """One per-document item in a binary batch relevance-scoring response."""
    doc_id: str = Field(..., description="Document id as given in the prompt")
    score: Literal[0, 1] = Field(..., description="0 = not relevant, 1 = relevant")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")


class GradedBatchItem(BaseModel):
    """One per-document item in a graded batch relevance-scoring response."""
    doc_id: str = Field(..., description="Document id as given in the prompt")
    score: Literal[0, 1, 2] = Field(..., description="0 = not relevant, 1 = maybe, 2 = is the answer")
    explanation: Optional[str] = Field(None, description="Explanation for why this score")


class BinaryBatchScore(BaseModel):
    """Response wrapping per-document binary scores for a single query batch."""
    ratings: List[BinaryBatchItem] = Field(
        ..., description="One rating per requested document, keyed by doc_id."
    )


class GradedBatchScore(BaseModel):
    """Response wrapping per-document graded scores for a single query batch."""
    ratings: List[GradedBatchItem] = Field(
        ..., description="One rating per requested document, keyed by doc_id."
    )
