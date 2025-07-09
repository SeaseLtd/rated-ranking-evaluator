import argparse
from src.config import load_config

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments for CLI.')

    parser.add_argument('-c', '--config_file', type=str,
                        help='Config file path to use for the application [default: \"config.yaml\"]',
                        required=False, default="config.yaml")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    try:
        config = load_config(args.config_file)
        print("Configuration loaded successfully.")
        # print(config.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error loading configuration: {e}")
