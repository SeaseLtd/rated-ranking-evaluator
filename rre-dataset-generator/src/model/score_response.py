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
            explanation:  Explanation for the generated score or None.

        Raises:
            ValueError: If the score is not valid for the given scale.
        """
        if scale not in ["binary", "graded"]:
            raise ValueError(f"Invalid scale: {scale}. Must be 'binary' or 'graded'.")
            
        if scale == "binary" and score not in {0, 1}:
            raise ValueError(f"Score must be 0 or 1 for binary scale, got {score}")
        elif scale == "graded" and score not in {0, 1, 2}:
            raise ValueError(f"Score must be 0, 1, or 2 for graded scale, got {score}")
            
        self.score = score

        if explanation is not None:
            if not isinstance(explanation, str) or not explanation.strip():
                raise ValueError("`explanation`, if provided, must be a non‑empty string.")
        self.explanation = explanation

    def get_score(self) -> int:
        """
        Returns the validated score.
        """
        return self.score

    def get_explanation(self) -> str:
        """
        Returns explanation.
        """
        return self.explanation
