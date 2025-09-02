from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Any

import yaml
from pydantic import BaseModel, Field, field_validator, FilePath, model_validator

log = logging.getLogger(__name__)


class Config(BaseModel):
    model_id: str = Field(..., description="Model id from HuggingFace models")
    corpus_path: FilePath = Field(..., description="Corpus jsonl file path")
    queries_path: FilePath = Field(..., description="Queries jsonl file path")
    candidates_path: FilePath = Field(..., description="Candidates jsonl file path")
    output_dest: Optional[Path] = Field(
        None,
        description="Path to save mteb output, by default saved into <output> dir.",
    )

    @field_validator("corpus_path", "queries_path", "candidates_path", mode="before")
    def check_jsonl_extension(cls, val: Any) -> Any:
        if val is None:
            return val
        path = FilePath(val)
        if path.suffix != ".jsonl":
            log.error(f"{val} must have .jsonl extension")
            raise ValueError(f"{val} must have .jsonl extension")
        return path

    @model_validator(mode="after")
    def create_default_output_dest(self) -> Config:
        if self.output_dest is None:
            default_dir = Path("output")
            default_dir.mkdir(exist_ok=True)
            self.output_dest = default_dir
        return self

    @classmethod
    def load(cls, config_path: str) -> Config:
        """
        Load and validate configuration from a yaml file.

        :param config_path: Path to the yaml config file
        :return: Parsed and validated Config object
        """
        with open(config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        log.debug("Mteb Configuration file loaded successfully.")
        return cls(**raw_config)
