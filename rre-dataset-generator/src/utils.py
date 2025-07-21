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
