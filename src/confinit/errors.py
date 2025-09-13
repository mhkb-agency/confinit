"""Error types used across the confinit package.

This module defines a small, explicit hierarchy of exceptions used by the
loader and sources. Each error provides actionable context to aid debugging.

Public classes
- ConfinitError: Base class for all confinit errors.
- MissingValue: Raised when a required field has no value in any source.
- TypeConversionError: Raised when converting a raw value to a target type fails.
- ConfSourceError: Raised for failures reading or parsing configuration sources.
"""

from __future__ import annotations


class ConfinitError(Exception):
    pass


class MissingValue(ConfinitError):
    def __init__(self, field: str, source_chain: list[str]) -> None:
        msg = "Missing required value for field '{f}' (checked: {c})".format(
            f=field, c=" > ".join(source_chain) or "defaults"
        )
        super().__init__(msg)
        self.field = field
        self.source_chain = source_chain


class TypeConversionError(ConfinitError):
    def __init__(self, field: str, expected: str, raw: object, reason: str) -> None:
        msg = (
            f"Type conversion error for field '{field}': expected {expected}, "
            f"got {raw!r} ({reason})"
        )
        super().__init__(msg)
        self.field = field
        self.expected = expected
        self.raw = raw
        self.reason = reason


class ConfSourceError(ConfinitError):
    """Raised when a configuration source cannot be read or parsed.

    Examples include unreadable .env files and TOML parse errors.
    """

    pass
