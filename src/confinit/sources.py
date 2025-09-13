"""Built-in configuration sources: env vars, .env files, and TOML files.

Public factory functions
- env(prefix: str | None = None): read environment variables (uppercase names,
  optional ``prefix`` before names).
- dotenv(path: str, prefix: str | None = None): read key=value pairs from a
  dotenv-like file; supports ``export``, quotes, and inline ``#`` comments.
- file(path: str): read top-level keys from a TOML file using ``tomllib``.

Each source implements a ``collect(schema) -> dict[field, (raw, SourceInfo)]``
used by the loader to merge values and record provenance.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Tuple
import tomllib

from .errors import ConfSourceError
from .types import SourceInfo

CollectResult = Dict[str, Tuple[Any, SourceInfo]]


def _upper_name(name: str) -> str:
    return name.upper()


class _EnvSource:
    def __init__(self, prefix: str | None = None) -> None:
        self.prefix = prefix

    def collect(self, schema: type) -> CollectResult:
        """Collect env var overrides for the given schema.

        Uppercases field names and optionally prefixes them. Only variables
        present in the environment are returned.
        """
        out: CollectResult = {}
        for f in schema.__dataclass_fields__.values():  # type: ignore[attr-defined]
            env_name = (
                _upper_name(f.name)
                if not self.prefix
                else f"{self.prefix}{_upper_name(f.name)}"
            )
            if env_name in os.environ:
                raw = os.environ[env_name]
                out[f.name] = (
                    raw,
                    SourceInfo(kind="env", layer=10, path=env_name, raw_value=raw),
                )
        return out


class _DotenvSource:
    def __init__(self, path: str, prefix: str | None = None) -> None:
        self.path = path
        self.prefix = prefix

    def collect(self, schema: type) -> CollectResult:
        """Read a dotenv-like file and return matching keys for the schema.

        Supports ``export`` prefix, quoted values, and inline ``#`` comments.
        If the file does not exist, returns an empty mapping.
        """
        file_path = Path(self.path)
        if not file_path.exists():
            return {}
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ConfSourceError(f"Failed to read .env at {self.path}: {e}") from e
        env_map = _parse_dotenv(content)
        out: CollectResult = {}
        for f in schema.__dataclass_fields__.values():  # type: ignore[attr-defined]
            names: list[str] = []
            if self.prefix:
                names.append(f"{self.prefix}{_upper_name(f.name)}")
            names.extend((_upper_name(f.name), f.name, f.name.lower()))
            for n in names:
                if n in env_map:
                    raw = env_map[n]
                    out[f.name] = (
                        raw,
                        SourceInfo(
                            kind="dotenv",
                            layer=20,
                            path=f"{self.path}:{n}",
                            raw_value=raw,
                        ),
                    )
                    break
        return out


class _TomlFileSource:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, schema: type) -> CollectResult:
        """Read a TOML file and map top-level keys to schema fields."""
        p = Path(self.path)
        if not p.exists():
            return {}
        try:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # pragma: no cover - upstream parse errors
            raise ConfSourceError(f"Failed to parse TOML at {self.path}: {e}") from e
        out: CollectResult = {}
        for f in schema.__dataclass_fields__.values():  # type: ignore[attr-defined]
            if f.name in data:
                raw = data[f.name]
                out[f.name] = (
                    raw,
                    SourceInfo(kind="file", layer=30, path=self.path, raw_value=raw),
                )
        return out


def env(prefix: str | None = None) -> _EnvSource:
    """Create an environment variable source.

    Args:
        prefix: Optional uppercase prefix like ``APP_``.

    Returns:
        An environment variable source instance.
    """
    return _EnvSource(prefix=prefix)


def dotenv(path: str, prefix: str | None = None) -> _DotenvSource:
    """Create a dotenv file source.

    Args:
        path: Path to the ``.env`` file.
        prefix: Optional uppercase prefix to search alongside bare names.

    Returns:
        A dotenv source instance.
    """
    return _DotenvSource(path=path, prefix=prefix)


def file(path: str) -> _TomlFileSource:
    """Create a TOML file source pointing to ``path``."""
    return _TomlFileSource(path=path)


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse dotenv text into a dict of key -> string value.

    Handles ``export`` prefix, simple quotes, and inline ``#`` comments.
    Lines without ``=`` are ignored.
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "#" in line:
            before, _, _after = line.partition("#")
            line = before.strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        result[key] = val
    return result
