import json
import collections

# --- Configuration ---
# Input file with <query, doc_id, gain> triplets
INPUT_FILE = 'relevance_judgements.csv'
# Output file for RRE
OUTPUT_FILE = 'generated_ratings.json'
# The name of the Elasticsearch index where documents are stored
INDEX_NAME = 'my_index_name'
# The field in the documents that contains the unique ID
ID_FIELD = 'id'
# The query template file to be used for all queries
QUERY_TEMPLATE = 'match_query.json'
# The placeholder name within the template (e.g., "${query}")
QUERY_PLACEHOLDER = 'query'


def create_ratings_file():
    """
    Reads a TSV file of relevance judgements and converts it into the RRE
    JSON format.
    """
    judgements_by_query = collections.defaultdict(list)

    print(f"Reading judgements from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f_in:
        for line in f_in:
            if line.startswith('#') or not line.strip():
                continue

            try:
                query, doc_id, gain = line.strip().split(',')
                judgements_by_query[query].append((doc_id, int(gain)))
            except ValueError:
                print(f"Skipping malformed line: {line.strip()}")

    query_groups = []
    for query_text, relevant_docs in judgements_by_query.items():
        relevant_documents_list = [
            {"document_id": doc_id, "gain": gain}
            for doc_id, gain in relevant_docs
        ]

        query_group = {
            "name": query_text,
            "queries": [
                {
                    "template": QUERY_TEMPLATE,
                    "placeholders": {
                        QUERY_PLACEHOLDER: query_text
                    }
                }
            ],
            "relevant_documents": relevant_documents_list
        }
        query_groups.append(query_group)

    final_ratings = {
        "index": INDEX_NAME,
        "id_field": ID_FIELD,
        "query_placeholder": QUERY_PLACEHOLDER,
        "query_groups": query_groups
    }

    print(f"Writing RRE-formatted ratings to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f_out:
        json.dump(final_ratings, f_out, indent=2)

    print("Done.")

if __name__ == "__main__":
    create_ratings_file()
