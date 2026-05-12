"""Tests for `LLMScoreResponse` construction and explanation normalization.

The blank-string normalization matters for the batch flow: providers can
return ``explanation=""`` instead of omitting the field, and the batch
result-assembly path used to raise a non-retryable ValueError on that input.
Normalizing ``""`` (or whitespace-only) to ``None`` matches the plan's
already-permitted "per-item explanation may be missing" contract and keeps
the single-pair flow consistent.
"""
from __future__ import annotations

import pytest

from rre_tools.dataset_generator.models import LLMScoreResponse


@pytest.mark.parametrize("blank", ["", " ", "\t", "\n", "   \n\t  "])
def test_blank_or_whitespace_explanation__normalized_to_none(blank):
    resp = LLMScoreResponse(score=1, scale="binary", explanation=blank)
    assert resp.explanation is None


def test_none_explanation__stays_none():
    resp = LLMScoreResponse(score=1, scale="binary", explanation=None)
    assert resp.explanation is None


def test_non_empty_explanation__preserved():
    resp = LLMScoreResponse(score=2, scale="graded", explanation="because reasons")
    assert resp.explanation == "because reasons"


def test_non_string_explanation__rejected():
    with pytest.raises(ValueError, match="must be a string"):
        LLMScoreResponse(score=1, scale="binary", explanation=123)  # type: ignore[arg-type]


def test_invalid_scale__rejected():
    with pytest.raises(ValueError, match="Invalid scale"):
        LLMScoreResponse(score=1, scale="fuzzy", explanation=None)


def test_score_out_of_range_for_scale__rejected():
    with pytest.raises(ValueError, match="binary scale"):
        LLMScoreResponse(score=2, scale="binary", explanation=None)
