"""Shared simple types used by confinit.

Public classes
- SourceInfo: Records where a value came from (kind/layer/path/raw_value)
  and is attached per-field to the resolved configuration object as
  ``cfg.__provenance__[field]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceInfo:
    kind: str
    layer: int
    path: str | None
    raw_value: Any
