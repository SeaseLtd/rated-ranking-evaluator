from typing import Dict, Type
from pydantic import HttpUrl

from rre_tools.core.search_engines.opensearch_engine import OpenSearchEngine
from rre_tools.core.search_engines.search_engine_base import BaseSearchEngine
from rre_tools.core.search_engines.solr_search_engine import SolrSearchEngine
from rre_tools.core.search_engines.elasticsearch_search_engine import ElasticsearchSearchEngine

import logging

log = logging.getLogger(__name__)


class SearchEngineFactory:
    SEARCH_ENGINE_REGISTRY: Dict[str, Type[BaseSearchEngine]] = {
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
