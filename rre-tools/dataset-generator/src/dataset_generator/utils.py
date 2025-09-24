import argparse

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    parser.add_argument('-v', '--verbose',action='store_true',
                        help='Activate debug mode for logging [default: False]')

    return parser.parse_args()
