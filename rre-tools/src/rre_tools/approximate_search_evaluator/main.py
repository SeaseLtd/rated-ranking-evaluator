import json
import shutil
import logging
from typing import Any
import subprocess
import argparse
from pathlib import Path

from rre_tools.shared.writers import RreWriter
from rre_tools.shared.data_store import DataStore
from rre_tools.shared.logger import setup_logging
from rre_tools.shared.writers import WriterConfig
from rre_tools.approximate_search_evaluator.config import Config

log = logging.getLogger(__name__)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse arguments for CLI.")

    parser.add_argument(
        "--config",
        type=str,
        help='Config file path to use for the application [default: "configs/approximate_search_evaluator/approximate_search_evaluator_config.yaml"]',
        required=False,
        default="configs/approximate_search_evaluator/approximate_search_evaluator_config.yaml",
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()

def add_vector(rating_filename: str | Path,
               embedding_filename: str | Path,
               datastore: DataStore) -> None:
    """
    Parse the writer output and add vectors
    under the '$vector' field inside each query's placeholders.
    """
    log.debug("Loading rating file: %s", rating_filename)
    with open(Path(rating_filename), "r", encoding="utf-8") as f:
        rating_data: dict[str, Any] = json.load(f)

    log.debug("Loading embeddings from: %s", embedding_filename)
    embeddings: dict[str, str] = {}
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
            log.debug("Query_id: %s", query_id)
            if query_id and (query_id in embeddings):
                placeholders["$vector"] = embeddings[query_id]
                updated_queries += 1

            query_dict["placeholders"] = placeholders

    log.debug("Updated %d queries with vectors.", updated_queries)

    with open(rating_filename, "w", encoding="utf-8") as f:
        json.dump(rating_data, f, indent=2, ensure_ascii=False)

    log.debug("Written updated ratings back to %s", rating_filename)
    return

def setup_rre(eval_folder : Path, search_engine_type : str, version : str) -> None:
    subprocess.run(
        [
            "mvn", "archetype:generate",
            "-Psease",
            "-B",
            "-DarchetypeGroupId=io.sease",
            f"-DarchetypeArtifactId=rre-maven-external-{search_engine_type}-archetype",
            "-DarchetypeVersion=1.1",
            "-DgroupId=io.sease.approximate-evaluator",
            f"-DartifactId={eval_folder}",
            "-Dversion=1.1",
            f"-D{'es' if search_engine_type == 'elasticsearch' else 'solr'}Version={version}"
        ],
        check=True
    )

def run_rre_evaluate(eval_folder : Path) -> None:
    """
    Run `mvn rre:evaluate` inside rre-evaluator-solr-external folder.
    """
    eval_dir = Path(__file__).parent.parent.parent.parent / eval_folder
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
    args = _parse_args()
    setup_logging(args.verbose)
    config: Config = Config.load(args.config)

    eval_folder = Path(f"{config.search_engine_type}-evaluator")
    rre_resources_folder = eval_folder / "src" / "etc"
    templates_folder = rre_resources_folder / "templates"
    conf_sets_folder = rre_resources_folder / "configuration_sets"
    ratings_folder = rre_resources_folder / "ratings"

    if eval_folder.is_dir():
        shutil.rmtree(eval_folder)

    setup_rre(eval_folder, config.search_engine_type, config.search_engine_version)

    if rre_resources_folder.exists() and rre_resources_folder.is_dir():
        shutil.rmtree(rre_resources_folder)

    templates_folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(config.query_template, templates_folder / config.query_template.name)

    conf_sets_folder.mkdir(parents=True, exist_ok=True)
    for version in ["v1.0", "v1.1"]: # if we use just one version, it breaks :)
        conf_sets_version_folder = conf_sets_folder / version
        conf_sets_version_folder.mkdir(parents=True, exist_ok=True)
        with open(conf_sets_version_folder / config.conf_sets_filename, "w", encoding="utf-8") as f:
            to_dump = {
                config.search_engine_url_alias: [config.search_engine_url.encoded_string()],
                config.collection_name_alias: config.collection_name
            }
            json.dump(to_dump, f, indent=2, ensure_ascii=False)


    log.debug("Initializing DataStore")
    data_store = DataStore()

    if config.ratings_path is not None:
        log.debug("Using the existing ratings file...")
        ratings_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy(config.ratings_path, ratings_folder / "ratings.json")
        ratings_file = config.ratings_path
    else:
        log.debug("Writing initial ratings file with RreWriter...")
        writer = RreWriter(
            writer_config=WriterConfig(
                index=config.collection_name,
                id_field=config.id_field,
                query_template=config.query_template.name,
                query_placeholder=config.query_placeholder if config.query_placeholder is not None else "$query",
                output_format='rre'
            )
        )
        writer.write(ratings_folder, data_store)
        ratings_file = ratings_folder / "ratings.json"

    if config.embeddings_folder is not None:
        log.debug("Adding vectors to ratings file...")
        add_vector(ratings_file, config.embeddings_folder / "queries_embeddings.jsonl", data_store)
    else:
        log.warning("No embeddings folder was specified. If the specified templates has a '$vector' placeholder, this "
                    "will break RRE evaluation.")

    log.info("Running Maven RRE evaluation...")
    run_rre_evaluate(eval_folder)
    log.info("Evaluation finished.")

    shutil.copy(eval_folder / "target" / "rre" / "evaluation.json", config.output_destination / "rre_evaluation_results.json")
    log.info(f"Evaluation file saved to `{config.output_destination}/` directory.")

    if not args.verbose:
        shutil.rmtree(eval_folder)
        log.debug("RRE evaluation folder not cleaned up.")


if __name__ == "__main__":
    main()
