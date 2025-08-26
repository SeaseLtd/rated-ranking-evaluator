from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError
import pytest

from src.config import Config


@pytest.fixture
def config():
    return Config.load("tests/unit/resources/good_config.yaml")


def test_good_config_expect_all_parameters_read(config):
    assert config.query_template == 'q=#$query##&fq=genre:horror&wt=json'
    assert config.search_engine_type == "solr"
    assert config.search_engine_collection_endpoint == HttpUrl("http://localhost:8983/solr/testcore")
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
    assert config.output_format == "quepid"
    assert config.output_destination == Path("output")
    assert config.save_llm_explanation is True
    assert config.llm_explanation_destination == Path("output/rating_explanation.json")
    assert config.index_name == "testcore"


def test_missing_optional_field_values():
    path = "tests/unit/resources/missing_optional.yaml"
    cfg = Config.load(path)

    assert hasattr(cfg, "queries")
    assert cfg.queries is None

    assert hasattr(cfg, "query_template")
    assert cfg.query_template == 'q=#$query##'


def test_missing_required_field_raises_error():
    path = "tests/unit/resources/missing_required.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(path)


def test_invalid_doc_number_type_raises_error():
    path = "tests/unit/resources/invalid_type.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(path)


def test_file_not_found_raises_exception():
    path = "tests/unit/resources/file_does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        _ = Config.load(path)


def test_mteb_config_expect_successful_load():
    path = "tests/unit/resources/mteb_config.yaml"
    mteb_config = Config.load(path)
    assert mteb_config.output_format == "mteb"
    assert mteb_config.output_destination == Path("output")
