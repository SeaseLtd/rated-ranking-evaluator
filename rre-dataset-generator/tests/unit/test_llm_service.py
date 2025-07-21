from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService
from src.model.document import Document
import pytest


def test_llm_service_test_connection():
    fake_llm = FakeListChatModel(responses=["Car"])
    service = LLMService(chat_model=fake_llm)

    doc1 = Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )

    response = service.generate_queries(doc1, 5)
    assert isinstance(response, str)
    assert "Car" in response

def test_llm_service_generate_score():
    fake_llm = FakeListChatModel(responses=["{\"score\": 1}"])
    service = LLMService(chat_model=fake_llm)

    doc1 = Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )
    query = "Is a Toyota the car of the year?"

    response = service.generate_score(doc1, query, relevance_scale='binary')

    assert isinstance(response, int)
    assert response == 1

def test_llm_service_generate_score_expected_return_str():
    fake_llm = FakeListChatModel(responses=["{\"score\": \"one\"}"])
    service = LLMService(chat_model=fake_llm)

    doc1 = Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )
    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError):
        _ = service.generate_score(doc1, query, relevance_scale='binary')


def test_llm_service_generate_score_expected_return_not_valid_int():
    fake_llm = FakeListChatModel(responses=["{\"score\": 3}"])
    service = LLMService(chat_model=fake_llm)

    doc1 = Document(
        id="doc1",
        fields={
            "title": "Car of the Year",
            "description": "The Toyota Camry, the nation's most popular car has now been rated as its best new model."
        }
    )
    query = "Is a Toyota the car of the year?"
    with pytest.raises(ValueError):
        _ = service.generate_score(doc1, query, relevance_scale='binary')
