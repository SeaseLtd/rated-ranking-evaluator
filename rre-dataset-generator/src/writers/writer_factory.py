from .abstract_writer import AbstractWriter
from .quepid_writer import QuepidWriter
import logging

log = logging.getLogger(__name__)


class WriterFactory:
    OUTPUT_FORMAT_REGISTRY = {
        "quepid": QuepidWriter,
        "rre": RreWriter,
    }

    @classmethod
    def build(cls, output_format: str) -> AbstractWriter:
        if output_format not in cls.OUTPUT_FORMAT_REGISTRY:
            log.error(f"Unsupported output format requested: {output_format}")
            raise ValueError(f"Unsupported output format: {output_format}")
        log.info(f"Selected output format: {output_format}")
        return cls.OUTPUT_FORMAT_REGISTRY[output_format]()
