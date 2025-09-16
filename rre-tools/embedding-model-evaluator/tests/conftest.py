"""Shared test configuration and fixtures."""

import warnings
import jsonlines
from pathlib import Path
from typing import Literal
import pytest
from embedding_model_evaluator.config import Config

# Suppress MTEB warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=SyntaxWarning)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Helper to write JSONL files for tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with jsonlines.open(path, mode="w") as file:
        file.write_all(rows)


@pytest.fixture
def sample_corpus():
    """Sample corpus data for testing."""
    return [
        {"id": "doc1", "title": "Machine Learning", "text": "Introduction to ML algorithms"},
        {"id": "doc2", "title": "Deep Learning", "text": "Neural networks and backpropagation"},
        {"id": "doc3", "title": "Natural Language Processing", "text": "Text processing techniques"},
        {"id": "doc4", "title": "Computer Vision", "text": "Image recognition methods"},
        {"id": "doc5", "title": "Reinforcement Learning", "text": "Agent-based learning systems"},
    ]


@pytest.fixture
def sample_queries():
    """Sample queries data for testing."""
    return [
        {"id": "q1", "text": "What is machine learning?"},
        {"id": "q2", "text": "How do neural networks work?"},
        {"id": "q3", "text": "Text processing methods"},
    ]


@pytest.fixture
def sample_candidates():
    """Sample candidates data for testing."""
    return [
        # Query 1: ML query
        {"query_id": "q1", "doc_id": "doc1", "rating": 2},  # Highly relevant
        {"query_id": "q1", "doc_id": "doc2", "rating": 1},  # Somewhat relevant
        {"query_id": "q1", "doc_id": "doc3", "rating": 0},  # Not relevant
        
        # Query 2: Neural networks query
        {"query_id": "q2", "doc_id": "doc2", "rating": 2},  # Highly relevant
        {"query_id": "q2", "doc_id": "doc1", "rating": 1},  # Somewhat relevant
        {"query_id": "q2", "doc_id": "doc4", "rating": 0},  # Not relevant
        
        # Query 3: NLP query
        {"query_id": "q3", "doc_id": "doc3", "rating": 2},  # Highly relevant
        {"query_id": "q3", "doc_id": "doc1", "rating": 0},  # Not relevant
    ]


@pytest.fixture
def temp_dataset_files(tmp_path, sample_corpus, sample_queries, sample_candidates):
    """Create temporary dataset files for testing."""
    corpus_path = tmp_path / "corpus.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    candidates_path = tmp_path / "candidates.jsonl"
    
    write_jsonl(corpus_path, sample_corpus)
    write_jsonl(queries_path, sample_queries)
    write_jsonl(candidates_path, sample_candidates)
    
    return {
        "corpus_path": corpus_path,
        "queries_path": queries_path,
        "candidates_path": candidates_path,
        "tmp_path": tmp_path
    }


@pytest.fixture
def mock_config(temp_dataset_files):
    """Create a mock config object for testing."""
    return Config(
        model_id="test-model",
        task_to_evaluate="retrieval",
        corpus_path=temp_dataset_files["corpus_path"],
        queries_path=temp_dataset_files["queries_path"],
        candidates_path=temp_dataset_files["candidates_path"],
        relevance_scale="graded",
        dataset_name="dummy-dataset",
        split="test",
        output_dest=temp_dataset_files["tmp_path"] / "output",
        embeddings_dest=temp_dataset_files["tmp_path"] / "output/embeddings",
    )


def create_test_config(
    tmp_path: Path, 
    task_to_evaluate: Literal["retrieval", "reranking"] = "retrieval"
) -> Config:
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
        dataset_name="dummy-dataset",
        split="test",
        output_dest=tmp_path / "output",
        embeddings_dest=tmp_path / "output/embeddings",
    )
