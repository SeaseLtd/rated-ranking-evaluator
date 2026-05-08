from typing import Any, Iterable, List
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

def normalize_discovered_field_values(values: Iterable[Any]) -> List[str]:
    """Normalize bucket keys returned by an engine's value-discovery query.

    Used by `BaseSearchEngine.fetch_field_values` implementations to turn raw bucket keys
    (Solr facet values, ES/OS aggregation `bucket.key`, Vespa grouping `bucket.value`) into
    `List[str]` that downstream string substitution can safely consume.

    This is intentionally separate from the per-engine `Document.fields` normalizers
    (`SolrSearchEngine._normalize`, `VespaSearchEngine._normalize_field_value`, etc.):
    those preserve containers as JSON; this rejects them so a misconfigured aggregation that
    produces nested buckets surfaces as a `ValueError` rather than landing
    `"{'key': 'comedy'}"` as a query.

    Steps (in order):
      1. Drop None.
      2. Accept only str/int/float/bool. Raise ValueError on list/dict/other containers.
      3. str(value) on accepted scalars.
      4. Strip surrounding whitespace.
      5. Drop empty strings after stripping.
      6. Preserve input order. No sorting, no deduping (DataStore.add_query handles dedupe
         via clean_text on the rendered query text).
    """
    out: List[str] = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, bool) or isinstance(v, (int, float, str)):
            stripped = str(v).strip()
            if stripped:
                out.append(stripped)
            continue
        raise ValueError(
            f"normalize_discovered_field_values: unsupported bucket value type {type(v).__name__} "
            f"({v!r}). Only scalars (str, int, float, bool) are supported; nested containers "
            f"indicate a compound aggregation, which is not supported."
        )
    return out


def join_fields_as_text(fields: dict[str, Any], exclude: set[str] | str) -> str:
    if isinstance(exclude, str):
        exclude = {exclude}

    text_parts = []
    for k, v in fields.items():
        if k.lower() not in exclude and v is not None:
            text_parts.append(_to_string(v))
    return " ".join(text_parts).strip()
