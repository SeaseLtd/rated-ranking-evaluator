# tests/test_models.py
import pytest
from pydantic import ValidationError

from src.model import Document, Query, Rating 

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

def test_query_add_doc__expects__deduplicates_document_ids():
    q = Query(text="t")
    d = Document(id="d1", fields={"k": 1})
    q.add_doc(d)
    q.add_doc(d)
    assert q.doc_ids == ["d1"]

def test_query_add_rating__expects__deduplicates_rating_ids():
    q = Query(text="t")
    r1 = Rating(doc_id="d1", query_id=q.id, score=1)
    q.add_rating(r1)
    q.add_rating(r1)
    assert q.related_ratings_ids == [r1.id]

def test_rating_non_negative__expects__raises_validation_error_for_negative_score():
    with pytest.raises(ValidationError):
        Rating(doc_id="d1", query_id="q1", score=-5)
