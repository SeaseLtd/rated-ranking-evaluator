from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def test_connection(self, prompt: str) -> str:
        """
        Send a test prompt to verify the model returns a response.
        """
        messages = [
            SystemMessage(
                content="You are a helpful assistant!"
            ),
            HumanMessage(
                content=prompt
            )
        ]

        response = self.chat_model.invoke(messages)
        return response.content.strip()
