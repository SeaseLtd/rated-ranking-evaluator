import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from rre_tools.dataset_generator.llm import LLMService
from rre_tools.core.models import Document
from rre_tools.dataset_generator.models import LLMScoreResponse
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


@pytest.mark.parametrize("scale, valid_score", [
    ("binary", 0),
    ("binary", 1),
    ("graded", 0),
    ("graded", 1),
    ("graded", 2),
])
def test_generate_score_with_valid_scale__expects__integer_score(scale, valid_score, example_doc):
    fake_llm = FakeListChatModel(responses=[f'{{"score": {valid_score}}}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    query = "Is a Toyota the car of the year?"
    response = service.generate_score(example_doc,
                                      query,
                                      relevance_scale=scale,
                                      explanation=False)
    assert isinstance(response, LLMScoreResponse)
    assert response.get_score() == valid_score
    assert response.explanation is None


def test_generate_score__with_invalid_json_response__expects__raises_value_error(example_doc):
    fake_llm = FakeListChatModel(responses=['{malformed-json}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    with pytest.raises(ValueError, match="Invalid LLM response:"):
        service.generate_score(example_doc, "query", relevance_scale="binary", explanation=True)


@pytest.mark.parametrize("scale, valid_score, explanation", [
    ("graded", 0, "The query is clearly not about cars."),
    ("graded", 1, "Camry is a car, so it is relevant."),
    ("graded", 2, "This exactly matches the definition of 'car of the year'."),
])
def test_generate_score_with_valid_explanation__expects__explanation(scale, valid_score, explanation, example_doc):

    llm_output = {"score": valid_score, "explanation": explanation}
    fake_llm = FakeListChatModel(responses=[json.dumps(llm_output)])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))

    response = service.generate_score(
        example_doc,
        "Is a Toyota the car of the year?",
        relevance_scale=scale,
        explanation=True
    )

    assert isinstance(response, LLMScoreResponse)
    assert response.get_score() == valid_score
    assert response.explanation == explanation


@pytest.mark.parametrize("scale, response_json", [
    # Binary scale invalids
    ('binary', 'not a json'),
    ('binary', '{"not_score": 1}'),
    ('binary', '{"score": "one"}'),
    ('binary', '{"score": 3}'),
    # Graded scale invalids
    ('graded', '{"score": -1}'),
    ('graded', '{"score": 1.5}'),
    ('graded', '{"score": null}'),
])
def test_generate_score_with_invalid_llm_responses__expects__raises_value_error(scale, response_json, example_doc):
    fake_llm = FakeListChatModel(responses=[response_json])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    query = "Is a Toyota the car of the year?"

    with pytest.raises(ValueError, match=r"^Invalid LLM response"):
        service.generate_score(example_doc, query, relevance_scale=scale)


def test_generate_score_with_invalid_relevance_scale__expects__raises_value_error(example_doc):
    fake_llm = FakeListChatModel(responses=['{"score": 1}'])
    service = LLMService(chat_model=FakeChatModelAdapter(fake_llm))
    query = "What car won?"
    with pytest.raises(ValueError, match="Invalid relevance scale"):
        service.generate_score(example_doc, query, relevance_scale='fuzzy')
