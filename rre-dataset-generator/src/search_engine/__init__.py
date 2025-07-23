from pydantic import HttpUrl

from .search_engine_base import BaseSearchEngine
from .solr_search_engine import SolrSearchEngine
import logging

log = logging.getLogger(__name__)

SEARCH_ENGINE_REGISTRY = {
    "solr": SolrSearchEngine,
}

def build_search_engine(search_engine_type: str, endpoint: HttpUrl) -> BaseSearchEngine:
    if search_engine_type not in SEARCH_ENGINE_REGISTRY:
        log.error("Unsupported search engine requested: %s", search_engine_type)
        raise ValueError(f"Unsupported search engine: {search_engine_type}")
    log.info("Searching in %s at endpoint : %s", search_engine_type.upper(), endpoint)
    return SEARCH_ENGINE_REGISTRY[search_engine_type](endpoint)
