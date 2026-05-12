import pytest
from pydantic import HttpUrl

from rre_tools.shared.search_engines import SearchEngineFactory, VespaSearchEngine


def test_build_vespa__expects__vespa_search_engine():
    search_engine = SearchEngineFactory.build(
        search_engine_type="vespa",
        endpoint=HttpUrl("http://localhost:8080/doc/"),
    )

    assert isinstance(search_engine, VespaSearchEngine)


def test_build_unsupported_search_engine__expects__value_error():
    with pytest.raises(ValueError, match="Unsupported search engine: unsupported"):
        SearchEngineFactory.build(
            search_engine_type="unsupported",
            endpoint=HttpUrl("http://localhost:8080/doc/"),
        )
