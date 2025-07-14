import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    return parser.parse_args()