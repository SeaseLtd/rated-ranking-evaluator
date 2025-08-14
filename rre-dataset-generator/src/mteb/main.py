import logging
import os
from pathlib import Path

import mteb
import numpy as np
from mteb.models.cache_wrapper import CachedEmbeddingWrapper, TextVectorMap

from src.mteb.custom_reranking_task import MyRerankingTask
from src.mteb.custom_retrieval_task import MyRetrievalTask
from src.mteb.helper import read_corpus

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logger = logging.getLogger("mteb-cache")

    model = mteb.get_model("sentence-transformers/all-MiniLM-L6-v2")
    cached = CachedEmbeddingWrapper(model, cache_path="cache")

    evaluation = mteb.MTEB(tasks=[MyRetrievalTask(), MyRerankingTask()])
    results = evaluation.run(cached, output_folder="results", overwrite_results=True)


    ROOT = Path(__file__).resolve().parent
    DATA_ROOT = ROOT / "data"
    corpus = read_corpus(os.path.join(DATA_ROOT, "corpus.jsonl"))

    texts = [doc["text"] for doc in corpus.values()]
    embeddings = cached.encode(texts, task_name="MyRetrievalTask", name="MyRetrievalTask-corpus", batch_size=256, normalize_embeddings=True)
    vector_map = TextVectorMap("cache/MyRetrievalTask")
    vector_map.load(name="MyRetrievalTask-corpus")
    pairs = list(zip(texts, embeddings))
    for text, embedding in pairs:
        print(text, embedding)
    print(vector_map.get_vector(texts[0]))

    cached.close()
    del cached

    vector_map.close()
    del vector_map
