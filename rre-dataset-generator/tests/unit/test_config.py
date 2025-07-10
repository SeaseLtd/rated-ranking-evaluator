import pytest
from src.config import load_config
from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError


@pytest.fixture
def config():
    return load_config("tests/unit/resources/good_config.yaml")


def test_query_template(config):
    assert config.query_template == 'q=#$query##&fq=genre:horror&wt=json'

def test_search_engine_type(config):
    assert config.search_engine_type == "solr"

def test_search_engine_endpoint(config):
    assert config.search_engine_collection_endpoint == HttpUrl("http://localhost:8983/solr/mycore")

def test_documents_filter(config):
    expected = [
        {"genre": ["horror", "fantasy"]},
        {"type": ["book"]}
    ]
    assert config.documents_filter == expected

def test_doc_number(config):
    assert config.doc_number == 100

def test_doc_fields(config):
    assert config.doc_fields == ["title", "description"]

def test_queries_file(config):
    assert config.queries == FilePath("queries.txt")

def test_generate_queries_from_documents(config):
    assert config.generate_queries_from_documents is True

def test_total_num_queries_to_generate(config):
    assert config.total_num_queries_to_generate == 10

def test_relevance_scale(config):
    assert config.relevance_scale == "graded"

def test_llm_configuration_file(config):
    assert config.llm_configuration_file == FilePath("llm_config.yaml")

def test_output_format(config):
    assert config.output_format == "Quepid"

def test_output_destination(config):
    assert config.output_destination == Path("output/generated_dataset.json")

def test_output_explanation(config):
    assert config.output_explanation is True

def test_missing_optional_field_values():
    path = "tests/unit/resources/missing_optional.yaml"
    cfg = load_config(path)
    assert hasattr(cfg, "output_explanation")
    assert cfg.output_explanation is False or cfg.output_explanation is None

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
