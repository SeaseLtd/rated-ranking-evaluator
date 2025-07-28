import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService
from src.model.document import Document
from src.model.query_response import LLMQueryResponse


@pytest.fixture
def example_doc():
    return Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )


def test_llm_service_generate_queries_EXPECTED_valid(example_doc):
    fake_llm = FakeListChatModel(responses=['["Toyota", "Best Car"]'])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 2)

    assert isinstance(response, LLMQueryResponse)
    assert response.get_queries() == ["Toyota", "Best Car"]


def test_llm_service_generate_queries_EXPECTED_empty_list(example_doc):
    fake_llm = FakeListChatModel(responses=['[]'])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 0)
    assert response.get_queries() == []


@pytest.mark.parametrize("invalid_response, expected_error", [
    ('not a json', "Invalid JSON in `response_content`"),
    ('["", " ", "Valid"]', "must not be empty or only whitespace"),
    ('["Good", 123, null]', "must be strings"),
])
def test_llm_service_generate_queries_with_invalid_responses_EXPECTED_error(invalid_response, expected_error, example_doc):
    fake_llm = FakeListChatModel(responses=[invalid_response])
    service = LLMService(chat_model=fake_llm)
    with pytest.raises(ValueError, match=expected_error):
        service.generate_queries(example_doc, 3)


def test_generate_queries_with_unicode_strings_EXPECTED_list_of_unicode_strings(example_doc):
    unicode_list = '["こんにちは", "你好", "¡Hola!"]'
    fake_llm = FakeListChatModel(responses=[unicode_list])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 3)
    assert response.get_queries() == ["こんにちは", "你好", "¡Hola!"]


def test_generate_queries_with_leading_trailing_whitespace_EXPECTED_strings_preserved(example_doc):
    list_with_whitespace = '["  hello  ", " world "]'
    fake_llm = FakeListChatModel(responses=[list_with_whitespace])
    service = LLMService(chat_model=fake_llm)
    response = service.generate_queries(example_doc, 2)
    assert response.get_queries() == ["  hello  ", " world "]