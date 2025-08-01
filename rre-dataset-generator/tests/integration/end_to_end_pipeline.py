from logging import Logger
from typing import List
import pytest

from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from dataset_generator import get_and_setup_logging, add_user_queries, generate_and_add_queries, \
    retrieve_and_add_documents, add_cartesian_product_scores
from src.config import Config
from src.llm.llm_service import LLMService
from src.model.document import Document
from src.search_engine.data_store import DataStore
from src.search_engine.search_engine_base import BaseSearchEngine
from src.search_engine.search_engine_factory import SearchEngineFactory

from src.writers.abstract_writer import AbstractWriter
from src.writers.writer_factory import WriterFactory


def end_to_end_pipeline_with_llm_mock(config):
    """Big Bang integration test with Solr using all pipeline steps."""

    log: Logger = get_and_setup_logging(True)

    # setup
    data_store: DataStore = DataStore()
    search_engine: BaseSearchEngine = SearchEngineFactory.build(search_engine_type=config.search_engine_type,
                                                                endpoint=config.search_engine_collection_endpoint)

    writer: AbstractWriter = WriterFactory.build(config.output_format, data_store)

    # pipeline starts
    add_user_queries(config, data_store)

    assert len(data_store.get_queries()) == 0

    # TO ADAPT LOOKING AT CONFIG PARAMS
    llm_return_list = ["[\"generated query 1\", \"generated query 2\"]",
                       "[\"generated query 3\", \"generated query 4\"]"]
    llm_return_list.extend(["{\"score\":0}"] * 12)
    llm: BaseChatModel = FakeListChatModel(responses=llm_return_list)
    service: LLMService = LLMService(chat_model=llm)

    docs_to_generate_queries: List[Document] = search_engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        doc_number=config.doc_number,
        doc_fields=config.doc_fields)
    log.debug(f"Number of documents retrieved for generation: {len(docs_to_generate_queries)}")

    generate_and_add_queries(config, data_store, service, docs_to_generate_queries)

    retrieve_and_add_documents(config, data_store, search_engine)

    add_cartesian_product_scores(config, data_store, service)

    writer.write(config.output_destination)

    log.info(f"Synthetic Dataset has been generated in: {config.output_destination}")
