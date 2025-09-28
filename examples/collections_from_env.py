"""Collections from ENV: lists and dicts via JSON/CSV.

Demonstrates:
- list[str] and list[int] via CSV and JSON
- dict[str, Any] via JSON (and shows structure preserved)

Run:
    uv run python examples/collections_from_env.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os

import confinit as ci


@dataclass
class Settings:
    tags: list[str]
    nums: list[int]
    meta: dict[str, Any]


def main() -> None:
    os.environ["TAGS"] = '"a b",c,d'
    os.environ["NUMS"] = "[1,2,3]"
    os.environ["META"] = '{"x": 1, "y": "z"}'

    cfg = ci.load(Settings, sources=[ci.env()])
    print("tags:", cfg.tags)
    print("nums:", cfg.nums)
    print("meta:", cfg.meta)


if __name__ == "__main__":
    main()
