import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from rre_tools.dataset_generator.models.query_response import LLMQueryResponse
from rre_tools.dataset_generator.models.score_response import LLMScoreResponse
from rre_tools.core.models.document import Document
from rre_tools.dataset_generator.models.query_schema import create_queries_schema
from rre_tools.dataset_generator.models.score_schema import BinaryScore, GradedScore

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> LLMQueryResponse:
        """
        Generate queries based on the given document and num_queries_generate_per_doc and
        Returns a list of generated `num_queries_generate_per_doc` queries or throws an exception if LLM hallucinates
        """
        schema: type[BaseModel] = create_queries_schema(num_queries_generate_per_doc)

        system_prompt = (
            f"You are a helpful assistant! Generate {num_queries_generate_per_doc} "
            "natural language search queries based strictly on the given document."
            "Avoid duplicates. Return a structured object matching the provided schema."
        )

        doc_json = document.model_dump_json(exclude={"is_used_to_generate_queries"})

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{doc_json}")
        ]

        # Use LangChain structured output
        structured_llm = self.chat_model.with_structured_output(schema)
        try:
            model_response = structured_llm.invoke(messages)
        except (ValidationError, KeyError) as e:
            log.debug("Invalid LLM response.")
            raise ValueError(f"Invalid LLM response: {e}")

        # Remove duplicate generated-queries
        seen = set()
        unique_queries: list[str] = []
        for query in model_response.queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        unique_queries_len = len(unique_queries)
        if unique_queries_len != num_queries_generate_per_doc:
            log.warning(f"Expected {num_queries_generate_per_doc} unique queries, got {unique_queries_len}")

        return LLMQueryResponse(response_content=json.dumps(unique_queries))

    def generate_score(self, document: Document, query: str, relevance_scale: str,
                       explanation: bool = False) -> LLMScoreResponse:
        """
        Generates a relevance score for a given document-query pair using a specified relevance scale.
        If explanation flag is set to true, score explanation is generated as well.
        """
        if relevance_scale not in {"binary", "graded"}:
            raise ValueError(f"Invalid relevance scale: {relevance_scale}")

        schema: type[BaseModel] = BinaryScore if relevance_scale == "binary" else GradedScore

        system_prompt = (f"You are a professional data labeler and, given a document with a set of fields and a query "
                         f"and you need to return the relevance score in a scale called {relevance_scale.upper()}. "
                         " Return a structured object matching the provided schema.")
        if explanation:
            system_prompt += (
                " Include a clear explanation justifying your score "
                "in the `explanation` field based on the provided schema."
            )
        else:
            system_prompt += (
                " Do not include any explanation."
            )

        messages = [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=f"Document: {document.model_dump_json(exclude={'is_used_to_generate_queries'})}\n"
                        f"Query:{query}\n"
            )
        ]

        # Use LangChain structured output
        structured_llm = self.chat_model.with_structured_output(schema)
        try:
            model_response = structured_llm.invoke(messages)
        except (ValidationError, KeyError) as e:
            log.debug("Invalid LLM response.")
            raise ValueError(f"Invalid LLM response: {e}")

        return LLMScoreResponse(
            score=model_response.score,
            scale=relevance_scale,
            explanation=(model_response.explanation if explanation else None)
        )
