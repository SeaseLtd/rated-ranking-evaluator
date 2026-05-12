"""Batch relevance-scoring prompt: default template, placeholder contract, validation."""
from __future__ import annotations

from pathlib import Path
from string import Formatter
from typing import Optional, Set

REQUIRED_BATCH_PROMPT_PLACEHOLDERS: frozenset[str] = frozenset({
    "query",
    "documents_json",
    "relevance_scale",
})

OPTIONAL_BATCH_PROMPT_PLACEHOLDERS: frozenset[str] = frozenset({
    "explanation_instruction",
    "rating_scale_description",
})

ALLOWED_BATCH_PROMPT_PLACEHOLDERS: frozenset[str] = (
    REQUIRED_BATCH_PROMPT_PLACEHOLDERS | OPTIONAL_BATCH_PROMPT_PLACEHOLDERS
)

DEFAULT_BATCH_SCORE_PROMPT: str = (
    "You are a professional data labeler. Given a query and a JSON array of "
    "documents, return a relevance score for each document on the {relevance_scale} "
    "scale.\n"
    "\n"
    "{rating_scale_description}\n"
    "\n"
    'Query: "{query}"\n'
    "\n"
    "Documents (JSON array):\n"
    "{documents_json}\n"
    "\n"
    "{explanation_instruction}\n"
    "\n"
    'Return a structured object with a "ratings" array. Each item must include '
    '"doc_id" (matching the input) and "score". Include exactly one item per input '
    "document, in any order.\n"
)


def validate_batch_prompt_template(template: str) -> None:
    """Validate a str.format-style batch-scoring prompt template.

    The placeholder grammar is intentionally a *closed* allow-list: each
    occurrence must be exactly one of the allowed names with no attribute
    access (``{query.foo}``), item access (``{documents_json[0]}``),
    conversion (``{query!r}``), or format spec (``{query:{width}}``). The
    motivation is the fail-early contract: the silent-corruption variants —
    notably ``{documents_json[0]}`` which renders only the first character of
    the JSON payload at runtime — are exactly what config-load validation is
    here to catch.

    Raises ValueError when:
      - the template cannot be parsed by string.Formatter (e.g. unescaped
        `{`/`}` in JSON example bodies — the classic str.format footgun);
      - any field reference is not exactly an allowed placeholder name
        (covers unknown names, attribute access, and item access);
      - any field uses a non-empty conversion or format spec;
      - a required placeholder is missing.
    """
    try:
        parsed = list(Formatter().parse(template))
    except ValueError as e:
        raise ValueError(
            "Batch scoring prompt template could not be parsed by string.Formatter "
            "(an unescaped '{' or '}' is the usual cause — use '{{' and '}}' to "
            f"include literal braces): {e}"
        ) from e

    seen: Set[str] = set()
    for _literal, field_name, format_spec, conversion in parsed:
        if field_name is None:
            continue
        if field_name == "":
            raise ValueError(
                "Batch scoring prompt template uses an unsupported positional "
                "placeholder '{}'. Use one of the named placeholders: "
                f"{sorted(ALLOWED_BATCH_PROMPT_PLACEHOLDERS)}."
            )
        # Exact match — no attribute access (`{query.x}`) or item access
        # (`{documents_json[0]}`). `{documents_json[0]}` would silently render
        # only the first character of the JSON payload at runtime, which is
        # precisely the silent corruption this validator exists to prevent.
        if field_name not in ALLOWED_BATCH_PROMPT_PLACEHOLDERS:
            raise ValueError(
                f"Batch scoring prompt template references unsupported placeholder "
                f"'{{{field_name}}}'. Allowed placeholders (exact names, no "
                f"attribute or item access): "
                f"{sorted(ALLOWED_BATCH_PROMPT_PLACEHOLDERS)}."
            )
        if conversion:
            raise ValueError(
                f"Batch scoring prompt template uses an unsupported conversion "
                f"'!{conversion}' on placeholder '{{{field_name}}}'. Conversions "
                f"are not part of the closed placeholder grammar."
            )
        if format_spec:
            # Note: a plain `{query}` parses as format_spec='' (falsy), so this
            # only rejects non-empty specs like `{query:{width}}` or `{query:>10}`.
            raise ValueError(
                f"Batch scoring prompt template uses an unsupported format spec "
                f"':{format_spec}' on placeholder '{{{field_name}}}'. Format "
                f"specs are not part of the closed placeholder grammar."
            )
        seen.add(field_name)

    missing = REQUIRED_BATCH_PROMPT_PLACEHOLDERS - seen
    if missing:
        raise ValueError(
            f"Batch scoring prompt template is missing required placeholder(s) "
            f"{sorted(missing)}. Required: "
            f"{sorted(REQUIRED_BATCH_PROMPT_PLACEHOLDERS)}."
        )


def load_batch_prompt(prompt_path: Optional[Path]) -> str:
    """Return the batch-scoring prompt template body.

    Reads `prompt_path` from disk when set, otherwise returns the built-in
    default. The service is filesystem-free: this is the single place where
    "file vs default" is decided.
    """
    if prompt_path is None:
        return DEFAULT_BATCH_SCORE_PROMPT
    return prompt_path.read_text(encoding="utf-8")
