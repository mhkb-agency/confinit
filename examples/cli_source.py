"""CLI source: overrides via command-line style args.

Demonstrates:
- Parsing of --key=value, key=value, key:value, and section.key=value
- Case-insensitive matching to dataclass field names

Run (example):
    uv run python examples/cli_source.py
"""

from __future__ import annotations

from dataclasses import dataclass

import confinit as ci


@dataclass
class Settings:
    workers: int = 1
    rate: float = 1.0
    name: str | None = None
    debug: bool = False


def main() -> None:
    args = [
        "--workers=12",
        "service.rate=2.5",
        "NAME:Alice",
        "DEBUG=true",
    ]
    cfg = ci.load(Settings, sources=[ci.cli(args)])
    print(cfg)
    for k, info in cfg.__provenance__.items():
        print("prov", k, "->", info)


if __name__ == "__main__":
    main()
