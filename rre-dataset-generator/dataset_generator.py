import logging

from src.config import Config
from src.search_engine.elasticsearch_search_engine import ElasticsearchSearchEngine
from src.utils import parse_args

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.logger import configure_logging
import logging

if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)
    if args.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.INFO)

    search_engine = ElasticsearchSearchEngine('http://localhost:9200/testindex/')

    docs = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                               doc_number=config.doc_number,
                                                               doc_fields=config.doc_fields)
    print(docs)
    # docs = search_engine.fetch_for_evaluation(keyword="and",
    #                                           query_template=config.query_template,
    #                                           doc_fields=config.doc_fields)
