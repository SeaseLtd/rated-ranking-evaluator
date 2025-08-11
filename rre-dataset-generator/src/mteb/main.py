import logging

import mteb
import numpy as np
from mteb.models.cache_wrapper import CachedEmbeddingWrapper, TextVectorMap

from src.mteb.custom_reranking_task import MyRerankingTask
from src.mteb.custom_retrieval_task import MyRetrievalTask

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logger = logging.getLogger("mteb-cache")

    model = mteb.get_model("sentence-transformers/all-MiniLM-L6-v2")
    cached = CachedEmbeddingWrapper(model, cache_path="cache")

    evaluation = mteb.MTEB(tasks=[MyRetrievalTask(), MyRerankingTask()])
    results = evaluation.run(cached, output_folder="results", overwrite_results=True)

    vector_map = TextVectorMap("cache/MyRetrievalTask")
    vector_map.load(name="MyRetrievalTask")
    vectors = np.asarray(vector_map.vectors)

    zero_mask = (vectors == 0).all(axis=1)
    vectors = vectors[~zero_mask]

    print(len(vectors))  # combined corpus + queries 'text' fields
    for vector in vectors:
        print(vector)

    cached.close()
    del cached

    vector_map.close()
    del vector_map

