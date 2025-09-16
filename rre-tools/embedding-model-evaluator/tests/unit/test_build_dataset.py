from __future__ import annotations

import sys
import subprocess
from pathlib import Path


def _script_path() -> Path:
    # tests/unit/test_build_dataset.py -> up two levels to package root
    return Path(__file__).resolve().parents[2] / "scripts" / "build_mteb_dataset.py"


def test_build_mteb_dataset_help_runs() -> None:
    script = _script_path()
    assert script.exists(), f"Script not found: {script}"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "Download an MTEB dataset" in output


def test_build_mteb_dataset_invalid_args_exits() -> None:
    script = _script_path()
    # Negative value should be rejected by validate_args and exit before any network i/o
    result = subprocess.run(
        [sys.executable, str(script), "--max-docs", "-1"], capture_output=True, text=True
    )
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "must be >= 0" in combined
