from .abstract_writer import AbstractWriter
from .mteb_writer import MtebWriter
from .quepid_writer import QuepidWriter
from .rre_writer import RreWriter
from src.model.writer_config import WriterConfig

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
    def build(cls, writer_config: WriterConfig) -> AbstractWriter:
        output_format: str = writer_config.output_format
        if output_format not in cls.OUTPUT_FORMAT_REGISTRY:
            log.error(f"Unsupported output format requested: {output_format}")
            raise ValueError(f"Unsupported output format: {output_format}")
        log.info(f"Selected output format: {output_format}")
        return cls.OUTPUT_FORMAT_REGISTRY[output_format](writer_config)
