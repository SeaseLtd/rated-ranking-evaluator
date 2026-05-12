"""Guard against accidental breakage of the built-in batch-scoring prompt."""
from __future__ import annotations

from rre_tools.dataset_generator.llm import (
    DEFAULT_BATCH_SCORE_PROMPT,
    validate_batch_prompt_template,
)


def test_default_batch_score_prompt__passes_config_load_validation():
    # If this raises, a future edit to DEFAULT_BATCH_SCORE_PROMPT broke the
    # placeholder contract (typo, unescaped JSON braces, missing required).
    validate_batch_prompt_template(DEFAULT_BATCH_SCORE_PROMPT)


def test_default_batch_score_prompt__contains_required_placeholders():
    # Belt-and-braces: substring check too, in case Formatter ever changes.
    for required in ("{query}", "{documents_json}", "{relevance_scale}"):
        assert required in DEFAULT_BATCH_SCORE_PROMPT
