from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    name: str
    model: str
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, gt=0)
    api_key_env: Optional[str] = None

    @staticmethod
    def load(path: str | Path = "llm_config.yaml") -> LLMConfig:
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"LLM config file not found: {path}")
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        return LLMConfig(**raw)

