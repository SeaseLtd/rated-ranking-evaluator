from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError
import pytest

from dataset_generator.config import Config


@pytest.fixture
def config(resource_folder):
    return Config.load(resource_folder / "good_config_solr.yaml")


def test_good_config__expects__all_parameters_read(config):
    assert config.query_template == Path('dataset-generator/tests/unit/resources/template_solr.json')
    assert config.search_engine_type == "solr"
    assert config.collection_name == "testcore"
    assert config.search_engine_url == HttpUrl("http://localhost:8983/solr/")
    assert config.search_engine_collection_endpoint == HttpUrl("http://localhost:8983/solr/testcore/")
    assert config.documents_filter == [
        {"genre": ["horror", "fantasy"]},
        {"type": ["book"]}
    ]
    assert config.doc_number == 100
    assert config.doc_fields == ["title", "description"]
    assert config.queries == FilePath("dataset-generator/tests/unit/resources/queries.txt")
    assert config.generate_queries_from_documents is True
    assert config.num_queries_needed == 10
    assert config.relevance_scale == "graded"
    assert config.llm_configuration_file == FilePath("dataset-generator/tests/unit/resources/llm_config.yaml")
    assert config.output_format == "quepid"
    assert config.output_destination == Path("output")
    assert config.save_llm_explanation is True
    assert config.llm_explanation_destination == Path("output/rating_explanation.json")


def test_missing_optional_field_values__expects__all_defaults_read(resource_folder):
    file_name = "missing_optional.yaml"
    cfg = Config.load(resource_folder / file_name)

    assert hasattr(cfg, "queries")
    assert cfg.queries is None

    assert hasattr(cfg, "query_template")
    assert cfg.query_template is None


def test_missing_required_field__expects__raises_validation_error(resource_folder):
    file_name = "missing_required.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(resource_folder / file_name)


def test_invalid_doc_number_type__expects__raises_validation_error(resource_folder):
    file_name = "invalid_type.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(resource_folder / file_name)


def test__expects__raises_file_not_found_error(resource_folder):
    file_name = "file_does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        _ = Config.load(resource_folder / file_name)


def test_mteb_config__expects__successful_load(resource_folder):
    file_name = "mteb_config.yaml"
    mteb_config = Config.load(resource_folder / file_name)
    assert mteb_config.output_format == "mteb"
    assert mteb_config.output_destination == Path("output")

def test_missing_both_templates_with_rre__expects__raises_validation_error(resource_folder):
    file_name = "missing_both_templates.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(resource_folder / file_name)
