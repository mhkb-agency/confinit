from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
import tomllib

__all__ = ["__version__", "main", "_detect_version"]


def _detect_version() -> str:
    try:
        return _pkg_version("confinit")
    except PackageNotFoundError:
        # Fallback: read from pyproject.toml when running from source
        for parent in Path(__file__).resolve().parents:
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                project = data.get("project")
                if isinstance(project, dict):
                    version = project.get("version")
                    if isinstance(version, str):
                        return version
                break
        return "0.0.0"


__version__: str = _detect_version()


def main() -> None:
    print("Hello from confinit!")
