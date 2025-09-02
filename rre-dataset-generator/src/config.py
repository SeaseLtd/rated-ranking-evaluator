from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, HttpUrl, Field, field_validator, FilePath, model_validator
import yaml
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class Config(BaseModel):
    query_template: str = Field("q=#$query##", description="Template string for queries with a placeholder for keywords.")
    search_engine_type: Literal['solr', 'elasticsearch', 'opensearch', 'vespa']
    index_name: str = Field(..., description="Name of the index/collection of the search engine")
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
    output_format: Literal['quepid', 'rre', 'mteb']
    output_destination: Path = Field(..., description="Path to save the output dataset.")
    save_llm_explanation: bool = False
    llm_explanation_destination: Optional[Path] = Field(None, description="Path to save the LLM rating explanation")
    corpora_file: Optional[FilePath] = Field(None, description="JSON formatted dataset file.")
    id_field: Optional[str] = Field(None, description="ID field for the unique key.")
    rre_query_template: Optional[FilePath] = Field(None, description="Query template for rre evaluator.")
    rre_query_placeholder: Optional[str] = Field(None, description="Key-value pair to substitute in the rre query template.")
    verbose: bool = False


    @field_validator('doc_fields')
    @classmethod
    def check_no_empty_fields(cls, value_field: List[str]) -> List[str]:
        if any(not f.strip() for f in value_field):
            log.error("docFields cannot contain empty strings.")
            raise ValueError("docFields cannot contain empty strings.")
        return value_field

    @field_validator('queries')
    @classmethod
    def check_doc_type(cls, value_field: Optional[FilePath]) -> Optional[FilePath]:
        if value_field is not None and value_field.suffix[1:] != "txt" :
            log.error("queries' file must have .txt extension")
            raise ValueError("queries' file must have .txt extension")
        return value_field

    @field_validator('llm_configuration_file')
    @classmethod
    def check_config_type(cls, value_field: Optional[FilePath]) -> Optional[FilePath]:
        if value_field is not None and value_field.suffix[1:] not in {"yaml", "yml"}:
            log.error("LLM_config file must have .yaml extension")
            raise ValueError("LLM_config file must have .yaml extension")
        return value_field

    @model_validator(mode="after")
    def validate_llm_explanation_fields(self) -> "Config":
        if self.save_llm_explanation and self.llm_explanation_destination is None:
            raise ValueError("llm_explanation_destination must be set when save_llm_explanation is set to True.")
        return self

    @property
    def relevance_label_set(self) -> set[int]:
        """
        Returns the set of valid labels based on the relevance scale.
        """
        if self.relevance_scale == "binary":
            return {0, 1}
        elif self.relevance_scale == "graded":
            return {0, 1, 2}
        else:
            error_msg = f"Unknown relevance scale: {self.relevance_scale}"
            log.error(error_msg)
            raise ValueError(error_msg)

    @model_validator(mode="after")
    def check_rre_fields_required(self) -> "Config":
        if self.output_format == "rre" and not self.corpora_file:
            raise ValueError("corpora_file is required when output_format='rre'")
        elif self.output_format == "rre" and not self.id_field:
            raise ValueError("id_field is required when output_format='rre'")
        elif self.output_format == "rre" and not self.rre_query_template:
            raise ValueError("rre_query_template is required when output_format='rre'")
        elif self.output_format == "rre" and not self.rre_query_placeholder:
            raise ValueError("rre_query_placeholder is required when output_format='rre'")
        return self

    @classmethod
    def load(cls, config_path: str) -> "Config":
        """
        Load and validate configuration from a YAML file.

        :param config_path: Path to the YAML config file
        :return: Parsed and validated Config object
        """
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        log.debug("Configuration file loaded successfully.")
        return cls(**raw_config)
