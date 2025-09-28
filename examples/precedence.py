"""Precedence: CLI > ENV > .env > file > defaults.

Demonstrates:
- Provide all layers and observe who wins when sources are ordered accordingly
- Provenance reflects where the winning value came from

Run:
    uv run python examples/precedence.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

import confinit as ci


@dataclass
class Settings:
    workers: int = 1


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # file layer
        (td_path / "config.toml").write_text("workers = 2\n", encoding="utf-8")
        # .env layer
        (td_path / ".env").write_text("WORKERS=6\n", encoding="utf-8")
        # ENV layer
        os.environ["WORKERS"] = "9"
        # CLI layer (highest precedence if placed first in sources)
        args = ["--workers=12"]

        cfg = ci.load(
            Settings,
            sources=[
                ci.cli(args),  # CLI
                ci.env(),  # ENV
                ci.dotenv(str(td_path / ".env")),  # .env
                ci.file(str(td_path / "config.toml")),  # file
            ],
        )

        print("workers:", cfg.workers)
        print("provenance:", cfg.__provenance__["workers"])  # -> kind='cli'


if __name__ == "__main__":
    main()
