"""Shared simple types used by confinit.

Public classes
- SourceInfo: Records where a value came from (kind/layer/path/raw_value)
  and is attached per-field to the resolved configuration object as
  ``cfg.__provenance__[field]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar


@dataclass(frozen=True)
class SourceInfo:
    """Provenance metadata for a resolved configuration field.

    A ``SourceInfo`` record is created by each source for every field it
    provides and is attached by ``confinit.load()`` to the resulting settings
    instance at ``cfg.__provenance__[field_name]``. It exists to make merges
    explainable: for any effective value you can see where it came from and why
    it won in the precedence chain.

    Fields
    - kind: Short identifier of the source that provided the value.
      Typical values: ``"cli"``, ``"env"``, ``"dotenv"``, ``"file"``,
      and ``"default"`` when the dataclass default was used.
    - layer: Informational precedence hint used across built-in sources
      (``cli=0``, ``env=10``, ``dotenv=20``, ``file=30``, ``default=99``).
      Note: actual resolution order is determined by the order of sources passed
      to ``load()``; ``layer`` helps diagnostics and tooling.
    - path: Location within the source, such as an environment variable name
      (e.g., ``"APP_WORKERS"``), a CLI flag (e.g., ``"--workers"``), a dotenv
      entry (``".env:KEY"``), or a file path like ``"config.toml"``.
    - raw_value: The unconverted value as read from the source (for TOML it may
      be a native Python type; for ENV/CLI/dotenv it is usually a string). When
      a field is annotated as ``Secret[...]``, the loader masks this value as
      ``"***"`` to avoid leaking sensitive data in logs.
    """

    kind: str
    layer: int
    path: str | None
    raw_value: Any


T = TypeVar("T")


class Secret(Generic[T]):
    """A wrapper for secret values that masks string/repr output.

    Access the underlying value via ``reveal()``.
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        self._value = value

    def reveal(self) -> T:
        return self._value

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "Secret(*** )".replace(" ", "")

    def __str__(self) -> str:
        return "***"

    def __eq__(self, other: object) -> bool:  # pragma: no cover - convenience
        if isinstance(other, Secret):
            return self._value == other._value
        return False


class Decoder:
    """A callable metadata wrapper for ``typing.Annotated`` decoders.

    Example:
        ``port: Annotated[int, Decoder(lambda s: int(s, 16))]``
    """

    __slots__ = ("_fn",)

    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self._fn = fn

    def __call__(self, value: Any) -> Any:  # pragma: no cover - simple proxy
        return self._fn(value)
