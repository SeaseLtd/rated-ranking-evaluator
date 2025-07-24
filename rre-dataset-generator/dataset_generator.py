# configuration params
from src.utils import parse_args
from src.config import Config
from src.llm.llm_service import LLMService
from src.llm.llm_config import LLMConfig

# data structures
from src.search_engine.data_store import DataStore

# build factories
from src.search_engine import build_search_engine
from src.llm import build_chat_model
from src.writers import build_writer

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

    search_engine = build_search_engine(search_engine_type=config.search_engine_type,
                                        endpoint=config.search_engine_collection_endpoint)
    data_store = DataStore()

    user_queries = []
    if config.queries is not None:
        with open(config.queries, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():
                    user_queries.append(line.strip())

    # retrieval of the documents needed to generate the queries
    docs_to_generate_queries = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                                        doc_number=config.doc_number,
                                                                        doc_fields=config.doc_fields)
    log.debug(f"Number of documents retrieved for generation: {len(docs_to_generate_queries)}")
    llm = build_chat_model(LLMConfig.load(config.llm_configuration_file))
    service = LLMService(chat_model=llm)

    num_queries_per_doc = int(( (config.num_queries_needed - len(user_queries)) // config.doc_number) * 1.5)

    # query generation step
    flag = False
    for doc in docs_to_generate_queries:
        data_store.add_document(doc.id, doc)
        query_texts = service.generate_queries(doc, num_queries_per_doc)
        for query_text in query_texts:
            if len(data_store.get_queries()) >= config.num_queries_needed:
                flag = True
                break
            query_id = data_store.add_query(query_text, doc.id)
            data_store.add_rating_score(query_id, doc.id, max(config.relevance_label_set))
        if flag:
            break

    log.debug(f"Number of documents evaluated: {len(docs_to_generate_queries)}")
    queries_to_add = data_store.get_queries()
    for query_rating_context in queries_to_add:
        for doc in data_store.get_documents():
            data_store.add_query(query_rating_context.get_query(), doc.id)

    # loop looking at all docs not rated in the data_store for that query
    for query_rating_context in data_store.get_queries():
        for doc_id in query_rating_context.get_doc_ids():
            if not data_store.has_rating_score(query_rating_context.get_query_id(), doc_id):
                score = service.generate_score(data_store.get_document(doc_id),
                                               query_rating_context.get_query(),
                                               config.relevance_scale)
                data_store.add_rating_score(query_rating_context.get_query_id(),
                                            doc_id,
                                            score)

    writer = build_writer(config.output_format, data_store)
    writer.write(config.output_destination)

    log.info(f"Synthetic Dataset has been generated in: {config.output_destination}")
