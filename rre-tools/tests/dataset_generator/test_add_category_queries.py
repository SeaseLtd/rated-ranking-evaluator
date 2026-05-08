from pathlib import Path

from rre_tools.dataset_generator.query_sources import add_category_queries
from rre_tools.shared.data_store import DataStore

from tests.dataset_generator.category_query_test_utils import (
    FakeSearchEngine,
    ValueDiscoveryEngine,
    empty_solr_facet_template,
    genre_query_template,
    make_config,
)


def test_add_category_queries__renders_and_dedupes(tmp_path):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy", "action", "comedy"],
             "query_text_template_file": str(template)},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([])

    add_category_queries(cfg, ds, engine)

    texts = sorted(q.text for q in ds.get_queries())
    assert texts == ["action movies", "comedy movies"]


def test_add_category_queries__none_is_noop(tmp_path):
    cfg = make_config(tmp_path, category_queries=None)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([])
    add_category_queries(cfg, ds, engine)
    assert ds.get_queries() == []


def test_add_category_queries__bare_values_when_template_omitted(tmp_path):
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy", "action"]},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([])

    add_category_queries(cfg, ds, engine)

    texts = sorted(q.text for q in ds.get_queries())
    assert texts == ["action", "comedy"]
    assert all(q.source == "category" for q in ds.get_queries())


def test_add_category_queries__engine_discovery_calls_fetch_field_values_once_per_source(tmp_path):
    facet = empty_solr_facet_template(tmp_path)
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values_query_template_file": str(facet)},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = ValueDiscoveryEngine(values_by_field={"genres": ["comedy", "action"]})

    add_category_queries(cfg, ds, engine)

    assert len(engine.calls) == 1
    template_arg, field_arg = engine.calls[0]
    assert Path(template_arg) == facet
    assert field_arg == "genres"
    texts = sorted(q.text for q in ds.get_queries())
    assert texts == ["action", "comedy"]
    assert all(q.source == "category" for q in ds.get_queries())


def test_add_category_queries__engine_discovery_renders_through_query_text_template(tmp_path):
    facet = empty_solr_facet_template(tmp_path)
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values_query_template_file": str(facet),
             "query_text_template_file": str(template)},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = ValueDiscoveryEngine(values_by_field={"genres": ["comedy", "action"]})

    add_category_queries(cfg, ds, engine)

    assert sorted(q.text for q in ds.get_queries()) == ["action movies", "comedy movies"]


def test_add_category_queries__engine_discovery_empty_result_warns_and_skips_source(tmp_path, caplog):
    facet = empty_solr_facet_template(tmp_path)
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values_query_template_file": str(facet)},
            {"fields": ["genres"], "values": ["fallback"],
             "query_text_template_file": str(template)},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = ValueDiscoveryEngine(values_by_field={"genres": []})

    with caplog.at_level("WARNING"):
        add_category_queries(cfg, ds, engine)

    warnings = [r for r in caplog.records if "no values" in r.getMessage()]
    assert len(warnings) == 1
    assert "field='genres'" in warnings[0].getMessage()
    assert any(q.text == "fallback movies" for q in ds.get_queries())


def test_add_category_queries__explicit_values_short_circuit_does_not_call_engine(tmp_path):
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy"]},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([])

    add_category_queries(cfg, ds, engine)

    assert [q.text for q in ds.get_queries()] == ["comedy"]


def test_add_category_queries__rendered_duplicates_dedupe(tmp_path):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy", "comedy "],
             "query_text_template_file": str(template)},
        ],
    )
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([])

    add_category_queries(cfg, ds, engine)

    assert len(ds.get_queries()) == 1
