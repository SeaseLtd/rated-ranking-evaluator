import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.config import Config
from src.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter

log = logging.getLogger(__name__)

RRE_OUTPUT_FILENAME = "ratings.json"

class RreWriter(AbstractWriter):
    """
    Writes query ratings in RRE format (ratings.json).
    """

    @classmethod
    def build(cls, config: Config, data_store: DataStore):
        return cls(
            datastore=data_store,
            index=config.index_name,
            corpora_file=config.corpora_file,
            id_field=config.id_field,
            query_template=config.rre_query_template,
            query_placeholder=config.rre_query_placeholder
        )

    def __init__(self, index: str, corpora_file: str, id_field: str,
                 query_template: str, query_placeholder: str):
        super().__init__()
        self.index = index
        self.corpora_file = corpora_file
        self.id_field = id_field
        self.query_template = query_template
        self.query_placeholder = query_placeholder

    def _build_json_doc_records(self, datastore: DataStore) -> dict[str, Any]:
        query_text_to_doc_and_scores = defaultdict(list)
        ratings = datastore.get_ratings()
        for rating in ratings:
            query = datastore.get_query(rating.query_id)
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
                            self.query_placeholder: query_text
                        }
                    }
                ],
                "relevant_documents": rating_to_doc_ids
            }
            query_groups.append(query_group)

        rre_formatted = {
            "index": self.index,
            "corpora_file": str(self.corpora_file),
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
