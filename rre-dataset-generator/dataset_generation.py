"""CLI entrypoint for the Dataset Generator.

This module provides a simple command-line interface (CLI) to run the dataset
generation pipeline. It delegates all the business logic to the
`DatasetGenerator` service.
"""

import logging
from pathlib import Path

import typer

from dataset_generator.logger import configure_logging

# Configure logging as soon as the module is loaded
configure_logging()

# Get a logger for this module
logger = logging.getLogger(__name__)

# Create a Typer app instance
app = typer.Typer()

@app.callback(invoke_without_command=True)
def main(
    config_path: Path = typer.Argument(default="config.yaml", help="Path to the configuration YAML file.")
):
    """Runs the dataset generation pipeline using the specified config."""
    logger.info(
        "Starting dataset generation process...",
        extra={"config_path": str(config_path)},
    )

if __name__ == "__main__":
    app()
