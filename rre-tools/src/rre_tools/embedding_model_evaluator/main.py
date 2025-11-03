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
import time
import json
from pathlib import Path
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
        help='Config file path to use for the application [default: '
             '"configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml"]',
        required=False,
        default="configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml",
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()


def _build_task(task_name: str, dataset_name: str, split: str) -> Any:
    """
    Instantiate the requested task from TASKS_REGISTRY and inject dataset/split.
    We try constructor kwargs first; if not supported, we set attributes (best-effort).
    This keeps us decoupled from CustomTask signatures while remaining robust.
    """

    task_cls = TASKS_REGISTRY[task_name]

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


def _get_mteb_leaderboard_avg_main_score(model_name: str, task_type: str) -> float:
    b = mteb.get_benchmark("MTEB(eng, v2)")
    task = [t for t in b.tasks if t.metadata.type == task_type]
    # load results from https://github.com/embeddings-benchmark/results
    results = mteb.load_results(models=[model_name], tasks=task).join_revisions()

    scores: list[float] = []
    for model_results in results.model_results:
        for task_result in model_results.task_results:
            for split_name, split_subsets in task_result.scores.items():
                for task_subset in split_subsets:
                    if "main_score" in task_subset:
                        val = task_subset["main_score"]
                        if isinstance(val, (int, float)):
                            scores.append(float(val))
    if len(scores) > 0:
        return sum(scores) / len(scores)
    return 0.0


def _append_mteb_leaderboard_score(file_path: Path, avg_main_score: float) -> None:
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    data["avg_main_score_mteb_leaderboard"] = avg_main_score

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main() -> None:
    args = _parse_args()
    setup_logging(args.verbose)
    config: Config = Config.load(args.config)

    # --- Sanity logs (explicit & helpful) ---
    log.info("MTEB run → task=%s | dataset=%s | split=%s | model=%s",
             config.task_to_evaluate, config.dataset_name, config.split, config.model_id)

    # --- Model + caching wrapper ---
    model = mteb.get_model(config.model_id, trust_remote_code=True)
    task_name = TASKS_NAME_MAPPING.get(config.task_to_evaluate, None)
    if task_name is None:
        log.error("Custom task name is not defined: %s", task_name)
        raise ValueError("Custom task name is not defined.")

    model_name_additional_path = config.model_id.replace("/", "__").replace(" ", "_")
    model_with_cache_path = CACHE_PATH / model_name_additional_path
    model_with_cache = CachedEmbeddingWrapper(model, cache_path=model_with_cache_path)

    # --- Task instance (in-memory) ---
    try:
        task = _build_task(
            task_name=task_name,
            dataset_name=config.dataset_name,
            split=config.split,
        )
    except Exception as e:
        log.error("Failed to build MTEB task: %s", e)
        raise ValueError("Failed to build MTEB task.")

    # --- Evaluation (in-memory) ---
    log.info("Starting MTEB evaluation...")
    start = time.time()
    evaluation = mteb.MTEB(tasks=[task])
    evaluation.run(
        model=model_with_cache,
        output_folder=config.output_dest,
        overwrite_results=True,
        config=config,
    )

    end = time.time()
    log.info("Finished MTEB evaluation.")
    log.info(f"Time took for MTEB evaluation: {(end - start) / 60:.2f} minutes")

    log.info("Adding mteb leaderboard average main score...")

    if config.output_dest is None:
        raise ValueError("config.output_dest is not set")

    # task result is in {output_folder} / {model_name} / {model_revision} / {task_name}.json
    task_result_path: Path = (config.output_dest / model_name_additional_path /
                              mteb.get_model_meta(config.model_id).revision / f"{task_name}.json")
    avg_main_score: float = _get_mteb_leaderboard_avg_main_score(model_name=config.model_id,
                                                                 task_type=config.task_to_evaluate.capitalize())
    _append_mteb_leaderboard_score(file_path=task_result_path, avg_main_score=avg_main_score)

    # --- Optional: write embeddings (kept for parity with previous behavior) ---
    writer = EmbeddingWriter(
        corpus_path=config.corpus_path,
        queries_path=config.queries_path,
        cached=model_with_cache,
        cache_path=model_with_cache_path,
        task_name=task_name,
        batch_size=256,
    )
    log.info(f"Writing embeddings to {config.embeddings_dest} ...")
    writer.write(config.embeddings_dest)
    log.info("Finished writing embeddings.")


if __name__ == "__main__":
    main()
