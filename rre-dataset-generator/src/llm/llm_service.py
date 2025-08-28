import json
from json import JSONDecodeError

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from src.model import LLMQueryResponse, LLMScoreResponse, Document
import logging

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
        response_content = response.content
        if not isinstance(response_content, str):
            response_content = json.dumps(response_content)

        try:
            output = LLMQueryResponse(response_content=response_content)
        except (KeyError, JSONDecodeError, ValueError) as e:
            log.warning(f"LLM unexpected response. Raw output: {response.content}")
            raise ValueError(f"Invalid LLM response: {e}")

        return output

    def generate_score(self, document: Document, query: str, relevance_scale: str,
                       explanation: bool = False) -> LLMScoreResponse:
        """
        Generates a relevance score for a given document-query pair using a specified relevance scale.
        If explanation flag is set to true, score explanation is generated as well.
        """
        if relevance_scale == "binary":
            description = (" - 0: the query is NOT relevant to the given document\n"
                           " - 1: the query is relevant to the given document")
        elif relevance_scale == "graded":
            description = (" - 0: the query is NOT relevant to the given document\n"
                           " - 1: the query may be relevant to the given document\n"
                           " - 2: the document proposed is the answer to the query")
        else:
            msg = f"Invalid relevance scale: {relevance_scale}"
            log.error(msg)
            raise ValueError(msg)

        system_prompt = (f"You are a professional data labeler and, given a document with a set of fields and a query "
                         f"and you need to return the relevance score in a scale called {relevance_scale.upper()}. "
                         f"The scores of this scale are built as follows:\n{description}\n")

        if explanation:
            system_prompt += (
                f"Return ONLY a **valid JSON** object with two keys:"
                " `score`: the related score as an integer value\n"
                " `explanation`: your concise explanation for that score\n"
                f"As an example, I expect a JSON response like the following: "
                f"{{\"score\": \"integer value\",\"explanation\": \"I rated this score because...\" }}"
            )
        else:
            system_prompt += (
                f"Return ONLY a **valid JSON** object with key 'score' and the related score as an integer value."
                f"I expect a JSON response like the following: {{\"score\": \"integer value\"}}"
            )

        messages = [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=f"Document: {document.model_dump_json()}\n"
                        f"Query:{query}\n"
            )
        ]

        response_content = self.chat_model.invoke(messages).content
        if isinstance(response_content, str):
            raw = response_content.strip()
        else:
            raw = json.dumps(response_content)

        try:
            score = json.loads(raw)['score']
            score_explanation = None
            if explanation:
                score_explanation = json.loads(raw)['explanation']
        except (JSONDecodeError, KeyError) as e:
            log.debug(f"LLM unexpected response. Raw output: {raw}")
            raise ValueError(f"Invalid LLM response: {e}")

        try:
            parsed = LLMScoreResponse(score=score, scale=relevance_scale, explanation=score_explanation)
            return parsed
        except ValueError as e:
            log.warning(f"Validation error for score '{score}' on scale '{relevance_scale}': {e}")
            raise e
