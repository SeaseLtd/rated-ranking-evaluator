import json
import logging
import os
from pathlib import Path

from src.config import Config
from src.search_engine.data_store import DataStore
from src.utils import _to_string
from src.writers.abstract_writer import AbstractWriter

log = logging.getLogger(__name__)


class MtebWriter(AbstractWriter):
    """
    MtebWriter: Write data namely corpus, queries, and candidates to JSONL file for MTEB
    https://github.com/embeddings-benchmark/mteb

    Corpus format: id,title,text
    Queries format: id,text
    Candidates format: query_id,doc_id,rating
    """

    @classmethod
    def build(cls, config: Config, data_store: DataStore):
        return cls(datastore=data_store)

    def _write_corpus(self, corpus_path: Path) -> None:
        """
        Writes corpus records extracted from search engine to JSONL file:
        {"id": <doc_id>, "title": <title>, "text": <description>}
        """
        with corpus_path.open("w", encoding="utf-8") as file:
            for doc in self.datastore.get_documents():
                doc_id = str(doc.id)
                fields = doc.fields
                title = _to_string(fields.get("title"))
                text = _to_string(fields.get("description"))

                row = {"id": doc_id, "title": title, "text": text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_queries(self, queries_path: Path) -> None:
        """
        Writes queries LLM-generated and/or user-defined records to JSONL file:
        {"id": <query_id>, "text": <query_text>}
        """
        with queries_path.open("w", encoding="utf-8") as file:
            for query_context in self.datastore.get_queries():
                query_id = query_context.get_query_id()
                query_text = query_context.get_query_text()

                row = {"id": query_id, "text": query_text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_candidates(self, candidates_path: Path) -> None:
        """
        Writes candidates to JSONL file:
        {"query_id": <query_id>, "doc_id": <doc_id>, "rating": <rating_score>}
        """
        with candidates_path.open("w", encoding="utf-8") as file:
            for query_context in self.datastore.get_queries():
                query_id = query_context.get_query_id()
                for doc_id in query_context.get_doc_ids():
                    if query_context.has_rating_score(doc_id):
                        rating_score = query_context.get_rating_score(doc_id)

                        row = {"query_id": query_id, "doc_id": doc_id, "rating": rating_score}
                        file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write(self, output_path: str | Path) -> None:
        """
        Write corpus, queries, and candidates JSONL files for MTEB.
        """
        path = Path(output_path)
        os.makedirs(path, exist_ok=True)
        try:
            self._write_corpus(path / "corpus.jsonl")
            log.info("Corpus written successfully")

            self._write_queries(path / "queries.jsonl")
            log.info("Queries written successfully")

            self._write_candidates(path / "candidates.jsonl")
            log.info("Candidates written successfully")

        except Exception as e:
            log.exception("Failed to write MTEB files: %s", e)
            raise
