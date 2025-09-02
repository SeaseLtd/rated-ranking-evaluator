import argparse

import mteb

from src.config import Config
from src.custom_tasks.reranking_task import CustomRerankingTask
from src.custom_tasks.retrieval_task import CustomRetrievalTask


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
    args = _parse_args()
    config: Config = Config.load(args.config)
    task_map = {
        "retrieval": CustomRetrievalTask(),
        "reranking": CustomRerankingTask(),
    }

    model = mteb.get_model(config.model_id)
    evaluation = mteb.MTEB(
        tasks=[task_map.get(config.task_to_evaluate, CustomRetrievalTask())]
    )
    evaluation.run(
        model, output_folder=config.output_dest, overwrite_results=True, config=config
    )


if __name__ == "__main__":
    main()
