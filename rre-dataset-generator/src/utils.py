import argparse
import re
import html
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    return parser.parse_args()

def clean_text(text):
    tag_regex = re.compile('<.*?>')
    text_without_html = re.sub(tag_regex, '', text)
    return html.unescape(re.sub("\s\s+", " ", text_without_html))

def count_non_empty_lines(file_path: Path) -> int:
    count = 0
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():  # Strip removes whitespace; if anything remains, it's a non-empty line
                count += 1
    return count
