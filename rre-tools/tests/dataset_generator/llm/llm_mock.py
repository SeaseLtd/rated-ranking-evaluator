from typing import List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult
from pydantic import BaseModel


class _StructuredOutputMockLLM:
    def __init__(self, fake_chat_model, schema: type[BaseModel]):
        self._fake_chat_model = fake_chat_model
        self._schema = schema

    def invoke(self, messages):
        payload = self._fake_chat_model.responses.pop(0)

        if isinstance(payload, self._schema):
            return payload

        if isinstance(payload, dict):
            return self._schema.model_validate(payload)

        if isinstance(payload, str):
            return self._schema.model_validate_json(payload)

        raise TypeError(f"Unexpected fake payload type: {type(payload)}")


class FakeChatModelAdapter(BaseChatModel):
    """Fake adapter for with_structured_output, as the FakeListChatModel doesn't support"""

    def __init__(self, fake_chat_model):
        super().__init__()
        self._fake_chat_model = fake_chat_model

    @property
    def _llm_type(self) -> str:
        return "fake_adapter"

    def _generate(self, messages: List, stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        raise NotImplementedError("_generate is not used in the test")

    def with_structured_output(self, schema: type[BaseModel]):
        return _StructuredOutputMockLLM(self._fake_chat_model, schema)
