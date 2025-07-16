from abc import ABC, abstractmethod
from src.search_engine.data_store import DataStore
import csv

class AbstractWriter(ABC):
    """
    Abstract base class for writers.
    
    The writer has to read the data structure and export it to a format (e.g.:quepid, rre..)
    """
    def __init__(self, datastore: DataStore):
        self.datastore = datastore

    @abstractmethod
    def write(self, output_path: str) -> None:
        """Writes the data from the datastore to a file."""
        pass
    

class QuepidWriter(AbstractWriter):
    """
    QuepidWriter: Write the data structure to a Quepid format (CSV).
    """
    def write(self, output_path: str) -> None:
        """
        Writes queries and their scored documents to a CSV file in Quepid format.
        The format is: query,docid,rating
        """
        queries = self.datastore.get_queries() # Query List
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['query', 'docid', 'rating'])
            
            for query in queries:
                for score in query.scores.values():
                    if score.value != -1:  # Only write rated documents
                        writer.writerow([query.text, score.doc_id, score.value])