from pydantic import HttpUrl, FilePath
from pathlib import Path
from pydantic_core import ValidationError
import pytest

from rre_tools.dataset_generator.config import Config


@pytest.fixture
def config(resource_folder):
    return Config.load(resource_folder / "good_config_solr.yaml")


def test_good_config__expects__all_parameters_read(config):
    assert config.query_template == Path('tests/resources/template_solr.json')
    assert config.search_engine_type == "solr"
    assert config.collection_name == "testcore"
    assert config.search_engine_url == HttpUrl("http://localhost:8983/solr/")
    assert config.search_engine_collection_endpoint == HttpUrl("http://localhost:8983/solr/testcore/")
    assert config.documents_filter == [
        {"genre": ["horror", "fantasy"]},
        {"type": ["book"]}
    ]
    assert config.number_of_docs == 100
    assert config.doc_fields == ["title", "description"]
    assert config.queries == FilePath("tests/resources/queries.txt")
    assert config.generate_queries_from_documents is True
    assert config.num_queries_needed == 10
    assert config.relevance_scale == "graded"
    assert config.llm_configuration_file == FilePath("tests/resources/llm_config.yaml")
    assert config.output_format == "quepid"
    assert config.output_destination == Path("output")
    assert config.save_llm_explanation is True
    assert config.llm_explanation_destination == Path("output/rating_explanation.json")

    # New optional param: defaults to None when not provided
    assert hasattr(config, "datastore_autosave_every_n_updates")
    assert config.datastore_autosave_every_n_updates is None


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


def test_invalid_number_of_docs_type__expects__raises_validation_error(resource_folder):
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


def test_autosave_valid_positive_int__expects__parsed(tmp_path):
    # Minimal valid config including autosave set to a positive integer
    cfg_text = (
        "search_engine_type: \"solr\"\n"
        "collection_name: \"testcore\"\n"
        "search_engine_url: \"http://localhost:8983/solr/\"\n"
        "number_of_docs: 2\n"
        "doc_fields: [\"title\"]\n"
        "num_queries_needed: 2\n"
        "relevance_scale: \"binary\"\n"
        "llm_configuration_file: \"tests/resources/llm_config.yaml\"\n"
        "output_format: \"quepid\"\n"
        "output_destination: \"output\"\n"
        "datastore_autosave_every_n_updates: 50\n"
    )
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    cfg = Config.load(str(cfg_path))
    assert cfg.datastore_autosave_every_n_updates == 50


def test_autosave_invalid_non_positive__expects__raises_validation_error(tmp_path):
    # autosave set to 0 should fail due to gt=0 validation
    cfg_text = (
        "search_engine_type: \"solr\"\n"
        "collection_name: \"testcore\"\n"
        "search_engine_url: \"http://localhost:8983/solr/\"\n"
        "number_of_docs: 2\n"
        "doc_fields: [\"title\"]\n"
        "num_queries_needed: 2\n"
        "relevance_scale: \"binary\"\n"
        "llm_configuration_file: \"tests/resources/llm_config.yaml\"\n"
        "output_format: \"quepid\"\n"
        "output_destination: \"output\"\n"
        "datastore_autosave_every_n_updates: 0\n"
    )
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    with pytest.raises(ValidationError):
        _ = Config.load(str(cfg_path))
