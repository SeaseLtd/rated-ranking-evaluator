from pathlib import Path

# Map simple "task key" -> registered MTEB task class name
TASKS_NAME_MAPPING = {
    "retrieval": "CustomRetrievalTask",
    "reranking": "CustomRerankingTask",
}

CACHE_PATH = Path("resources/cache")
