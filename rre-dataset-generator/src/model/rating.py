from dataclasses import dataclass
from typing import Optional


@dataclass
class Rating:
    score: int
    reasoning: Optional[str] = None
