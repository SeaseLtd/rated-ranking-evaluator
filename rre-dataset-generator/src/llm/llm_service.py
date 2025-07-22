from json import JSONDecodeError
from typing import List, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging

from src.model.document import Document
from typing import Union, List

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> Union[List[str], str]:
        """
        Generate queries based on the given document and num_queries_generate_per_doc and
        Returns a list of generated queries or just a generated string in case of LLM hallucination
        """
        system_prompt = (
            f"You are a helpful assistant! Generate {num_queries_generate_per_doc} "
            "queries based on the given document below. " #keyword-phrase-based
            "**Output only** a JSON array of strings—nothing else. "
            "Example format: [\"first query\", \"second query\"]"
        )

        doc_json = document.model_dump_json()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{doc_json}")
        ]

        raw = self.chat_model.invoke(messages).content.strip()

        # in case LLM hallucinates
        try:
            return json.loads(raw)
        except JSONDecodeError:
            log.warning("LLM hallucinated and its response: %s", raw)
            return raw

    def generate_score(self, document: Document, query: str, relevance_scale: str) -> int:
        """
        Generates a relevance score for a given document-query pair using a specified relevance scale.
        """
        if relevance_scale == "binary":
            scale = {0, 1}
            description = (" - 0: the query is NOT relevant to the given document"
                           " - 1: the query is relevant to the given document")
        elif relevance_scale == "graded":
            scale = {0, 1, 2}
            description = (" - 0: the query is NOT relevant to the given document"
                           " - 1: the query may be relevant to the given document"
                           " - 2: the document proposed is the answer to the query")
        else:
            error_msg = "The relevance scale must be either 'binary' or 'graded'"
            log.error(error_msg)
            raise ValueError(error_msg)

        messages = [
            SystemMessage(
                content=f"You are a professional data labeler and, given a documents with a set of fields and a query "
                        f"text, you need to return the relevance score in a scale called {relevance_scale.upper()}. The "
                        f"scores of this scale are built as follows:\n{description}\n"
                        f"Knowing this, return a JSON object with key 'score' and the related score as an integer value."
                        f"I'm expecting a JSON response like the following: {{\"score\": `integer`}}"
            ),
            HumanMessage(
                content=f"Document: {document.model_dump_json()}\n"
                        f"Query:{query}\n"
            )
        ]

        #response = self.chat_model.with_structured_output(method="json_mode").invoke(messages)
        raw = self.chat_model.invoke(messages).content.strip()
        try:
            response =  int(json.loads(raw)['score'])
            if response not in scale:
                error_msg = f"LLM hallucinated the value of the scale. Returned: {response}"
                log.warning(error_msg)
                raise ValueError(error_msg)
            return response
        except JSONDecodeError:
            error_msg = f"LLM hallucinated and its response: {raw}"
            log.warning(error_msg)
            raise ValueError(error_msg)
