"""Unit tests for `validate_batch_prompt_template`.

The validator enforces a *closed* placeholder grammar at config load: each
field reference must be exactly one of the allowed names with no attribute
access, item access, conversion, or format spec. The tests below cover each
rejected variant — most importantly the silent-corruption case
`{documents_json[0]}`, which would render only the first character of the
JSON payload at runtime if it slipped through.
"""
from __future__ import annotations

import pytest

from rre_tools.dataset_generator.llm import validate_batch_prompt_template


REQUIRED_BODY = (
    "Query: {query}\n"
    "Docs: {documents_json}\n"
    "Scale: {relevance_scale}\n"
)


def test_minimal_valid_template__passes():
    validate_batch_prompt_template(REQUIRED_BODY)


def test_template_with_optional_placeholders__passes():
    body = REQUIRED_BODY + "{explanation_instruction}\n{rating_scale_description}\n"
    validate_batch_prompt_template(body)


def test_template_with_escaped_braces__passes():
    body = REQUIRED_BODY + 'Literal braces are fine: {{"k": "v"}}\n'
    validate_batch_prompt_template(body)


def test_missing_required_placeholder__rejected():
    body = "Query: {query}\nScale: {relevance_scale}\n"  # no documents_json
    with pytest.raises(ValueError, match="required placeholder"):
        validate_batch_prompt_template(body)


def test_unknown_placeholder_name__rejected():
    body = REQUIRED_BODY + "Mystery: {documents}\n"
    with pytest.raises(ValueError, match="unsupported placeholder"):
        validate_batch_prompt_template(body)


def test_unescaped_json_braces__rejected():
    body = REQUIRED_BODY + 'Example: {"id": 1}\n'
    with pytest.raises(ValueError):
        validate_batch_prompt_template(body)


def test_attribute_access_on_known_placeholder__rejected():
    # Without exact-match validation this used to pass, then raise at runtime
    # with `AttributeError: 'str' object has no attribute 'nope'`.
    body = REQUIRED_BODY + "Bad: {query.nope}\n"
    with pytest.raises(ValueError, match="unsupported placeholder"):
        validate_batch_prompt_template(body)


def test_item_access_on_known_placeholder__rejected():
    # The silent-corruption case: `{documents_json[0]}` renders only the first
    # character of the JSON payload at runtime. Must be caught at config load.
    body = (
        "Query: {query}\n"
        "Docs: {documents_json[0]}\n"
        "Scale: {relevance_scale}\n"
    )
    with pytest.raises(ValueError, match="unsupported placeholder"):
        validate_batch_prompt_template(body)


def test_conversion_on_placeholder__rejected():
    body = (
        "Query: {query!r}\n"
        "Docs: {documents_json}\n"
        "Scale: {relevance_scale}\n"
    )
    with pytest.raises(ValueError, match="unsupported conversion"):
        validate_batch_prompt_template(body)


def test_format_spec_on_placeholder__rejected():
    body = (
        "Query: {query:>10}\n"
        "Docs: {documents_json}\n"
        "Scale: {relevance_scale}\n"
    )
    with pytest.raises(ValueError, match="unsupported format spec"):
        validate_batch_prompt_template(body)


def test_nested_format_spec__rejected():
    # `{query:{width}}` raises `KeyError: 'width'` only when format() runs.
    body = (
        "Query: {query:{width}}\n"
        "Docs: {documents_json}\n"
        "Scale: {relevance_scale}\n"
    )
    with pytest.raises(ValueError, match="unsupported format spec"):
        validate_batch_prompt_template(body)


def test_positional_placeholder__rejected():
    body = "Query: {} {documents_json} {relevance_scale}\n"
    with pytest.raises(ValueError, match="positional placeholder"):
        validate_batch_prompt_template(body)
