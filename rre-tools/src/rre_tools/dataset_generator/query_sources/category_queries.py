from __future__ import annotations

from logging import Logger, getLogger
from typing import List, Optional

from rre_tools.dataset_generator.config import Config
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.search_engines import BaseSearchEngine

log: Logger = getLogger(__name__)


def add_category_queries(config: Config, data_store: DataStore,
                         search_engine: BaseSearchEngine) -> None:
    """Render category queries from explicit values or engine value-discovery, and add them.

    Explicit-values mode: ``source.values`` is a list typed by the user.
    Engine-discovery mode: ``source.values_query_template_file`` is set instead, and the
    engine returns the distinct values for ``source.fields[0]`` at run time.

    Single warning site for empty value-discovery results — engine
    ``fetch_field_values`` implementations return ``[]`` *silently* when the response path
    exists but is empty so we don't log the same condition at two layers.

    With a ``query_text_template_file``: each value replaces the engine-appropriate
    placeholder (``@kw`` for Vespa, ``$query`` for Solr/Elasticsearch/OpenSearch) in the
    template content. Without one: each value is used directly as the query text.
    Deduplication is handled by ``DataStore.add_query``.
    """
    if not config.category_queries:
        return
    placeholder = config.category_query_placeholder
    for source in config.category_queries:
        # Explicit-values mode never calls the engine. The if/else is deliberate (rather
        # than `source.values or engine.fetch_field_values(...)`): a future config knob
        # that empties `values` mid-pipeline must not silently fall through to an engine
        # call the user didn't ask for.
        if source.values is not None:
            values: List[str] = list(source.values)
        else:
            values = search_engine.fetch_field_values(
                source.values_query_template_file, source.fields[0]
            )

        if not values:
            log.warning(
                f"[add_category_queries] no values for field='{source.fields[0]}' "
                f"(template={source.values_query_template_file}); skipping this source"
            )
            continue

        template: Optional[str] = (
            source.query_text_template_file.read_text(encoding="utf-8").strip()
            if source.query_text_template_file is not None
            else None
        )
        for value in values:
            query_text = value if template is None else template.replace(placeholder, value)
            data_store.add_query(query_text, source="category")
            log.debug(f"[add_category_queries] added query='{query_text}'")
