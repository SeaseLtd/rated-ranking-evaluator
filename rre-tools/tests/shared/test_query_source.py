import json
from pathlib import Path

import pytest

from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Query


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "datastore.json"


@pytest.fixture
def ds(tmp_db_path: Path) -> DataStore:
    return DataStore(path=tmp_db_path, ignore_saved_data=True)


def test_add_query__default_source_is_cached(ds):
    q = ds.add_query("hello world")
    assert q.source == "cached"


def test_add_query__explicit_source_is_set(ds):
    q = ds.add_query("hello world", source="user")
    assert q.source == "user"


def test_add_query__promotes_cached_to_user(ds):
    """Re-asserting a previously-cached query as user-supplied promotes its label."""
    q1 = ds.add_query("comedy movies")  # default cached
    assert q1.source == "cached"

    q2 = ds.add_query("comedy movies", source="user")
    assert q2 is q1  # dedup hit
    assert q1.source == "user"


def test_add_query__promotes_llm_to_category(ds):
    q = ds.add_query("comedy movies", source="llm")
    assert q.source == "llm"
    ds.add_query("comedy movies", source="category")
    assert q.source == "category"


def test_add_query__does_not_demote_user_to_llm(ds):
    """A user-asserted query must not be downgraded by a later LLM-gen with the same text."""
    q = ds.add_query("comedy movies", source="user")
    ds.add_query("comedy movies", source="llm")
    assert q.source == "user"


def test_add_query__does_not_demote_category_to_cached(ds):
    q = ds.add_query("comedy movies", source="category")
    ds.add_query("comedy movies")  # no source -> no-op on existing
    assert q.source == "category"


def test_query_source_not_persisted(tmp_path: Path):
    """The source label is a runtime concern: it must not be written to the JSON cache."""
    db_path = tmp_path / "datastore.json"
    ds = DataStore(path=db_path, ignore_saved_data=True)
    ds.add_query("comedy movies", source="user")
    ds.save()

    raw = json.loads(db_path.read_text(encoding="utf-8"))
    assert raw["queries"]
    assert all("source" not in entry for entry in raw["queries"])


def test_query_source_resets_to_cached_on_load(tmp_path: Path):
    """A user/category-labeled query saved in run 1 should load as 'cached' in run 2."""
    db_path = tmp_path / "datastore.json"
    ds = DataStore(path=db_path, ignore_saved_data=True)
    ds.add_query("comedy movies", source="user")
    ds.save()

    reloaded = DataStore(path=db_path, ignore_saved_data=False)
    qs = reloaded.get_queries()
    assert len(qs) == 1
    assert qs[0].source == "cached"


def test_query_model__source_default():
    q = Query(text="hi")
    assert q.source == "cached"
