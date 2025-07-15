from src.config import Config
from src.utils import parse_args

if __name__ == "__main__":
    args = parse_args()

    config = Config.load(args.config_file)

