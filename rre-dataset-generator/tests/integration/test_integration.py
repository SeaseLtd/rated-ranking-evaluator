from langchain_core.language_models import FakeListChatModel

from src.config import Config
from src.utils import parse_args, count_non_empty_lines

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.llm.llm_service import LLMService
from src.search_engine.data_store import DataStore
from src.model.document import Document
#from src.writers import QuepidWriter

from tests.mocks.solr import MockResponseSolrEngine, MockResponseUniqueKey

from src.logger import configure_logging
import logging
import requests
import sys


def test_main(monkeypatch):
    test_args = ['dataset_generator.py', '--config_file', 'tests/integration/resources/good_config.yaml', '--verbose']
    monkeypatch.setattr(sys, 'argv', test_args)

    arg = parse_args()

    config = Config.load(arg.config_file)

    if arg.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)
    log = logging.getLogger(__name__)

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="mock_id"))
    search_engine = SolrSearchEngine(str(config.search_engine_collection_endpoint))
    data_store = DataStore()

    user_queries = []
    with open(config.queries, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():  # Strip removes whitespace; if anything remains, it's a non-empty line
                user_queries.append(line.strip())

    # retrieval of the documents needed to generate the queries
    mocked_docs = [
         {
            "mock_id": "1",
            "mock_title": "A first mocked title",
            "mock_description": "A first mocked description"
        },
        {
            "mock_id": "2",
            "mock_title": "A second mocked title",
            "mock_description": "A second mocked description"
        },
        {
            "mock_id": "3",
            "mock_title": "A third mocked title",
            "mock_description": "A third mocked description"
        },
    ]
    mocked_docs_dict = [{
        'id': mocked_doc['mock_id'],
        'fields': {k: v for k, v in mocked_doc.items() if k != "mock_id"}
    }
    for mocked_doc in mocked_docs]

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseSolrEngine(mocked_docs, status_code=200))
    docs_to_generate_queries = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                                        doc_number=config.doc_number,
                                                                        doc_fields=config.doc_fields)

    assert docs_to_generate_queries == [Document(**mocked_doc) for mocked_doc in mocked_docs_dict]

    mocked_llm = FakeListChatModel(responses=["Mocked LLM response"])
    service = LLMService(chat_model=mocked_llm)

    num_queries_per_doc = ( (config.num_queries_needed - count_non_empty_lines(config.queries)) // config.doc_number) + 1

    # query generation step
    for doc in docs_to_generate_queries:
        data_store.add_document(doc.id, doc)
        query_text = service.generate_queries(doc, num_queries_per_doc)
        data_store.add_query(query_text, doc.id)

    # retrieval of the document we need to store for user queries
    for query_text in user_queries:
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_text,
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        for doc in docs_eval:
            data_store.add_document(doc.id, doc)
            data_store.add_query(query_text, doc.id)

    # retrieval of the document we need to store for generated queries
    for query_rating_context in data_store.get_queries():
        docs_eval = search_engine.fetch_for_evaluation(keyword=query_rating_context.get_query(),
                                                       query_template=config.query_template,
                                                       doc_fields=config.doc_fields)
        for doc in docs_eval:
            data_store.add_document(doc.id, doc)
            data_store.add_query(query_rating_context.get_query(), doc.id)


    # loop looking at all docs not rated in the data_store for that query
    for query_rating_context in data_store.get_queries():
        for doc_id in query_rating_context.get_doc_ids():
            score = service.generate_score(data_store.get_document(doc_id),
                                           query_rating_context.get_query(),
                                           config.relevance_scale)
            data_store.add_rating_score(query_rating_context.get_query_id(),
                                        doc_id,
                                        score)

    if config.output_format == 'quepid':
        writer = QuepidWriter(data_store)
        writer.write(config.output_destination)
    else:
        error_msg = "Other format than 'quepid' are not yet supported"
        log.error(error_msg)
        raise NotImplementedError(error_msg)

    log.info(f"Synthetic Dataset has been generated in: {config.output_destination}")
