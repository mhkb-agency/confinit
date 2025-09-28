"""Secrets: masking in values and provenance.

Demonstrates:
- Using `Secret[str]` for sensitive fields
- `str(secret)` is masked, `reveal()` returns the actual value
- Provenance raw_value is masked as well

Run:
    uv run python examples/secrets.py
"""

from __future__ import annotations

from dataclasses import dataclass
import os

import confinit as ci


@dataclass
class Settings:
    token: ci.Secret[str]


def main() -> None:
    os.environ["TOKEN"] = "super-secret"
    cfg = ci.load(Settings, sources=[ci.env()])
    print("token (masked):", str(cfg.token))
    print("token (revealed):", cfg.token.reveal())
    print("provenance:", cfg.__provenance__["token"])  # raw_value='***'


if __name__ == "__main__":
    main()
