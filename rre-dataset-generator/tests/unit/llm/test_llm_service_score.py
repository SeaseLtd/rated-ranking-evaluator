import pytest
import json
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
def test_generate_score_with_valid_scale_and_score_EXPECTED_integer_score(scale, valid_score, example_doc):
    fake_llm = FakeListChatModel(responses=[f'{{"score": {valid_score}}}'])
    service = LLMService(chat_model=fake_llm)
    query = "Is a Toyota the car of the year?"
    response = service.generate_score(example_doc, query, relevance_scale=scale)
    assert isinstance(response, int)
    assert response == valid_score


@pytest.mark.parametrize("response_json, expected_error", [
    ('not a json', 'Invalid LLM response'),
    ('{"not_score": 1}', 'Invalid LLM response'),
    ('{"score": "one"}', 'Score must be 0 or 1 for binary scale, got one'),
    ('{"score": 3}', 'Score must be 0 or 1 for binary scale, got 3')
])
def test_generate_score_with_invalid_llm_responses_EXPECTED_value_error(response_json, expected_error, example_doc):
    fake_llm = FakeListChatModel(responses=[response_json])
    service = LLMService(chat_model=fake_llm)
    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError, match=expected_error):
        service.generate_score(example_doc, query, relevance_scale='binary')


@pytest.mark.parametrize("response_json, expected_error", [
    ('{"score": -1}', 'Score must be 0, 1, or 2 for graded scale, got -1'),
    ('{"score": 1.5}', 'Score must be 0, 1, or 2 for graded scale, got 1.5'),
    ('{"score": null}', 'Score must be 0, 1, or 2 for graded scale, got None'),
])
def test_generate_score_with_more_invalid_score_types_EXPECTED_value_error(response_json, expected_error, example_doc):
    fake_llm = FakeListChatModel(responses=[response_json])
    service = LLMService(chat_model=fake_llm)
    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError, match=expected_error):
        service.generate_score(example_doc, query, relevance_scale='graded')


def test_generate_score_with_invalid_relevance_scale_EXPECTED_value_error(example_doc):
    fake_llm = FakeListChatModel(responses=['{"score": 1}'])
    service = LLMService(chat_model=fake_llm)
    query = "What car won?"
    with pytest.raises(ValueError, match="Invalid relevance scale"):
        service.generate_score(example_doc, query, relevance_scale='fuzzy')
