from src.config import Config
from src.utils import parse_args

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.llm.llm_service import LLMService
from src.llm.llm_provider_factory import build_openai
from src.llm.llm_config import LLMConfig
from src.search_engine.data_store import DataStore
from src.writers import QuepidWriter

from src.logger import configure_logging
import logging


if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)
    if args.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)

    if args.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)
    log = logging.getLogger(__name__)

    search_engine = SolrSearchEngine(str(config.search_engine_collection_endpoint))
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
    llm = build_openai(LLMConfig.load(config.llm_configuration_file))
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
            data_store.add_rating_score(query_id, doc.id, 2)
        if flag:
            break

    all_docs = docs_to_generate_queries
    # retrieval of the document we need to store for user queries
    for query_text in user_queries:
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_text,
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        all_docs.extend(docs_eval)
        for doc in docs_eval:
            data_store.add_document(doc.id, doc)
            data_store.add_query(query_text, doc.id)

    # retrieval of the document we need to store for generated queries
    for query_rating_context in data_store.get_queries():
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_rating_context.get_query(),
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        all_docs.extend(docs_eval)
        for doc in docs_eval:
            data_store.add_document(doc.id, doc)
            data_store.add_query(query_rating_context.get_query(), doc.id)

    log.debug(f"Number of documents evaluated: {len(docs_to_generate_queries)}")
    for query_rating_context in data_store.get_queries(): #query: 1
        for doc in all_docs: #doc: 1, 2
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

    if config.output_format == 'quepid':
        writer = QuepidWriter(data_store)
        writer.write(str(config.output_destination))
    else:
        error_msg = "Other format than 'quepid' are not yet supported"
        log.error(error_msg)
        raise NotImplementedError(error_msg)

    log.info(f"Synthetic Dataset has been generated in: {config.output_destination}")
