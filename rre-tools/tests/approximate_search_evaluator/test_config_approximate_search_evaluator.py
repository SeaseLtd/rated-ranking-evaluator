from pydantic import HttpUrl
from pathlib import Path
from pydantic_core import ValidationError
import pytest

from rre_tools.approximate_search_evaluator.config import Config

# --------------- solr ---------------
def test_good_config_solr__expects__all_parameters_read(resource_folder):
    file_name = resource_folder / "good_config_solr.yaml"
    config = Config.load(resource_folder / file_name)

    assert config.query_template == Path('tests/resources/approximate_search_evaluator/template_solr.json')
    assert config.search_engine_type == "solr"
    assert config.collection_name == "testcore"
    assert config.search_engine_url == HttpUrl("http://localhost:8983/solr/")

    assert config.id_field == "new_id"
    assert config.query_placeholder == "$query_placeholder"
    assert config.search_engine_version == "4.10.4"
    assert config.ratings_path == Path("tests/resources/approximate_search_evaluator/ratings.json")
    assert config.embeddings_folder == Path("tests/resources/approximate_search_evaluator/embeddings")
    assert config.output_destination == Path("solr_resources")

    assert hasattr(config, "conf_sets_filename")
    assert config.conf_sets_filename == "solr-settings.json"

    assert hasattr(config, "collection_name_alias")
    assert config.collection_name_alias == "collectionName"

    assert hasattr(config, "search_engine_url_alias")
    assert config.search_engine_url_alias == "baseUrls"


def test_missing_optional_solr_field_values__expects__all_defaults_read(resource_folder):
    file_name = "missing_optional_solr.yaml"
    config = Config.load(resource_folder / file_name)

    assert hasattr(config, "id_field")
    assert config.id_field == "id"

    assert hasattr(config, "query_placeholder")
    assert config.query_placeholder == "$query"

    assert hasattr(config, "search_engine_version")
    assert config.search_engine_version == "8.3.0"

    assert hasattr(config, "ratings_path")
    assert config.ratings_path is None

    assert hasattr(config, "embeddings_folder")
    assert config.embeddings_folder is None

    assert hasattr(config, "output_destination")
    assert config.output_destination == Path("resources")


@pytest.mark.parametrize("file_name", [
    "missing_query_template.yaml",
    "missing_search_engine_type.yaml",
    "missing_collection_name.yaml",
    "missing_search_engine_url.yaml"
])
def test_missing_non_optional_field__expects__raises_validation_error(resource_folder, file_name):
    with pytest.raises(ValidationError):
        _ = Config.load(resource_folder / file_name)


def test__expects__raises_file_not_found_error(resource_folder):
    file_name = "file_does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        _ = Config.load(resource_folder / file_name)



# --------------- elasticsearch ---------------
def test_good_config_elasticsearch__expects__all_parameters_read(resource_folder):
    config = Config.load(resource_folder / "good_config_elasticsearch.yaml")
    assert config.query_template == Path('tests/resources/approximate_search_evaluator/template_elasticsearch.json')
    assert config.search_engine_type == "elasticsearch"
    assert config.collection_name == "testcore"
    assert config.search_engine_url == HttpUrl("http://localhost:9200/")

    assert config.id_field == "new_id"
    assert config.query_placeholder == "$query_placeholder"
    assert config.search_engine_version == "6.5.4"
    assert config.ratings_path == Path("tests/resources/approximate_search_evaluator/ratings.json")
    assert config.embeddings_folder == Path("tests/resources/approximate_search_evaluator/embeddings")
    assert config.output_destination == Path("elastic_resources")

    assert hasattr(config, "conf_sets_filename")
    assert config.conf_sets_filename == "index-settings.json"

    assert hasattr(config, "collection_name_alias")
    assert config.collection_name_alias == "index"

    assert hasattr(config, "search_engine_url_alias")
    assert config.search_engine_url_alias == "hostUrls"


def test_missing_optional_elasticsearch_field_values__expects__all_defaults_read(resource_folder):
    file_name = "missing_optional_elasticsearch.yaml"
    config = Config.load(resource_folder / file_name)

    assert hasattr(config, "id_field")
    assert config.id_field == "_id"

    assert hasattr(config, "query_placeholder")
    assert config.query_placeholder == "$query"

    assert hasattr(config, "search_engine_version")
    assert config.search_engine_version == "7.4.2"

    assert hasattr(config, "ratings_path")
    assert config.ratings_path is None

    assert hasattr(config, "embeddings_folder")
    assert config.embeddings_folder is None

    assert hasattr(config, "output_destination")
    assert config.output_destination == Path("resources")
