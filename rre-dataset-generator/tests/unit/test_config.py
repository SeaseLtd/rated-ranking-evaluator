import pytest
from src.config import load_config
from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError


@pytest.fixture
def config():
    return load_config("tests/unit/resources/good_config.yaml")


def test_good_config_expect_all_parameters_read(config):
    assert config.query_template == 'q=#$query##&fq=genre:horror&wt=json'
    assert config.search_engine_type == "solr"
    assert config.search_engine_collection_endpoint == HttpUrl("http://localhost:8983/solr/mycore")
    assert config.documents_filter == [
        {"genre": ["horror", "fantasy"]},
        {"type": ["book"]}
    ]
    assert config.doc_number == 100
    assert config.doc_fields == ["title", "description"]
    assert config.queries == FilePath("tests/unit/resources/queries.txt")
    assert config.generate_queries_from_documents is True
    assert config.num_queries_needed == 10
    assert config.relevance_scale == "graded"
    assert config.llm_configuration_file == FilePath("tests/unit/resources/llm_config.yaml")
    assert config.output_destination == Path("output/generated_dataset.json")

def test_missing_optional_field_values():
    path = "tests/unit/resources/missing_optional.yaml"
    cfg = load_config(path)

    assert hasattr(cfg, "queries")
    assert cfg.queries is None

    assert hasattr(cfg, "query_template")
    assert cfg.query_template == 'q=#$query##'


def test_missing_required_field_raises_error():
    path = "tests/unit/resources/missing_required.yaml"
    with pytest.raises(ValidationError):
        _ = load_config(path)

def test_invalid_doc_number_type_raises_error():
    path = "tests/unit/resources/invalid_type.yaml"
    with pytest.raises(ValidationError):
        _ = load_config(path)

def test_file_not_found_raises_exception():
    path = "tests/unit/resources/file_does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        _ = load_config(path)
