import json
from json import JSONDecodeError

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from src.model.query_response import LLMQueryResponse
from src.model.score_response import LLMScoreResponse
import logging

from src.model.document import Document

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> LLMQueryResponse:
        """
        Generate queries based on the given document and num_queries_generate_per_doc and
        Returns a list of generated queries or just a generated string in case of LLM hallucination
        """
        system_prompt = (
            f"You are a helpful assistant! Generate {num_queries_generate_per_doc} "
            "queries based on the given document below. "
            "**Output only** a JSON array of strings—nothing else. "
            "Example format: [\"first query\", \"second query\"]"
        )

        doc_json = document.model_dump_json()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{doc_json}")
        ]

        # The response from invoke is an AIMessage object which contains all the needed info
        response = self.chat_model.invoke(messages)

        try:
           output = LLMQueryResponse(response_content=response.content)
        except (KeyError, JSONDecodeError, ValueError) as e:
            log.warning(f"LLM unexpected response. Raw output: {response.content}")
            raise ValueError(f"Invalid LLM response: {e}")

        return output
    

    def generate_score(self, document: Document, query: str, relevance_scale: str) -> LLMScoreResponse:
        """
        Generates a relevance score for a given document-query pair using a specified relevance scale.
        """
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

        messages = [
            SystemMessage(
                content=f"You are a professional data labeler and, given a documents with a set of fields and a query "
                        f"text, you need to return the relevance score in a scale called {relevance_scale.upper()}. The "
                        f"scores of this scale are built as follows:\n{description}\n"
                        f"Knowing this, ONLY return a **valid JSON** object  with key 'score' "
                        f"and the related score as an integer value."
                        f"I'm expecting a **valid JSON** response like the following: {{\"score\": `integer`}}"
            ),
            HumanMessage(
                content=f"Document: {document.model_dump_json()}\n"
                        f"Query:{query}\n"
            )
        ]

        raw = self.chat_model.invoke(messages).content.strip()

        try:
            score = json.loads(raw)['score']
        except (JSONDecodeError, KeyError) as e:
            log.debug(f"LLM unexpected response. Raw output: {raw}")
            raise ValueError(f"Invalid LLM response: {e}")

        try:
            parsed = LLMScoreResponse(score=score, scale=relevance_scale)
            return parsed
        except ValueError as e:
            log.warning(f"Validation error for score '{score}' on scale '{relevance_scale}': {e}")
            raise e


