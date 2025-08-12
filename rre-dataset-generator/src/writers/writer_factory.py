from .abstract_writer import AbstractWriter
from .quepid_writer import QuepidWriter
import logging
from src.search_engine.data_store import DataStore
from .rre_writer import RreWriter
from ..config import Config

log = logging.getLogger(__name__)


class WriterFactory:
    OUTPUT_FORMAT_REGISTRY = {
        "quepid": QuepidWriter,
        "rre": RreWriter,
    }

    @classmethod
    def build(cls, config: Config, data_store: DataStore) -> AbstractWriter:
        output_format = config.output_format
        if output_format not in cls.OUTPUT_FORMAT_REGISTRY:
            log.error("Unsupported output format requested: %s", output_format)
            raise ValueError(f"Unsupported output format: {output_format}")
        log.info("Selected output format: %s", output_format)
        return cls.OUTPUT_FORMAT_REGISTRY[output_format].build(config, data_store)
