import pytest
from pathlib import Path

@pytest.fixture
def resource_folder():
    return Path(__file__).parent.parent / "resources"

import warnings

# Since some warnings are raised at import time, I found this solution
warnings.filterwarnings("ignore", category=DeprecationWarning)
