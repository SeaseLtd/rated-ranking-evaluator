from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Literal

import yaml
from pydantic import BaseModel, Field, FilePath, HttpUrl

log = logging.getLogger(__name__)


class Config(BaseModel):
    query_template: FilePath = Field(
        ...,
        description="Path pointing to a template file for queries with a placeholder for keywords."
    )
    search_engine_type: Literal['solr', 'elasticsearch', 'opensearch', 'vespa']
    collection_name: str = Field(..., description="Name of the index/collection of the search engine")
    # vespa_schema: Optional[str] = Field(None, description="Schema name for Vespa search engine")
    search_engine_url: HttpUrl
    search_engine_version: str = Field(..., description="Search engine version.")

    id_field: Optional[str] = Field("id", description="ID field for the unique key.")
    query_placeholder: Optional[str] = Field(None,
                                             description="Key-value pair to substitute in the rre query template.")
    ratings_path: Optional[Path] = Field(None, description="Path to the rre ratings file.")
    embeddings_folder: Optional[Path] = Field(
        None,
        description="Path to collect embeddings, by default saved in <resources/embeddings> folder.",
    )

    @property
    def conf_sets_filename(self) -> str:
        if self.search_engine_type == "solr":
            return "solr-settings.json"
        else:
            return "index-settings.json"

    @property
    def collection_name_alias(self) -> str:
        if self.search_engine_type == "solr":
            return "collectionName"
        else:
            return "index"

    @property
    def search_engine_url_alias(self) -> str:
        if self.search_engine_type == "solr":
            return "baseUrls"
        else:
            return "hostUrls"


    @classmethod
    def load(cls, config_path: str) -> Config:
        """
        Load and validate configuration from a yaml file.

        :param config_path: Path to the yaml config file
        :return: Parsed and validated Config object
        """
        with open(config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        log.debug("Rre Configuration file loaded successfully.")
        return cls(**raw_config)
