import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService
from src.model.document import Document


@pytest.fixture
def example_doc():
    return Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )


@pytest.mark.parametrize("scale, valid_score", [
    ("binary", 0),
    ("binary", 1),
    ("graded", 0),
    ("graded", 1),
    ("graded", 2),
])
def test_llm_service_generate_score_valid(scale, valid_score, example_doc):
    fake_llm = FakeListChatModel(responses=[f'{{"score": {valid_score}}}'])
    service = LLMService(chat_model=fake_llm)
    query = "Is a Toyota the car of the year?"
    response = service.generate_score(example_doc, query, relevance_scale=scale)
    assert isinstance(response, int)
    assert response == valid_score


@pytest.mark.parametrize("response_json", [
    'not a json',
    '{"not_score": 1}',
    '{"score": "one"}',
    '{"score": 3}'
])
def test_llm_service_generate_score_invalid_responses(response_json, example_doc):
    fake_llm = FakeListChatModel(responses=[response_json])
    service = LLMService(chat_model=fake_llm)
    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError):
        service.generate_score(example_doc, query, relevance_scale='binary')


def test_llm_service_generate_score_invalid_scale(example_doc):
    fake_llm = FakeListChatModel(responses=['{"score": 1}'])
    service = LLMService(chat_model=fake_llm)
    query = "What car won?"
    with pytest.raises(ValueError, match="Invalid relevance scale"):
        service.generate_score(example_doc, query, relevance_scale='fuzzy')
