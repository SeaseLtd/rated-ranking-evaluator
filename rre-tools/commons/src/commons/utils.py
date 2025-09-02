from typing import Any

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
