import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from rre_tools.dataset_generator.llm import LLMService
from rre_tools.shared.models import Document
from rre_tools.dataset_generator.models import LLMQueryResponse
from llm_mock import FakeChatModelAdapter


@pytest.fixture
def example_doc():
    return Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )


def test_llm_service_generate_queries__expects__valid(example_doc):
    fake_llm = FakeListChatModel(responses=['{"queries": ["Toyota", "Best Car"]}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    response = service.generate_queries(example_doc, 2, None)

    assert isinstance(response, LLMQueryResponse)
    assert response.get_queries() == ["Toyota", "Best Car"]


def test_llm_service_generate_queries__expects__empty_list(example_doc):
    fake_llm = FakeListChatModel(responses=['{"queries":[]}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    response = service.generate_queries(example_doc, 0, None)
    assert response.get_queries() == []


@pytest.mark.parametrize("invalid_response, expected_error", [
    ('not a json', r"Invalid JSON"),
    ('{"queries":["", " ", "Valid"]}', r"(at least 1 character|min_length|String should have at least 1)"),
    ('{"queries":["Good", 123, null]}', r"(valid string|string_type)"),
])
def test_llm_service_generate_queries_with_invalid_responses__expects__error(invalid_response, expected_error, example_doc):
    fake_llm = FakeListChatModel(responses=[invalid_response])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    with pytest.raises(ValueError, match=expected_error):
        service.generate_queries(example_doc, 3, None)


def test_generate_queries_with_unicode_strings__expects__list_of_unicode_strings(example_doc):
    fake_llm = FakeListChatModel(responses=['{"queries":["こんにちは", "你好", "¡Hola!"]}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    response = service.generate_queries(example_doc, 3, None)
    assert response.get_queries() == ["こんにちは", "你好", "¡Hola!"]


def test_generate_queries_with_leading_trailing_whitespace__expects__whitespace_stripped(example_doc):
    fake_llm = FakeListChatModel(responses=['{"queries":["  hello  ", " world "]}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    response = service.generate_queries(example_doc, 2, None)
    assert response.get_queries() == ["hello", "world"]