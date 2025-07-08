"""CLI entrypoint for the Dataset Generator.

This module provides a simple command-line interface (CLI) to run the dataset
generation pipeline.
"""

import argparse
from src.logger import configure_logging
import logging

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for dataset_generator CLI.')

    parser.add_argument('-d', '--dummy', type=str,
                        help='Dummy var',
                        required=False, default="default")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    configure_logging(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    try:
        log.debug(f"Dummy variable {args.dummy} loaded successfully.")
    except Exception as e:
        log.debug(f"Error parsing args: {e}")
