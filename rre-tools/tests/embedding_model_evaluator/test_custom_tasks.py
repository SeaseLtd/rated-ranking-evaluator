from pathlib import Path
import pytest
import jsonlines


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with jsonlines.open(path, mode="w") as file:
        file.write_all(rows)


def _create_dataset_and_load_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    corpus_path = tmp_path / "corpus.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    candidates_path = tmp_path / "candidates.jsonl"

    _write_jsonl(
        corpus_path,
        [
            {"id": "d1", "title": "title1", "text": "text1 test1"},
            {"id": "d2", "title": "title2", "text": "text1 test2"},
            {"id": "d3", "title": "title3", "text": "text3 test3"},
        ],
    )
    _write_jsonl(
        queries_path,
        [{"id": "q1", "text": "text1 test1"}],
    )
    _write_jsonl(
        candidates_path,
        [
            {"query_id": "q1", "doc_id": "d1", "rating": 2},
            {"query_id": "q1", "doc_id": "d2", "rating": 1},
            {"query_id": "q1", "doc_id": "d3", "rating": 0},
        ],
    )

    return corpus_path, queries_path, candidates_path

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_custom_retrieval_task_with_valid_data__expects__loads_corpus_queries_and_relevant_docs_correctly(tmp_path: Path) -> None:
    from rre_tools.embedding_model_evaluator.custom_mteb_tasks.retrieval_task import CustomRetrievalTask
    corpus_path, queries_path, candidates_path = _create_dataset_and_load_paths(tmp_path)
    retrieval_task = CustomRetrievalTask()
    retrieval_task.load_data(corpus_path=corpus_path, queries_path=queries_path, candidates_path=candidates_path)

    assert "test" in retrieval_task.corpus and isinstance(
        retrieval_task.corpus["test"], dict
    )
    assert "test" in retrieval_task.queries and isinstance(
        retrieval_task.queries["test"], dict
    )
    assert "test" in retrieval_task.relevant_docs and isinstance(
        retrieval_task.relevant_docs["test"], dict
    )

    relevant_docs = retrieval_task.relevant_docs["test"]
    assert set(relevant_docs.keys()) == {"q1"}
    assert relevant_docs["q1"]["d1"] == 2
    assert relevant_docs["q1"]["d2"] == 1
    assert "d3" not in relevant_docs["q1"]
    assert retrieval_task.data_loaded is True

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_custom_reranking_task_with_valid_data__expects__loads_dataset_with_positive_and_negative_examples(tmp_path: Path) -> None:
    from rre_tools.embedding_model_evaluator.custom_mteb_tasks.reranking_task import CustomRerankingTask
    corpus_path, queries_path, candidates_path = _create_dataset_and_load_paths(tmp_path)
    reranking_task = CustomRerankingTask()
    reranking_task.load_data(corpus_path=corpus_path,
                             queries_path=queries_path,
                             candidates_path=candidates_path,
                             relevance_scale="binary")

    assert hasattr(reranking_task, "dataset")
    assert "test" in reranking_task.dataset

    dataset = reranking_task.dataset["test"]
    assert len(dataset) == 1
    row = dataset[0]

    assert set(dataset.column_names) == {"query", "positive", "negative"}

    assert row["query"] == "text1 test1"

    pos = set(row["positive"])
    neg = set(row["negative"])

    assert "title1\n\ntext1 test1" in pos
    assert "title3\n\ntext3 test3" in neg

    assert reranking_task.data_loaded is True
