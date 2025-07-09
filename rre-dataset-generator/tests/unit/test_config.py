import pytest
from src.config import load_config
from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError


@pytest.fixture
def config():
    return load_config("tests/unit/resources/good_config.yaml")


def test_query_template(config):
    assert config.QueryTemplate == 'q=#$query##&fq=genre:horror&wt=json'

def test_search_engine_type(config):
    assert config.SearchEngineType == "Solr"

def test_search_engine_endpoint(config):
    assert config.SearchEngineCollectionEndpoint == HttpUrl("http://localhost:8983/solr/mycore")

def test_documents_filter(config):
    expected = [
        {"genre": ["horror", "fantasy"]},
        {"type": ["book"]}
    ]
    assert config.documentsFilter == expected

def test_doc_number(config):
    assert config.docNumber == 100

def test_doc_fields(config):
    assert config.docFields == ["title", "body"]

def test_queries_file(config):
    assert config.queries == FilePath("queries.txt")

def test_generate_queries_from_documents(config):
    assert config.generateQueriesFromDocuments is True

def test_total_num_queries(config):
    assert config.totalNumQueriesToGenerate == 10

def test_relevance_scale(config):
    assert config.RelevanceScale == "Graded"

def test_llm_configuration_file(config):
    assert config.LLMConfigurationFile == FilePath("llm_config.yaml")

def test_output_format(config):
    assert config.OutputFormat == "Quepid"

def test_output_destination(config):
    assert config.OutputDestination == Path("output/generated_dataset.json")

def test_output_explanation(config):
    assert config.OutputExplanation is True

def test_missing_optional_field_values():
    path = "tests/unit/resources/missing_optional.yaml"
    cfg = load_config(path)
    assert hasattr(cfg, "OutputExplanation")
    assert cfg.OutputExplanation is False or cfg.OutputExplanation is None

    assert hasattr(cfg, "QueryTemplate")
    assert cfg.QueryTemplate == 'q=#$query##'


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
