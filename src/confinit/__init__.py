"""Confinit public API.

Primary entry points
- load: Resolve a dataclass schema from multiple sources.
- env / dotenv / file: Built-in sources.
- Errors and types: ConfinitError, MissingValue, TypeConversionError, ConfSourceError, SourceInfo.

Runtime version
- __version__ is detected from installed metadata; when running from source,
  falls back to reading ``pyproject.toml``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
import tomllib

from .errors import ConfSourceError, ConfinitError, MissingValue, TypeConversionError
from .types import SourceInfo, Secret, Decoder
from .sources import env, dotenv, file, cli
from .loader import load

__all__ = [
    "__version__",
    "main",
    "_detect_version",
    # public API
    "load",
    "env",
    "dotenv",
    "file",
    "cli",
    "ConfinitError",
    "MissingValue",
    "TypeConversionError",
    "ConfSourceError",
    "SourceInfo",
    "Secret",
    "Decoder",
]


def _detect_version() -> str:
    """Return the runtime package version.

    Tries installed metadata first; if unavailable (running from source),
    falls back to reading ``pyproject.toml`` at the repository root.
    """
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
    """CLI entrypoint used for a quick sanity run."""
    print("confinit: v{}".format(__version__))
