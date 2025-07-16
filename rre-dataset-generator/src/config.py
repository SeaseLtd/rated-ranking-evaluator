from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, HttpUrl, Field, field_validator, FilePath
import yaml
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class Config(BaseModel):
    query_template: Optional[str] = Field("q=#$query##", description="Template string for queries with a placeholder for keywords.")
    search_engine_type: Literal['solr', 'elasticsearch', 'opensearch', 'vespa']
    search_engine_collection_endpoint: HttpUrl
    documents_filter: Optional[List[Dict[str, List[str]]]] = Field(
        None,
        description="Optional list of filter conditions for documents"
    )
    doc_number: int = Field(..., gt=0, description="Number of documents to retrieve from the search engine.")
    doc_fields: List[str] = Field(..., min_length=1, description="Fields used for context and scoring.")
    queries: Optional[FilePath] = Field(None, description="Optional file containing predefined queries.")
    generate_queries_from_documents: Optional[bool] = True
    num_queries_needed: int = Field(..., gt=0, description="Total number of queries to generate.")
    relevance_scale: Literal['binary', 'graded']
    llm_configuration_file: FilePath = Field(..., description="Path to the LLM configuration file.")
    output_format: Literal['quepid', 'rre']
    output_destination: Path = Field(..., description="Path to save the output dataset.")

    @field_validator('doc_fields')
    def check_no_empty_fields(cls, v):
        if any(not f.strip() for f in v):
            log.error("docFields cannot contain empty strings.")
            raise ValueError("docFields cannot contain empty strings.")
        return v

    @field_validator('queries')
    def check_doc_type(cls, v):
        if v is not None:
            if v.suffix[1:] != "txt":
                log.error("queries' file must have .txt extension")
                raise ValueError("queries' file must have .txt extension")
        return v

    @field_validator('llm_configuration_file')
    def check_config_type(cls, v):
        if v is not None:
            if v.suffix[1:] not in {"yaml", "yml"}:
                log.error("LLM_config file must have .yaml extension")
                raise ValueError("LLM_config file must have .yaml extension")
        return v

    @classmethod
    def load(cls, config_path: str) -> Config:
        """
        Load and validate configuration from a YAML file.

        :param config_path: Path to the YAML config file
        :return: Parsed and validated Config object
        """
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        log.debug("Configuration file loaded successfully.")
        return cls(**raw_config)
