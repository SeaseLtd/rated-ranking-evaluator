import json
import logging
import random
import time
from typing import Dict, Iterable, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from rre_tools.dataset_generator.models.query_response import LLMQueryResponse
from rre_tools.dataset_generator.models.score_response import LLMScoreResponse
from rre_tools.shared.models.document import Document
from rre_tools.dataset_generator.models.query_schema import create_queries_schema
from rre_tools.dataset_generator.models.score_schema import (
    BinaryBatchScore,
    BinaryScore,
    GradedBatchScore,
    GradedScore,
)

log = logging.getLogger(__name__)

# Base delay for exponential backoff between batch retries (seconds). The
# delay for retry attempt `n` (0-indexed) is `_BATCH_RETRY_BASE_SECONDS * 2**n`
# plus jitter in `[0, _BATCH_RETRY_BASE_SECONDS)`.
_BATCH_RETRY_BASE_SECONDS: float = 1.0


class _BatchResponseContractError(ValueError):
    """Internal marker for missing / unknown / duplicate doc_id failures.

    Used purely to populate ``BatchScoringError.__cause__`` for response-shape
    failures so the chained-traceback story is consistent with the
    invocation-failure path. Not part of the public API — callers always see
    ``BatchScoringError`` and read its ``reason`` / ``__cause__`` attributes.
    """


class BatchScoringError(RuntimeError):
    """Raised when a batch scoring call cannot be made clean within retries.

    Carries the query id, the doc ids that were asked for, the batch size, and
    the number of attempts made — useful for log lines and any future rerun
    tooling. The underlying cause is chained via ``raise ... from e``.
    """

    def __init__(
        self,
        query_id: str,
        asked_doc_ids: List[str],
        attempts: int,
        reason: str,
    ):
        self.query_id = query_id
        self.asked_doc_ids = list(asked_doc_ids)
        self.batch_size = len(self.asked_doc_ids)
        self.attempts = attempts
        self.reason = reason
        super().__init__(
            f"Batch scoring failed for query_id={query_id} after {attempts} "
            f"attempt(s) on a batch of {self.batch_size} doc(s): {reason}"
        )


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

    @staticmethod
    def _rating_scale_description(relevance_scale: str) -> str:
        if relevance_scale == "binary":
            return "Scale: 0 = not relevant, 1 = relevant."
        return (
            "Scale: 0 = not relevant, 1 = maybe relevant, 2 = exact / strong match."
        )

    @staticmethod
    def _explanation_instruction(explanation: bool) -> str:
        if explanation:
            return (
                "For each item include a clear explanation justifying the score "
                "in the 'explanation' field."
            )
        return "Do not include any explanation."

    @staticmethod
    def _render_documents_json(documents: Iterable[Document]) -> str:
        items = [{"doc_id": doc.id, "fields": doc.fields} for doc in documents]
        return json.dumps(items, ensure_ascii=False)

    def generate_scores_batch(
        self,
        query_id: str,
        query_text: str,
        documents: List[Document],
        relevance_scale: str,
        explanation: bool,
        prompt_template: str,
        max_retries: int,
    ) -> Dict[str, LLMScoreResponse]:
        """Score multiple docs against a single query in one LLM call.

        On success returns a dict keyed by doc.id with one entry per requested
        doc. Any of: outright invocation failure (validation error, network /
        rate-limit error), missing doc_id, unknown doc_id, or duplicate doc_id
        in the response triggers a whole-batch retry with exponential backoff.
        After ``max_retries`` additional attempts on top of the initial call
        the batch is still not clean → raises :class:`BatchScoringError`.

        ``query_id`` is carried for log / error context only; it is *not* sent
        to the LLM. Only ``query_text`` and the documents go into the prompt.
        """
        if relevance_scale not in {"binary", "graded"}:
            raise ValueError(f"Invalid relevance scale: {relevance_scale}")
        if not documents:
            return {}

        schema: type[BaseModel] = (
            GradedBatchScore if relevance_scale == "graded" else BinaryBatchScore
        )
        asked_ids: List[str] = [doc.id for doc in documents]
        asked_id_set = set(asked_ids)
        documents_json = self._render_documents_json(documents)
        rendered_prompt = prompt_template.format(
            query=query_text,
            documents_json=documents_json,
            relevance_scale=relevance_scale,
            explanation_instruction=self._explanation_instruction(explanation),
            rating_scale_description=self._rating_scale_description(relevance_scale),
        )
        messages = [HumanMessage(content=rendered_prompt)]
        structured_llm = self.chat_model.with_structured_output(schema)

        last_reason = "no attempts made"
        # `last_exc` carries the cause for the eventual `raise ... from`.
        # Invocation failures land here as the real provider exception;
        # response-contract failures land here as a synthetic
        # `_BatchResponseContractError` so the final BatchScoringError has a
        # uniform `__cause__` regardless of failure class — keeps tracebacks
        # and any tooling that inspects `.__cause__` consistent across the
        # four conditions in the response-id contract.
        last_exc: Optional[BaseException] = None
        total_attempts = max_retries + 1
        for attempt in range(total_attempts):
            try:
                model_response = structured_llm.invoke(messages)
            except Exception as e:  # ValidationError, network, rate-limit, ...
                last_exc = e
                last_reason = f"invocation failure: {type(e).__name__}: {e}"
                log.warning(
                    "[generate_scores_batch] %s query_id=%s batch_size=%d attempt=%d/%d",
                    last_reason, query_id, len(asked_ids), attempt + 1, total_attempts,
                )
                if attempt < total_attempts - 1:
                    self._sleep_backoff(attempt)
                continue

            returned_ids = [item.doc_id for item in model_response.ratings]  # type: ignore[union-attr]
            returned_id_set = set(returned_ids)

            if len(returned_ids) != len(returned_id_set):
                duplicates = sorted(
                    {rid for rid in returned_ids if returned_ids.count(rid) > 1}
                )
                last_reason = f"duplicate doc_id(s) in response: {duplicates}"
                last_exc = _BatchResponseContractError(last_reason)
            elif missing := asked_id_set - returned_id_set:
                last_reason = f"missing doc_id(s) in response: {sorted(missing)}"
                last_exc = _BatchResponseContractError(last_reason)
            elif unknown := returned_id_set - asked_id_set:
                last_reason = f"unknown doc_id(s) in response: {sorted(unknown)}"
                last_exc = _BatchResponseContractError(last_reason)
            else:
                # Clean response: build the result dict.
                result: Dict[str, LLMScoreResponse] = {}
                for item in model_response.ratings:  # type: ignore[union-attr]
                    result[item.doc_id] = LLMScoreResponse(
                        score=item.score,
                        scale=relevance_scale,
                        explanation=(item.explanation if explanation else None),
                    )
                return result

            log.warning(
                "[generate_scores_batch] %s query_id=%s batch_size=%d attempt=%d/%d",
                last_reason, query_id, len(asked_ids), attempt + 1, total_attempts,
            )
            if attempt < total_attempts - 1:
                self._sleep_backoff(attempt)

        err = BatchScoringError(
            query_id=query_id,
            asked_doc_ids=asked_ids,
            attempts=total_attempts,
            reason=last_reason,
        )
        raise err from last_exc

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        """Sleep for `base * 2**attempt` seconds plus jitter in `[0, base)`."""
        delay = _BATCH_RETRY_BASE_SECONDS * (2 ** attempt) + random.uniform(
            0, _BATCH_RETRY_BASE_SECONDS
        )
        time.sleep(delay)
