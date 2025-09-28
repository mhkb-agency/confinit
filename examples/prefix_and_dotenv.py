"""ENV prefix and dotenv with prefix.

Demonstrates:
- Using `env(prefix="APP_")` and `dotenv(path, prefix="APP_")`
- How prefixed and bare names are matched by dotenv

Run:
    uv run python examples/prefix_and_dotenv.py
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
    rate: float = 1.0


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        envfile = td_path / ".env"
        envfile.write_text("APP_WORKERS=6\nrate=3.5\n", encoding="utf-8")
        (td_path / "config.toml").write_text(
            "workers = 2\nrate = 1.0\n", encoding="utf-8"
        )

        os.environ["APP_WORKERS"] = "9"

        cfg = ci.load(
            Settings,
            sources=[
                ci.env(prefix="APP_"),
                ci.dotenv(str(envfile), prefix="APP_"),
                ci.file(str(td_path / "config.toml")),
            ],
        )

        print("workers:", cfg.workers)  # 9 from ENV APP_WORKERS
        print("rate:", cfg.rate)  # 3.5 from .env (bare name also matched)
        print("prov workers:", cfg.__provenance__["workers"])  # kind='env'
        print("prov rate:", cfg.__provenance__["rate"])  # kind='dotenv'


if __name__ == "__main__":
    main()
