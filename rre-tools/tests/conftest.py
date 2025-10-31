import pytest
from pathlib import Path
import warnings

@pytest.fixture
def resource_folder():
    return Path(__file__).parent / "resources"

# Since some warnings are raised at import time, I found this solution
warnings.filterwarnings("ignore", category=DeprecationWarning)
