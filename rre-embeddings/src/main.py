import argparse
import logging

import mteb
from mteb.models.cache_wrapper import CachedEmbeddingWrapper

from src.config import Config
from src.custom_tasks.reranking_task import CustomRerankingTask
from src.custom_tasks.retrieval_task import CustomRetrievalTask
from src.writers.embedding_writer import EmbeddingWriter

log = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse arguments for CLI.")

    parser.add_argument(
        "--config",
        type=str,
        help='Config file path to use for the application [default: "config.yaml"]',
        required=False,
        default="config.yaml",
    )

    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = _parse_args()
    config: Config = Config.load(args.config)
    task_map = {
        "retrieval": CustomRetrievalTask(),
        "reranking": CustomRerankingTask(),
    }

    model = mteb.get_model(config.model_id)

    cached = CachedEmbeddingWrapper(model, cache_path="cache")
    log.info(f"Started evaluating MTEB {config.task_to_evaluate} task")
    evaluation = mteb.MTEB(
        tasks=[task_map.get(config.task_to_evaluate, CustomRetrievalTask())]
    )
    evaluation.run(
        cached, output_folder=config.output_dest, overwrite_results=True, config=config
    )
    log.info(f"Finished evaluating MTEB {config.task_to_evaluate} task")

    task_name = "CustomRetrievalTask"
    if config.task_to_evaluate == "reranking":
        task_name = "CustomRerankingTask"

    writer: EmbeddingWriter = EmbeddingWriter(
        config=config,
        cached=cached,
        cache_path="cache",
        task_name=task_name,
        normalize_embeddings=True,
        batch_size=256,
    )
    log.info(f"Writing documents and queries embeddings to {config.embeddings_dest} ")
    writer.write(config.embeddings_dest)


if __name__ == "__main__":
    main()
