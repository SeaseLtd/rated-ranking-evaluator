from types import SimpleNamespace

from rre_tools.dataset_generator.main import (
    add_cartesian_product_scores,
    expand_docset_with_search_engine_top_k,
    get_queries_within_budget,
)
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.models import Document


class FakeLLMService:
    def __init__(self):
        self.calls = []

    def generate_score(self, document, query, relevance_scale, explanation=False):
        self.calls.append((document.id, query, relevance_scale, explanation))
        return SimpleNamespace(score=1, explanation=None, get_score=lambda: 1)


class FakeSearchEngine:
    def __init__(self):
        self.queries = []

    def fetch_for_evaluation(self, keyword, query_template, doc_fields):
        self.queries.append(keyword)
        return [Document(id=f"doc-{keyword}", fields={"title": [keyword]})]


def _config(**overrides):
    values = {
        "num_queries_needed": 2,
        "query_template": "select * from test where userInput(@kw)",
        "doc_fields": ["title"],
        "relevance_scale": "graded",
        "save_llm_explanation": False,
        "llm_micro_batch_size": 1,
        "llm_batch_max_retries": 3,
        "llm_batch_score_prompt": None,
        "llm_max_workers": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_expand_docset_with_search_engine_top_k__expects__query_budget_respected():
    data_store = DataStore(ignore_saved_data=True)
    for query in ["q1", "q2", "q3"]:
        data_store.add_query(query)

    llm_service = FakeLLMService()
    search_engine = FakeSearchEngine()

    expand_docset_with_search_engine_top_k(_config(), data_store, llm_service, search_engine,
                                           prompt_template="ignored at micro_batch_size=1")

    assert search_engine.queries == ["q1", "q2"]
    assert [call[1] for call in llm_service.calls] == ["q1", "q2"]


def test_add_cartesian_product_scores__expects__query_budget_respected():
    data_store = DataStore(ignore_saved_data=True)
    for query in ["q1", "q2", "q3"]:
        data_store.add_query(query)
    for doc_id in ["d1", "d2"]:
        data_store.add_document(Document(id=doc_id, fields={"title": [doc_id]}, is_used_to_generate_queries=True))

    llm_service = FakeLLMService()

    add_cartesian_product_scores(_config(), data_store, llm_service,
                                 prompt_template="ignored at micro_batch_size=1")

    assert [call[1] for call in llm_service.calls] == ["q1", "q1", "q2", "q2"]


def test_get_queries_within_budget__prioritizes_user_and_category_over_cached():
    """Regression: when the cache is full, fresh user/category queries must still make the cut.

    Pre-fix bug: get_queries_within_budget did `queries[:N]` which is purely positional, so
    cached queries (loaded first into the dict) saturated the budget and category/user queries
    appended later were silently dropped from scoring.
    """
    data_store = DataStore(ignore_saved_data=True)
    for q in ["cached1", "cached2", "cached3"]:
        data_store.add_query(q)  # default 'cached'
    data_store.add_query("user1", source="user")
    data_store.add_query("category1", source="category")

    selected = get_queries_within_budget(_config(num_queries_needed=2), data_store)
    selected_texts = [q.text for q in selected]
    assert selected_texts == ["user1", "category1"]


def test_get_queries_within_budget__within_tier_keeps_insertion_order():
    """Within the same priority tier, the original insertion order is preserved."""
    data_store = DataStore(ignore_saved_data=True)
    data_store.add_query("u_first", source="user")
    data_store.add_query("c_first", source="category")
    data_store.add_query("u_second", source="user")

    selected = get_queries_within_budget(_config(num_queries_needed=3), data_store)
    assert [q.text for q in selected] == ["u_first", "c_first", "u_second"]


def test_get_queries_within_budget__llm_outranks_cached():
    data_store = DataStore(ignore_saved_data=True)
    for q in ["cached1", "cached2"]:
        data_store.add_query(q)
    data_store.add_query("llm1", source="llm")

    selected = get_queries_within_budget(_config(num_queries_needed=1), data_store)
    assert [q.text for q in selected] == ["llm1"]


def test_get_queries_within_budget__truncates_to_num_queries_needed():
    data_store = DataStore(ignore_saved_data=True)
    for q in ["a", "b", "c"]:
        data_store.add_query(q)
    selected = get_queries_within_budget(_config(num_queries_needed=2), data_store)
    assert [q.text for q in selected] == ["a", "b"]
