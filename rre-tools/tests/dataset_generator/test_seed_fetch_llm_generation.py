from rre_tools.dataset_generator import main as main_mod
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document

from tests.dataset_generator.category_query_test_utils import (
    FakeLLMService,
    FakeSearchEngine,
    make_config,
)


def test_fetch_and_add_seed_documents__marks_cache_hit_doc_for_cartesian(tmp_path):
    cfg = make_config(tmp_path)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    cached = Document(id="d1", fields={"title": "t"}, is_used_to_generate_queries=False)
    ds.add_document(cached)

    fetched = Document(id="d1", fields={"title": "t"})
    engine = FakeSearchEngine([fetched])

    main_mod.fetch_and_add_seed_documents(cfg, ds, engine)

    assert "d1" in {d.id for d in ds.get_cartesian_prod_docs()}


def test_fetch_and_add_seed_documents__new_docs_flagged(tmp_path):
    cfg = make_config(tmp_path)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    engine = FakeSearchEngine([Document(id="d1", fields={"title": "t1"})])

    main_mod.fetch_and_add_seed_documents(cfg, ds, engine)

    assert ds.get_document("d1").is_used_to_generate_queries is True


def test_generate_and_add_queries_from_documents__cached_queries_do_not_block_llm_gen(tmp_path):
    cfg = make_config(tmp_path, num_queries_needed=2, number_of_docs=1)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    for i in range(5):
        ds.add_query(f"cached{i}")
    seed = Document(id="d1", fields={"title": "t1"}, is_used_to_generate_queries=True)
    ds.add_document(seed)

    llm = FakeLLMService(queries_per_doc={"d1": ["fresh-llm-query"]})

    main_mod.generate_and_add_queries_from_documents(cfg, ds, llm, [seed])

    assert llm.generate_queries_calls == ["d1"]
    fresh = next((q for q in ds.get_queries() if q.text == "fresh-llm-query"), None)
    assert fresh is not None
    assert fresh.source == "llm"


def test_generate_and_add_queries_from_documents__existing_llm_queries_count_against_budget(tmp_path):
    cfg = make_config(tmp_path, num_queries_needed=2, number_of_docs=1)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    ds.add_query("pre-llm-1", source="llm")
    ds.add_query("pre-llm-2", source="llm")
    seed = Document(id="d1", fields={"title": "t1"}, is_used_to_generate_queries=True)
    ds.add_document(seed)

    llm = FakeLLMService(queries_per_doc={"d1": ["should-not-be-generated"]})

    main_mod.generate_and_add_queries_from_documents(cfg, ds, llm, [seed])

    assert llm.generate_queries_calls == []
    assert not any(q.text == "should-not-be-generated" for q in ds.get_queries())


def test_generate_and_add_queries_from_documents__no_extra_llm_call_after_inner_loop_fills_budget(tmp_path):
    cfg = make_config(tmp_path, num_queries_needed=1, number_of_docs=1)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    seed1 = Document(id="d1", fields={"title": "t1"}, is_used_to_generate_queries=True)
    seed2 = Document(id="d2", fields={"title": "t2"}, is_used_to_generate_queries=True)
    ds.add_document(seed1)
    ds.add_document(seed2)

    llm = FakeLLMService(queries_per_doc={"d1": ["q1"], "d2": ["q2"]})

    main_mod.generate_and_add_queries_from_documents(cfg, ds, llm, [seed1, seed2])

    assert llm.generate_queries_calls == ["d1"]


def test_generate_and_add_queries_from_documents__user_and_category_fill_budget_skip_llm(tmp_path):
    cfg = make_config(tmp_path, num_queries_needed=2, number_of_docs=1)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    ds.add_query("u1", source="user")
    ds.add_query("c1", source="category")
    seed = Document(id="d1", fields={"title": "t1"}, is_used_to_generate_queries=True)
    ds.add_document(seed)

    llm = FakeLLMService(queries_per_doc={"d1": ["never-added"]})

    main_mod.generate_and_add_queries_from_documents(cfg, ds, llm, [seed])

    assert llm.generate_queries_calls == []
    assert not any(q.text == "never-added" for q in ds.get_queries())


def test_generate_and_add_queries_from_documents__pre_rates_seed_doc_with_max(tmp_path):
    cfg = make_config(tmp_path, num_queries_needed=2, number_of_docs=1)
    ds = DataStore(path=tmp_path / "ds.json", ignore_saved_data=True)
    seed = Document(id="d1", fields={"title": "t1"}, is_used_to_generate_queries=True)
    ds.add_document(seed)

    llm = FakeLLMService(queries_per_doc={"d1": ["the synthetic query"]})

    main_mod.generate_and_add_queries_from_documents(cfg, ds, llm, [seed])

    queries = ds.get_queries()
    assert any(q.text == "the synthetic query" for q in queries)
    generated = next(q for q in queries if q.text == "the synthetic query")
    rating = ds.rating_by_pair.get((generated.id, "d1"))
    assert rating is not None
    assert rating.score == max(cfg.relevance_label_set)
