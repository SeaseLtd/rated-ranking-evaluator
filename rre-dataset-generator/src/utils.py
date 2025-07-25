import argparse
import re
import html

_TAG_REGEX = re.compile('<.*?>')

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    parser.add_argument('-v', '--verbose',action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()

def clean_text(text: str) -> str:
    text_without_html = re.sub(_TAG_REGEX, '', text).strip()
    return html.unescape(re.sub(r"\s{2,}", " ", text_without_html))

import json
from pathlib import Path
def json_to_jsonl_elasticsearch(input_file_path: Path) -> None:
    # Load the list of JSON objects from the input file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Write each object as a separate line in the JSONL file
    with open(str(input_file_path)+'l', 'w', encoding='utf-8') as f:
        for obj in data:
            f.write(json.dumps({"index":{'_id': obj['id']}}) + '\n')
            f.write(json.dumps({k:obj[k] for k in obj.keys() if k != 'id'}) + '\n')
