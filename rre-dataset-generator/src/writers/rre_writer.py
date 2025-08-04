import json
import logging
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any

from src.search_engine.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter

log = logging.getLogger(__name__)


class RreWriter(AbstractWriter):
    """
    Writes query ratings in RRE format (ratings.json).
    """

    QUERY_TEMPLATE = {"q": "$query"}

    QUERY_PLACEHOLDER = "$query"

    @classmethod
    def from_factory(cls, data_store, **kwargs):
        return cls(
            datastore=data_store,
            index=kwargs['index'],
            id_field=kwargs['id_field']
        )

    @staticmethod
    def _create_query_template_file(query_template: Dict[str, str]) -> str:
        """Write the query template to a temporary file and return the file path."""

        temp = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json")
        json.dump(query_template, temp)
        temp.close()
        return temp.name

    def __init__(self, datastore: DataStore, index: str, id_field: str):
        super().__init__(datastore)
        self.index = index
        self.id_field = id_field

    def _build_json_doc_records(self) -> dict[str, Any]:
        query_to_doc_ratings = defaultdict(list)

        for query_text, doc_id, rating in self._get_queries_with_ratings():
            query_to_doc_ratings[query_text].append((doc_id, int(rating)))

        query_groups = []
        for query_text, relevant_docs in query_to_doc_ratings.items():
            rating_to_doc_ids = defaultdict(list)
            for doc_id, gain in relevant_docs:
                rating_to_doc_ids[str(gain)].append(doc_id)

            query_group = {
                "name": query_text,
                "queries": [
                    {
                        "template": self._create_query_template_file(self.QUERY_TEMPLATE),
                        "placeholders": {
                            self.QUERY_PLACEHOLDER: query_text
                        }
                    }
                ],
                "relevant_documents": rating_to_doc_ids
            }
            query_groups.append(query_group)

        rre_formatted = {
            "index": self.index,
            "id_field": self.id_field,
            "query_placeholder": self.QUERY_PLACEHOLDER,
            "query_groups": query_groups
        }
        return rre_formatted

    def write(self, output_path: str | Path) -> None:
        """
        Writes queries and their ratings to json file in RRE format.
        """
        output_path = Path(output_path)
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, 'w', newline='') as json_file:
            log.debug("Started writing RRE formatted records to json file")
            json.dump(self._build_json_doc_records(), json_file, indent=2)
            log.debug("Finished writing RRE formatted records to json file")
