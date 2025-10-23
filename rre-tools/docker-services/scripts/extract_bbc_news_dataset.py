import argparse
import json
import uuid

from datasets import load_dataset
from tqdm import tqdm

CONTENT_MAX_LEN = 1000
DATASET_SIZE = 100000


def truncate_content(txt: str) -> str:
    if len(txt) > CONTENT_MAX_LEN:
        truncated: str = txt[:CONTENT_MAX_LEN]

        next_dot = txt.find('.', CONTENT_MAX_LEN)
        if next_dot != -1 and next_dot - CONTENT_MAX_LEN < 200:
            truncated = txt[:next_dot + 1]

        return truncated
    return txt


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Extract BBC News Dataset")
    parser.add_argument('--filename', type=str, default='dataset.json', help='Output filename')
    args = parser.parse_args()

    months = ['2025-06', '2025-05', '2025-04', '2025-03', '2025-02', '2025-01',
              '2024-12', '2024-11', '2024-10', '2024-09', '2024-08', '2024-07', '2024-06', '2024-05', '2024-04',
              '2024-03', '2024-02', '2024-01',
              '2023-12', '2023-11', '2023-10', '2023-09', '2023-08', '2023-07', '2023-06', '2023-05', '2023-04',
              '2023-03', '2023-02', '2023-01',
              '2022-12', '2022-11', '2022-10', '2022-09', '2022-08', '2022-07', '2022-06', '2022-05', '2022-04',
              '2022-03', '2022-02', '2022-01',
              '2021-12', '2021-11', '2021-10', '2021-09', '2021-08', '2021-07', '2021-06', '2021-05', '2021-04',
              '2021-03', '2021-02', '2021-01',
              '2020-12', '2020-11', '2020-10', '2020-09', '2020-08', '2020-07', '2020-06', '2020-05', '2020-04',
              '2020-03', '2020-02', '2020-01',
              '2019-12', '2019-11', '2019-10', '2019-09', '2019-08', '2019-07', '2019-06', '2019-05', '2019-04',
              '2019-03', '2019-02', '2019-01',
              '2018-12', '2018-11', '2018-10', '2018-09', '2018-08', '2018-07', '2018-06', '2018-05', '2018-04',
              '2018-03', '2018-02', '2018-01',
              '2017-12', '2017-11', '2017-10', '2017-09', '2017-08', '2017-07', '2017-06', '2017-05', '2017-04',
              '2017-03', '2017-02', '2017-01'
              ]
    all_results = []
    seen_links = set()

    for month in tqdm(months):
        ds = load_dataset("RealTimeData/bbc_news_alltime", month)

        for elem in ds['train']:
            # skip if section=empty/None
            if not elem.get("section") or elem.get("section") is None:
                continue

            if not elem.get("title"):
                continue

            # skip duplicates based on the web link
            link = elem.get("link")
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            # truncate long content
            content = elem.get("content", "")
            if not content:
                continue
            text = truncate_content(content)
            elem["content"] = text

            elem["id"] = str(uuid.uuid4())

            #  id first shows up in the json file
            id_val = elem.pop("id")
            new_elem = {"id": id_val, **elem}

            all_results.append(new_elem)
            if len(all_results) == DATASET_SIZE:
                break
        if len(all_results) == DATASET_SIZE:
            break
    print(len(all_results))

    # for solr + vespa
    with open(args.filename, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    # for opensearch + elasticsearch
    # with open("dataset.jsonl", "w", encoding="utf-8") as f:
    #   for obj in all_results:
    #      f.write(json.dumps(obj, ensure_ascii=False) + "\n")
