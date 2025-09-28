"""Built-in configuration sources: CLI args, env vars, .env files, TOML.

Public factory functions
- cli(args: list[str] | None = None): read CLI overrides like ``--key=value``
  or ``section.key=value`` / ``KEY=V``. Highest-precedence layer when used
  first in ``sources`` as per the documented order.
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
import sys
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


class _CliSource:
    def __init__(self, args: list[str] | None = None) -> None:
        # Capture args once to make behavior deterministic for tests
        self._args = list(args) if args is not None else sys.argv[1:]

    def _parse_args(self) -> Dict[str, str]:
        """Parse CLI args into a mapping of name -> raw string value.

        Accepted forms:
        - ``--key=value`` or ``key=value``
        - ``key:value``
        - dotted names like ``section.key=value`` map to ``key``
        Duplicate keys keep first occurrence (highest priority within CLI).
        """
        out: Dict[str, str] = {}
        for arg in self._args:
            a = arg
            if a.startswith("--"):
                a = a[2:]
            # Support both '=' and ':' separators
            if "=" in a:
                name, _, value = a.partition("=")
            elif ":" in a:
                name, _, value = a.partition(":")
            else:
                continue
            # Take the last dotted token (section.key -> key)
            key = name.split(".")[-1].strip()
            if key and key not in out:
                out[key] = value
        return out

    def collect(self, schema: type) -> CollectResult:
        values = self._parse_args()
        out: CollectResult = {}
        for f in schema.__dataclass_fields__.values():  # type: ignore[attr-defined]
            # Match case-insensitively
            for candidate in (f.name, f.name.lower(), f.name.upper()):
                if candidate in values:
                    raw = values[candidate]
                    out[f.name] = (
                        raw,
                        SourceInfo(
                            kind="cli", layer=0, path=f"--{candidate}", raw_value=raw
                        ),
                    )
                    break
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


def cli(args: list[str] | None = None) -> _CliSource:
    """Create a CLI source reading from ``args`` (defaults to ``sys.argv[1:]``).

    Place this source first in ``sources`` to achieve the documented precedence
    of ``CLI > ENV > .env > file > defaults``.
    """
    return _CliSource(args=args)


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
