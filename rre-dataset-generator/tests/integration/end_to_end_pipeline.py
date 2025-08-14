from logging import Logger
from typing import List
import pytest
import os
import csv

from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from dataset_generator import (
    get_and_setup_logging, add_user_queries, generate_and_add_queries,
    retrieve_and_add_documents, add_cartesian_product_scores
)
from src.llm.llm_service import LLMService
from src.model.document import Document
from src.model.query_rating_context import QueryRatingContext
from src.search_engine.data_store import DataStore
from src.search_engine.search_engine_base import BaseSearchEngine
from src.search_engine.search_engine_factory import SearchEngineFactory
from src.writers.abstract_writer import AbstractWriter
from src.writers.writer_factory import WriterFactory


def end_to_end_pipeline_with_llm_mock(config, tmp_path):
    """Big Bang integration test with Solr using all pipeline steps."""

    log: Logger = get_and_setup_logging(True)

    # setup
    data_store: DataStore = DataStore()
    search_engine: BaseSearchEngine = SearchEngineFactory.build(
        search_engine_type=config.search_engine_type,
        endpoint=config.search_engine_collection_endpoint
    )
    writer: AbstractWriter = WriterFactory.build(config, data_store)

    add_user_queries(config, data_store)

    assert len(data_store.get_queries()) == 0, "Queries should be empty before generation"

    llm_return_list = [
        "[\"generated query 1\", \"generated query 2\"]",
        "[\"generated query 3\", \"generated query 4\"]"
    ]
    llm_return_list.extend(["{\"score\":0}"] * 12)
    llm: BaseChatModel = FakeListChatModel(responses=llm_return_list)
    service: LLMService = LLMService(chat_model=llm)

    docs_to_generate_queries: List[Document] = search_engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        doc_number=config.doc_number,
        doc_fields=config.doc_fields
    )
    assert len(docs_to_generate_queries) == config.doc_number, "Unexpected number of docs fetched"
    assert all(isinstance(doc, Document) for doc in docs_to_generate_queries)

    generate_and_add_queries(config, data_store, service, docs_to_generate_queries)
    queries = data_store.get_queries()
    assert len(queries) == config.num_queries_needed, "Unexpected number of queries generated"
    assert all(isinstance(q, QueryRatingContext) and q.get_query_text().strip() for q in queries), "Queries must be non-empty strings"

    retrieve_and_add_documents(config, data_store, search_engine)
    retrieved_docs = data_store.get_documents()
    assert len(retrieved_docs) > 0, "No documents retrieved"
    assert all(isinstance(doc, Document) for doc in retrieved_docs)

    add_cartesian_product_scores(config, data_store, service)
    pairs = []
    for query_ctx in data_store.get_queries():
        query_text = query_ctx.get_query_text()
        for doc_id in query_ctx.get_doc_ids():
            rating = query_ctx.get_rating_score(doc_id)
            if rating != QueryRatingContext.DOC_NOT_RATED:
                pairs.append((query_text, doc_id, rating))
    assert len(pairs) > 0, "No query-document pairs scored"

    for p in pairs:
        assert len(p) == 3, f"Something missing in pair {p}"
        assert isinstance(p[2], int), "Score must be numeric"
        assert p[2] in config.relevance_label_set, "Score out of expected range"

    output_file = tmp_path / "generated_dataset.csv"
    writer.write(output_file)
    assert output_file.exists(), f"File not found: {output_file}"

    with open(config.output_destination, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        assert header == ["query", "docid", "rating"], f"Unexpected header: {header}"
        rows = list(reader)
        assert len(rows) > 0, "CSV is empty"
        for row in rows:
            assert len(row) == 3, f"Unexpected CSV row format: {row}"
            assert any(row[1] == doc.id for doc in retrieved_docs), f"DocID in CSV not in retrieved docs: {row[1]}"
            assert int(row[2]) in config.relevance_label_set, f"Rating must be in the relevance label set: {row[2]}"
