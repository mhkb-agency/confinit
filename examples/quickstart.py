"""Quickstart: minimal dataclass settings with default sources.

Demonstrates:
- Define a schema with `@dataclass` and type hints
- Load values from default sources: env(), dotenv('.env'), file('config.toml')
- Inspect the provenance map attached at cfg.__provenance__

Run:
    uv run python examples/quickstart.py
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import confinit as ci


@dataclass
class Settings:
    debug: bool = False
    workers: int = 4


def main() -> None:
    # For demo purposes, set a couple env vars. In real usage, these would
    # come from your environment or files.
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("WORKERS", "6")

    cfg = ci.load(Settings)
    print("debug:", cfg.debug)
    print("workers:", cfg.workers)

    print("\nProvenance:")
    for k, info in cfg.__provenance__.items():
        print(f"  {k}: {info}")


if __name__ == "__main__":
    main()
