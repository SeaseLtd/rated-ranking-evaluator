"""Tests for `LLMService.generate_scores_batch` and `BatchScoringError`."""
from __future__ import annotations

import json
from typing import List

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from rre_tools.dataset_generator.llm import (
    BatchScoringError,
    DEFAULT_BATCH_SCORE_PROMPT,
    LLMService,
)
from rre_tools.dataset_generator.models import LLMScoreResponse
from rre_tools.shared.models import Document

from llm_mock import FakeChatModelAdapter


@pytest.fixture
def docs() -> List[Document]:
    return [
        Document(id=f"d{i}", fields={"title": f"Title {i}"}) for i in range(10)
    ]


def _make_service(responses):
    fake_llm = FakeListChatModel(responses=list(responses))
    return LLMService(chat_model=FakeChatModelAdapter(fake_llm))


def _clean_response(doc_ids, explanation: bool = False, score: int = 1) -> str:
    items = []
    for did in doc_ids:
        item: dict = {"doc_id": did, "score": score}
        if explanation:
            item["explanation"] = f"why {did}"
        items.append(item)
    return json.dumps({"ratings": items})


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Default to instant sleeps for unit tests."""
    monkeypatch.setattr(
        "rre_tools.dataset_generator.llm.llm_service.time.sleep", lambda _d: None
    )


def test_generate_scores_batch__happy_path__maps_scores_by_doc_id(docs):
    response = _clean_response([d.id for d in docs], score=1)
    service = _make_service([response])

    out = service.generate_scores_batch(
        query_id="q1", query_text="hello", documents=docs,
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == {d.id for d in docs}
    for d in docs:
        assert isinstance(out[d.id], LLMScoreResponse)
        assert out[d.id].get_score() == 1
        assert out[d.id].explanation is None


def test_generate_scores_batch__shuffled_response__still_maps_by_doc_id(docs):
    shuffled_ids = list(reversed([d.id for d in docs]))
    response = _clean_response(shuffled_ids, score=2)
    service = _make_service([response])

    out = service.generate_scores_batch(
        query_id="q1", query_text="hi", documents=docs,
        relevance_scale="graded", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == {d.id for d in docs}
    assert all(out[did].get_score() == 2 for did in (d.id for d in docs))


def test_generate_scores_batch__missing_doc_id_then_clean__retries_and_succeeds(docs):
    asked = [d.id for d in docs]
    bad = _clean_response(asked[:-1])  # missing the last one
    good = _clean_response(asked)
    service = _make_service([bad, good])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs,
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == set(asked)


def test_generate_scores_batch__unknown_doc_id_then_clean__retries_and_succeeds(docs):
    asked = [d.id for d in docs]
    bad = _clean_response(asked + ["hallucinated-id"])
    good = _clean_response(asked)
    service = _make_service([bad, good])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs,
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == set(asked)


def test_generate_scores_batch__duplicate_doc_id_then_clean__retries_and_succeeds(docs):
    asked = [d.id for d in docs]
    bad = _clean_response(asked + [asked[0]])  # d0 twice
    good = _clean_response(asked)
    service = _make_service([bad, good])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs,
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == set(asked)


def test_generate_scores_batch__invocation_failure_then_clean__retries_and_succeeds(docs):
    asked = [d.id for d in docs]
    good = _clean_response(asked)
    # First payload is invalid JSON for the schema -> ValidationError inside _StructuredOutputMockLLM
    service = _make_service(['{"this": "is not a ratings response"}', good])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs,
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
    )

    assert set(out.keys()) == set(asked)


def test_generate_scores_batch__persistent_failure__raises_batch_scoring_error(docs):
    asked = [d.id for d in docs]
    bad = _clean_response(asked[:-1])  # always missing one
    # max_retries=2 → 3 total attempts; provide 3 identically-broken responses.
    service = _make_service([bad, bad, bad])

    with pytest.raises(BatchScoringError) as exc_info:
        service.generate_scores_batch(
            query_id="q1", query_text="x", documents=docs,
            relevance_scale="binary", explanation=False,
            prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=2,
        )

    err = exc_info.value
    assert err.query_id == "q1"
    assert err.batch_size == len(docs)
    assert err.asked_doc_ids == asked
    assert err.attempts == 3
    assert "missing" in err.reason.lower()


def test_generate_scores_batch__response_contract_failure__chains_cause(docs):
    """Regression: __cause__ should be populated even for missing/unknown/duplicate
    doc_id failures, not only for invocation failures, so traceback inspection
    and any cause-aware tooling behave uniformly across failure classes."""
    asked = [d.id for d in docs]
    bad = _clean_response(asked[:-1])  # missing one
    service = _make_service([bad])

    with pytest.raises(BatchScoringError) as exc_info:
        service.generate_scores_batch(
            query_id="q1", query_text="x", documents=docs,
            relevance_scale="binary", explanation=False,
            prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
        )

    cause = exc_info.value.__cause__
    assert cause is not None
    assert "missing" in str(cause).lower()


def test_generate_scores_batch__invocation_failure__chains_provider_exception(docs):
    """The other half of the contract: invocation failures should chain the
    real provider exception, not a synthetic one."""
    service = _make_service(['{"this": "is not a ratings response"}'])

    with pytest.raises(BatchScoringError) as exc_info:
        service.generate_scores_batch(
            query_id="q1", query_text="x", documents=docs,
            relevance_scale="binary", explanation=False,
            prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
        )

    # The real cause is a pydantic ValidationError from model_validate_json.
    cause = exc_info.value.__cause__
    assert cause is not None
    assert "ValidationError" in type(cause).__name__ or isinstance(cause, ValueError)


def test_generate_scores_batch__retry_uses_exponential_backoff(monkeypatch, docs):
    sleeps: list[float] = []
    monkeypatch.setattr(
        "rre_tools.dataset_generator.llm.llm_service.time.sleep",
        lambda d: sleeps.append(d),
    )
    # Pin jitter to 0 so we get exactly base * 2**attempt.
    monkeypatch.setattr(
        "rre_tools.dataset_generator.llm.llm_service.random.uniform",
        lambda _a, _b: 0.0,
    )

    asked = [d.id for d in docs]
    bad = _clean_response(asked[:-1])
    # max_retries=3 → 4 attempts; all bad → 3 sleeps (no sleep after the last attempt).
    service = _make_service([bad, bad, bad, bad])
    with pytest.raises(BatchScoringError):
        service.generate_scores_batch(
            query_id="q1", query_text="x", documents=docs,
            relevance_scale="binary", explanation=False,
            prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=3,
        )

    # Base = 1.0; attempts 0,1,2 -> 1, 2, 4.
    assert sleeps == [1.0, 2.0, 4.0]


def test_generate_scores_batch__explanation_true__returns_explanations(docs):
    asked = [d.id for d in docs[:3]]
    response = _clean_response(asked, explanation=True, score=1)
    service = _make_service([response])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs[:3],
        relevance_scale="binary", explanation=True,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
    )

    for did in asked:
        exp = out[did].explanation
        # Plan note: per-item explanation is Optional[str] in the schema.
        assert exp is None or (isinstance(exp, str) and exp != "")
        assert exp == f"why {did}"


def test_generate_scores_batch__blank_explanation_item__normalized_to_none_not_raised(docs):
    """Regression: provider returns explanation="" for one item when the user
    asked for explanations. Before the LLMScoreResponse normalization, this
    raised a non-retryable ValueError out of result assembly, bypassing the
    BatchScoringError contract. Now it should silently come through as None
    for that doc — the plan permits per-item explanations to be missing."""
    asked = [d.id for d in docs[:3]]
    response_json = (
        '{"ratings": ['
        f'{{"doc_id": "{asked[0]}", "score": 1, "explanation": "real reason"}},'
        f'{{"doc_id": "{asked[1]}", "score": 1, "explanation": ""}},'
        f'{{"doc_id": "{asked[2]}", "score": 1, "explanation": "   "}}'
        ']}'
    )
    service = _make_service([response_json])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs[:3],
        relevance_scale="binary", explanation=True,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
    )

    assert out[asked[0]].explanation == "real reason"
    assert out[asked[1]].explanation is None
    assert out[asked[2]].explanation is None


def test_generate_scores_batch__explanation_false__returns_none(docs):
    asked = [d.id for d in docs[:3]]
    # Even if the model included explanations, the service should suppress them.
    response = _clean_response(asked, explanation=True, score=1)
    service = _make_service([response])

    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=docs[:3],
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
    )

    for did in asked:
        assert out[did].explanation is None


def test_generate_scores_batch__invalid_relevance_scale__raises_value_error(docs):
    service = _make_service([])
    with pytest.raises(ValueError, match="Invalid relevance scale"):
        service.generate_scores_batch(
            query_id="q1", query_text="x", documents=docs,
            relevance_scale="fuzzy", explanation=False,
            prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
        )


def test_generate_scores_batch__empty_documents__returns_empty():
    service = _make_service([])
    out = service.generate_scores_batch(
        query_id="q1", query_text="x", documents=[],
        relevance_scale="binary", explanation=False,
        prompt_template=DEFAULT_BATCH_SCORE_PROMPT, max_retries=0,
    )
    assert out == {}
