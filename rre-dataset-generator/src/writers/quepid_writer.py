import csv
import os
from pathlib import Path
from typing import List, Tuple

from src.config import Config
from src.writers.abstract_writer import AbstractWriter
from src.data_store import DataStore

class QuepidWriter(AbstractWriter):
    """
    QuepidWriter: Write the data structure to a Quepid format (CSV).
    The format is: query, docid, rating
    """

    def _get_queries_and_ratings(self, datastore: DataStore) -> List[Tuple[str, str, int]]:
        """Helper to extract (query_text, doc_id, rating) tuples from the datastore."""
        result = []
        for rating in datastore.get_ratings():
            result.append((rating.query_id, rating.doc_id, rating.score))
        return result

    def write(self, output_path: str | Path, datastore: DataStore) -> None:
        """Writes queries and their scored documents to a CSV file in Quepid format."""
        output_path = Path(output_path)
        os.makedirs(output_path.parent, exist_ok=True)

        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['query', 'docid', 'rating'])
            
            rated_pairs = self._get_queries_and_ratings(datastore)
            for query_id, doc_id, rating in rated_pairs:
                writer.writerow([query_id, doc_id, rating])
