from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field, model_validator
import yaml


class ProviderCfg(BaseModel):
    model: str
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, gt=0)
    api_key_env: Optional[str] = None


class LLMConfig(BaseModel):
    default_provider: str
    providers: Dict[str, ProviderCfg]

    @model_validator(mode="after")
    def validate_default_provider_exists(self) -> "LLMConfig":
        if self.default_provider not in self.providers:
            raise ValueError(f"default_provider '{self.default_provider}' not found in providers.")
        return self

    @staticmethod
    def load(path: str | Path = "llm_config.yaml") -> "LLMConfig":
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"LLM config file not found: {path}")
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        return LLMConfig(**raw)
