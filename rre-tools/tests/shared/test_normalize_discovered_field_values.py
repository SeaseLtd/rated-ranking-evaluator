import pytest

from rre_tools.shared.utils import normalize_discovered_field_values


def test_normalize__drops_none():
    assert normalize_discovered_field_values([None]) == []


def test_normalize__drops_empty_and_whitespace_only():
    assert normalize_discovered_field_values(["", "  "]) == []


def test_normalize__strips_surrounding_whitespace():
    assert normalize_discovered_field_values(["  comedy ", "action"]) == ["comedy", "action"]


def test_normalize__coerces_int_float_bool_to_str():
    assert normalize_discovered_field_values([123, 4.5, True]) == ["123", "4.5", "True"]


def test_normalize__rejects_dict_with_value_error():
    with pytest.raises(ValueError):
        normalize_discovered_field_values([{"a": 1}])


def test_normalize__rejects_list_with_value_error():
    with pytest.raises(ValueError):
        normalize_discovered_field_values([["nested"]])


def test_normalize__preserves_input_order():
    # No sort, no dedupe — DataStore.add_query handles cleaned-text dedupe.
    assert normalize_discovered_field_values(["b", "a", "b"]) == ["b", "a", "b"]
