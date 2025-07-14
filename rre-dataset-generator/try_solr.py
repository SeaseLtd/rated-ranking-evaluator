import logging
import json

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.config import Config
from src.utils import parse_args
from src.logger import configure_logging

configure_logging(level=logging.DEBUG)

if __name__ == "__main__":
    args = parse_args()

    log = logging.getLogger(__name__)

    config = Config.load(args.config_file)

    search_engine = SolrSearchEngine('http://localhost:8983/solr/testcore/')

    # docs = search_engine.extract_documents_to_generate_queries(documents_filter=config.documents_filter,
    #                                                            doc_number=config.doc_number)

    docs = search_engine.extract_documents_to_evaluate_system(keyword="and", query_template=config.query_template)

    with open("result.json", "w") as file:
        json.dump(docs, file, indent=4)