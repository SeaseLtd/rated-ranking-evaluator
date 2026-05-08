from pathlib import Path

import pytest
from pydantic_core import ValidationError

from rre_tools.dataset_generator.config import Config


def _base_cfg_kwargs(tmp_path: Path) -> dict:
    """Minimal kwargs for a valid Config; tests override what they need."""
    llm_cfg = tmp_path / "llm_cfg.yaml"
    llm_cfg.write_text("name: mock\nmodel: mock-model\nmax_tokens: 16\n", encoding="utf-8")
    return dict(
        query_template=None,
        search_engine_type="solr",
        collection_name="testcore",
        search_engine_url="http://localhost:8983/solr/",
        documents_filter=None,
        number_of_docs=1,
        doc_fields=["title", "genres"],
        queries=None,
        generate_queries_from_documents=True,
        num_queries_needed=1,
        relevance_scale="graded",
        llm_configuration_file=llm_cfg,
        output_format="quepid",
        output_destination=tmp_path,
        save_llm_explanation=False,
        llm_explanation_destination=None,
        id_field=None,
        rre_query_template=None,
        rre_query_placeholder=None,
        verbose=False,
        datastore_autosave_every_n_updates=None,
        enable_cartesian_product=False,
    )


def _write_template(tmp_path: Path, content: str = "$query movies\n") -> Path:
    template = tmp_path / "genre_query.tmpl"
    template.write_text(content, encoding="utf-8")
    return template


def test_category_queries__valid_config_renders_expected_query_strings(tmp_path):
    template = _write_template(tmp_path)
    cfg = Config(
        **_base_cfg_kwargs(tmp_path),
        category_queries=[
            {"fields": ["genres"], "values": ["comedy", "action"], "query_text_template_file": str(template)},
        ],
    )

    source = cfg.category_queries[0]
    raw = source.query_text_template_file.read_text(encoding="utf-8").strip()
    rendered = [raw.replace(cfg.category_query_placeholder, v) for v in source.values]
    assert rendered == ["comedy movies", "action movies"]


def test_category_queries__vespa_uses_at_kw_placeholder(tmp_path):
    template = _write_template(tmp_path, content="@kw movies\n")
    base = _base_cfg_kwargs(tmp_path)
    base["search_engine_type"] = "vespa"
    base["search_engine_url"] = "http://localhost:8080/search/"
    base["query_template"] = None
    cfg = Config(
        **base,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
        ],
    )
    assert cfg.category_query_placeholder == "@kw"


def test_category_queries__vespa_template_with_dollar_query_fails_validation(tmp_path):
    """Sanity: a Vespa-engine config rejects a template that uses $query (Solr convention)."""
    template = _write_template(tmp_path, content="$query movies\n")
    base = _base_cfg_kwargs(tmp_path)
    base["search_engine_type"] = "vespa"
    base["search_engine_url"] = "http://localhost:8080/search/"
    base["query_template"] = None
    with pytest.raises(ValidationError, match="@kw"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
            ],
        )


def test_category_queries__missing_template_file_fails_validation(tmp_path):
    with pytest.raises(ValidationError):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(tmp_path / "nope.tmpl")},
            ],
        )


def test_category_queries__template_without_placeholder_fails_validation(tmp_path):
    template = _write_template(tmp_path, content="just movies\n")
    with pytest.raises(ValidationError):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
            ],
        )


def test_category_queries__empty_string_in_fields_fails_validation(tmp_path):
    template = _write_template(tmp_path)
    with pytest.raises(ValidationError):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": [" "], "values": ["comedy"], "query_text_template_file": str(template)},
            ],
        )


def test_category_queries__empty_string_in_values_fails_validation(tmp_path):
    template = _write_template(tmp_path)
    with pytest.raises(ValidationError):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values": [""], "query_text_template_file": str(template)},
            ],
        )


def test_category_queries__multiple_fields_rejected(tmp_path):
    template = _write_template(tmp_path)
    with pytest.raises(ValidationError, match="not yet supported"):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {
                    "fields": ["genres", "sub_genres"],
                    "values": ["comedy"],
                    "query_text_template_file": str(template),
                },
            ],
        )


def test_category_queries__field_not_in_doc_fields_fails_validation(tmp_path):
    template = _write_template(tmp_path)
    base = _base_cfg_kwargs(tmp_path)
    base["doc_fields"] = ["title"]  # 'genres' is missing
    with pytest.raises(ValidationError, match="doc_fields"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
            ],
        )


def test_category_queries__omitted_defaults_to_none(tmp_path):
    cfg = Config(**_base_cfg_kwargs(tmp_path))
    assert cfg.category_queries is None


def test_category_queries__template_omitted_uses_bare_values(tmp_path):
    """`query_text_template_file` is optional; without it, each value is the query text directly."""
    cfg = Config(
        **_base_cfg_kwargs(tmp_path),
        category_queries=[
            {"fields": ["genres"], "values": ["comedy", "action"]},
        ],
    )
    assert cfg.category_queries[0].query_text_template_file is None


def test_category_queries__same_path_as_query_template_fails_validation(tmp_path):
    """Pointing query_text_template_file at the engine retrieval template (e.g. a YQL or Solr
    JSON file) is the most common misuse — substitution would dump the engine payload as the
    query string. Reject it explicitly with a clear error."""
    shared = tmp_path / "query_template.yql"
    shared.write_text("select * from movie where userInput($query) LIMIT 2\n", encoding="utf-8")
    base = _base_cfg_kwargs(tmp_path)
    base["query_template"] = str(shared)
    with pytest.raises(ValidationError, match="same file as the engine retrieval"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(shared)},
            ],
        )


def test_category_queries__same_path_as_rre_query_template_fails_validation(tmp_path):
    shared = tmp_path / "rre_query.json"
    shared.write_text('{"q": "$query"}\n', encoding="utf-8")
    base = _base_cfg_kwargs(tmp_path)
    base["query_template"] = None
    base["rre_query_template"] = str(shared)
    with pytest.raises(ValidationError, match="same file as the engine retrieval"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(shared)},
            ],
        )


def test_generate_queries_from_documents__omitted_defaults_to_true(tmp_path):
    base = _base_cfg_kwargs(tmp_path)
    base.pop("generate_queries_from_documents")
    cfg = Config(**base)
    assert cfg.generate_queries_from_documents is True


def test_generate_queries_from_documents__explicit_false_is_respected(tmp_path):
    base = _base_cfg_kwargs(tmp_path)
    base["generate_queries_from_documents"] = False
    cfg = Config(**base)
    assert cfg.generate_queries_from_documents is False


def _write_solr_facet_template(tmp_path: Path) -> Path:
    p = tmp_path / "genre_facet_solr.json"
    p.write_text(
        '{"q": "*:*", "facet": "true", "facet.field": "genres", "facet.limit": 100, "rows": 0}\n',
        encoding="utf-8",
    )
    return p


def test_category_queries__values_and_values_query_template_file_both_set_fails(tmp_path):
    facet = _write_solr_facet_template(tmp_path)
    with pytest.raises(ValidationError, match="exactly one"):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values": ["comedy"], "values_query_template_file": str(facet)},
            ],
        )


def test_category_queries__neither_values_nor_values_query_template_file_fails(tmp_path):
    with pytest.raises(ValidationError, match="exactly one"):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"]},
            ],
        )


def test_category_queries__values_null_with_values_query_template_file_passes(tmp_path):
    facet = _write_solr_facet_template(tmp_path)
    cfg = Config(
        **_base_cfg_kwargs(tmp_path),
        category_queries=[
            {"fields": ["genres"], "values": None, "values_query_template_file": str(facet)},
        ],
    )
    assert cfg.category_queries[0].values is None
    assert cfg.category_queries[0].values_query_template_file is not None


def test_category_queries__values_null_and_values_query_template_file_null_fails(tmp_path):
    with pytest.raises(ValidationError, match="exactly one"):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values": None, "values_query_template_file": None},
            ],
        )


def test_category_queries__values_query_template_file_at_query_template_path_fails(tmp_path):
    """values_query_template_file pointing at top-level query_template (engine retrieval payload)."""
    shared = tmp_path / "query_template.json"
    shared.write_text('{"q": "$query"}\n', encoding="utf-8")
    base = _base_cfg_kwargs(tmp_path)
    base["query_template"] = str(shared)
    with pytest.raises(ValidationError, match="value-discovery"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values_query_template_file": str(shared)},
            ],
        )


def test_category_queries__values_query_template_file_at_rre_query_template_path_fails(tmp_path):
    shared = tmp_path / "rre_query.json"
    shared.write_text('{"q": "$query"}\n', encoding="utf-8")
    base = _base_cfg_kwargs(tmp_path)
    base["query_template"] = None
    base["rre_query_template"] = str(shared)
    with pytest.raises(ValidationError, match="value-discovery"):
        Config(
            **base,
            category_queries=[
                {"fields": ["genres"], "values_query_template_file": str(shared)},
            ],
        )


def test_category_queries__values_query_template_file_same_as_query_text_template_file_fails(tmp_path):
    """Three-way collision check: values_query_template_file must not equal
    query_text_template_file on the same source."""
    shared = tmp_path / "shared.json"
    shared.write_text('{"q": "*:*"}\n', encoding="utf-8")
    with pytest.raises(ValidationError, match="different concepts"):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {
                    "fields": ["genres"],
                    "values_query_template_file": str(shared),
                    "query_text_template_file": str(shared),
                },
            ],
        )


def test_category_queries__values_query_template_file_missing_path_fails(tmp_path):
    with pytest.raises(ValidationError):
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {"fields": ["genres"], "values_query_template_file": str(tmp_path / "nope.json")},
            ],
        )


def test_check_no_empty_values__accepts_none_after_values_made_optional(tmp_path):
    """Regression: when values is `None` (engine-discovery mode) the field validator must not crash."""
    facet = _write_solr_facet_template(tmp_path)
    # If `check_no_empty_values` doesn't accept None, this would raise during model construction.
    Config(
        **_base_cfg_kwargs(tmp_path),
        category_queries=[
            {"fields": ["genres"], "values_query_template_file": str(facet)},
        ],
    )


def test_path_collision_validator_runs_before_placeholder_content_validator(tmp_path):
    """Pointing query_text_template_file at a value-discovery JSON file must produce the
    informative 'different concepts' error, not a misleading 'missing placeholder' one.

    Without correct validator ordering, placeholder validation runs first and complains that
    the JSON file is missing `$query`, masking the actual mistake.
    """
    shared = tmp_path / "shared.json"
    shared.write_text('{"q": "*:*"}\n', encoding="utf-8")
    with pytest.raises(ValidationError) as exc:
        Config(
            **_base_cfg_kwargs(tmp_path),
            category_queries=[
                {
                    "fields": ["genres"],
                    "values_query_template_file": str(shared),
                    "query_text_template_file": str(shared),
                },
            ],
        )
    msg = str(exc.value)
    assert "different concepts" in msg
    assert "must contain the literal placeholder" not in msg


def test_generate_queries_from_documents__null_fails_validation(tmp_path):
    cfg_text = (
        'search_engine_type: "solr"\n'
        'collection_name: "testcore"\n'
        'search_engine_url: "http://localhost:8983/solr/"\n'
        'number_of_docs: 1\n'
        'doc_fields: ["title"]\n'
        'num_queries_needed: 1\n'
        'relevance_scale: "graded"\n'
        'llm_configuration_file: "tests/resources/llm_config.yaml"\n'
        'output_format: "quepid"\n'
        'output_destination: "output"\n'
        'generate_queries_from_documents: null\n'
    )
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    with pytest.raises(ValidationError):
        Config.load(str(cfg_path))
