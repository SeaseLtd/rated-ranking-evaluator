from typing import Any
import re
import html
import unicodedata

def is_json_serializable(value: Any) -> bool:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(is_json_serializable(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and is_json_serializable(val) for k, val in value.items())
    return False

def _to_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(str(val) for val in value if val is not None)
    return str(value)

# ────────────────────────────────────────────
# Text normalization helpers
# ────────────────────────────────────────────

_TAG_REGEX = re.compile(r"<.*?>")
_CTRL_REGEX = re.compile(r"[\u0000-\u001F\u007F-\u009F]")
_WS_REGEX = re.compile(r"\s+")

def clean_text(text: str) -> str:
    """Safe text cleaning used for document field values.

    Operations (in order):
    - HTML entity unescape
    - Remove HTML tags
    - Unicode NFKC normalization
    - Replace control chars with spaces
    - Collapse all whitespace to single spaces and strip

    Intentionally does NOT change case, remove punctuation, or strip accents.
    """
    if text is None:
        return ""
    # Unescape entities to expose tags like &lt;tag&gt;
    t = html.unescape(text)
    # Remove naive HTML tags
    t = re.sub(_TAG_REGEX, "", t)
    # Normalize unicode (compatibility composition)
    t = unicodedata.normalize("NFKC", t)
    # Replace control characters with spaces
    t = _CTRL_REGEX.sub(" ", t)
    # Normalize whitespace
    t = _WS_REGEX.sub(" ", t).strip()
    return t

def join_fields_as_text(fields: dict[str, Any], exclude: set[str] | str) -> str:
    if isinstance(exclude, str):
        exclude = {exclude}

    text_parts = []
    for k, v in fields.items():
        if k.lower() not in exclude and v is not None:
            text_parts.append(_to_string(v))
    return " ".join(text_parts).strip()
