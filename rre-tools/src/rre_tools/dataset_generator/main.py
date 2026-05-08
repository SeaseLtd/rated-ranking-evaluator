from __future__ import annotations

# ------ temporary import for corpus.json bug workaround ------
import json
from pathlib import Path
from rre_tools.shared.utils import _to_string
import argparse
# -------------------------------------------------------------

from typing import List
from langchain_core.language_models import BaseChatModel
from logging import Logger, getLogger

# project imports
from rre_tools.shared.logger import setup_logging
from rre_tools.dataset_generator.llm import LLMConfig, LLMService, LLMServiceFactory
from rre_tools.shared.models import Document, Query
from rre_tools.shared.models.query import SOURCE_PRIORITY
from rre_tools.shared.writers import WriterFactory, AbstractWriter, WriterConfig
from rre_tools.shared.search_engines import SearchEngineFactory, BaseSearchEngine
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.utils import join_fields_as_text

from rre_tools.dataset_generator.models import LLMQueryResponse, LLMScoreResponse
from rre_tools.dataset_generator.config import Config
from rre_tools.dataset_generator.query_sources import add_category_queries

log: Logger = getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config', type=str,
                        help='Config file path to use for the application [default: "configs/dataset_generator/dataset_generator_config.yaml"]',
                        required=False, default="configs/dataset_generator/dataset_generator_config.yaml")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()


def add_user_queries(config: Config, data_store: DataStore) -> None:
    """Loads queries from file (if exists) and adds them as Query objects."""
    if config.queries is not None:
        with config.queries.open("r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if clean_line:
                    data_store.add_query(clean_line, source="user")
            log.info(f"Added user-defined queries from file={config.queries}")


def fetch_and_add_seed_documents(config: Config, data_store: DataStore,
                                 search_engine: BaseSearchEngine) -> List[Document]:
    """Fetch seed documents from the search engine and ensure each is flagged as a cartesian seed.

    Returns the list of fetched documents so callers can reuse them without re-fetching.
    """
    docs_to_generate_queries: List[Document] = search_engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        number_of_docs=config.number_of_docs,
        doc_fields=config.doc_fields
    )

    for doc in docs_to_generate_queries:
        doc.is_used_to_generate_queries = True
        data_store.add_document(doc)
        # Cache hit path: add_document() returned early without updating the stored object.
        data_store.mark_document_as_query_seed(doc.id)

    return docs_to_generate_queries


def generate_and_add_queries_from_documents(config: Config, data_store: DataStore, llm_service: LLMService,
                                            seed_docs: List[Document]) -> None:
    """Generate queries with the LLM service from already-fetched seed documents.

    Adds queries and pre-rates each generated query against its source document with the max
    label from the relevance scale: a query produced from a doc is by definition a perfect match.

    Budget accounting honors the source-priority ordering used by `get_queries_within_budget`:
    only queries with priority <= 'llm' (i.e. user/category/llm) consume budget slots here.
    Cached queries do *not* — they're displaceable, so a saturated cache must not block fresh
    LLM generation.
    """
    llm_threshold = SOURCE_PRIORITY["llm"]

    def _slots_filled() -> int:
        return sum(1 for q in data_store.get_queries() if SOURCE_PRIORITY[q.source] <= llm_threshold)

    remaining = max(0, config.num_queries_needed - _slots_filled())
    if remaining == 0:
        return

    num_queries_per_doc: int = int((remaining // max(1, config.number_of_docs)) + 1)  # always greater or equal to 1
    log.debug(f"Number of documents retrieved for generation: {len(seed_docs)}")
    log.debug(f"Pending queries to generate: {remaining}")
    log.debug(f"Number of queries per document: {num_queries_per_doc}")

    for doc in seed_docs:
        # Re-check between outer iterations so we don't burn an LLM call on doc N+1
        # after the inner loop on doc N already filled the budget.
        if _slots_filled() >= config.num_queries_needed:
            return
        query_response: LLMQueryResponse = llm_service.generate_queries(doc, num_queries_per_doc,
                                                                        config.max_query_terms)
        for query_ in query_response.get_queries():
            if _slots_filled() >= config.num_queries_needed:
                return
            query_obj: Query = data_store.add_query(query_, source="llm")
            data_store.create_rating_score(
                query_obj.id, doc.id, max(config.relevance_label_set),
                "Default max rating is assigned because the query is generated by the document"
            )


def get_queries_within_budget(config: Config, data_store: DataStore) -> List[Query]:
    """Pick the per-run query budget, prioritizing fresh sources over cached ones.

    Stable sort by `(SOURCE_PRIORITY[query.source], insertion_index)` so user/category
    queries asserted this run always make the cut before queries loaded from the disk
    cache, while preserving insertion order within each priority tier.
    """
    queries = data_store.get_queries()
    indexed = list(enumerate(queries))
    indexed.sort(key=lambda iq: (SOURCE_PRIORITY[iq[1].source], iq[0]))
    queries_within_budget = [q for _, q in indexed[:config.num_queries_needed]]
    if len(queries) > len(queries_within_budget):
        log.info(
            "Processing %s of %s queries due to num_queries_needed=%s",
            len(queries_within_budget),
            len(queries),
            config.num_queries_needed,
        )
    return queries_within_budget


def add_cartesian_product_scores(config: Config, data_store: DataStore, llm_service: LLMService) -> None:
    """Complete the (query, doc) matrix with LLM scores."""
    log.debug("Cartesian product is enabled, so adding cartesian product scores")
    for query_obj in get_queries_within_budget(config, data_store):
        for doc_obj in data_store.get_cartesian_prod_docs():
            if not data_store.has_rating_score(query_obj.id, doc_obj.id):
                score_resp: LLMScoreResponse = llm_service.generate_score(
                    doc_obj, query_obj.text, config.relevance_scale, config.save_llm_explanation
                )
                data_store.create_rating_score(
                    query_obj.id, doc_obj.id, score_resp.get_score(),
                    score_resp.explanation if config.save_llm_explanation else None
                )


def expand_docset_with_search_engine_top_k(config: Config, data_store: DataStore,
                                           llm_service: LLMService, search_engine: BaseSearchEngine) -> None:
    """Retrieve docs for each query and score the (q, doc) pairs."""
    if config.query_template is not None:
        log.debug(f"Searching for documents with query template in {config.query_template}")
        for query_obj in get_queries_within_budget(config, data_store):
            docs_eval: List[Document] = search_engine.fetch_for_evaluation(
                keyword=query_obj.text, query_template=config.query_template, doc_fields=config.doc_fields
            )
            for doc_obj in docs_eval:
                data_store.add_document(doc_obj)
                if not data_store.has_rating_score(query_obj.id, doc_obj.id):
                    score_resp: LLMScoreResponse = llm_service.generate_score(
                        doc_obj, query_obj.text, config.relevance_scale, config.save_llm_explanation
                    )
                    data_store.create_rating_score(
                        query_obj.id, doc_obj.id, score_resp.score,
                        score_resp.explanation if config.save_llm_explanation else None
                    )
    else:
        log.warning("Query template not found. Skipping retrieval.")


def main() -> None:
    # configuration and logger definition
    args = parse_args()
    config: Config = Config.load(args.config)
    writer_config: WriterConfig = config.build_writer_config()
    setup_logging(args.verbose)

    # setup
    data_store: DataStore = DataStore(
        autosave_every_n_updates=config.datastore_autosave_every_n_updates
    )
    search_engine: BaseSearchEngine = SearchEngineFactory.build(
        search_engine_type=config.search_engine_type,
        endpoint=config.search_engine_collection_endpoint
    )
    llm: BaseChatModel = LLMServiceFactory.build(LLMConfig.load(config.llm_configuration_file))
    service: LLMService = LLMService(chat_model=llm)
    writer: AbstractWriter = WriterFactory.build(writer_config)

    # load user queries
    add_user_queries(config, data_store)

    # render category-derived queries from each source's explicit values, or from values
    # discovered by the engine when values_query_template_file is set instead of values.
    add_category_queries(config, data_store, search_engine)

    # fetch seed documents only when something downstream actually needs them
    seed_docs: List[Document] = []
    if config.enable_cartesian_product or config.generate_queries_from_documents:
        seed_docs = fetch_and_add_seed_documents(config, data_store, search_engine)

    # generate more queries with LLM service from the same seed documents, if enabled
    if config.generate_queries_from_documents:
        generate_and_add_queries_from_documents(config, data_store, service, seed_docs)

    # score initial docset
    if config.enable_cartesian_product:
        add_cartesian_product_scores(config, data_store, service)

    # expand the docset with search engine topK (adding direct ratings)
    expand_docset_with_search_engine_top_k(config, data_store, service, search_engine)

    # write results
    output_destination = config.output_destination
    log.info(f"Synthetic Dataset has been generated in: {output_destination}")
    data_store.save()
    writer.write(output_destination, data_store)

    # save explanation  - forced to extract value before invoking export_all_records_with_explanation (mypy)
    if config.save_llm_explanation:
        if llm_explanation_path := config.llm_explanation_destination:
            data_store.export_all_records_with_explanation(llm_explanation_path)
            log.info(f"Dataset with LLM explanation is saved into: {llm_explanation_path}")

    # TODO:
    #  work on a better solution, instead of overwriting the corpus.json file, and maybe modify the MtebWriter with the
    #  fetch from the search engine
    if config.output_format == "mteb":
        # copy pasted from MtebWriter
        corpus_path = Path(output_destination) / "corpus.jsonl"
        corpus_path.unlink(missing_ok=True)
        with corpus_path.open("a", encoding="utf-8") as file:
            for doc in search_engine.fetch_all(doc_fields=config.doc_fields):
                doc_id = str(doc.id)
                fields = doc.fields
                title = _to_string(fields.get("title"))
                text = join_fields_as_text(fields=fields, exclude={'id', 'title'})

                row = {"id": doc_id, "title": title, "text": text}
                file.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
