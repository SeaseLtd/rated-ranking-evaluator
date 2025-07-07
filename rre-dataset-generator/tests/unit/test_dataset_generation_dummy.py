import sys
import os
import logging
from typer.testing import CliRunner

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dataset_generator.main import app
from dataset_generator.logger import configure_logging

# Configure logging as soon as the module is loaded
configure_logging()


def test_argparse_yaml_with_list(caplog):
    # Set up logging capture
    caplog.set_level(logging.INFO)
    
    runner = CliRunner()
    # Pass config_path as a positional argument
    result = runner.invoke(app, ["src/yaml_configs/config.yml"])
    
    # Print the logs for debugging
    for record in caplog.records:
        print(f"LOG: {record.message}")
    
    # Check if the log message appears in any of the log records
    assert any("Starting dataset generation process..." in record.message 
              for record in caplog.records)
    assert result.exit_code == 0