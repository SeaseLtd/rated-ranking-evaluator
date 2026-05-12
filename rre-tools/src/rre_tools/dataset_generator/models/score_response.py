from typing import Optional


class LLMScoreResponse:
    """
    Parses and validates an LLM score response.
    """
    def __init__(self, score: int, scale: str = "graded", explanation: Optional[str] = None):
        """
        Initializes the object by validating the score.

        Args:
            score:      The relevance score.
            scale:      The relevance scale, either 'binary' {0,1} or 'graded' {0,1,2}.
            explanation:  Explanation for the generated score or None. Blank /
                whitespace-only strings are normalized to None — providers
                sometimes return ``""`` instead of omitting the field, and the
                batch scoring contract already permits per-item explanations to
                be missing, so treating ``""`` as "missing" is semantically
                faithful and avoids raising a non-retryable ValueError out of
                the batch result-assembly path.

        Raises:
            ValueError: If the score is not valid for the given scale or if
                ``explanation`` is provided and is not a string.
        """
        if scale not in ["binary", "graded"]:
            raise ValueError(f"Invalid scale: {scale}. Must be 'binary' or 'graded'.")

        if scale == "binary" and score not in {0, 1}:
            raise ValueError(f"Score must be 0 or 1 for binary scale, got {score}")
        elif scale == "graded" and score not in {0, 1, 2}:
            raise ValueError(f"Score must be 0, 1, or 2 for graded scale, got {score}")

        self.score = score

        if explanation is not None and not isinstance(explanation, str):
            raise ValueError("`explanation`, if provided, must be a string.")
        if isinstance(explanation, str) and not explanation.strip():
            explanation = None
        self.explanation = explanation

    def get_score(self) -> int:
        """
        Returns the validated score.
        """
        return self.score

