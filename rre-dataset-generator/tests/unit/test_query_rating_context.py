# tests/test_query_rating_context.py

import pytest
from src.model.query_rating_context import QueryRatingContext


def test_initialization_with_doc_id():
    ctx = QueryRatingContext(query="AI", doc_id="d1")
    assert ctx.get_query_text() == "AI"
    assert ctx.get_doc_ids() == ["d1"]
    assert ctx.has_rating_score("d1") is False


def test_add_doc_id_and_rating():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    ctx.add_rating_score("d1", 1)
    assert ctx.get_rating_score("d1") == 1
    assert ctx.has_rating_score("d1") is True


def test_overwrite_rating_score():
    ctx = QueryRatingContext(query="AI", doc_id="d1")
    ctx.add_rating_score("d1", 0)
    ctx.add_rating_score("d1", 1)
    assert ctx.get_rating_score("d1") == 1


def test_to_and_from_dict_roundtrip():
    ctx1 = QueryRatingContext(query="AI")
    ctx1.add_doc_id("d1")
    ctx1.add_rating_score("d1", 1)
    d = ctx1.to_dict()
    ctx2 = QueryRatingContext.from_dict(d)
    assert ctx2.get_query_id() == ctx1.get_query_id()
    assert ctx2.get_query_text() == ctx1.get_query_text()
    assert ctx2.get_rating_score("d1") == 1


def test_duplicate_doc_id_is_ignored():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    ctx.add_doc_id("d1")  # should not raise or duplicate
    assert ctx.get_doc_ids() == ["d1"]


def test_missing_rating_raises_keyerror():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    with pytest.raises(KeyError):
        ctx.get_rating_score("d1")
