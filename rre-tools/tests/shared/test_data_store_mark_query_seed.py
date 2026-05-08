import logging
from pathlib import Path

import pytest

from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "datastore.json"


@pytest.fixture
def ds(tmp_db_path: Path) -> DataStore:
    return DataStore(path=tmp_db_path, ignore_saved_data=True)


def test_mark_document_as_query_seed__flips_flag_when_false(ds):
    doc = Document(id="d1", fields={"title": "t"}, is_used_to_generate_queries=False)
    ds.add_document(doc)
    assert ds.get_document("d1").is_used_to_generate_queries is False

    ds.mark_document_as_query_seed("d1")
    assert ds.get_document("d1").is_used_to_generate_queries is True
    assert "d1" in {d.id for d in ds.get_cartesian_prod_docs()}


def test_mark_document_as_query_seed__idempotent(ds):
    doc = Document(id="d1", fields={"title": "t"}, is_used_to_generate_queries=False)
    ds.add_document(doc)

    ds.mark_document_as_query_seed("d1")
    ds.mark_document_as_query_seed("d1")

    assert ds.get_document("d1").is_used_to_generate_queries is True
    assert len(ds.get_documents()) == 1


def test_mark_document_as_query_seed__unknown_id_is_safe_noop(ds, caplog):
    caplog.set_level(logging.WARNING)
    ds.mark_document_as_query_seed("missing")
    assert len(ds.get_documents()) == 0
    assert any("doc_not_found" in rec.getMessage() for rec in caplog.records)
