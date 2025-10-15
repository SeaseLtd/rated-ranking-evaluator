import pytest
import csv
from pathlib import Path

from rre_tools.shared.data_store import DataStore
from rre_tools.shared.writers.writer_config import WriterConfig
from rre_tools.shared.writers.quepid_writer import QuepidWriter, QUEPID_OUTPUT_FILENAME
from rre_tools.shared.models import Document


@pytest.fixture
def writer_config():
    return WriterConfig(
        output_format='quepid',
        index='testcore'
    )

# helper shared with other writer tests
def _add_query_with_doc(ds: DataStore, qtext: str, doc_id: str) -> str:
    doc = Document(id=doc_id, fields={"field": "v"})
    ds.add_document(doc)
    # Capture the query object from the datastore to get the correct ID
    query_in_store = ds.add_query(qtext)
    return query_in_store.id


# ---------------- fixtures -----------------
@pytest.fixture
def populated_datastore() -> DataStore:
    ds = DataStore(ignore_saved_data=True)
    q1_id = _add_query_with_doc(ds, "test query 1", "doc1")
    _add_query_with_doc(ds, "test query 1", "doc2")  # doc for q1
    _add_query_with_doc(ds, "test query 1", "doc3")  # doc for q1
    ds.create_rating_score(q1_id, "doc1", 1)
    ds.create_rating_score(q1_id, "doc2", 2)

    q2 = _add_query_with_doc(ds, "test query 2", "doc4")
    ds.create_rating_score(q2, "doc4", 3)

    _add_query_with_doc(ds, "test query 3", "doc5")  # no ratings
    return ds


@pytest.fixture
def empty_datastore() -> DataStore:
    return DataStore(ignore_saved_data=True)


@pytest.fixture
def unrated_datastore() -> DataStore:
    ds = DataStore(ignore_saved_data=True)
    _add_query_with_doc(ds, "query 1", "doc1")
    _add_query_with_doc(ds, "query 2", "doc2")
    return ds


# ---------------- tests -----------------

class TestQuepidWriter:
    def _assert_csv(self, file: Path, expected_rows: list[tuple[str, str, str]]):
        with open(file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            assert next(reader) == ["query", "docid", "rating"]
            assert set(map(tuple, reader)) == set(expected_rows)

    def test_write_success(self, writer_config, populated_datastore, tmp_path: Path):
        out = tmp_path / QUEPID_OUTPUT_FILENAME
        QuepidWriter(writer_config).write(tmp_path, populated_datastore)
        self._assert_csv(out, [
            ("test query 1", "doc1", "1"),
            ("test query 1", "doc2", "2"),
            ("test query 2", "doc4", "3"),
        ])

    def test_write_empty(self, writer_config, empty_datastore, tmp_path: Path):
        out = tmp_path / QUEPID_OUTPUT_FILENAME
        QuepidWriter(writer_config).write(tmp_path, empty_datastore)
        self._assert_csv(out, [])

    def test_write_no_rated_docs(self, writer_config, unrated_datastore, tmp_path: Path):
        out = tmp_path / QUEPID_OUTPUT_FILENAME
        QuepidWriter(writer_config).write(tmp_path, unrated_datastore)
        self._assert_csv(out, [])

    def test_special_characters(self, writer_config, tmp_path: Path):
        ds = DataStore(ignore_saved_data=True)
        qtext = 'query with "quotes" and a comma,'
        doc = 'doc_id_with_a_newline\n'
        qid = _add_query_with_doc(ds, qtext, doc)
        ds.create_rating_score(qid, doc, 1)
        out = tmp_path / QUEPID_OUTPUT_FILENAME
        QuepidWriter(writer_config).write(tmp_path, ds)
        self._assert_csv(out, [(qtext, doc, "1")])

    def test_zero_rating(self, writer_config, tmp_path: Path):
        ds = DataStore(ignore_saved_data=True)
        qid = _add_query_with_doc(ds, "query 1", "doc1")
        ds.create_rating_score(qid, "doc1", 0)
        out = tmp_path / QUEPID_OUTPUT_FILENAME
        QuepidWriter(writer_config).write(tmp_path, ds)
        self._assert_csv(out, [("query 1", "doc1", "0")])
