import json
import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from rre_tools.dataset_generator.models.query_response import LLMQueryResponse
from rre_tools.dataset_generator.models.score_response import LLMScoreResponse
from rre_tools.shared.models.document import Document
from rre_tools.dataset_generator.models.query_schema import create_queries_schema
from rre_tools.dataset_generator.models.score_schema import BinaryScore, GradedScore

log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    @staticmethod
    def _build_query_generation_prompt(num_queries_generate_per_doc: int, max_query_terms: Optional[int]) -> str:

        prompt_core = (
            f"You are an expert search query analyst. Your task is to generate {num_queries_generate_per_doc} "
            f"unique, high-quality, and *semantically diverse* "
            f"natural language search queries based strictly on the given document."
        )

        rules = [
            "1. **Strictly Relevant:** All queries MUST be based *only* on information present in the document.",
            "2. **Natural:** Queries must sound like a real person searching, not robotic lists of keywords.",
            "3. **Semantically Diverse (CRITICAL):** Each query must target a different *sub-topic, intent, "
            "or angle* of the document."
            "Do NOT generate queries that are just minor variations of each other. "
            "This includes, but is not limited to:",
            "    - Simple plural/singular changes (e.g., 'car' vs 'cars').",
            "    - Minor grammatical changes (e.g., 'extend' vs 'extends').",
            "    - Adding/removing stop-words (e.g., 'a', 'the', 'for').",
            "4. **No Duplicates:** Do not generate identical queries."
        ]

        if max_query_terms is not None:
            rules.append(
                f"5. **Strict Length Limit:** Each query MUST contain *at most* {max_query_terms} words."
                f"Do NOT exceed this limit."
            )

        system_prompt = (
                f"{prompt_core}\n"
                "**CRITICAL RULES:**\n"
                + "\n".join(rules) +
                "\nReturn a structured object matching the provided schema."
        )

        return system_prompt

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int,
                         max_query_terms: Optional[int]) -> LLMQueryResponse:
        """
        Generate queries based on the given document and num_queries_generate_per_doc and max_query_terms. If
        max_query_terms is not None, then the generated query length is at most max_query_terms.
        Returns a list of generated `num_queries_generate_per_doc` queries or throws an exception
        if LLM hallucinates
        """

        log.info(f"Generating up to {num_queries_generate_per_doc} queries for document id={document.id}")

        schema: type[BaseModel] = create_queries_schema(num_queries_generate_per_doc)
        system_prompt = self._build_query_generation_prompt(num_queries_generate_per_doc=num_queries_generate_per_doc,
                                                            max_query_terms=max_query_terms)

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
        for query in model_response.queries:  # type: ignore[union-attr]
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        unique_queries_len = len(unique_queries)
        if unique_queries_len != num_queries_generate_per_doc:
            log.warning(f"Expected {num_queries_generate_per_doc} unique queries, got {unique_queries_len}")

        log.info(f"Generated {unique_queries_len} unique queries for document id={document.id}")

        return LLMQueryResponse(response_content=json.dumps(unique_queries))

    def generate_score(self, document: Document, query: str, relevance_scale: str,
                       explanation: bool = False) -> LLMScoreResponse:
        """
        Generates a relevance score for a given document-query pair using a specified relevance scale.
        If explanation flag is set to true, score explanation is generated as well.
        """

        log.debug(f"Generating a rating for document_id={document.id} and query={query}")

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

        log.debug(f"Generated a rating rating=model_response.score for document_id={document.id} and query={query}")

        return LLMScoreResponse(
            score=model_response.score,  # type: ignore[union-attr]
            scale=relevance_scale,
            explanation=(model_response.explanation if explanation else None)  # type: ignore[union-attr]
        )
