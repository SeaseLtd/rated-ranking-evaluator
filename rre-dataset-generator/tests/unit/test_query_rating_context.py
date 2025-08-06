# tests/test_query_rating_context.py

import pytest
from src.model.query_rating_context import QueryRatingContext


def test_initialization__with_doc_id__expects__context_is_created_with_unrated_doc():
    ctx = QueryRatingContext(query="AI", doc_id="d1")
    assert ctx.get_query_text() == "AI"
    assert ctx.get_doc_ids() == ["d1"]
    assert ctx.has_rating_score("d1") is False


def test_add_rating_score__to_existing_doc__expects__rating_is_added():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    ctx.add_rating_score("d1", 1)
    assert ctx.get_rating_score("d1") == 1
    assert ctx.has_rating_score("d1") is True


def test_add_rating_score__when_rating_exists__expects__score_is_overwritten():
    ctx = QueryRatingContext(query="AI", doc_id="d1")
    ctx.add_rating_score("d1", 0)
    ctx.add_rating_score("d1", 1)
    assert ctx.get_rating_score("d1") == 1


def test_serialization__to_and_from_dict__expects__data_is_preserved():
    ctx1 = QueryRatingContext(query="AI")
    ctx1.add_doc_id("d1")
    ctx1.add_rating_score("d1", 1)
    d = ctx1.to_dict()
    ctx2 = QueryRatingContext.from_dict(d)
    assert ctx2.get_query_id() == ctx1.get_query_id()
    assert ctx2.get_query_text() == ctx1.get_query_text()
    assert ctx2.get_rating_score("d1") == 1


def test_add_doc_id__when_doc_id_exists__expects__duplicate_is_ignored():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    ctx.add_doc_id("d1")  # should not raise or duplicate
    assert ctx.get_doc_ids() == ["d1"]


def test_get_rating_score__when_no_rating_exists__expects__default_score_is_returned():
    ctx = QueryRatingContext(query="AI")
    ctx.add_doc_id("d1")
    assert ctx.get_rating_score("d1") == QueryRatingContext.DOC_NOT_RATED
