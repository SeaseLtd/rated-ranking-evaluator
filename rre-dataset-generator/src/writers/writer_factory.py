from .abstract_writer import AbstractWriter
from .mteb_writer import MtebWriter
from .quepid_writer import QuepidWriter
from .rre_writer import RreWriter

from typing import Mapping, Type, TypeAlias
import logging

log = logging.getLogger(__name__)

WriterType: TypeAlias = Type[AbstractWriter]

class WriterFactory:
    OUTPUT_FORMAT_REGISTRY: Mapping[str, WriterType] = {
        "quepid": QuepidWriter,
        "rre": RreWriter,
        "mteb": MtebWriter,
    }

    @classmethod
    def build(cls, output_format: str) -> AbstractWriter:
        if output_format not in cls.OUTPUT_FORMAT_REGISTRY:
            log.error(f"Unsupported output format requested: {output_format}")
            raise ValueError(f"Unsupported output format: {output_format}")
        log.info(f"Selected output format: {output_format}")
        return cls.OUTPUT_FORMAT_REGISTRY[output_format]()
