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
    assert config.datastore_autosave_every_n_updates == 50
    assert not config.enable_cartesian_product


def test_missing_optional_field_values__expects__all_defaults_read(resource_folder):
    file_name = "missing_optional.yaml"
    config = Config.load(resource_folder / file_name)

    assert hasattr(config, "queries")
    assert config.queries is None

    assert hasattr(config, "query_template")
    assert config.query_template is None

    assert hasattr(config, "datastore_autosave_every_n_updates")
    assert config.datastore_autosave_every_n_updates is None

    assert hasattr(config, "enable_cartesian_product")
    assert config.enable_cartesian_product


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


def test_vespa_config_without_schema__expects__schema_defaults_to_collection_name(tmp_path):
    cfg_text = (
        "search_engine_type: \"vespa\"\n"
        "collection_name: \"movie\"\n"
        "search_engine_url: \"http://localhost:8080/search/\"\n"
        "number_of_docs: 2\n"
        "doc_fields: [\"title\"]\n"
        "num_queries_needed: 2\n"
        "relevance_scale: \"binary\"\n"
        "llm_configuration_file: \"tests/resources/llm_config.yaml\"\n"
        "output_format: \"quepid\"\n"
        "output_destination: \"output\"\n"
    )
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    cfg = Config.load(str(cfg_path))

    assert cfg.vespa_schema == "movie"
    assert cfg.search_engine_collection_endpoint == HttpUrl("http://localhost:8080/search/movie/")


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


_MIN_VALID_CFG = (
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
)


def _write_cfg_with(tmp_path, extra_yaml: str):
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(_MIN_VALID_CFG + extra_yaml, encoding="utf-8")
    return cfg_path


def test_default_llm_micro_batch_size__expects__one(tmp_path):
    cfg = Config.load(str(_write_cfg_with(tmp_path, "")))
    assert cfg.llm_micro_batch_size == 1


def test_default_llm_batch_max_retries__expects__three(tmp_path):
    cfg = Config.load(str(_write_cfg_with(tmp_path, "")))
    assert cfg.llm_batch_max_retries == 3


def test_default_llm_batch_score_prompt__expects__none(tmp_path):
    cfg = Config.load(str(_write_cfg_with(tmp_path, "")))
    assert cfg.llm_batch_score_prompt is None


def test_default_llm_max_workers__expects__one(tmp_path):
    cfg = Config.load(str(_write_cfg_with(tmp_path, "")))
    assert cfg.llm_max_workers == 1


def test_llm_max_workers_zero__expects__raises_validation_error(tmp_path):
    cfg_path = _write_cfg_with(tmp_path, "llm_max_workers: 0\n")
    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))


def test_llm_max_workers_positive__expects__parsed(tmp_path):
    cfg_path = _write_cfg_with(tmp_path, "llm_max_workers: 4\n")
    cfg = Config.load(str(cfg_path))
    assert cfg.llm_max_workers == 4


def test_llm_micro_batch_size_zero__expects__raises_validation_error(tmp_path):
    cfg_path = _write_cfg_with(tmp_path, "llm_micro_batch_size: 0\n")
    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))


def test_llm_batch_max_retries_negative__expects__raises_validation_error(tmp_path):
    cfg_path = _write_cfg_with(tmp_path, "llm_batch_max_retries: -1\n")
    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))


def test_valid_batch_prompt_template__expects__loads(tmp_path):
    prompt = tmp_path / "batch_prompt.txt"
    prompt.write_text(
        "Score the docs on {relevance_scale} for query '{query}'.\n"
        "Documents:\n{documents_json}\n",
        encoding="utf-8",
    )
    cfg_path = _write_cfg_with(tmp_path, f"llm_batch_score_prompt: \"{prompt}\"\n")
    cfg = Config.load(str(cfg_path))
    assert cfg.llm_batch_score_prompt == prompt


def test_batch_prompt_missing_required_placeholder__expects__raises_validation_error(tmp_path):
    # No {documents_json} placeholder.
    prompt = tmp_path / "bad_prompt.txt"
    prompt.write_text("Query: {query}, scale: {relevance_scale}\n", encoding="utf-8")
    cfg_path = _write_cfg_with(tmp_path, f"llm_batch_score_prompt: \"{prompt}\"\n")
    with pytest.raises(ValidationError, match=r"required placeholder"):
        Config.load(str(cfg_path))


def test_batch_prompt_unknown_placeholder__expects__raises_validation_error(tmp_path):
    # Typo: {documents} instead of {documents_json}.
    prompt = tmp_path / "bad_prompt.txt"
    prompt.write_text(
        "Query: {query}\nDocs: {documents}\nScale: {relevance_scale}\n",
        encoding="utf-8",
    )
    cfg_path = _write_cfg_with(tmp_path, f"llm_batch_score_prompt: \"{prompt}\"\n")
    with pytest.raises(ValidationError, match=r"unsupported placeholder"):
        Config.load(str(cfg_path))


def test_batch_prompt_unescaped_json_braces__expects__raises_validation_error(tmp_path):
    # Unescaped JSON example in the template body — classic str.format footgun.
    prompt = tmp_path / "bad_prompt.txt"
    prompt.write_text(
        "Query: {query}\n"
        "Docs (example): {\"id\": 1}\n"
        "Real docs: {documents_json}\n"
        "Scale: {relevance_scale}\n",
        encoding="utf-8",
    )
    cfg_path = _write_cfg_with(tmp_path, f"llm_batch_score_prompt: \"{prompt}\"\n")
    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))


def test_batch_prompt_validated_even_when_batch_size_is_one(tmp_path):
    # The user runs at size=1 today; the broken prompt must still fail at config load
    # so flipping to size=10 tomorrow doesn't blow up at runtime.
    prompt = tmp_path / "bad_prompt.txt"
    prompt.write_text("Only {query}\n", encoding="utf-8")
    cfg_path = _write_cfg_with(
        tmp_path,
        "llm_micro_batch_size: 1\n"
        f"llm_batch_score_prompt: \"{prompt}\"\n",
    )
    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))


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
