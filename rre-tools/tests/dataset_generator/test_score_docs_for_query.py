"""Tests for the `score_docs_for_query` dispatcher in main.py."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Dict, List

import pytest

from rre_tools.dataset_generator.main import score_docs_for_query
from rre_tools.dataset_generator.llm import BatchScoringError
from rre_tools.dataset_generator.models import LLMScoreResponse
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


def _config(**overrides):
    values = {
        "relevance_scale": "binary",
        "save_llm_explanation": False,
        "llm_micro_batch_size": 1,
        "llm_batch_max_retries": 3,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeLLMService:
    def __init__(self, score: int = 1):
        self._score = score
        self.generate_score_calls: List[tuple] = []
        self.generate_scores_batch_calls: List[tuple] = []

    def generate_score(self, document: Document, query: str, relevance_scale: str,
                       explanation: bool = False) -> LLMScoreResponse:
        self.generate_score_calls.append((document.id, query, relevance_scale, explanation))
        return LLMScoreResponse(score=self._score, scale=relevance_scale, explanation=None)

    def generate_scores_batch(self, *, query_id, query_text, documents, relevance_scale,
                              explanation, prompt_template, max_retries) -> Dict[str, LLMScoreResponse]:
        self.generate_scores_batch_calls.append(
            (query_id, query_text, [d.id for d in documents], relevance_scale,
             explanation, max_retries)
        )
        return {
            d.id: LLMScoreResponse(score=self._score, scale=relevance_scale, explanation=None)
            for d in documents
        }


def _setup_store_with_query_and_docs(num_docs: int):
    ds = DataStore(ignore_saved_data=True)
    query = ds.add_query("query text")
    docs = []
    for i in range(num_docs):
        doc = Document(id=f"d{i}", fields={"title": f"t{i}"})
        ds.add_document(doc)
        docs.append(doc)
    return ds, query, docs


def test_score_docs_for_query__skips_already_rated_pairs():
    ds, query, docs = _setup_store_with_query_and_docs(3)
    ds.create_rating_score(query.id, docs[0].id, 1)

    llm = FakeLLMService(score=1)

    score_docs_for_query(
        _config(llm_micro_batch_size=2), ds, llm,
        prompt_template="ignored", query=query, documents=docs,
    )

    # Only d1 and d2 should be sent.
    batch_call = llm.generate_scores_batch_calls[0]
    sent_ids = batch_call[2]
    assert set(sent_ids) == {"d1", "d2"}


def test_score_docs_for_query__splits_25_docs_into_batches_of_10_10_5():
    ds, query, docs = _setup_store_with_query_and_docs(25)
    llm = FakeLLMService(score=1)

    score_docs_for_query(
        _config(llm_micro_batch_size=10), ds, llm,
        prompt_template="ignored", query=query, documents=docs,
    )

    batch_sizes = [len(call[2]) for call in llm.generate_scores_batch_calls]
    assert batch_sizes == [10, 10, 5]
    # And the legacy single-pair API was never called.
    assert llm.generate_score_calls == []


def test_score_docs_for_query__at_micro_batch_size_1__uses_legacy_single_pair_path():
    ds, query, docs = _setup_store_with_query_and_docs(3)
    llm = FakeLLMService(score=1)

    score_docs_for_query(
        _config(llm_micro_batch_size=1), ds, llm,
        prompt_template="should-not-be-used", query=query, documents=docs,
    )

    # Legacy single-pair path: 3 calls, one per doc; batch API never touched.
    assert [c[0] for c in llm.generate_score_calls] == ["d0", "d1", "d2"]
    assert llm.generate_scores_batch_calls == []

    # All ratings written.
    for d in docs:
        assert ds.has_rating_score(query.id, d.id)


def test_score_docs_for_query__on_batch_scoring_error__propagates():
    ds, query, docs = _setup_store_with_query_and_docs(3)

    class _RaisingLLM(FakeLLMService):
        def generate_scores_batch(self, **kw):
            raise BatchScoringError(
                query_id=query.id, asked_doc_ids=[d.id for d in docs],
                attempts=4, reason="missing doc_id(s)",
            )

    llm = _RaisingLLM()

    with pytest.raises(BatchScoringError):
        score_docs_for_query(
            _config(llm_micro_batch_size=2), ds, llm,
            prompt_template="ignored", query=query, documents=docs,
        )


def test_score_docs_for_query__no_pending__early_return():
    ds, query, docs = _setup_store_with_query_and_docs(2)
    for d in docs:
        ds.create_rating_score(query.id, d.id, 1)

    llm = FakeLLMService(score=1)
    score_docs_for_query(
        _config(llm_micro_batch_size=2), ds, llm,
        prompt_template="ignored", query=query, documents=docs,
    )
    assert llm.generate_scores_batch_calls == []
    assert llm.generate_score_calls == []


def test_score_docs_for_query__duplicate_doc_ids__deduped_at_micro_batch_size_1():
    """Pre-batching loop was idempotent against duplicates because has_rating_score
    was re-checked before each single-pair call; this helper has to dedupe explicitly."""
    ds = DataStore(ignore_saved_data=True)
    query = ds.add_query("query text")
    d1 = Document(id="d1", fields={"title": "t1"})
    ds.add_document(d1)

    llm = FakeLLMService(score=1)
    score_docs_for_query(
        _config(llm_micro_batch_size=1), ds, llm,
        prompt_template="ignored", query=query, documents=[d1, d1, d1],
    )

    # Exactly one LLM call, exactly one rating.
    assert len(llm.generate_score_calls) == 1
    assert llm.generate_score_calls[0][0] == "d1"
    assert ds.has_rating_score(query.id, "d1")


def test_score_docs_for_query__duplicate_doc_ids__deduped_at_batch_size_greater_than_1():
    """At size>1 a duplicate would otherwise trip the LLM's one-item-per-input
    contract: model returns one item for the (only) unique id, service raises
    'missing doc_id' and retries until abort. Dedup eliminates the failure mode."""
    ds = DataStore(ignore_saved_data=True)
    query = ds.add_query("query text")
    d1 = Document(id="d1", fields={"title": "t1"})
    d2 = Document(id="d2", fields={"title": "t2"})
    ds.add_document(d1)
    ds.add_document(d2)

    llm = FakeLLMService(score=1)
    score_docs_for_query(
        _config(llm_micro_batch_size=5), ds, llm,
        prompt_template="ignored", query=query, documents=[d1, d2, d1, d2, d1],
    )

    # One batch call carrying exactly the two unique ids, first-occurrence order.
    assert len(llm.generate_scores_batch_calls) == 1
    sent_ids = llm.generate_scores_batch_calls[0][2]
    assert sent_ids == ["d1", "d2"]
    assert ds.has_rating_score(query.id, "d1")
    assert ds.has_rating_score(query.id, "d2")
