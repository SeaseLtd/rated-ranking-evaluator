import csv
import os
from pathlib import Path

from src.writers.abstract_writer import AbstractWriter


class QuepidWriter(AbstractWriter):
    """
    QuepidWriter: Write the data structure to a Quepid format (CSV).
    The format is: query,docid,rating
    """

    def write(self, output_path: str | Path) -> None:
        """
        Writes queries and their scored documents to a CSV file in Quepid format.
        """
        output_path = Path(output_path)
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['query', 'docid', 'rating'])

            # Use the helper method to get all rated query-document pairs
            for query_text, doc_id, rating in self._get_queries_with_ratings():
                writer.writerow([query_text, doc_id, rating])
