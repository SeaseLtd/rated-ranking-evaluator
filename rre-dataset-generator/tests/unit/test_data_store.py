








# import json
# import logging
# from pathlib import Path

# import pytest
# from pydantic import model_validator
# from src.data_store import DataStore
# from src.model import Document, Query, Rating

# # -----------------------
# # fixtures
# # -----------------------
# @pytest.fixture
# def tmp_datastore_path(tmp_path: Path) -> Path:
#     """A path pointing to a temporary datastore file."""
#     return tmp_path / "datastore.json"


# @pytest.fixture
# def empty_datastore(tmp_datastore_path: Path) -> DataStore:
#     """Return an empty DataStore instance that skips auto-loading from disk."""
#     return DataStore(path=tmp_datastore_path, ignore_saved_data=True)


# @pytest.fixture
# def populated_datastore(empty_datastore: DataStore) -> DataStore:
#     """DataStore pre-populated with one document and one query linked together."""
#     ds = empty_datastore

#     doc = Document(id="doc-1", fields={"title": "Foo"})
#     query = Query(id="query-1", text="foo")

#     ds.add_doc(doc)
#     ds.add_query(query)
#     ds.add_doc_to_query(query.id, doc.id)

#     return ds


# # -----------------------
# # helpers
# # -----------------------

# def _create_rating(ds: DataStore, query_id: str, doc_id: str, score: int = 1) -> str:
#     """Convenience wrapper that stores/returns the rating id."""
#     return ds.add_rating_score(query_id, doc_id, score)


# # -----------------------
# # tests – basic add & has
# # -----------------------

# def test_add_doc__expects__doc_stored(empty_datastore: DataStore):
#     doc = Document(id="d1", fields={"field": "value"})
#     empty_datastore.add_doc(doc)

#     assert empty_datastore.has_doc("d1") is True
#     assert empty_datastore.get_doc("d1") == doc


# def test_add_doc__expects__duplicate_ignored(caplog, populated_datastore: DataStore):
#     caplog.set_level(logging.ERROR)

#     duplicate = Document(id="doc-1", fields={"title": "Bar"})
#     populated_datastore.add_doc(duplicate)

#     assert populated_datastore.get_doc("doc-1").fields["title"] == "Foo"
#     assert "already exists" in caplog.text


# def test_add_query__expects__query_text_unique(caplog, empty_datastore: DataStore):
#     caplog.set_level(logging.ERROR)

#     q1 = Query(id="q1", text="same text")
#     q2 = Query(id="q2", text="same text")

#     empty_datastore.add_query(q1)
#     empty_datastore.add_query(q2)

#     assert empty_datastore.has_query("q1") is True
#     assert empty_datastore.has_query("q2") is False
#     assert "already exists" in caplog.text

# # -----------------------
# # tests – add_doc_to_query
# # -----------------------
# @pytest.mark.parametrize(
#     "query_id, doc_id, expected_log",
#     [
#         ("missing_query", "doc-1", "Query missing_query not found"),
#         ("query-1", "missing_doc", "Document missing_doc not found"),
#     ],
# )
# def test_add_doc_to_query__expects__invalid_ids_logged(caplog, populated_datastore: DataStore, query_id, doc_id, expected_log):
#     caplog.set_level(logging.ERROR)

#     populated_datastore.add_doc_to_query(query_id, doc_id)

#     assert expected_log in caplog.text


# def test_add_doc_to_query__expects__association_created(populated_datastore: DataStore):
#     query = populated_datastore.get_query("query-1")
#     assert "doc-1" in query.related_docs_ids

# # -----------------------
# # tests – rating score retrieval & creation
# # -----------------------

# def test_get_rating_score__expects__none_when_no_rating(populated_datastore: DataStore):
#     assert populated_datastore.get_rating_score("query-1", "doc-1") is None


# def test_add_rating_score__expects__rating_created(populated_datastore: DataStore):
#     rating_id = _create_rating(populated_datastore, "query-1", "doc-1", score=3)

#     assert populated_datastore.has_rating(rating_id)
#     assert rating_id in populated_datastore.get_query("query-1").related_ratings_ids
#     assert populated_datastore.get_rating_score("query-1", "doc-1") == 3


# def test_add_rating_score__expects__duplicate_returns_existing_id(populated_datastore: DataStore):
#     first_id = _create_rating(populated_datastore, "query-1", "doc-1", score=2)
#     second_id = _create_rating(populated_datastore, "query-1", "doc-1", score=4)

#     assert first_id == second_id
#     # original score should remain unchanged (2) per implementation
#     assert populated_datastore.get_rating_score("query-1", "doc-1") == 2


# @pytest.mark.parametrize(
#     "query_id, doc_id, log_msg",
#     [
#         ("missing_query", "doc-1", "Query missing_query not found"),
#         ("query-1", "missing_doc", "Document missing_doc not found"),
#     ],
# )
# def test_get_rating_score__expects__error_logged_for_missing_entities(caplog, populated_datastore: DataStore, query_id, doc_id, log_msg):
#     caplog.set_level(logging.ERROR)
#     assert populated_datastore.get_rating_score(query_id, doc_id) is None
#     assert log_msg in caplog.text

# # -----------------------
# # tests – persistence round-trip
# # -----------------------

# def test_save_and_load__expects__objects_roundtrip(tmp_datastore_path: Path):
#     # Prepare datastore, add objects and save
#     ds1 = DataStore(path=tmp_datastore_path, ignore_saved_data=True)

#     doc = Document(id="d1", fields={"f": "v"})
#     query = Query(id="q1", text="foo")
#     ds1.add_doc(doc)
#     ds1.add_query(query)
#     _create_rating(ds1, query.id, doc.id, score=5)
#     ds1.save()

#     # Re-instantiate to load from disk
#     ds2 = DataStore(path=tmp_datastore_path, ignore_saved_data=False)

#     assert ds2.get_doc("d1").id == doc.id
#     assert ds2.get_query("q1") == query
#     assert ds2.get_doc("d1").fields == doc.fields
#     assert ds2.get_rating_score("q1", "d1") == 5

#     # verify persisted file structure
#     content = json.loads(tmp_datastore_path.read_text())
#     assert set(content.keys()) == {"docs", "queries", "ratings"}
