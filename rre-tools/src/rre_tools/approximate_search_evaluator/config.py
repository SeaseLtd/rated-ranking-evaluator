from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Literal

import yaml
from pydantic import BaseModel, Field, FilePath, HttpUrl, model_validator
from rre_tools.approximate_search_evaluator.constants import ELASTICSEARCH_SUPPORTED_VERSIONS, SOLR_SUPPORTED_VERSIONS

log = logging.getLogger(__name__)


class Config(BaseModel):
    query_template: FilePath = Field(
        ...,
        description="Path pointing to a template file for queries with a placeholder for keywords."
    )
    search_engine_type: Literal['solr', 'elasticsearch']
    collection_name: str = Field(..., description="Name of the index/collection of the search engine")
    search_engine_url: HttpUrl = Field(..., description="Search engine URL")
    search_engine_version: str = Field(default="latest", description="Search engine version.")
    id_field: Optional[str] = Field(None, description="ID field for the unique key.")
    query_placeholder: str = Field(
        default="$query",
        description="Key-value pair to substitute in the rre query template."
    )
    ratings_path: Optional[Path] = Field(
        None,
        description="Path to the rre ratings file. If not given, the content of the datastore is used."
    )
    embeddings_folder: Optional[Path] = Field(
        None,
        description="Path to collect embeddings. If not given, embeddings are not collected.",
    )
    output_destination: Path = Field(Path("resources"), description="Path to save the output dataset. By default, the "
                                                                    "dataset will be saved into the `resources` folder.")

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
        else:           # self.search_engine_type == "elasticsearch"
            return "index"

    @property
    def search_engine_url_alias(self) -> str:
        if self.search_engine_type == "solr":
            return "baseUrls"
        else:           # self.search_engine_type == "elasticsearch"
            return "hostUrls"

    @model_validator(mode="after")
    def validate_search_engine_version(self) -> "Config":
        if self.search_engine_type == "solr" :
            versions_to_check = SOLR_SUPPORTED_VERSIONS
        else:           # self.search_engine_type == "elasticsearch"
            versions_to_check = ELASTICSEARCH_SUPPORTED_VERSIONS

        if self.search_engine_version == "latest":
            self.search_engine_version = versions_to_check[-1]
        elif self.search_engine_version not in versions_to_check:
            raise ValueError(f"Search engine version {self.search_engine_version} is not supported for {self.search_engine_type}")
        return self

    @model_validator(mode="after")
    def adjust_id_field(self) -> "Config":
        if self.id_field is None:
            if self.search_engine_type == "solr":
                self.id_field = "id"
            else:  # self.search_engine_type == "elasticsearch"
                self.id_field = "_id"
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

        log.debug("Approximate Search Evaluator configuration file loaded successfully.")
        return cls(**raw_config)
