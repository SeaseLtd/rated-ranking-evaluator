import argparse
from src.config import load_config

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    return parser.parse_args()

if __name__ == "__main__":
    from src.logger import configure_logging
    import logging

    args = parse_args()

    configure_logging(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    try:
        config = load_config(args.config_file)
        log.debug("Configuration loaded successfully.")
        # print(config.model_dump_json(indent=2))
    except Exception as e:
        log.debug(f"Error loading configuration: {e}")
