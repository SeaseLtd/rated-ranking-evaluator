# configuration params
from langchain_core.language_models import BaseChatModel
from src.writers.abstract_writer import AbstractWriter
from src.search_engine.search_engine_base import BaseSearchEngine
from src.utils import parse_args
from src.config import Config
from src.llm.llm_service import LLMService
from src.llm.llm_config import LLMConfig

# data structures
from src.search_engine.data_store import DataStore

# build factories
from src.llm.llm_provider_factory import LLMServiceFactory
from src.writers.writer_factory import WriterFactory
from src.search_engine.search_engine_factory import SearchEngineFactory

# logging
from src.logger import configure_logging
import logging


if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)

    if args.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)
    log = logging.getLogger(__name__)

    search_engine: BaseSearchEngine = SearchEngineFactory.build(search_engine_type=config.search_engine_type,
                                              endpoint=config.search_engine_collection_endpoint)
    data_store = DataStore()

    num_queries = 0
    if config.queries is not None:
        with open(config.queries, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():
                    data_store.add_query(line)
                    num_queries += 1

    # retrieval of the documents needed to generate the queries
    docs_to_generate_queries = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                                        doc_number=config.doc_number,
                                                                        doc_fields=config.doc_fields)
    log.debug(f"Number of documents retrieved for generation: {len(docs_to_generate_queries)}")
    llm: BaseChatModel = LLMServiceFactory.build(LLMConfig.load(config.llm_configuration_file))
    service = LLMService(chat_model=llm)

    num_queries_per_doc = int(( (config.num_queries_needed - num_queries) // config.doc_number) * 1.5)

    # query generation step
    all_queries_generated = False
    for doc in docs_to_generate_queries:
        data_store.add_document(doc.id, doc)
        queries = service.generate_queries(doc, num_queries_per_doc)
        for query_text in queries:
            if len(data_store.get_queries()) >= config.num_queries_needed:
                all_queries_generated = True
                break
            query_id = data_store.add_query(query_text, doc.id)
            data_store.add_rating_score(query_id, doc.id, max(config.relevance_label_set))
        if all_queries_generated:
            break

    log.debug(f"Number of documents evaluated: {len(docs_to_generate_queries)}")

    # retrieval of the document we need to store for generated queries
    for query_rating_context in data_store.get_queries():
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_rating_context.get_query(),
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        for doc in docs_eval:
            if not data_store.has_document(doc.id):
                data_store.add_document(doc.id, doc)

    # loop looking at all docs not rated in the data_store for that query
    for query_rating_context in data_store.get_queries():
        for doc in data_store.get_documents():
            if not data_store.has_rating_score(query_rating_context.get_query_id(), doc.id):
                score = service.generate_score(data_store.get_document(doc.id),
                                               query_rating_context.get_query(),
                                               config.relevance_scale)
                data_store.add_rating_score(query_rating_context.get_query_id(),
                                            doc.id,
                                            score)

    writer: AbstractWriter = WriterFactory.build(config.output_format, data_store)
    writer.write(config.output_destination)

    log.info(f"Synthetic Dataset has been generated in: {config.output_destination}")
