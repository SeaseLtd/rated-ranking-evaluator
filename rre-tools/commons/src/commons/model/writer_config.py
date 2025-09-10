from typing import Optional, Literal
import logging
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

log = logging.getLogger(__name__)

class WriterConfig(BaseModel):
    output_format: Literal['quepid', 'rre', 'mteb']
    index: str = Field(..., description="Name of the index/collection of the search engine")
    id_field: Optional[str] = Field(None, description="ID field for the unique key.")
    query_template: Optional[Path | str] = Field(None, description="Query template for rre evaluator.")
    query_placeholder: Optional[str] = Field(None,
                                                 description="Key-value pair to substitute in the rre query template.")

    @classmethod
    @field_validator("query_template", mode="before")
    def ensure_path(cls, v: Path | None) -> Path | None:
        if v is None:
            return v
        return Path(v)
