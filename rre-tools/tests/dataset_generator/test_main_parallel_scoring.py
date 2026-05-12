"""Tests for parallel relevance scoring.

Exercises both ``add_cartesian_product_scores`` and ``expand_docset_with_search_engine_top_k``
at ``llm_max_workers > 1`` to confirm:
- workers really overlap on the LLM call (peak in-flight > 1);
- results match the sequential path (set comparison — completion order differs
  under threads);
- a worker failure (``BatchScoringError``) propagates out of the executor.
"""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Dict, List

import pytest

from rre_tools.dataset_generator.llm import BatchScoringError
from rre_tools.dataset_generator.main import (
    add_cartesian_product_scores,
    expand_docset_with_search_engine_top_k,
)
from rre_tools.dataset_generator.models import LLMScoreResponse
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


def _config(**overrides):
    values = {
        "num_queries_needed": 100,
        "query_template": "select * from test where userInput(@kw)",
        "doc_fields": ["title"],
        "relevance_scale": "binary",
        "save_llm_explanation": False,
        "llm_micro_batch_size": 1,
        "llm_batch_max_retries": 3,
        "llm_batch_score_prompt": None,
        "llm_max_workers": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _ConcurrencyTrackingLLM:
    """LLM fake that records max in-flight calls across threads.

    Each call sleeps for ``hold_seconds`` so multiple threads can overlap.
    """

    def __init__(self, hold_seconds: float = 0.05):
        self._hold = hold_seconds
        self._lock = threading.Lock()
        self._in_flight = 0
        self.max_in_flight = 0
        self.total_calls = 0

    def _enter(self) -> None:
        with self._lock:
            self._in_flight += 1
            self.total_calls += 1
            if self._in_flight > self.max_in_flight:
                self.max_in_flight = self._in_flight

    def _exit(self) -> None:
        with self._lock:
            self._in_flight -= 1

    def generate_score(self, document: Document, query: str, relevance_scale: str,
                       explanation: bool = False) -> LLMScoreResponse:
        self._enter()
        try:
            time.sleep(self._hold)
        finally:
            self._exit()
        return LLMScoreResponse(score=1, scale=relevance_scale, explanation=None)

    def generate_scores_batch(self, *, query_id, query_text, documents, relevance_scale,
                              explanation, prompt_template, max_retries) -> Dict[str, LLMScoreResponse]:
        self._enter()
        try:
            time.sleep(self._hold)
        finally:
            self._exit()
        return {
            d.id: LLMScoreResponse(score=1, scale=relevance_scale, explanation=None)
            for d in documents
        }


class _FakeSearchEngine:
    """Thread-safe fake; returns the same single doc per query."""

    def __init__(self):
        self._lock = threading.Lock()
        self.queries: List[str] = []

    def fetch_for_evaluation(self, keyword, query_template, doc_fields):
        with self._lock:
            self.queries.append(keyword)
        return [Document(id=f"doc-{keyword}", fields={"title": keyword})]


# ─────────────────────────────────────────────────────────────────────
# Scoring — top-K path
# ─────────────────────────────────────────────────────────────────────
def test_expand_topk__parallel_workers__overlap_in_flight():
    """At llm_max_workers=4 with 4 queries and slow per-query calls,
    peak concurrency should exceed 1."""
    ds = DataStore(ignore_saved_data=True)
    for q in ["q1", "q2", "q3", "q4"]:
        ds.add_query(q)

    llm = _ConcurrencyTrackingLLM(hold_seconds=0.05)
    se = _FakeSearchEngine()

    expand_docset_with_search_engine_top_k(
        _config(llm_max_workers=4), ds, llm, se, prompt_template="ignored",
    )

    assert llm.total_calls == 4
    assert llm.max_in_flight > 1, "expected overlap with 4 workers"


def test_expand_topk__single_worker__no_overlap_matches_sequential():
    """At llm_max_workers=1 the path is strictly sequential — peak in-flight == 1
    and ratings written exactly match the sequential path."""
    ds = DataStore(ignore_saved_data=True)
    for q in ["q1", "q2", "q3"]:
        ds.add_query(q)

    llm = _ConcurrencyTrackingLLM(hold_seconds=0.01)
    se = _FakeSearchEngine()

    expand_docset_with_search_engine_top_k(
        _config(llm_max_workers=1), ds, llm, se, prompt_template="ignored",
    )

    assert llm.max_in_flight == 1
    # Sequential order is deterministic.
    assert se.queries == ["q1", "q2", "q3"]
    assert {r.doc_id for r in ds.get_ratings()} == {"doc-q1", "doc-q2", "doc-q3"}


def test_expand_topk__parallel_workers__same_ratings_as_sequential():
    """Same input + same fake LLM responses produce the same ratings set
    regardless of llm_max_workers (set comparison; order is non-deterministic)."""
    def run(max_workers: int):
        ds = DataStore(ignore_saved_data=True)
        for q in ["q1", "q2", "q3", "q4", "q5"]:
            ds.add_query(q)
        llm = _ConcurrencyTrackingLLM(hold_seconds=0.005)
        se = _FakeSearchEngine()
        expand_docset_with_search_engine_top_k(
            _config(llm_max_workers=max_workers), ds, llm, se, prompt_template="ignored",
        )
        return {(r.query_id, r.doc_id, r.score) for r in ds.get_ratings()}, ds

    sequential, ds_seq = run(1)
    parallel, ds_par = run(4)

    # Build a query-text → rating-set comparison so the two runs (with different
    # randomly-generated query ids) can be compared by semantics.
    def by_text(ds):
        text_by_id = {q.id: q.text for q in ds.get_queries()}
        return {(text_by_id[r.query_id], r.doc_id, r.score) for r in ds.get_ratings()}

    assert by_text(ds_seq) == by_text(ds_par)


def test_expand_topk__worker_raises_batch_scoring_error__propagates():
    """A worker raising BatchScoringError must surface out of the executor,
    not silently fail the run."""
    ds = DataStore(ignore_saved_data=True)
    for q in ["q1", "q2"]:
        ds.add_query(q)

    class _Raising(_ConcurrencyTrackingLLM):
        def generate_score(self, *a, **kw):
            raise BatchScoringError(
                query_id="q1", asked_doc_ids=["doc-q1"], attempts=4, reason="missing",
            )

    llm = _Raising(hold_seconds=0.0)
    se = _FakeSearchEngine()

    with pytest.raises(BatchScoringError):
        expand_docset_with_search_engine_top_k(
            _config(llm_max_workers=4), ds, llm, se, prompt_template="ignored",
        )


# ─────────────────────────────────────────────────────────────────────
# Scoring — cartesian path
# ─────────────────────────────────────────────────────────────────────
def test_cartesian__parallel_workers__overlap_and_same_ratings():
    ds = DataStore(ignore_saved_data=True)
    for q in ["q1", "q2", "q3", "q4"]:
        ds.add_query(q)
    for did in ["d1", "d2"]:
        ds.add_document(Document(id=did, fields={"title": did}, is_used_to_generate_queries=True))

    llm = _ConcurrencyTrackingLLM(hold_seconds=0.04)

    add_cartesian_product_scores(
        _config(llm_max_workers=4), ds, llm, prompt_template="ignored",
    )

    # 4 queries x 2 docs = 8 calls
    assert llm.total_calls == 8
    assert llm.max_in_flight > 1
    # Full cartesian product is rated
    assert len(ds.get_ratings()) == 8


def test_cartesian__single_worker__sequential_call_order_is_deterministic():
    """At llm_max_workers=1 the call order is deterministic and the cartesian
    helper iterates queries in budget order. Locks the sequential ordering down
    so a future refactor can't drift it under llm_max_workers=1."""
    ds = DataStore(ignore_saved_data=True)
    for q in ["q1", "q2"]:
        ds.add_query(q)
    for did in ["d1", "d2"]:
        ds.add_document(Document(id=did, fields={"title": did}, is_used_to_generate_queries=True))

    class _OrderRecordingLLM(_ConcurrencyTrackingLLM):
        def __init__(self):
            super().__init__(hold_seconds=0.0)
            self.call_order: List[str] = []

        def generate_score(self, document, query, relevance_scale, explanation=False):
            self.call_order.append(f"{query}:{document.id}")
            return super().generate_score(document, query, relevance_scale, explanation)

    llm = _OrderRecordingLLM()
    add_cartesian_product_scores(
        _config(llm_max_workers=1), ds, llm, prompt_template="ignored",
    )

    # q1 then q2; within each, d1 then d2 (insertion order from get_cartesian_prod_docs).
    assert llm.call_order == ["q1:d1", "q1:d2", "q2:d1", "q2:d2"]
