from rre_tools.dataset_generator import main as main_mod
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document

from tests.dataset_generator.category_query_test_utils import (
    FakeLLMService,
    FakeSearchEngine,
    genre_query_template,
    make_config,
    patch_main_dependencies,
)


def test_main__category_only_skips_llm_gen_and_still_fetches_seeds_for_cartesian(tmp_path, monkeypatch):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=False,
        enable_cartesian_product=True,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
        ],
    )

    seed_doc = Document(id="d1", fields={"title": "Some movie", "genres": ["comedy"]})
    engine = FakeSearchEngine([seed_doc])
    llm = FakeLLMService()

    patch_main_dependencies(monkeypatch, cfg, engine, llm)

    captured = {}

    class _DataStoreCapture(DataStore):
        def __init__(self, *a, **kw):
            super().__init__(path=tmp_path / "ds.json", ignore_saved_data=True,
                             autosave_every_n_updates=kw.get("autosave_every_n_updates"))
            captured["ds"] = self

    monkeypatch.setattr(main_mod, "DataStore", _DataStoreCapture)

    main_mod.main()

    ds = captured["ds"]
    assert any(q.text == "comedy movies" for q in ds.get_queries())
    assert engine.fetch_calls == 1
    assert "d1" in {d.id for d in ds.get_cartesian_prod_docs()}
    assert llm.generate_queries_calls == []


def test_main__engine_discovery_with_cartesian_produces_ratings(tmp_path, monkeypatch):
    facet = tmp_path / "facet_solr.json"
    facet.write_text('{"q": "*:*", "facet": "true", "facet.field": "genres", "rows": 0}\n', encoding="utf-8")
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=False,
        enable_cartesian_product=True,
        category_queries=[
            {"fields": ["genres"], "values_query_template_file": str(facet),
             "query_text_template_file": str(template)},
        ],
    )

    seed_doc = Document(id="d1", fields={"title": "Some movie", "genres": ["comedy"]})

    class _DiscoveryEngine:
        def __init__(self):
            self.fetch_calls = 0
            self.value_calls = 0

        def fetch_for_query_generation(self, documents_filter, number_of_docs, doc_fields):
            self.fetch_calls += 1
            return [seed_doc]

        def fetch_field_values(self, values_query_template, field):
            self.value_calls += 1
            return ["comedy"]

    engine = _DiscoveryEngine()
    llm = FakeLLMService(score=2)

    patch_main_dependencies(monkeypatch, cfg, engine, llm, stub_cartesian=False)

    captured = {}

    class _DataStoreCapture(DataStore):
        def __init__(self, *a, **kw):
            super().__init__(path=tmp_path / "ds.json", ignore_saved_data=True,
                             autosave_every_n_updates=kw.get("autosave_every_n_updates"))
            captured["ds"] = self

    monkeypatch.setattr(main_mod, "DataStore", _DataStoreCapture)

    main_mod.main()

    ds = captured["ds"]
    category_query = next(q for q in ds.get_queries() if q.text == "comedy movies")

    assert engine.value_calls == 1
    assert engine.fetch_calls == 1
    assert llm.generate_score_calls == [("d1", "comedy movies")]
    rating = ds.rating_by_pair.get((category_query.id, "d1"))
    assert rating is not None
    assert rating.score == 2


def test_main__category_query_rated_against_seed_doc_via_cartesian(tmp_path, monkeypatch):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=False,
        enable_cartesian_product=True,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
        ],
    )

    seed_doc = Document(id="d1", fields={"title": "Some movie", "genres": ["comedy"]})
    engine = FakeSearchEngine([seed_doc])
    llm = FakeLLMService(score=2)

    patch_main_dependencies(monkeypatch, cfg, engine, llm, stub_cartesian=False)

    captured = {}

    class _DataStoreCapture(DataStore):
        def __init__(self, *a, **kw):
            super().__init__(path=tmp_path / "ds.json", ignore_saved_data=True,
                             autosave_every_n_updates=kw.get("autosave_every_n_updates"))
            captured["ds"] = self

    monkeypatch.setattr(main_mod, "DataStore", _DataStoreCapture)

    main_mod.main()

    ds = captured["ds"]
    category_query = next(q for q in ds.get_queries() if q.text == "comedy movies")

    assert llm.generate_score_calls == [("d1", "comedy movies")]
    rating = ds.rating_by_pair.get((category_query.id, "d1"))
    assert rating is not None
    assert rating.score == 2


def test_main__both_flags_off_does_not_call_search_engine(tmp_path, monkeypatch):
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=False,
        enable_cartesian_product=False,
    )

    engine = FakeSearchEngine([Document(id="d1", fields={"title": "t"})])
    llm = FakeLLMService()

    patch_main_dependencies(monkeypatch, cfg, engine, llm)
    monkeypatch.setattr(main_mod, "DataStore",
                        lambda **kw: DataStore(path=tmp_path / "ds.json", ignore_saved_data=True,
                                               autosave_every_n_updates=kw.get("autosave_every_n_updates")))

    main_mod.main()

    assert engine.fetch_calls == 0
    assert llm.generate_queries_calls == []


def test_main__llm_gen_reuses_seed_docs_no_double_fetch(tmp_path, monkeypatch):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=True,
        enable_cartesian_product=True,
        category_queries=[
            {"fields": ["genres"], "values": ["comedy"], "query_text_template_file": str(template)},
        ],
        num_queries_needed=10,
        number_of_docs=1,
    )

    seed = Document(id="d1", fields={"title": "Some movie", "genres": ["comedy"]})
    engine = FakeSearchEngine([seed])
    llm = FakeLLMService(queries_per_doc={"d1": ["q-from-doc"]})

    patch_main_dependencies(monkeypatch, cfg, engine, llm)
    monkeypatch.setattr(main_mod, "DataStore",
                        lambda **kw: DataStore(path=tmp_path / "ds.json", ignore_saved_data=True,
                                               autosave_every_n_updates=kw.get("autosave_every_n_updates")))

    main_mod.main()

    assert engine.fetch_calls == 1
    assert llm.generate_queries_calls == ["d1"]


def test_main__category_fills_budget_then_llm_gen_skipped(tmp_path, monkeypatch):
    template = genre_query_template(tmp_path)
    cfg = make_config(
        tmp_path,
        generate_queries_from_documents=True,
        enable_cartesian_product=True,
        category_queries=[
            {"fields": ["genres"],
             "values": ["comedy", "action", "horror"],
             "query_text_template_file": str(template)},
        ],
        num_queries_needed=2,
        number_of_docs=1,
    )

    engine = FakeSearchEngine([Document(id="d1", fields={"title": "t", "genres": ["comedy"]})])
    llm = FakeLLMService(queries_per_doc={"d1": ["should-not-be-added"]})

    patch_main_dependencies(monkeypatch, cfg, engine, llm)
    monkeypatch.setattr(main_mod, "DataStore",
                        lambda **kw: DataStore(path=tmp_path / "ds.json", ignore_saved_data=True,
                                               autosave_every_n_updates=kw.get("autosave_every_n_updates")))

    main_mod.main()

    assert engine.fetch_calls == 1
    assert llm.generate_queries_calls == []
