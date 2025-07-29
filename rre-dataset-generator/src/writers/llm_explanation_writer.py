import json
from pathlib import Path
from typing import List, Tuple

from src.writers.abstract_writer import AbstractWriter


class LlmExplanationWriter(AbstractWriter):
    def write(self, output_path: str | Path) -> None:
        records = []
        for query, doc_id, score, reasoning in self._get_queries_with_ratings_and_reasoning():
            record = {
                "query": query,
                "doc_id": doc_id,
                "rating": score,
                "reasoning": reasoning,
            }
            records.append(record)

        with open(output_path, "w", encoding="utf-8") as jsonfile:
            json.dump(records, jsonfile, indent=2, ensure_ascii=False)

    def _get_queries_with_ratings_and_reasoning(self) -> List[Tuple[str, str, int, str]]:
        """
        Helper method to extract (query_text, doc_id, rating, rating_reasoning) tuples from the datastore.
        This can be used by subclasses to get the data in a consistent format.
        """
        result = []
        for query_context in self.datastore.get_queries():
            query_text = query_context.get_query()
            for doc_id in query_context.get_doc_ids():
                if query_context.has_rating_reasoning(doc_id) and query_context.has_rating_score(doc_id):
                    rating = query_context.get_rating(doc_id)
                    result.append((query_text, doc_id, rating.score, rating.reasoning))
        return result
