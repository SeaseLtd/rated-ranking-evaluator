import argparse
import json
import uuid

from datasets import load_dataset
from tqdm import tqdm

CONTENT_MAX_LEN = 1000
DATASET_SIZE = 100000


def truncate_content(txt: str) -> str:
    if len(txt) <= CONTENT_MAX_LEN:
        return txt

    truncated_txt: str = txt[:CONTENT_MAX_LEN]
    last_dot_index = truncated_txt.rfind('.')

    if last_dot_index != -1:
        # text size <= CONTENT_MAX_LEN
        return txt[:last_dot_index + 1]

    # find the first dot after CONTENT_MAX_LEN
    next_dot_index = txt.find('.', CONTENT_MAX_LEN)

    if next_dot_index != -1:
        return txt[:next_dot_index + 1]

    return truncated_txt


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Extract BBC News Dataset")
    parser.add_argument('--filename', type=str, default='dataset.json', help='Output filename')
    args = parser.parse_args()

    months = []
    end_year = 2025
    end_month = 6

    start_year = 2017
    start_month = 1

    curr_year = end_year
    curr_month = end_month
    while curr_year >= start_year and curr_month >= start_month:
        months.append(f"{curr_year}-{curr_month:02d}")
        curr_month -= 1
        if curr_month == 0:
            curr_month = 12
            curr_year -= 1

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

    # for solr + vespa
    with open(args.filename, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    # for opensearch + elasticsearch
    # with open("dataset.jsonl", "w", encoding="utf-8") as f:
    #   for obj in all_results:
    #      f.write(json.dumps(obj, ensure_ascii=False) + "\n")
