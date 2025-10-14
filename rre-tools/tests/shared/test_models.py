# tests/test_models.py
import pytest
from pydantic import ValidationError

from rre_tools.shared.models import Document, Query, Rating

def test_document_ok__expects__returns_id_and_field_value():
    d = Document(id="x", fields={"k": 1})
    assert d.id == "x"
    assert d.fields["k"] == 1

def test_document_empty_fields__expects__raises_value_error():
    with pytest.raises(ValueError):
        Document(id="x", fields={})

def test_document_empty_key__expects__raises_value_error():
    with pytest.raises(ValueError):
        Document(id="x", fields={"": 1})

def test_rating_non_negative__expects__raises_validation_error_for_negative_score():
    with pytest.raises(ValidationError):
        Rating(doc_id="d1", query_id="q1", score=-5)


# ---------------- Additional edge cases ----------------

@pytest.mark.parametrize(
    "fields",
    [
        {"a": None, "b": True, "c": 1, "d": 3.14, "e": "text"},
        {"list": [1, 2, 3], "mixed": ["x", 1, None, True]},
        {"nested": {"k": "v", "n": 2, "deep": {"x": [1, 2, {"y": False}]}}},
        {"empty_list": []},
    ],
)
def test_document_fields_json_serializable_valid(fields):
    d = Document(id="doc", fields=fields)
    assert d.id == "doc"
    assert isinstance(d.fields, dict)


@pytest.mark.parametrize(
    "fields",
    [
        {"not_json": set([1, 2])},
        {"obj": object()},
        {"func": lambda x: x},
        # non-string key at top-level
        {1: "a"},
        # non-string key nested
        {"nested": {1: "a"}},
        # nested non-serializable
        {"nested": {"k": [1, 2, set([3])]}}
    ],
)
def test_document_fields_json_serializable_invalid(fields):
    with pytest.raises(ValueError):
        Document(id="doc", fields=fields)


def test_document_empty_id__expects__validation_error():
    with pytest.raises(ValidationError):
        Document(id="", fields={"k": 1})


def test_query_requires_text__expects__validation_error():
    with pytest.raises(ValidationError):
        Query()


def test_query_auto_generates_id__expects__non_empty_string():
    q = Query(text="hello")
    assert isinstance(q.id, str) and len(q.id) > 0


@pytest.mark.parametrize("score", [0, 1, 123456789])
def test_rating_non_negative_scores__expects__ok(score):
    r = Rating(doc_id="d", query_id="q", score=score)
    assert r.score == score


