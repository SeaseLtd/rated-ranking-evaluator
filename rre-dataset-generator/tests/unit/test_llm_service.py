from langchain_core.language_models.fake_chat_models import FakeListChatModel
from src.llm.llm_service import LLMService


def test_llm_service_test_connection():
    fake_llm = FakeListChatModel(responses=["Hello, world!"])
    service = LLMService(chat_model=fake_llm)

    response = service.test_connection()
    assert isinstance(response, str)
    assert "Hello, world!" in response

