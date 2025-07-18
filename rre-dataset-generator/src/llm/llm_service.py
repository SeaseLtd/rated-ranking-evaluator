import logging
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.model.document import Document
from src.model.llm_schemas import LLMQueryResponse

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> LLMQueryResponse:
        """
        Generate queries based on the given document, returning a structured response.

        :param document: The document to generate queries from.
        :param num_queries_generate_per_doc: The number of queries to generate.
        :return: An LLMResponse object with the generated content and metadata.
        """
        system_prompt = (
            f"You are a helpful assistant! Generate {num_queries_generate_per_doc} "
            "keyword-phrase-based queries based on the given document below. "
            "**Output only** a JSON array of strings—nothing else. "
            'Example format: ["first query", "second query"]'
        )

        doc_json = document.model_dump_json()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{doc_json}")
        ]

        # The response from invoke is an AIMessage object which contains all the needed info
        response = self.chat_model.invoke(messages)

        # Extract token usage and model name from response metadata
        # usage = response.response_metadata.get("token_usage", {})
        # model_name = response.response_metadata.get("model_name", "unknown")
        # finish_reason = response.response_metadata.get("finish_reason", "unknown")

        output = LLMQueryResponse(
            content=response.content,
            # model=model_name,
            # usage={
            #     "prompt_tokens": usage.get("prompt_tokens", 0),
            #     "completion_tokens": usage.get("completion_tokens", 0),
            #     "total_tokens": usage.get("total_tokens", 0),
            # },
            # finish_reason=finish_reason,
        )
        return output
