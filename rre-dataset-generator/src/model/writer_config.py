from typing import Optional, Literal
import logging
import yaml

from pydantic import BaseModel, Field, FilePath

log = logging.getLogger(__name__)

class WriterConfig(BaseModel):
    output_format: Literal['quepid', 'rre', 'mteb']
    index: str = Field(..., description="Name of the index/collection of the search engine")
    id_field: Optional[str] = Field(None, description="ID field for the unique key.")
    query_template: Optional[FilePath] = Field(None, description="Query template for rre evaluator.")
    query_placeholder: Optional[str] = Field(None,
                                                 description="Key-value pair to substitute in the rre query template.")

    @classmethod
    def load(cls, config_path: str) -> "WriterConfig":
        """
        Load and validate configuration from a YAML file.

        :param config_path: Path to the YAML config file
        :return: Parsed and validated Config object
        """
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        log.debug("Configuration file loaded successfully.")
        return cls(**raw_config)
