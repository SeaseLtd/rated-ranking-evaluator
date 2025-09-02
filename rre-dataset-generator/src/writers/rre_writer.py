import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.model.writer_config import WriterConfig
from src.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter

log = logging.getLogger(__name__)

RRE_OUTPUT_FILENAME = "ratings.json"

class RreWriter(AbstractWriter):
    """
    Writes query ratings in RRE format (ratings.json).
    """

    def __init__(self, config: WriterConfig):
        super().__init__(config)
        self.index = self.config.index
        self.id_field = self.config.id_field
        self.query_template = self.config.query_template
        self.query_placeholder = self.config.query_placeholder

    def _build_json_doc_records(self, datastore: DataStore) -> dict[str, Any]:
        query_text_to_doc_and_scores = defaultdict(list)
        ratings = datastore.get_ratings()
        for rating in ratings:
            query = datastore.get_query(rating.query_id)
            if query:
                query_text_to_doc_and_scores[query.text].append((rating.doc_id, int(rating.score)))

        query_groups = []
        for query_text, related_docs_and_scores in query_text_to_doc_and_scores.items():
            rating_to_doc_ids = defaultdict(list)
            for doc_id, score in related_docs_and_scores:
                rating_to_doc_ids[str(score)].append(doc_id)

            query_group = {
                "name": query_text,
                "queries": [
                    {
                        "template": str(self.query_template),
                        "placeholders": {
                            str(self.query_placeholder): query_text
                        }
                    }
                ],
                "relevant_documents": rating_to_doc_ids
            }
            query_groups.append(query_group)

        rre_formatted = {
            "index": self.index,
            "id_field": self.id_field,
            "query_placeholder": self.query_placeholder,
            "query_groups": query_groups
        }
        return rre_formatted

    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """
        Writes queries and their ratings to ratings.json file in RRE format.
        """
        output_path = Path(output_path) / RRE_OUTPUT_FILENAME
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as json_file:
            log.debug("Started writing RRE formatted records to json file")
            json.dump(self._build_json_doc_records(datastore), json_file, indent=2)
            log.debug("Finished writing RRE formatted records to json file")
