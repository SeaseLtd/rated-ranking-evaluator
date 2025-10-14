import json
import logging
from pathlib import Path

from rre_tools.shared.data_store import DataStore
from rre_tools.shared.utils import _to_string, join_fields_as_text
from rre_tools.shared.writers.abstract_writer import AbstractWriter

log = logging.getLogger(__name__)


class MtebWriter(AbstractWriter):
    """
    MtebWriter: Write data namely corpus, queries, and candidates to JSONL file for MTEB
    https://github.com/embeddings-benchmark/mteb

    Corpus format: id,title,text
    Queries format: id,text
    Candidates format: query_id,doc_id,rating
    """

    def _write_corpus(self, corpus_path: Path, datastore: DataStore) -> None:
        """
        Writes corpus records extracted from search engine to JSONL file:
        {"id": <doc_id>, "title": <title>, "text": <doc_fields>}
        """
        with corpus_path.open("w", encoding="utf-8") as file:
            for doc in datastore.get_documents():
                doc_id = str(doc.id)
                fields = doc.fields
                title = _to_string(fields.get("title"))
                text = join_fields_as_text(fields=fields, exclude=['id', 'title'])

                row = {"id": doc_id, "title": title, "text": text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_queries(self, queries_path: Path, datastore: DataStore) -> None:
        """
        Writes queries LLM-generated and/or user-defined records to JSONL file:
        {"id": <query_id>, "text": <query_text>}
        """
        with queries_path.open("w", encoding="utf-8") as file:
            for query in datastore.get_queries():
                row = {"id": query.id, "text": query.text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_candidates(self, candidates_path: Path, datastore: DataStore) -> None:
        """
        Writes candidates to JSONL file:
        {"query_id": <query_id>, "doc_id": <doc_id>, "rating": <rating_score>}
        """
        with candidates_path.open("w", encoding="utf-8") as file:
            for rating in datastore.get_ratings():
                row = {"query_id": rating.query_id, "doc_id": rating.doc_id, "rating": rating.score}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """
        Write corpus, queries, and candidates JSONL files for MTEB.
        
        Args:
            output_path: Directory where the MTEB files will be written
            datastore: DataStore containing the data to write
        """
        path = Path(output_path)
        path.mkdir(parents=True, exist_ok=True)
        try:
            self._write_corpus(path / "corpus.jsonl", datastore)
            log.info("Corpus written successfully")

            self._write_queries(path / "queries.jsonl", datastore)
            log.info("Queries written successfully")

            self._write_candidates(path / "candidates.jsonl", datastore)
            log.info("Candidates written successfully")

        except Exception as e:
            log.exception("Failed to write MTEB files: %s", e)
            raise
