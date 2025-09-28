"""Annotated decoders: custom parsing before type conversion.

Demonstrates:
- Using `typing.Annotated[T, Decoder(fn)]` to pre-process raw values
- Example parses a hex string into an int

Run:
    uv run python examples/annotated_decoder.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
import os

import confinit as ci


@dataclass
class Settings:
    port: Annotated[int, ci.Decoder(lambda s: int(str(s), 16))]


def main() -> None:
    os.environ["PORT"] = "FF"
    cfg = ci.load(Settings, sources=[ci.env()])
    print("port:", cfg.port)  # 255


if __name__ == "__main__":
    main()
