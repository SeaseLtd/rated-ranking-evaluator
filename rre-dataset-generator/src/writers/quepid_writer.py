import csv
import os
from pathlib import Path
from typing import List, Tuple

from src.config import Config
from src.search_engine.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter
from src.search_engine.data_store import DataStore
from src.model.document import Document


class QuepidWriter(AbstractWriter):
    """
    QuepidWriter: Write the data structure to a Quepid format (CSV).
    The format is: query,docid,rating
    """

    @classmethod
    def build(cls, config: Config, data_store: DataStore):
        return cls(datastore=data_store)

    def write(self, output_path: str | Path) -> None:
        """
        Writes queries and their scored documents to quepid.csv file.
        """
        output_path = Path(output_path) / "quepid.csv"
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['query', 'docid', 'rating'])

            # Use the helper method to get all rated query-document pairs
            for query_text, doc_id, rating in self._get_queries_with_ratings():
                writer.writerow([query_text, doc_id, rating])


def create_sample_data() -> Tuple[DataStore, List[Tuple[str, str, int]]]:
    """
    Creates a sample dataset with queries and documents for demonstration purposes.
    
    Returns:
        Tuple containing:
            - DataStore: Populated with sample data
            - List[Tuple[str, str, int]]: Expected output data for verification
    """
    # Initialize DataStore
    datastore = DataStore(ignore_saved_data=True)
    
    # Sample documents
    documents = [
        ("doc1", {"title": "Introduction to Python", "content": "Python is a high-level programming language..."}),
        ("doc2", {"title": "Advanced Python Features", "content": "This document covers advanced Python features..."}),
        ("doc3", {"title": "Python for Data Science", "content": "Data science with Python is very popular..."}),
        ("doc4", {"title": "Web Development with Python", "content": "Python can be used for web development..."}),
        ("doc5", {"title": "Machine Learning Basics", "content": "Introduction to machine learning concepts..."}),
    ]
    
    # Add documents to datastore
    for doc_id, fields in documents:
        datastore.add_document(doc_id, Document(id=doc_id, fields=fields))
    
    # Sample queries with ratings
    query_data = [
        ("python programming", [("doc1", 2), ("doc2", 1)]),
        ("data science", [("doc3", 2), ("doc5", 1)]),
        ("web development", [("doc4", 2), ("doc1", 0)]),
    ]
    
    # Add queries and ratings to datastore
    expected_output = []
    for query_text, doc_ratings in query_data:
        query_id = datastore.add_query(query_text)
        for doc_id, rating in doc_ratings:
            datastore.add_rating_score(query_id, doc_id, rating)
            expected_output.append((query_text, doc_id, rating))
    
    return datastore, expected_output


if __name__ == "__main__":
    # Create sample data
    datastore, expected_data = create_sample_data()
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "quepid_ratings.csv"
    
    # Write the data using QuepidWriter
    writer = QuepidWriter(datastore)
    writer.write(output_file)
    
    # Verify the output
    print(f"Generated Quepid ratings file: {output_file.absolute()}")
    print("\nSample data written:")
    print("query, docid, rating")
    print("-" * 40)
    for i, (query, doc_id, rating) in enumerate(expected_data[:5], 1):
        print(f"{i}. {query[:30]}..., {doc_id}, {rating}")
    
    print(f"\nTotal ratings written: {len(expected_data)}")
