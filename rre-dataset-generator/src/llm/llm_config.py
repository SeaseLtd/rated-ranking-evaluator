from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    name: str
    model: str
    max_tokens: int = Field(default=512, gt=0)
    api_key_env: Optional[str] = None

    @classmethod
    def load(cls, path: str | Path = "llm_config.yaml") -> LLMConfig:
        path = Path(path).resolve()
        if not path.exists():
            log.error("LLM config file not found: %s", path)
            raise FileNotFoundError(f"LLM config file not found: {path}")
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        return cls(**raw)

