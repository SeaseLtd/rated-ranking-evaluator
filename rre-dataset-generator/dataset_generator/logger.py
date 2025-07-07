"""
This module uses Python's standard ``logging`` module to emit logs in a JSON format, ensuring the output is machine-readable.

The main components are:
- ``JsonFormatter``: A custom formatter class that converts log records into
  a single line of JSON.
- ``configure_logging``: An idempotent function to set up the root logger with
  the custom JSON formatter.

"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# A set of all standard attributes of a LogRecord.
# Used by the custom formatter to extract any "extra" data from the record.
LOGRECORD_STANDARD_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName",
}


class JsonFormatter(logging.Formatter):
    """
    Formats log records as a single line of JSON.
    
    This formatter ensures that logs are machine-readable, which is ideal for
    log aggregation systems like ELK, Datadog, or Splunk.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Converts a LogRecord to a JSON string.

        The final JSON object includes standard log information, the formatted
        message, and any extra data passed to the logger.
        """
        # Start with the basic information
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra_data = {
            key: value
            for key, value in record.__dict__.items()
            if key not in LOGRECORD_STANDARD_ATTRS
        }
        if extra_data:
            payload.update(extra_data)

        return json.dumps(payload, separators=(',', ':'))


def configure_logging(level: str | int = logging.INFO) -> None:
    """
    Configures the root logger for the application.

    This function is idempotent and safe to call multiple times. It checks if
    handlers are already configured to avoid duplication.
    """
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        root_logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root_logger.addHandler(handler)


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

    # 4. Log with extra data for structured logging
    print("\n--- Logging with extra context ---")
    log.info(
        "User action recorded",
        extra={"user_id": "user-123", "request_id": "abc-xyz-789"},
        # The 'extra' dictionary will be flattened into the JSON output
    )

    # 5. Log an exception
    print("\n--- Logging an exception ---")
    try:
        result = 1 / 0
    except ZeroDivisionError:
        log.error("An exception occurred", exc_info=True)

    print("\nConfiguration complete. Check the console for JSON log output.")
