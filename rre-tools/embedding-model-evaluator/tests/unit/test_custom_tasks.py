"""Unit tests for custom tasks."""

from pathlib import Path

import pytest
import jsonlines

from embedding_model_evaluator.custom_tasks.reranking_task import CustomRerankingTask
from embedding_model_evaluator.custom_tasks.retrieval_task import CustomRetrievalTask
from embedding_model_evaluator.config import Config


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Helper to write JSONL files for tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with jsonlines.open(path, mode="w") as file:
        file.write_all(rows)


def create_test_config(tmp_path: Path, task_to_evaluate: str = "retrieval") -> Config:
    """Helper to create test config with minimal dataset."""
    corpus_path = tmp_path / "corpus.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    candidates_path = tmp_path / "candidates.jsonl"

    write_jsonl(corpus_path, [
        {"id": "d1", "title": "title1", "text": "text1 test1"},
        {"id": "d2", "title": "title2", "text": "text1 test2"},
        {"id": "d3", "title": "title3", "text": "text3 test3"},
    ])
    
    write_jsonl(queries_path, [
        {"id": "q1", "text": "text1 test1"}
    ])
    
    write_jsonl(candidates_path, [
        {"query_id": "q1", "doc_id": "d1", "rating": 2},
        {"query_id": "q1", "doc_id": "d2", "rating": 1},
        {"query_id": "q1", "doc_id": "d3", "rating": 0},
    ])

    return Config(
        model_id="dummy-model",
        task_to_evaluate=task_to_evaluate,
        corpus_path=corpus_path,
        queries_path=queries_path,
        candidates_path=candidates_path,
        relevance_scale="graded",
        output_dest=tmp_path / "output",
        embeddings_dest=tmp_path / "output/embeddings",
    )


class TestCustomRetrievalTask:
    """Unit tests for CustomRetrievalTask."""
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_load_data_success(self, tmp_path: Path) -> None:
        """Test successful data loading for retrieval task."""
        config = create_test_config(tmp_path, "retrieval")
        task = CustomRetrievalTask()
        task.load_data(config=config)

        # Verify data structure
        assert "test" in task.corpus and isinstance(task.corpus["test"], dict)
        assert "test" in task.queries and isinstance(task.queries["test"], dict)
        assert "test" in task.relevant_docs and isinstance(task.relevant_docs["test"], dict)

        # Verify relevant_docs filtering (only rating > 0)
        relevant_docs = task.relevant_docs["test"]
        assert set(relevant_docs.keys()) == {"q1"}
        assert relevant_docs["q1"]["d1"] == 2
        assert relevant_docs["q1"]["d2"] == 1
        assert "d3" not in relevant_docs["q1"]  # rating=0, should be filtered
        assert task.data_loaded is True
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_load_data_no_config(self) -> None:
        """Test error handling when no config provided."""
        task = CustomRetrievalTask()
        with pytest.raises(ValueError, match="No config is provided"):
            task.load_data(None)
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_string_id_casting(self, tmp_path: Path) -> None:
        """Test that all IDs are properly cast to strings."""
        config = create_test_config(tmp_path, "retrieval")
        task = CustomRetrievalTask()
        task.load_data(config=config)
        
        # Verify string IDs
        corpus = task.corpus["test"]
        queries = task.queries["test"]
        
        assert all(isinstance(doc_id, str) for doc_id in corpus.keys())
        assert all(isinstance(query_id, str) for query_id in queries.keys())


class TestCustomRerankingTask:
    """Unit tests for CustomRerankingTask."""
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_load_data_success(self, tmp_path: Path) -> None:
        """Test successful data loading for reranking task."""
        config = create_test_config(tmp_path, "reranking")
        task = CustomRerankingTask()
        task.load_data(config=config)

        # Verify data structure
        assert hasattr(task, "dataset")
        assert "test" in task.dataset

        dataset = task.dataset["test"]
        assert len(dataset) == 1
        row = dataset[0]

        assert set(dataset.column_names) == {"query", "positive", "negative"}
        assert row["query"] == "text1 test1"

        # Verify graded relevance behavior
        pos = set(row["positive"])
        neg = set(row["negative"])

        assert "title1\n\ntext1 test1" in pos  # rating=2
        assert "title3\n\ntext3 test3" in neg  # rating=0
        assert task.data_loaded is True
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_compose_text_function(self) -> None:
        """Test the compose_text helper function."""
        from embedding_model_evaluator.custom_tasks.reranking_task import compose_text
        
        # Both title and text
        result = compose_text("Title", "Text content")
        assert result == "Title\n\nText content"
        
        # Only title
        result = compose_text("Title", None)
        assert result == "Title"
        
        # Only text
        result = compose_text(None, "Text content")
        assert result == "Text content"
        
        # Empty/None values
        result = compose_text("", "")
        assert result == ""
        
        result = compose_text(None, None)
        assert result == ""


class TestTasksRegistration:
    """Test that tasks can be imported and instantiated."""
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_tasks_can_be_imported(self) -> None:
        """Test that both tasks can be imported without errors."""
        # Basic instantiation test
        reranking_task = CustomRerankingTask()
        retrieval_task = CustomRetrievalTask()
        
        assert reranking_task is not None
        assert retrieval_task is not None
