import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService
from src.model.document import Document
from src.model.llm_schemas import LLMQueryResponse


@pytest.fixture
def example_doc():
    return Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )


def test_llm_service_generate_queries_valid(example_doc):
    fake_llm = FakeListChatModel(responses=['["Toyota", "Best Car"]'])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 2)

    assert isinstance(response, LLMQueryResponse)
    assert response.content_list == ["Toyota", "Best Car"]


def test_llm_service_generate_queries_empty_list(example_doc):
    fake_llm = FakeListChatModel(responses=['[]'])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 0)
    assert isinstance(response, LLMQueryResponse)
    assert response.content_list == []


def test_llm_service_generate_queries_invalid_json(example_doc):
    fake_llm = FakeListChatModel(responses=['not a json'])
    service = LLMService(chat_model=fake_llm)
    with pytest.raises(ValueError, match="Invalid JSON in `content`"):
        service.generate_queries(example_doc, 2)


def test_llm_service_generate_queries_with_empty_string(example_doc):
    fake_llm = FakeListChatModel(responses=['["", " ", "Valid"]'])
    service = LLMService(chat_model=fake_llm)
    with pytest.raises(ValueError, match="must not be empty or only whitespace"):
        service.generate_queries(example_doc, 3)


def test_llm_service_generate_queries_non_string_items(example_doc):
    fake_llm = FakeListChatModel(responses=['["Good", 123, null]'])
    service = LLMService(chat_model=fake_llm)
    with pytest.raises(ValueError, match="must be strings"):
        service.generate_queries(example_doc, 3)