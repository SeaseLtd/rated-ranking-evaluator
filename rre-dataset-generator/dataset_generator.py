from src.config import Config
from src.utils import parse_args

from src.search_engine.solr_search_engine import SolrSearchEngine

if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)

    search_engine = SolrSearchEngine('http://localhost:8983/solr/testcore/')

    docs = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                               doc_number=config.doc_number,
                                                               doc_fields=config.doc_fields)

    # docs = search_engine.fetch_for_evaluation(keyword="and",
    #                                           query_template=config.query_template,
    #                                           doc_fields=config.doc_fields)
