from pathlib import Path
from typing import Sequence

import jsonlines

from rre_tools.core.data_store import DataStore
from rre_tools.core.models import Document, WriterConfig
from rre_tools.core.writers.quepid_writer import QuepidWriter
from rre_tools.embedding_model_evaluator.config import Config as MTEBConfig
from rre_tools.embedding_model_evaluator.embedding_writer import EmbeddingWriter
from rre_tools.embedding_model_evaluator.constants import TASKS_NAME_MAPPING
from rre_tools.dataset_generator.config import Config as DGConfig


# ---------------- commons ----------------

def test_save_and_load_nested_paths__expects__data_persisted_correctly(tmp_path: Path) -> None:
    """
    Verifies that DataStore can save and load nested paths.
    """
    nested_path = tmp_path / "level1" / "level2" / "datastore.json"
    ds = DataStore(path=nested_path, ignore_saved_data=True)

    # minimal data roundtrip
    doc = Document(id="doc1", fields={"title": "t"})
    ds.add_document(doc)
    q = ds.add_query("q1")
    ds.create_rating_score(q.id, doc.id, 1)

    ds.save()

    assert nested_path.exists()
    assert nested_path.parent.exists()

    ds2 = DataStore(path=nested_path)
    assert len(ds2.get_documents()) == 1
    assert len(ds2.get_queries()) == 1
    assert len(ds2.get_ratings()) == 1


# ---------------- embedding-model-evaluator ----------------

class _FakeCache:
    def __init__(self, vectors: Sequence[Sequence[float]]):
        self._vectors = vectors

    def encode(self, texts, *, task_name: str, batch_size: int):
        return self._vectors

    def close(self) -> None:
        pass


def test_embedding_writer_with_nested_dirs__expects__creates_files_in_nested_dirs(tmp_path: Path) -> None:
    """
    Verifies that EmbeddingWriter handles nested output directories.
    """
    cfg: MTEBConfig = MTEBConfig.load(
        "embedding-model-evaluator/tests/unit/resources/valid_config.yaml"
    )

    dest = tmp_path / "out" / "embeddings"

    cached_doc = _FakeCache(vectors=[[0.1, 0.2, 0.3]])
    cached_query = _FakeCache(vectors=[[1.0, 1.1, 1.2]])

    writer = EmbeddingWriter(
        config=cfg,
        cached=cached_doc,
        cache_path=tmp_path / "cache",
        task_name=TASKS_NAME_MAPPING["retrieval"],
        batch_size=32,
    )

    writer.write(dest)

    docs_file = dest / "documents_embeddings.jsonl"
    assert docs_file.exists()
    # sanity read
    with jsonlines.open(docs_file) as r:
        _ = list(r)

    writer = EmbeddingWriter(
        config=cfg,
        cached=cached_query,
        cache_path=tmp_path / "cache",
        task_name=TASKS_NAME_MAPPING["retrieval"],
        batch_size=32,
    )

    writer.write(dest)

    queries_file = dest / "queries_embeddings.jsonl"
    assert queries_file.exists()
    with jsonlines.open(queries_file) as r:
        _ = list(r)


# ---------------- dataset-generator ----------------

def test_dataset_generator_with_nested_paths__expects__handles_paths_cross_platform(tmp_path: Path) -> None:
    """
    Verifies that DatasetGenerator handles nested output directories.
    """
    # create minimal valid LLM config file
    llm_cfg_path = tmp_path / "llm.yaml"
    llm_cfg_path.write_text("name: openai\napi_key_env: OPENAI_API_KEY\nmodel: gpt-4o-mini\nmax_tokens: 32\n")

    template_path = tmp_path / "template.json"
    template_path.write_text("{'q': '*:*'}")

    # create dynamic config yaml with nested output paths
    cfg_path = tmp_path / "dg_config.yaml"
    cfg_content = f"""
    query_template: "{template_path.as_posix()}"
    search_engine_type: "solr"
    collection_name: "testcore"
    search_engine_url: "http://localhost:8983/solr/"
    doc_number: 1
    doc_fields: ["title", "description"]
    num_queries_needed: 1
    relevance_scale: "binary"
    llm_configuration_file: "{llm_cfg_path.as_posix()}"
    output_format: "mteb"
    output_destination: "{(tmp_path / 'nested' / 'out').as_posix()}"
    """
    cfg_path.write_text(cfg_content)

    cfg = DGConfig.load(str(cfg_path))
    assert isinstance(cfg.output_destination, Path)

    # ensure we can create dirs/files with the Path (cross-platform)
    target_dir = cfg.output_destination / "subdir"
    target_dir.mkdir(parents=True, exist_ok=True)
    assert target_dir.exists()

# ---------------- commons (encoding) ----------------
def test_writer_with_special_chars__expects__correctly_handles_specials(tmp_path: Path) -> None:
    """Verifies that writers correctly handle non-ASCII chars thanks to UTF-8 encoding."""
    ds = DataStore(ignore_saved_data=True)
    doc = Document(id="doc-ñ", fields={"title": "t"})
    ds.add_document(doc)

    # Query with tildes and other special chars
    query_text = "evaluación para un niño"
    q = ds.add_query(query_text)
    ds.create_rating_score(q.id, doc.id, 1)

    # Using QuepidWriter as a representative example
    # TODO: expand tests to the rest of the writers
    writer_cfg = WriterConfig(output_format="quepid", index="test")
    writer = QuepidWriter(writer_cfg)
    writer.write(tmp_path, ds)

    output_file = tmp_path / "quepid.csv"
    assert output_file.exists()

    # Read the file back and check content
    # If encoding was missing, this would fail on some systems
    content = output_file.read_text(encoding="utf-8")
    assert query_text in content
    assert "doc-ñ" in content

