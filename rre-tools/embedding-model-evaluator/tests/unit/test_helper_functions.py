"""Comprehensive unit tests for helper functions."""

import pytest
import tempfile
import jsonlines
from pathlib import Path

from embedding_model_evaluator.utilities.helper import (
    read_corpus, read_queries, read_candidates, _validate_shapes
)


class TestHelperFunctions:
    """Test suite for helper functions with comprehensive coverage."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample test data with various edge cases."""
        return {
            "corpus": [
                {"id": "doc1", "title": "Title 1", "text": "Content 1"},
                {"id": "doc2", "title": "", "text": "Content 2"},  # Empty title
                {"id": "doc3", "title": "Title 3", "text": ""},  # Empty text
                {"id": 123, "title": "Title 4", "text": "Content 4"},  # Numeric ID
            ],
            "queries": [
                {"id": "q1", "text": "Query 1"},
                {"id": "q2", "text": "Query 2"},
                {"id": 456, "text": "Query 3"},  # Numeric ID
            ],
            "candidates": [
                {"query_id": "q1", "doc_id": "doc1", "rating": 2},
                {"query_id": "q1", "doc_id": "doc2", "rating": 1},
                {"query_id": "q1", "doc_id": "doc3", "rating": 0},
                {"query_id": "q2", "doc_id": "doc1", "rating": 1},
                {"query_id": 456, "doc_id": 123, "rating": 2},  # Numeric IDs
            ]
        }
    
    @pytest.fixture
    def temp_files(self, sample_data):
        """Create temporary test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_path = Path(tmpdir) / "corpus.jsonl"
            queries_path = Path(tmpdir) / "queries.jsonl"
            candidates_path = Path(tmpdir) / "candidates.jsonl"
            
            # Write test data
            with jsonlines.open(corpus_path, mode='w') as writer:
                for item in sample_data["corpus"]:
                    writer.write(item)
                    
            with jsonlines.open(queries_path, mode='w') as writer:
                for item in sample_data["queries"]:
                    writer.write(item)
                    
            with jsonlines.open(candidates_path, mode='w') as writer:
                for item in sample_data["candidates"]:
                    writer.write(item)
            
            yield {
                "corpus": corpus_path,
                "queries": queries_path,
                "candidates": candidates_path
            }
    
    def test_read_corpus_basic(self, temp_files):
        """Test basic corpus reading functionality."""
        corpus = read_corpus(temp_files["corpus"])
        
        # Check structure
        assert isinstance(corpus, dict)
        assert len(corpus) == 4
        
        # Check string conversion
        assert all(isinstance(k, str) for k in corpus.keys())
        assert "doc1" in corpus
        assert "123" in corpus  # Numeric ID converted to string
        
        # Check content
        assert corpus["doc1"]["title"] == "Title 1"
        assert corpus["doc1"]["text"] == "Content 1"
        assert corpus["doc2"]["title"] == ""  # Empty title preserved
        assert corpus["doc3"]["text"] == ""   # Empty text preserved
    
    def test_read_queries_basic(self, temp_files):
        """Test basic queries reading functionality."""
        queries = read_queries(temp_files["queries"])
        
        # Check structure
        assert isinstance(queries, dict)
        assert len(queries) == 3
        
        # Check string conversion
        assert all(isinstance(k, str) for k in queries.keys())
        assert "q1" in queries
        assert "456" in queries  # Numeric ID converted to string
        
        # Check content
        assert queries["q1"] == "Query 1"
        assert queries["456"] == "Query 3"
    
    def test_read_candidates_basic(self, temp_files):
        """Test basic candidates reading functionality."""
        result = read_candidates(temp_files["candidates"])
        
        # Check structure
        assert isinstance(result, dict)
        assert "candidates" in result
        assert "relevant_docs" in result
        
        candidates = result["candidates"]
        relevant_docs = result["relevant_docs"]
        
        # Check string conversion
        assert all(isinstance(k, str) for k in candidates.keys())
        assert "q1" in candidates
        assert "456" in candidates  # Numeric ID converted
        
        # Check nested string conversion
        for qid, docs in candidates.items():
            assert all(isinstance(did, str) for did in docs.keys())
        
        # Check ratings
        assert candidates["q1"]["doc1"] == 2
        assert candidates["q1"]["doc2"] == 1
        assert candidates["q1"]["doc3"] == 0
        assert candidates["456"]["123"] == 2  # Numeric IDs converted
        
        # Check relevant_docs filtering (rating > 0)
        assert "q1" in relevant_docs
        assert "doc1" in relevant_docs["q1"]  # rating=2
        assert "doc2" in relevant_docs["q1"]  # rating=1
        assert "doc3" not in relevant_docs["q1"]  # rating=0 excluded
        assert relevant_docs["456"]["123"] == 2
    
    def test_validate_shapes_success(self, temp_files):
        """Test validation with valid data."""
        corpus = read_corpus(temp_files["corpus"])
        queries = read_queries(temp_files["queries"])
        candidates_data = read_candidates(temp_files["candidates"])
        
        # Convert to list of tuples format expected by _validate_shapes
        candidates_list = [
            (qid, did, rating) 
            for qid, docs in candidates_data["candidates"].items() 
            for did, rating in docs.items()
        ]
        
        # Should not raise any exceptions
        _validate_shapes(corpus, queries, candidates_list)
    
    def test_validate_shapes_missing_docs(self):
        """Test validation with missing document IDs."""
        corpus = {"doc1": {"title": "Title", "text": "Text"}}
        queries = {"q1": "Query"}
        candidates = [("q1", "doc1", 1), ("q1", "missing_doc", 2)]
        
        # Should raise ValueError for missing references
        with pytest.raises(ValueError, match="Missing references"):
            _validate_shapes(corpus, queries, candidates)
    
    def test_validate_shapes_missing_queries(self):
        """Test validation with missing query IDs."""
        corpus = {"doc1": {"title": "Title", "text": "Text"}}
        queries = {"q1": "Query"}
        candidates = [("q1", "doc1", 1), ("missing_query", "doc1", 2)]
        
        # Should raise ValueError for missing references
        with pytest.raises(ValueError, match="Missing references"):
            _validate_shapes(corpus, queries, candidates)
    
    def test_empty_files(self):
        """Test behavior with empty files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty files
            empty_corpus = Path(tmpdir) / "empty_corpus.jsonl"
            empty_queries = Path(tmpdir) / "empty_queries.jsonl"
            empty_candidates = Path(tmpdir) / "empty_candidates.jsonl"
            
            for path in [empty_corpus, empty_queries, empty_candidates]:
                path.touch()
            
            # Should handle empty files gracefully
            corpus = read_corpus(empty_corpus)
            queries = read_queries(empty_queries)
            candidates_data = read_candidates(empty_candidates)
            
            assert corpus == {}
            assert queries == {}
            assert candidates_data["candidates"] == {}
            assert candidates_data["relevant_docs"] == {}
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed_path = Path(tmpdir) / "malformed.jsonl"
            
            # Write malformed data (missing required fields)
            with jsonlines.open(malformed_path, mode='w') as writer:
                writer.write({"id": "doc1"})  # Missing title/text
                writer.write({"title": "Title", "text": "Text"})  # Missing id
            
            # Should handle gracefully (may raise KeyError or return partial data)
            try:
                corpus = read_corpus(malformed_path)
                # If it succeeds, check what we got
                assert isinstance(corpus, dict)
            except KeyError:
                # Expected behavior for missing required fields
                pass


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_files(self):
        """Test behavior with nonexistent files."""
        nonexistent = Path("/nonexistent/file.jsonl")
        
        with pytest.raises(FileNotFoundError):
            read_corpus(nonexistent)
        
        with pytest.raises(FileNotFoundError):
            read_queries(nonexistent)
        
        with pytest.raises(FileNotFoundError):
            read_candidates(nonexistent)
    
    def test_large_dataset_simulation(self):
        """Test with simulated large dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            large_corpus = Path(tmpdir) / "large_corpus.jsonl"
            
            # Create a moderately large dataset
            with jsonlines.open(large_corpus, mode='w') as writer:
                for i in range(1000):
                    writer.write({
                        "id": f"doc_{i}",
                        "title": f"Title {i}",
                        "text": f"Content {i}"
                    })
            
            corpus = read_corpus(large_corpus)
            assert len(corpus) == 1000
            assert all(isinstance(k, str) for k in corpus.keys())
    
    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_path = Path(tmpdir) / "unicode.jsonl"
            
            unicode_data = [
                {"id": "doc1", "title": "Título español", "text": "Contenido con ñ"},
                {"id": "doc2", "title": "中文标题", "text": "中文内容"},
                {"id": "doc3", "title": "العربية", "text": "محتوى عربي"},
            ]
            
            with jsonlines.open(unicode_path, mode='w') as writer:
                for item in unicode_data:
                    writer.write(item)
            
            corpus = read_corpus(unicode_path)
            assert len(corpus) == 3
            assert corpus["doc1"]["title"] == "Título español"
            assert corpus["doc2"]["title"] == "中文标题"
            assert corpus["doc3"]["title"] == "العربية"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
