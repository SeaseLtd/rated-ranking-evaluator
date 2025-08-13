from pydantic import HttpUrl

from .opensearch_engine import OpenSearchEngine
from .search_engine_base import BaseSearchEngine
from .solr_search_engine import SolrSearchEngine
from .elasticsearch_search_engine import ElasticsearchSearchEngine

import logging

log = logging.getLogger(__name__)


class SearchEngineFactory:
    SEARCH_ENGINE_REGISTRY = {
        "solr": SolrSearchEngine,
        "opensearch": OpenSearchEngine,
        "elasticsearch": ElasticsearchSearchEngine
    }

    @classmethod
    def build(cls, search_engine_type: str, endpoint: HttpUrl) -> BaseSearchEngine:
        if search_engine_type not in cls.SEARCH_ENGINE_REGISTRY:
            log.error("Unsupported search engine requested: %s", search_engine_type)
            raise ValueError(f"Unsupported search engine: {search_engine_type}")
        log.info("Searching in %s at endpoint : %s", search_engine_type.upper(), endpoint)
        return cls.SEARCH_ENGINE_REGISTRY[search_engine_type](endpoint)
