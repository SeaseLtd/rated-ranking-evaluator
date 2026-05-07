from types import SimpleNamespace

from rre_tools.dataset_generator.main import add_cartesian_product_scores, expand_docset_with_search_engine_top_k
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
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_expand_docset_with_search_engine_top_k__expects__query_budget_respected():
    data_store = DataStore(ignore_saved_data=True)
    for query in ["q1", "q2", "q3"]:
        data_store.add_query(query)

    llm_service = FakeLLMService()
    search_engine = FakeSearchEngine()

    expand_docset_with_search_engine_top_k(_config(), data_store, llm_service, search_engine)

    assert search_engine.queries == ["q1", "q2"]
    assert [call[1] for call in llm_service.calls] == ["q1", "q2"]


def test_add_cartesian_product_scores__expects__query_budget_respected():
    data_store = DataStore(ignore_saved_data=True)
    for query in ["q1", "q2", "q3"]:
        data_store.add_query(query)
    for doc_id in ["d1", "d2"]:
        data_store.add_document(Document(id=doc_id, fields={"title": [doc_id]}, is_used_to_generate_queries=True))

    llm_service = FakeLLMService()

    add_cartesian_product_scores(_config(), data_store, llm_service)

    assert [call[1] for call in llm_service.calls] == ["q1", "q1", "q2", "q2"]
