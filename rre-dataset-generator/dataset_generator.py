# configuration params
from logging import Logger, getLogger, DEBUG, INFO
from typing import List

from src.logger import configure_logging
from src.config import Config
from src.utils import parse_args
from src.data_store import DataStore
from src.llm import LLMConfig, LLMServiceFactory, LLMService
from src.model import Query, Document, LLMQueryResponse, LLMScoreResponse
from src.search_engine import SearchEngineFactory
from src.writers import WriterFactory


class Pipeline:
    def __init__(self, config: Config):
        self.config = config
        self.log = self._setup_logging(config.verbose)
        self.data_store = DataStore()
        self.search_engine = SearchEngineFactory.build(
            search_engine_type=config.search_engine_type,
            endpoint=config.search_engine_collection_endpoint
        )
        llm_model = LLMServiceFactory.build(LLMConfig.load(config.llm_configuration_file))
        self.llm_service = LLMService(chat_model=llm_model)
        self.writer = WriterFactory.build(config)

    @staticmethod
    def _setup_logging(verbose: bool = False) -> Logger:
        log_level = DEBUG if verbose else INFO
        configure_logging(log_level)
        return getLogger(__name__)

    def run(self):
        self.log.info("Starting dataset generation pipeline...")

        self._add_user_queries()
        docs_for_generation = self._fetch_docs_for_query_generation()
        self._generate_and_add_queries(docs_for_generation)
        self._retrieve_and_add_documents()
        self._add_cartesian_product_scores()
        self._write_output()
        # save the dataset stored as a JSON file
        self.data_store.save() 
        
        self.log.info(f"Synthetic Dataset has been generated in: {self.config.output_destination}")
        if self.config.save_llm_explanation:
            self._export_explanations()
            self.log.info(f"Dataset with LLM explanation is saved into: {self.config.llm_explanation_destination}")

    def _add_user_queries(self):
        if not self.config.queries:
            return
        self.log.info(f"Adding user-provided queries from {self.config.queries}")
        with open(self.config.queries, 'r', encoding='utf-8') as f:
            for line in f:
                if cleaned := line.strip():
                    self.data_store.add_query(Query(text=cleaned))

    def _fetch_docs_for_query_generation(self) -> List[Document]:
        self.log.info(f"Fetching {self.config.doc_number} documents for query generation.")
        docs = self.search_engine.fetch_for_query_generation(
            documents_filter=self.config.documents_filter,
            doc_number=self.config.doc_number,
            doc_fields=self.config.doc_fields
        )
        self.log.debug(f"Retrieved {len(docs)} documents.")
        return docs

    def _generate_and_add_queries(self, docs: List[Document]):
        num_existing_queries = len(self.data_store.get_queries())
        if num_existing_queries >= self.config.num_queries_needed:
            return

        # Guardas sanas
        if not docs:
            self.log.warning("No documents available for query generation. Skipping.")
            return

        self.log.info("Generating new queries...")
        queries_to_gen = self.config.num_queries_needed - num_existing_queries
        num_queries_per_doc = max(1, int((queries_to_gen / len(docs)) * 1.5))  # evita 0 o div/0

        for doc in docs:
            self.data_store.add_document(doc)
            q_response: LLMQueryResponse = self.llm_service.generate_queries(doc, num_queries_per_doc)
            for query_text in q_response.get_queries():
                if len(self.data_store.get_queries()) >= self.config.num_queries_needed:
                    return
                query = Query(text=query_text, generated_from_doc_id=doc.id)
                query_id = self.data_store.add_query(query)  # ← usar el id que puede ser el existente
                self.data_store.create_rating_score(
                    query_id, doc.id, max(self.config.relevance_label_set),
                    "Default max rating for document that generated the query."
                )

    def _retrieve_and_add_documents(self):
        self.log.info("Retrieving documents for all queries...")
        for query in self.data_store.get_queries():
            docs_eval = self.search_engine.fetch_for_evaluation(
                keyword=query.text,
                query_template=self.config.query_template,
                doc_fields=self.config.doc_fields
            )
            for doc in docs_eval:
                if not self.data_store.has_document(doc.id):
                    self.data_store.add_document(doc)

    def _add_cartesian_product_scores(self):
        self.log.info("Generating relevance scores for all query-document pairs...")
        for query in self.data_store.get_queries():
            for doc in self.data_store.get_documents():
                if not self.data_store.has_rating_score(query.id, doc.id):
                    score_response: LLMScoreResponse = self.llm_service.generate_score(
                        doc, query.text, self.config.relevance_scale, self.config.save_llm_explanation
                    )
                    self.data_store.create_rating_score(
                        query.id, doc.id, score_response.score, score_response.explanation
                    )

    def _write_output(self):
        self.log.info(f"Writing output to {self.config.output_destination}...")
        self.writer.write(self.config.output_destination, self.data_store)

    def _export_explanations(self):
        """Export LLM explanations for all query-document pairs to a JSON file with:
            - query: The query text
            - doc_id: The document ID
            - rating: The relevance score
            - explanation: The LLM's explanation for the rating
        """
        if not self.config.llm_explanation_destination:
            self.log.info("No explanation destination configured. Skipping export.")
            return
            
        self.log.info(f"Exporting explanations to {self.config.llm_explanation_destination}...")
        try:
            self.data_store.export_all_records_with_explanation(self.config.llm_explanation_destination)
            self.log.info(f"Successfully exported explanations to {self.config.llm_explanation_destination}")
        except Exception as e:
            self.log.error(f"Failed to export explanations: {str(e)}")
            raise

if __name__ == "__main__":
    args = parse_args()
    cfg = Config.load(args.config_file)
    cfg.verbose = args.verbose
    pipeline = Pipeline(config=cfg)
    pipeline.run()
