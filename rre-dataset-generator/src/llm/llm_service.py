from json import JSONDecodeError

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from src.model.llm_schemas import LLMQueryResponse, LLMScoreResponse
import json
import logging

from src.model.document import Document

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> LLMQueryResponse:
        """Generates queries based on the given document.

        Args:
            document: The document to generate queries from.
            num_queries_generate_per_doc: The number of queries to generate.

        Returns:
            An LLMQueryResponse object containing the generated queries and metadata.
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

        output = LLMQueryResponse(content=response.content)
        return output
    

    def generate_score(self, document: Document, query: str, relevance_scale: str) -> int:
        if relevance_scale == "binary":
            allowed = {0, 1}
            description = (" - 0: the query is NOT relevant to the given document\n"
                        " - 1: the query is relevant to the given document")
        elif relevance_scale == "graded":
            allowed = {0, 1, 2}
            description = (" - 0: the query is NOT relevant to the given document\n"
                        " - 1: the query may be relevant to the given document\n"
                        " - 2: the document proposed is the answer to the query")
        else:
            msg = f"Invalid relevance scale: {relevance_scale}"
            log.error(msg)
            raise ValueError(msg)

        system_prompt = (
            f"You are a professional data labeler.\n"
            f"Given a document and a query, return the relevance score using the {relevance_scale.upper()} scale:\n"
            f"{description}\n"
            f"Expected JSON format: {{\"score\": integer}}"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{document.model_dump_json()}\n\nQuery:\n{query}")
        ]

        raw = self.chat_model.invoke(messages).content.strip()

        try:
            parsed = LLMScoreResponse(score=json.loads(raw)['score'])
        except (KeyError, JSONDecodeError, ValueError) as e:
            log.warning(f"LLM hallucinated. Raw output: {raw}")
            raise ValueError(f"Invalid LLM response: {e}")

        if parsed.score not in allowed:
            msg = f"Score '{parsed.score}' is not valid in {relevance_scale} scale"
            log.warning(msg)
            raise ValueError(msg)

        return parsed.score