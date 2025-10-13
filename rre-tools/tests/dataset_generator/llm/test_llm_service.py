import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from rre_tools.core.models import Document
from rre_tools.dataset_generator.models import LLMQueryResponse, LLMScoreResponse
from rre_tools.dataset_generator.llm import LLMService
from ...mocks.llm_mock import FakeChatModelAdapter


@pytest.fixture
def example_doc():
    """Provides a sample Document object for testing."""
    return Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )


def test_llm_service_generate_queries__expects__response(example_doc):
    # Test that the service can generate queries from a document
    fake_llm = FakeListChatModel(responses=['{"queries": ["Car","Auto","Vehicle","Sedan","Toyota"]}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))

    response = service.generate_queries(example_doc, 5)

    assert isinstance(response, LLMQueryResponse)
    assert response.get_queries() == ["Car","Auto","Vehicle","Sedan","Toyota"]


def test_llm_service_generate_score__expects__response(example_doc):
    fake_llm = FakeListChatModel(responses=['{"score": 1}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))

    query = "Is a Toyota the car of the year?"

    response = service.generate_score(example_doc, query, relevance_scale='binary')

    assert isinstance(response, LLMScoreResponse)
    assert response.get_score() == 1


@pytest.mark.parametrize("invalid_response", [
    '{"score": "one"}',
    '{"score": 3}',
])
def test_llm_service_generate_score_with_invalid_responses__expects__raises_value_error(example_doc, invalid_response):
    fake_llm = FakeListChatModel(responses=[invalid_response])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))

    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError):
        _ = service.generate_score(example_doc, query, relevance_scale='binary')