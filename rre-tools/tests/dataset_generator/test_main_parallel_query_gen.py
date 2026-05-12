"""Tests for parallel query generation from seed documents.

Exercises ``generate_and_add_queries_from_documents`` at ``llm_max_workers > 1``.

Key invariants:
- Worker LLM calls overlap (peak in-flight > 1).
- Results are *applied* on the main thread in seed-doc order — so the stored
  query set, source labels, pre-rating linkage, and budget cutoff are identical
  to the sequential path for the same fake responses.
- Outer/inner budget guards still kick in.
"""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Dict, List

from rre_tools.dataset_generator.main import generate_and_add_queries_from_documents
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


def _config(**overrides):
    """Minimal SimpleNamespace config — all paths through
    ``generate_and_add_queries_from_documents`` only read the listed fields."""
    values = {
        "num_queries_needed": 10,
        "number_of_docs": 4,
        "max_query_terms": None,
        "relevance_scale": "binary",
        "relevance_label_set": {0, 1},
        "llm_max_workers": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _ConcurrencyTrackingQueryLLM:
    """Fake LLMService.generate_queries that records peak in-flight calls."""

    def __init__(self, queries_per_doc: Dict[str, List[str]], hold_seconds: float = 0.05):
        self._queries_per_doc = queries_per_doc
        self._hold = hold_seconds
        self._lock = threading.Lock()
        self._in_flight = 0
        self.max_in_flight = 0
        self.generate_queries_calls: List[str] = []

    def generate_queries(self, doc: Document, num_queries_per_doc: int, max_query_terms):
        with self._lock:
            self._in_flight += 1
            self.generate_queries_calls.append(doc.id)
            if self._in_flight > self.max_in_flight:
                self.max_in_flight = self._in_flight
        try:
            time.sleep(self._hold)
        finally:
            with self._lock:
                self._in_flight -= 1
        queries = self._queries_per_doc.get(doc.id, [f"q-from-{doc.id}"])
        return SimpleNamespace(get_queries=lambda: list(queries))


def test_query_gen__parallel_workers__overlap_in_flight():
    ds = DataStore(ignore_saved_data=True)
    seed_docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(4)]
    for d in seed_docs:
        ds.add_document(d)

    llm = _ConcurrencyTrackingQueryLLM(
        queries_per_doc={f"d{i}": [f"query-from-d{i}"] for i in range(4)},
        hold_seconds=0.05,
    )

    generate_and_add_queries_from_documents(
        _config(llm_max_workers=4, num_queries_needed=10, number_of_docs=4),
        ds, llm, seed_docs,
    )

    # All 4 calls fired; at least 2 overlapped under 4 workers.
    assert len(llm.generate_queries_calls) == 4
    assert llm.max_in_flight > 1


def test_query_gen__parallel_workers__results_applied_in_seed_doc_order():
    """Same fake responses + parallel run must produce the same stored queries,
    in the same insertion order, as the sequential run. This is the contract
    that 'apply in seed-doc order' protects."""
    seed_docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(3)]
    responses = {
        "d0": ["q-a", "q-b"],
        "d1": ["q-c", "q-d"],
        "d2": ["q-e", "q-f"],
    }

    def run(max_workers: int) -> List[str]:
        ds = DataStore(ignore_saved_data=True)
        for d in seed_docs:
            ds.add_document(d)
        # Slow workers so threading actually scrambles completion order in the
        # parallel run; the apply-in-seed-order contract should still hold.
        llm = _ConcurrencyTrackingQueryLLM(
            queries_per_doc=responses,
            hold_seconds=0.04 if max_workers > 1 else 0.0,
        )
        generate_and_add_queries_from_documents(
            _config(llm_max_workers=max_workers, num_queries_needed=10, number_of_docs=3),
            ds, llm, seed_docs,
        )
        return [q.text for q in ds.get_queries()]

    sequential = run(1)
    parallel = run(4)

    assert sequential == ["q-a", "q-b", "q-c", "q-d", "q-e", "q-f"]
    assert parallel == sequential


def test_query_gen__parallel_workers__pre_rating_tied_to_source_seed_doc():
    """Each generated query must be pre-rated against the seed doc it was
    generated from — not some other doc that happened to finish concurrently."""
    seed_docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(3)]
    responses = {
        "d0": ["q-from-d0"],
        "d1": ["q-from-d1"],
        "d2": ["q-from-d2"],
    }

    ds = DataStore(ignore_saved_data=True)
    for d in seed_docs:
        ds.add_document(d)

    llm = _ConcurrencyTrackingQueryLLM(queries_per_doc=responses, hold_seconds=0.03)
    generate_and_add_queries_from_documents(
        _config(llm_max_workers=4, num_queries_needed=10, number_of_docs=3),
        ds, llm, seed_docs,
    )

    text_by_id = {q.id: q.text for q in ds.get_queries()}
    for r in ds.get_ratings():
        # Each rating's query text encodes the seed doc id it came from.
        assert text_by_id[r.query_id] == f"q-from-{r.doc_id}"
        assert r.score == 1  # max of {0, 1}


def test_query_gen__parallel_workers__outer_budget_guard_stops_applying():
    """When earlier seed-doc responses fill the budget, later docs' responses
    must NOT be applied. Note that, by design, the executor still runs the
    in-flight submitted futures to completion — but their applications are
    skipped, so the stored query set matches the sequential outer-guard path."""
    seed_docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(4)]
    responses = {
        "d0": ["q-d0-a", "q-d0-b"],   # fills the budget of 2 by itself
        "d1": ["q-d1-a"],             # must not be applied
        "d2": ["q-d2-a"],
        "d3": ["q-d3-a"],
    }

    ds = DataStore(ignore_saved_data=True)
    for d in seed_docs:
        ds.add_document(d)

    llm = _ConcurrencyTrackingQueryLLM(queries_per_doc=responses, hold_seconds=0.0)
    generate_and_add_queries_from_documents(
        _config(llm_max_workers=4, num_queries_needed=2, number_of_docs=4),
        ds, llm, seed_docs,
    )

    stored_texts = {q.text for q in ds.get_queries()}
    assert stored_texts == {"q-d0-a", "q-d0-b"}
    # Each stored query is rated only against its own seed doc.
    assert len(ds.get_ratings()) == 2
