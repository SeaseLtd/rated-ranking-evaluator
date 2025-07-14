from src.config import Config
from src.utils import parse_args

if __name__ == "__main__":
    from src.logger import configure_logging
    import logging

    args = parse_args()

    configure_logging(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    try:
        config = Config.load(args.config_file)
        log.debug("Configuration loaded successfully.")
    except Exception as e:
        log.debug(f"Error loading configuration: {e}")
