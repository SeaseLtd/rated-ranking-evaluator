import json
import os
from pathlib import Path

from src.config import Config
from src.search_engine.data_store import DataStore
from src.utils import _to_string
from src.writers.abstract_writer import AbstractWriter


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

    def write_corpus(self, output_path: str | Path) -> None:
        """
        Writes corpus records extracted from search engine to JSONL file:
        {"id": <doc_id>, "title": <title>, "text": <description>}
        """
        path = Path(output_path)
        os.makedirs(path.parent, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for doc in self.datastore.get_documents():
                doc_id = str(doc.id)
                fields = doc.fields
                title = _to_string(fields.get("title"))
                text = _to_string(fields.get("description"))

                row = {"id": doc_id, "title": title, "text": text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write_queries(self, output_path: str | Path) -> None:
        """
        Writes queries LLM-generated and/or user-defined records to JSONL file:
        {"id": <query_id>, "text": <query_text>}
        """
        path = Path(output_path)
        os.makedirs(path.parent, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for query_context in self.datastore.get_queries():
                query_id = query_context.get_query_id()
                query_text = query_context.get_query_text()

                row = {"id": query_id, "text": query_text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write_candidates(self, output_path: str | Path) -> None:
        """
        Writes candidates to JSONL file:
        {"query_id": <query_id>, "doc_id": <doc_id>, "rating": <rating_score>}
        """
        path = Path(output_path)
        os.makedirs(path.parent, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for query_context in self.datastore.get_queries():
                query_id = query_context.get_query_id()
                for doc_id in query_context.get_doc_ids():
                    if query_context.has_rating_score(doc_id):
                        rating_score = query_context.get_rating_score(doc_id)

                        row = {"query_id": query_id, "doc_id": doc_id, "rating": rating_score}
                        file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write(self, output_path: str | Path) -> None:
        """
        Call these methods to write to JSONL files for MTEB: self.write_corpus(), self.write_queries() and
        self.write_candidates()
        """
        pass
