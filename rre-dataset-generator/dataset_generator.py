from src.config import Config
from src.utils import parse_args
import json

from src.search_engine.solr_search_engine import SolrSearchEngine

if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)

    search_engine = SolrSearchEngine('http://localhost:8983/solr/testcore/')

    # docs = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
    #                                                            doc_number=config.doc_number)

    docs = search_engine.fetch_for_evaluation(keyword="and", query_template=config.query_template)

    with open("solr_extracted_dataset.json", "w") as file:
        json.dump(docs, file, indent=4)
        file.write('\n')