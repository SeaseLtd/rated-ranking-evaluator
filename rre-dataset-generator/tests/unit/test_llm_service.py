from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService
from src.model.document import Document


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

