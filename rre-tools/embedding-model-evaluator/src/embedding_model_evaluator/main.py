import argparse
import logging
from pathlib import Path

import mteb
from mteb.models.cache_wrapper import CachedEmbeddingWrapper
from mteb.overview import TASKS_REGISTRY

from embedding_model_evaluator.config import Config
from embedding_model_evaluator.custom_tasks import CustomRerankingTask, CustomRetrievalTask # noqa: F401
from embedding_model_evaluator.writers import EmbeddingWriter
from commons.logger import configure_logging # type: ignore[import]

log = logging.getLogger(__name__)

CACHE_PATH = Path("resources") / "cache"

TASKS_NAME_MAPPING = {
        "retrieval": "CustomRetrievalTask",
        "reranking": "CustomRerankingTask",
    }


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
    configure_logging()

    args = _parse_args()
    config: Config = Config.load(args.config)

    model = mteb.get_model(config.model_id)

    model_with_cached_emb = CachedEmbeddingWrapper(model, cache_path=CACHE_PATH)
    log.info(f"Started evaluating MTEB {config.task_to_evaluate} task")
    evaluation = mteb.MTEB(
        tasks=[TASKS_REGISTRY[TASKS_NAME_MAPPING.get(config.task_to_evaluate, "CustomRetrievalTask")]()]
    )
    evaluation.run(
        model=model_with_cached_emb,
        output_folder=config.output_dest,
        overwrite_results=True,
        config=config
    )
    log.info(f"Finished evaluating MTEB {config.task_to_evaluate} task")

    writer: EmbeddingWriter = EmbeddingWriter(
        config=config,
        cached=model_with_cached_emb,
        cache_path=CACHE_PATH,
        task_name=TASKS_NAME_MAPPING.get(config.task_to_evaluate, "CustomRetrievalTask"),
        normalize_embeddings=True,
        batch_size=256,
    )
    log.info(f"Writing documents and queries embeddings to {config.embeddings_dest} ")
    writer.write(config.embeddings_dest)


if __name__ == "__main__":
    main()
