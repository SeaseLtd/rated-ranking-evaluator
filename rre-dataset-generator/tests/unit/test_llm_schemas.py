import pytest
from src.model.llm_schemas import LLMQueryResponse
from pydantic import ValidationError

# ─────────────────────────────────────────────────────────────────────────────
# Test cases: valid inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_valid_json_list_of_strings():
    response = LLMQueryResponse(content='["Answer 1", "Answer 2", "Answer 3"]')
    assert response.content_list == ["Answer 1", "Answer 2", "Answer 3"]

def test_valid_single_item_list():
    response = LLMQueryResponse(content='["Only one item"]')
    assert response.content_list == ["Only one item"]

def test_valid_with_leading_trailing_whitespace():
    response = LLMQueryResponse(content='["  hello  ", " world "]')
    assert response.content_list == ["  hello  ", " world "]

# ─────────────────────────────────────────────────────────────────────────────
# Test cases: invalid inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_json_string():
    with pytest.raises(ValueError, match="Invalid JSON in `content`"):
        LLMQueryResponse(content='["incomplete string]')

def test_json_not_a_list():
    with pytest.raises(ValueError, match="`content` must be a JSON list"):
        LLMQueryResponse(content='"not a list"')

def test_list_with_non_string_elements():
    with pytest.raises(ValueError, match="must be strings"):
        LLMQueryResponse(content='["valid", 123, true]')

def test_list_with_empty_string():
    with pytest.raises(ValidationError, match="must not be empty or only whitespace"):
        LLMQueryResponse(content='["valid", ""]')

def test_list_with_whitespace_only_string():
    with pytest.raises(ValidationError, match="must not be empty or only whitespace"):
        LLMQueryResponse(content='["okay", "    "]')

# ─────────────────────────────────────────────────────────────────────────────
# Test cases: edge inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_list():
    response = LLMQueryResponse(content='[]')
    assert response.content_list == []

def test_very_large_list(monkeypatch):
    long_list = [f"item_{i}" for i in range(10000)]
    json_str = str(long_list).replace("'", '"')  # crude conversion for valid JSON
    response = LLMQueryResponse(content=json_str)
    assert len(response.content_list) == 10000
    assert response.content_list[0] == "item_0"
    assert response.content_list[-1] == "item_9999"

def test_unicode_strings():
    response = LLMQueryResponse(content='["こんにちは", "你好", "¡Hola!"]')
    assert response.content_list == ["こんにちは", "你好", "¡Hola!"]
