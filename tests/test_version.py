from __future__ import annotations

from pathlib import Path
import tomllib

import confinit


def test_version_matches_pyproject() -> None:
    # Locate repository root from this test file
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found at repository root"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    assert isinstance(version, str)
    assert confinit.__version__ == version
