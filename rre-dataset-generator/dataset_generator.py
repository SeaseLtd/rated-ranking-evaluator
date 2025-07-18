from src.config import Config
from src.utils import parse_args, count_non_empty_lines

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.llm.llm_service import LLMService
from src.llm.llm_provider_factory import build_openai
from src.llm.llm_config import LLMConfig
from src.search_engine.data_store import DataStore


if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)

    search_engine = SolrSearchEngine('http://localhost:8983/solr/testcore/')
    data_store = DataStore()

    docs_to_generate_queries = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                                        doc_number=config.doc_number,
                                                                        doc_fields=config.doc_fields)

    llm = build_openai(LLMConfig.load(config.llm_configuration_file))
    service = LLMService(chat_model=llm)

    num_queries_per_doc = ( (config.num_queries_needed - count_non_empty_lines(config.queries)) // config.doc_number) + 1

    for doc in docs_to_generate_queries:
        data_store.add_document(doc.id, doc)
        query = service.generate_queries(doc, num_queries_per_doc)
        data_store.add_query(query, doc.id)

    for query_id in data_store.get_queries():
        query_text = data_store.get_query(query_id)
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_text,
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        for doc in docs_eval:
            data_store.add_document(doc.id, doc)

        # loop looking at all docs not rated in the data_store for that query
