#!/usr/bin/env python3
"""
MTEB execution pipeline entrypoint for Module 2.

- Loads MTEB tasks in-memory (no export to disk required).
- Evaluates either Retrieval or Re-ranking using a cached-embedding wrapper.
- Writes embeddings to disk only after evaluation (optional but kept as before).
- Dataset/split/model/task are driven by Config.
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

import mteb
from mteb.models.cache_wrapper import CachedEmbeddingWrapper
from mteb.overview import TASKS_REGISTRY

from rre_tools.embedding_model_evaluator.config import Config
from rre_tools.embedding_model_evaluator.custom_mteb_tasks import (  # noqa: F401 (tasks must be imported to register)
    CustomRerankingTask,
    CustomRetrievalTask,
)
from rre_tools.embedding_model_evaluator.embedding_writer import EmbeddingWriter
from rre_tools.embedding_model_evaluator.constants import TASKS_NAME_MAPPING, CACHE_PATH
from rre_tools.shared.logger import setup_logging  # type: ignore[import]

log = logging.getLogger(__name__)

CACHE_PATH.mkdir(parents=True, exist_ok=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embedding Model Evaluator (MTEB, in-memory).")
    parser.add_argument(
        "--config",
        type=str,
        help='Config file path to use for the application [default: "configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml"]',
        required=False,
        default="configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml",
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()

def _build_task(task_key: str, dataset_name: str, split: str) -> Any:
    """
    Instantiate the requested task from TASKS_REGISTRY and inject dataset/split.
    We try constructor kwargs first; if not supported, we set attributes (best-effort).
    This keeps us decoupled from CustomTask signatures while remaining robust.
    """
    task_cls_name = TASKS_NAME_MAPPING.get(task_key, "CustomRetrievalTask")
    if task_cls_name not in TASKS_REGISTRY:
        available = ", ".join(sorted(TASKS_REGISTRY.keys()))
        raise KeyError(f"Task '{task_cls_name}' not in TASKS_REGISTRY. Available: {available}")

    task_cls = TASKS_REGISTRY[task_cls_name]

    # Try the flexible constructor path.
    try:
        task = task_cls(dataset_names=[dataset_name], eval_splits=[split])
        return task
    except TypeError:
        # Fallback: default constructor + attribute injection
        task = task_cls()
        if hasattr(task, "dataset_names"):
            setattr(task, "dataset_names", [dataset_name])
        if hasattr(task, "eval_splits"):
            setattr(task, "eval_splits", [split])
        return task


def main() -> None:
    args = _parse_args()
    setup_logging(args.verbose)
    config: Config = Config.load(args.config)

    # --- Sanity logs (explicit & helpful) ---
    log.info("MTEB run → task=%s | dataset=%s | split=%s | model=%s",
             config.task_to_evaluate, config.dataset_name, config.split, config.model_id)

    # --- Model + caching wrapper ---
    model = mteb.get_model(config.model_id, trust_remote_code=True)
    model_name_additional_path = config.model_id.replace("/", "__").replace(" ", "_")
    model_with_cache_path = CACHE_PATH / model_name_additional_path
    model_with_cache = CachedEmbeddingWrapper(model, cache_path=model_with_cache_path)

    # --- Task instance (in-memory) ---
    try:
        task = _build_task(
            task_key=config.task_to_evaluate,
            dataset_name=config.dataset_name,
            split=config.split,
        )
    except Exception as e:
        log.exception("Failed to build MTEB task: %s", e)
        raise

    # --- Evaluation (in-memory) ---
    log.info("Starting MTEB evaluation...")
    evaluation = mteb.MTEB(tasks=[task])
    evaluation.run(
        model=model_with_cache,
        output_folder=config.output_dest,
        overwrite_results=True,
        config=config,
    )
    log.info("Finished MTEB evaluation.")

    # --- Optional: write embeddings (kept for parity with previous behavior) ---
    writer = EmbeddingWriter(
        corpus_path=config.corpus_path,
        queries_path=config.queries_path,
        cached=model_with_cache,
        cache_path=model_with_cache_path,
        task_name=TASKS_NAME_MAPPING.get(config.task_to_evaluate, "CustomRetrievalTask"),
        batch_size=256,
    )
    log.info(f"Writing embeddings to {config.embeddings_dest} ...")
    writer.write(config.embeddings_dest)
    log.info("Done.")


if __name__ == "__main__":
    main()
