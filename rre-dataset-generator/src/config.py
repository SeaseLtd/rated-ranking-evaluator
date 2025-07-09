from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, HttpUrl, Field, field_validator, FilePath
import yaml
from pathlib import Path


class Config(BaseModel):
    QueryTemplate: Optional[str] = Field("q=#$query##", description="Template string for queries with a placeholder for keywords.")
    SearchEngineType: Literal['Solr', 'Elasticsearch', 'Opensearch', 'Vespa']
    SearchEngineCollectionEndpoint: HttpUrl
    documentsFilter: Optional[List[Dict[str, List[str]]]] = Field(
        None,
        description="Optional list of filter conditions for documents"
    )
    docNumber: int = Field(..., gt=0, description="Number of documents to retrieve from the search engine.")
    docFields: List[str] = Field(..., min_length=1, description="Fields used for context and scoring.")
    queries: Optional[FilePath] = Field(None, description="Optional file containing predefined queries.")
    generateQueriesFromDocuments: Optional[bool] = True
    totalNumQueriesToGenerate: int = Field(..., gt=0, description="Total number of queries to generate.")
    RelevanceScale: Literal['Binary', 'Graded']
    LLMConfigurationFile: FilePath = Field(..., description="Path to the LLM configuration file.")
    OutputFormat: Literal['Quepid', 'RRE']
    OutputDestination: Path = Field(..., description="Path to save the output dataset.")
    OutputExplanation: Optional[bool] = Field(False, description="Whether to generate an explanation file.")

    @field_validator('docFields')
    def check_no_empty_fields(cls, v):
        if any(not f.strip() for f in v):
            raise ValueError("docFields cannot contain empty strings.")
        return v

    @field_validator('queries')
    def check_doc_type(cls, v):
        if v is not None:
            if v.suffix[1:] != "txt":
                raise ValueError("queries' file must have TXT extension")
        return v

    @field_validator('LLMConfigurationFile')
    def check_config_type(cls, v):
        if v is not None:
            if v.suffix[1:] != "yaml" and v.suffix[1:] != "yml":
                raise ValueError("queries' file must have YAML extension")
        return v


def load_config(config_path: str) -> Config:
    """
    Load and validate configuration from a YAML file.

    :param config_path: Path to the YAML config file
    :return: Parsed and validated Config object
    """
    # try:
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)
    return Config(**raw_config)
    # except Exception as e:
    #     raise RuntimeError(f"Error loading config: {e}")


# Example usage in pipeline
if __name__ == "__main__":
    from src.logger import configure_logging
    import logging

    configure_logging(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    config = load_config("config.yaml")
    log.debug("Configuration loaded successfully.")
