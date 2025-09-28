"""Errors and debugging examples.

Demonstrates:
- TypeConversionError when a value cannot be converted to the target type
- MissingValue when a required field has no value and no default
- ConfSourceError when a TOML file cannot be parsed

Run:
    uv run python examples/errors_and_debugging.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

import confinit as ci


def show_type_error() -> None:
    @dataclass
    class S:
        active: bool

    try:
        cfg = ci.load(S, sources=[ci.cli(["--active=maybe"])])
        print(cfg)
    except ci.TypeConversionError as e:
        print("TypeConversionError:", e)


def show_missing_value() -> None:
    @dataclass
    class S:
        required: int

    try:
        ci.load(S, sources=[])
    except ci.MissingValue as e:
        print("MissingValue:", e)


def show_conf_source_error() -> None:
    @dataclass
    class S:
        k: int | None = None

    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.toml"
        bad.write_text("[not-closed\nkey = 1", encoding="utf-8")
        try:
            ci.load(S, sources=[ci.file(str(bad))])
        except ci.ConfSourceError as e:
            print("ConfSourceError:", e)


def main() -> None:
    show_type_error()
    show_missing_value()
    show_conf_source_error()


if __name__ == "__main__":
    main()
