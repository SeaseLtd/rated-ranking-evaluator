import json
import logging
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict

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
            index=kwargs['index'],
            id_field=kwargs['id_field'],
            datastore=data_store
        )

    def __init__(self, index: str, id_field: str, datastore: DataStore):
        super().__init__(datastore)
        self.index = index
        self.id_field = id_field

    def _build_json_doc_records(self) -> dict:
        query_to_doc_ratings = defaultdict(list)

        for query_text, doc_id, rating in self._get_queries_with_ratings():
            query_to_doc_ratings[query_text].append((doc_id, int(rating)))

        query_groups = []
        for query_text, relevant_docs in query_to_doc_ratings.items():
            relevant_documents = [
                {"document_id": doc_id, "gain": gain}
                for doc_id, gain in relevant_docs
            ]

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
                "relevant_documents": relevant_documents
            }
            query_groups.append(query_group)

        rre_formatted = {
            "index": self.index,
            "id_field": self.id_field,
            "query_placeholder": self.QUERY_PLACEHOLDER,
            "query_groups": query_groups
        }

        return rre_formatted

    def _create_query_template_file(self, query_template: Dict[str, str]) -> str:
        """Write the query template to a temporary file and return the file path."""
        temp = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json")
        json.dump(query_template, temp)
        temp.close()
        return temp.name

    def write(self, output_path: str | Path) -> None:
        """
        Writes queries and their ratings to json file in RRE format.
        """
        output_path = Path(output_path)
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, 'w', newline='') as json_file:
            log.debug("Started writing RRE formatted records to json file")
            json.dump(self._build_json_doc_records, json_file, indent=2)
            log.debug("Finished writing RRE formatted records to json file")
