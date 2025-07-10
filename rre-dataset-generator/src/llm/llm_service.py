from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def test_connection(self, prompt: str = "Say hello in 5 different languages") -> str:
        """
        Send a test prompt to verify the model returns a response.
        """
        response = self.chat_model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
