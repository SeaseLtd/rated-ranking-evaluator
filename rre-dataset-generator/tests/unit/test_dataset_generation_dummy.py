from src.logger import configure_logging
import pytest
from dataset_generator import parse_args


# Configure logging as soon as the module is loaded
configure_logging()

@pytest.fixture
def args():
    return parse_args()

def test_argparse_with_defaults(args):
    assert args.config_file == "config.yaml"
