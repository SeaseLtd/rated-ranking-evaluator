"""Concurrency tests for :class:`DataStore`.

Cover the RLock contract directly: mutators under N threads must not lose
updates, and the autosave-during-mutations path must never write a snapshot
containing dangling rating references (a rating whose query or doc isn't in
the saved set).
"""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


def test_data_store__concurrent_add_document_and_rating__no_lost_updates(tmp_path: Path):
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    query = ds.add_query("q1")

    n_workers = 200

    def _worker(i: int) -> None:
        doc = Document(id=f"d{i}", fields={"title": f"t{i}"})
        ds.add_document(doc)
        ds.create_rating_score(query.id, doc.id, 1)

    with ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(_worker, range(n_workers)))

    assert len(ds.get_documents()) == n_workers
    assert len(ds.get_ratings()) == n_workers
    # Every rating points to a real doc and the one real query.
    docs_ids = {d.id for d in ds.get_documents()}
    for r in ds.get_ratings():
        assert r.query_id == query.id
        assert r.doc_id in docs_ids


def test_data_store__concurrent_create_rating_score_same_pair__idempotent(tmp_path: Path):
    """The has_rating_score → create_rating_score idiom is not atomic across
    threads, but create_rating_score is idempotent on the (query, doc) key —
    the second writer is a no-op. Verifies the duplicate-write race is harmless.
    """
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    query = ds.add_query("q1")
    doc = Document(id="d1", fields={"title": "t"})
    ds.add_document(doc)

    def _worker(_: int):
        ds.create_rating_score(query.id, doc.id, 1)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_worker, range(64)))

    assert len(ds.get_ratings()) == 1


def test_data_store__autosave_under_concurrent_mutations__snapshot_has_no_dangling_refs(
    tmp_path: Path,
):
    """Most-load-bearing concurrency test: pound `create_rating_score` from many
    threads with `autosave_every_n_updates=1`. Every autosave must produce a valid
    snapshot (parses as JSON; every rating references a query/doc that also
    appears in the saved set). Without `save()` holding the lock during
    `model_dump`, autosave could capture a rating whose query/doc was being
    inserted concurrently.
    """
    path = tmp_path / "ds.json"
    ds = DataStore(path=path, ignore_saved_data=True, autosave_every_n_updates=1)

    n_workers = 100

    def _worker(i: int) -> None:
        # Each worker adds a brand-new query AND brand-new doc, then a rating
        # tying them together. Three updates per worker, autosave fires on each.
        q = ds.add_query(f"query-{i}")
        doc = Document(id=f"d-{i}", fields={"title": f"t{i}"})
        ds.add_document(doc)
        ds.create_rating_score(q.id, doc.id, 1)

    with ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(_worker, range(n_workers)))

    # In-memory invariants
    assert len(ds.get_queries()) == n_workers
    assert len(ds.get_documents()) == n_workers
    assert len(ds.get_ratings()) == n_workers

    # Final on-disk snapshot must parse and have no dangling refs
    raw = json.loads(path.read_text(encoding="utf-8"))
    saved_query_ids = {q["id"] for q in raw["queries"]}
    saved_doc_ids = {d["id"] for d in raw["docs"]}
    for r in raw["ratings"]:
        assert r["query_id"] in saved_query_ids, f"dangling query_id={r['query_id']}"
        assert r["doc_id"] in saved_doc_ids, f"dangling doc_id={r['doc_id']}"


def test_data_store__load_called_inside_init__lock_already_initialized(tmp_path: Path):
    """Regression guard: DataStore.__init__ must assign self._lock *before* load().

    load() calls add_document / add_query / _add_rating which all acquire the
    lock; if _lock isn't set yet, the first call would `AttributeError`.
    """
    path = tmp_path / "ds.json"
    # Prep a non-empty saved store so load() actually does work
    ds0 = DataStore(path=path, ignore_saved_data=True)
    q = ds0.add_query("q1")
    doc = Document(id="d1", fields={"title": "t"})
    ds0.add_document(doc)
    ds0.create_rating_score(q.id, doc.id, 1)
    ds0.save()

    # Without the init-before-load fix this raises AttributeError on first add_document
    ds1 = DataStore(path=path)
    assert len(ds1.get_queries()) == 1
    assert len(ds1.get_documents()) == 1
    assert len(ds1.get_ratings()) == 1


def test_data_store__autosave_does_not_truncate_cache_during_load(tmp_path: Path):
    """Regression guard for the load-with-autosave corruption.

    Repro from the original report: 3 docs / 3 queries / 3 ratings on disk,
    open with ``autosave_every_n_updates=4``. Without suppressing autosave
    during replay, the counter crosses 4 mid-load and writes a partial
    snapshot back over the source file — final on-disk state observed as
    (3 docs, 3 queries, 2 ratings).
    """
    path = tmp_path / "ds.json"

    # Prepare the canonical 3/3/3 store.
    ds0 = DataStore(path=path, ignore_saved_data=True)
    docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(3)]
    queries = [ds0.add_query(f"q{i}") for i in range(3)]
    for d in docs:
        ds0.add_document(d)
    for q, d in zip(queries, docs):
        ds0.create_rating_score(q.id, d.id, 1)
    ds0.save()

    # Sanity: the file is what we expect before the next open.
    pre = json.loads(path.read_text(encoding="utf-8"))
    assert len(pre["docs"]) == 3
    assert len(pre["queries"]) == 3
    assert len(pre["ratings"]) == 3

    # Open with autosave_every_n_updates=4 — would previously corrupt the file
    # during load() because the mid-load counter crosses 4.
    ds1 = DataStore(path=path, autosave_every_n_updates=4)

    # In-memory state is fully loaded.
    assert len(ds1.get_documents()) == 3
    assert len(ds1.get_queries()) == 3
    assert len(ds1.get_ratings()) == 3

    # On-disk state is unchanged — no partial snapshot was written.
    post = json.loads(path.read_text(encoding="utf-8"))
    assert post == pre


def test_data_store__autosave_counter_resets_after_load(tmp_path: Path):
    """After load(), the next real mutation should account from a fresh
    autosave counter — not from whatever residual the replay left behind.
    Otherwise opening a near-threshold store would autosave on the first
    user mutation, masking the suppression fix above.
    """
    path = tmp_path / "ds.json"

    # Prepare a stored 3/3/3 store as before.
    ds0 = DataStore(path=path, ignore_saved_data=True)
    docs = [Document(id=f"d{i}", fields={"title": f"t{i}"}) for i in range(3)]
    queries = [ds0.add_query(f"q{i}") for i in range(3)]
    for d in docs:
        ds0.add_document(d)
    for q, d in zip(queries, docs):
        ds0.create_rating_score(q.id, d.id, 1)
    ds0.save()
    pre = json.loads(path.read_text(encoding="utf-8"))

    # Open with autosave threshold larger than the number of mutations
    # we'll do next — autosave should NOT fire after one extra add.
    ds1 = DataStore(path=path, autosave_every_n_updates=10)
    new_doc = Document(id="d-extra", fields={"title": "t-extra"})
    ds1.add_document(new_doc)

    # File on disk still reflects only the pre-existing state — the in-memory
    # change has not been autosaved yet.
    after_one_mutation = json.loads(path.read_text(encoding="utf-8"))
    assert after_one_mutation == pre


def test_data_store__autosave_io_runs_outside_lock(tmp_path: Path):
    """Regression guard for autosave holding the lock through file I/O.

    Strategy: intercept the lowest-level file write that any autosave
    implementation must go through (``Path.write_text``) and, at that moment,
    probe whether the DataStore's lock is held by *anyone*. If the mutator
    that triggered the autosave is still holding it, the autosave is
    serializing worker writes behind disk I/O.

    The probe is ``ds._lock.acquire(blocking=False)`` from a separate thread:
    RLock is owner-aware, so the probe fails iff some *other* thread holds
    the lock at that instant.
    """
    path = tmp_path / "ds.json"
    ds = DataStore(path=path, ignore_saved_data=True, autosave_every_n_updates=1)

    real_write_text = Path.write_text
    probe_results: list[bool] = []

    def write_text_probe(self_path, *args, **kwargs):
        # Probe from a different thread so we can detect when the mutator
        # thread is the lock owner — `_lock.acquire(blocking=False)` from
        # the same thread always succeeds on an RLock (re-entry).
        result: list[Optional[bool]] = [None]

        def probe():
            acquired = ds._lock.acquire(blocking=False)
            if acquired:
                ds._lock.release()
            result[0] = acquired

        t = threading.Thread(target=probe)
        t.start()
        t.join(timeout=1.0)
        probe_results.append(bool(result[0]))
        return real_write_text(self_path, *args, **kwargs)

    with patch.object(Path, "write_text", write_text_probe):
        # Single mutation triggers autosave (threshold=1).
        ds.add_document(Document(id="d1", fields={"title": "t"}))

    assert probe_results, "autosave write_text was never invoked"
    # The bug case: probe returns False because the outer mutator still
    # holds ds._lock during file I/O. The fix case: probe returns True
    # because the lock was released before write_text was called.
    assert all(probe_results), (
        f"Autosave is holding ds._lock through file I/O — lock-acquired "
        f"probe results: {probe_results}"
    )
