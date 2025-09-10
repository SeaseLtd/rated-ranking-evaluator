import json
import shutil
import logging
from typing import Dict, Any
import subprocess
from pathlib import Path

from commons.writers import RreWriter
from commons.data_store import DataStore
from commons.logger import configure_logging
from commons.model import WriterConfig

logger = logging.getLogger(__name__)

EMBEDDING_FILENAME = Path("resources/embeddings/queries_embeddings.jsonl")
RATING_FILENAME = Path("rre-evaluator-solr-external/src/ratings/ratings.json")
TEMPLATE_FILENAME = Path("rre-evaluator-solr-external/src/templates/only_vector.json")
DATASTORE_PATH = Path("resources/tmp/datastore.json")


def add_vector(rating_filename: str | Path,
               embedding_filename: str | Path,
               datastore: DataStore) -> None:
    """
    Parse the writer output and add vectors
    under the '$vector' field inside each query's placeholders.
    """
    logger.info("Loading rating file: %s", rating_filename)
    with open(Path(rating_filename), "r", encoding="utf-8") as f:
        rating_data: Dict[str, Any] = json.load(f)

    logger.info("Loading embeddings from: %s", embedding_filename)
    embeddings: Dict[str, str] = {}
    with open(Path(embedding_filename), "r", encoding="utf-8") as f:
        for line in f:
            line_json = json.loads(line)

            embeddings[line_json["id"]] = str(line_json["vector"])

    updated_queries = 0
    for group in rating_data.get("query_groups", []):
        for query_dict in group.get("queries", []):
            placeholders = query_dict.get("placeholders", {})
            query_text = placeholders.get("$query", "")
            query_id = datastore.query_text_to_query_id.get(query_text)

            if query_id and (query_id in embeddings):
                placeholders["$vector"] = embeddings[query_id]
                updated_queries += 1

            query_dict["placeholders"] = placeholders

    logger.info("Updated %d queries with vectors.", updated_queries)

    with open(rating_filename, "w", encoding="utf-8") as f:
        json.dump(rating_data, f, indent=2, ensure_ascii=False)

    logger.info("Written updated ratings back to %s", rating_filename)
    return

def run_rre_evaluate() -> None:
    """
    Run `mvn rre:evaluate` inside rre-evaluator-solr-external folder.
    """
    eval_dir = Path(__file__).parent.parent.parent / "rre-evaluator-solr-external"
    subprocess.run(
        ["mvn", "rre:evaluate"],
        cwd=eval_dir,
        check=True
    )


def main() -> None:
    """
    Generates RRE ratings file with RreWriter,
    enriches it with embeddings, and prepares and execute RRE evaluation.
    """
    configure_logging(logging.INFO)

    TEMPLATE_FILENAME.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path("resources/only_vector.json"), TEMPLATE_FILENAME)

    logger.info("Initializing DataStore from %s", DATASTORE_PATH)
    data_store = DataStore(path=DATASTORE_PATH)

    logger.info("Writing initial ratings file with RreWriter...")
    writer = RreWriter(
        writer_config=WriterConfig(
            index="testcore",
            id_field="id",
            query_template=TEMPLATE_FILENAME.name,
            query_placeholder="$query",
            output_format='rre'
        )
    )
    writer.write(RATING_FILENAME.parent, data_store)

    logger.info("Adding vectors to ratings file...")
    add_vector(RATING_FILENAME, EMBEDDING_FILENAME, data_store)

    logger.info("Running Maven RRE evaluation...")
    run_rre_evaluate()
    logger.info("Evaluation finished.")


if __name__ == "__main__":
    main()
