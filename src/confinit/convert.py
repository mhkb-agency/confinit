"""Type conversion helpers for confinit.

Responsibilities
- Convert raw values from sources into annotated field types.
- Support Optional[T] (PEP 604), Enum by name/value, Path, bool parsing,
  and basic built-ins (str/int/float).

Public helpers (internal API)
- _convert_value(raw, target, field_name): perform conversion for a field.
- issubclass_safe: safe ``issubclass`` wrapper for dynamic types.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin
import types as _pytypes

from .errors import TypeConversionError


def _convert_value(raw: Any, target: Any, field_name: str) -> Any:
    """Convert ``raw`` to the ``target`` annotation for a field.

    Supports Optional[T] (via PEP 604 unions), Enum by name/value, Path,
    bool parsing, and basic built-ins. Falls back to returning the raw
    value (or its string) when conversion is not required.
    """
    origin = get_origin(target)
    args = get_args(target)

    if origin is __import__("typing").Union or origin is getattr(
        _pytypes, "UnionType", None
    ):
        non_none = [a for a in args if a is not type(None)]  # noqa: E721
        if len(non_none) == 1:
            if raw in (None, ""):
                return None
            return _convert_value(raw, non_none[0], field_name)
        expected = f"Union[{', '.join(getattr(a, '__name__', str(a)) for a in args)}]"
        raise TypeConversionError(field_name, expected, raw, "unsupported union form")

    if isinstance(target, type) and issubclass_safe(target, Enum):
        return _convert_enum(raw, target, field_name)

    if target in (str, Any) or target is None:
        return raw if isinstance(raw, str) else str(raw)

    if target is int:
        try:
            return int(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "int", raw, str(e)) from e

    if target is float:
        try:
            return float(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "float", raw, str(e)) from e

    if target is bool:
        return _to_bool(raw, field_name)

    if isinstance(target, type) and issubclass_safe(target, Path):
        try:
            return Path(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "Path", raw, str(e)) from e

    if isinstance(target, type):
        if isinstance(raw, target):  # type: ignore[arg-type]
            return raw

    return raw


def _to_bool(raw: Any, field_name: str) -> bool:
    """Parse flexible booleans (true/false/1/0/yes/no/on/off)."""
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().lower()
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}
    if s in truthy:
        return True
    if s in falsy:
        return False
    raise TypeConversionError(
        field_name, "bool", raw, "accepted: true/false/1/0/yes/no/on/off"
    )


def _convert_enum(raw: Any, enum_type: type[Enum], field_name: str) -> Enum:
    """Convert by matching Enum name (case-insensitive) or value string."""
    s = str(raw)
    for member in enum_type:
        if member.name.lower() == s.lower():
            return member
    for member in enum_type:
        if str(member.value) == s:
            return member
    raise TypeConversionError(
        field_name, enum_type.__name__, raw, "no matching enum member"
    )


def issubclass_safe(cls: Any, base: type) -> bool:
    """Like ``issubclass`` but guards against non-type inputs."""
    try:
        return isinstance(cls, type) and issubclass(cls, base)
    except Exception:
        return False
