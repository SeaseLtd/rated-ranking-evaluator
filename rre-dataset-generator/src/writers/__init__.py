from .abstract_writer import AbstractWriter
from .quepid_writer import QuepidWriter
import logging
from src.search_engine.data_store import DataStore

log = logging.getLogger(__name__)

OUTPUT_FORMAT_REGISTRY = {
    "quepid": QuepidWriter,
}

def build_writer(output_format: str, data_store: DataStore) -> AbstractWriter:
    if output_format not in OUTPUT_FORMAT_REGISTRY:
        log.error("Unsupported output format requested: %s", output_format)
        raise ValueError(f"Unsupported output format: {output_format}")
    log.info("Selected output format: %s", output_format)
    return OUTPUT_FORMAT_REGISTRY[output_format](data_store)