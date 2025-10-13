import json
from typing import List

class LLMQueryResponse:
    """
    Parses and validates a JSON response containing a list of queries.
    """
    _queries: List[str]

    def __init__(self, response_content: str):
        """
        Initializes the object by parsing and validating the JSON string.

        Args:
            response_content: A string containing a JSON-encoded list of strings.

        Raises:
            ValueError: If the content is not a valid JSON list of non-empty strings.
        """
        try:
            parsed_content = json.loads(response_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in `response_content`: {e}")

        if not isinstance(parsed_content, list):
            raise ValueError("`response_content` must be a JSON list.")

        if not all(isinstance(item, str) for item in parsed_content):
            raise ValueError("All items in `response_content` must be strings.")

        if any(not item.strip() for item in parsed_content):
            raise ValueError("Items in `response_content` must not be empty or only whitespace.")

        self._queries = parsed_content

    def get_queries(self) -> List[str]:
        """
        Returns the validated list of queries.
        """
        return self._queries
