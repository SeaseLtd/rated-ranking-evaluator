import sys
from dataset_generator.utils import parse_args  # Replace with the actual module name

def test_parse_args(monkeypatch):
    test_args = ['dataset-generator', '--config_file', 'test_config.yaml', '--verbose']
    monkeypatch.setattr(sys, 'argv', test_args)

    args = parse_args()

    assert args.config_file == 'test_config.yaml'
    assert args.verbose is True

def test_parse_args_with_default(monkeypatch):
    test_args = ['dataset-generator']
    monkeypatch.setattr(sys, 'argv', test_args)

    args = parse_args()

    assert args.config_file == 'config.yaml'
    assert args.verbose is False
