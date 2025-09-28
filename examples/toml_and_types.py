"""Reading TOML and converting to typed fields.

Demonstrates:
- TOML source via `file()` and type conversions to bool/float/Enum/Path/str

Run:
    uv run python examples/toml_and_types.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import tempfile

import confinit as ci


class Color(Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Settings:
    debug: bool = False
    workers: int = 4
    rate: float = 1.5
    data_dir: Path | None = None
    color: Color = Color.RED
    name: str = ""


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "config.toml"
        p.write_text(
            (
                "debug = true\n"
                "workers = 8\n"
                "rate = 2.25\n"
                'color = "blue"\n'
                'data_dir = "/var/lib/app"\n'
                "name = 123\n"  # coerced to str("123")
            ),
            encoding="utf-8",
        )

        cfg = ci.load(Settings, sources=[ci.file(str(p))])
        print(cfg)
        print("provenance color:", cfg.__provenance__["color"])  # kind='file'


if __name__ == "__main__":
    main()
