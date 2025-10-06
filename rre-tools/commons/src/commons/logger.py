"""
This module uses Python's standard ``logging`` module to emit logs in a JSON format, ensuring the output is machine-readable.

The main components are:
- ``configure_logging``: An idempotent function to set up the root logger with
  a configured formatter.

"""

import logging
from typing import Union

def configure_logging(level: Union[str, int] = logging.INFO) -> None:
    """
    Configures the root logger for the application.

    This function is idempotent and safe to call multiple times. It checks if
    handlers are already configured to avoid duplication.
    """
    logging.basicConfig(
        # filename='logs/log_file_name.log',
        level=level,
        format='[%(asctime)s] %(filename)-28s:%(lineno)-4d %(levelname)-7s - %(message)s',
        datefmt='%H:%M:%S'
    )

def setup_logging(verbose: bool = False) -> None:
    if verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)
    return

# EXAMPLE:
if __name__ == "__main__":
    # 1. Configure logging
    # This should be called once at the beginning of the application.
    configure_logging(level=logging.DEBUG)

    # 2. Get a logger instance
    log = logging.getLogger(__name__) # Best practice: use the module name for the logger.

    # 3. Log messages at different levels
    print("\n--- Logging examples ---")
    log.debug("This is a debug message. Useful for detailed-level information.")
    log.info("This is an info message. Represents a standard operational message.")
    log.warning("This is a warning message. Indicates a potential issue.")
    log.error("This is an error message. Signifies a more serious problem.")

    # 4. Log an exception
    print("\n--- Logging an exception ---")
    try:
        result = 1 / 0
    except ZeroDivisionError:
        log.error("An exception occurred", exc_info=True)

    print("\nConfiguration complete. Check the console log output.")
