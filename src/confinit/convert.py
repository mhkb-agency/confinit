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
import json
import csv

from .errors import TypeConversionError
from .types import Secret, Decoder


def _convert_value(raw: Any, target: Any, field_name: str) -> Any:
    """Convert ``raw`` to the ``target`` annotation for a field.

    Supports Optional[T] (via PEP 604 unions), Enum by name/value, Path,
    bool parsing, and basic built-ins. Falls back to returning the raw
    value (or its string) when conversion is not required.
    """
    # Unwrap typing.Annotated to collect Decoder metadata
    base_target = target
    origin = get_origin(base_target)
    args = get_args(base_target)

    if origin is __import__("typing").Annotated:
        base, *meta = args
        # Apply decoders in the order provided
        for m in meta:
            if isinstance(m, Decoder):
                try:
                    raw = m(raw)
                except Exception as e:  # pragma: no cover - user decoder
                    raise TypeConversionError(
                        field_name, base.__name__, raw, str(e)
                    ) from e
        base_target = base
        origin = get_origin(base_target)
        args = get_args(base_target)

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

    if isinstance(base_target, type) and issubclass_safe(base_target, Enum):
        return _convert_enum(raw, base_target, field_name)

    # Secret[T] wraps converted T while masking its display
    if _is_secret_origin(base_target):
        inner = get_args(base_target) or (str,)
        inner_t = inner[0]
        inner_val = _convert_value(raw, inner_t, field_name)
        return Secret(inner_val)

    if base_target is str:
        return raw if isinstance(raw, str) else str(raw)

    if base_target is Any or base_target is None:
        return raw

    if base_target is int:
        try:
            return int(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "int", raw, str(e)) from e

    if base_target is float:
        try:
            return float(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "float", raw, str(e)) from e

    if base_target is bool:
        return _to_bool(raw, field_name)

    if isinstance(base_target, type) and issubclass_safe(base_target, Path):
        try:
            return Path(raw)
        except Exception as e:
            raise TypeConversionError(field_name, "Path", raw, str(e)) from e

    # Lists and dicts from ENV (string) or pass-through from TOML
    if origin in (list, tuple) or str(origin).endswith("typing.List"):
        # Determine element type (default to str)
        elem_t = (get_args(base_target) or (str,))[0]
        # If we already have a list, convert each element
        if isinstance(raw, (list, tuple)):
            return [_convert_value(v, elem_t, field_name) for v in list(raw)]
        # If a string, parse JSON first, then CSV fallback
        if isinstance(raw, str):
            s = raw.strip()
            seq: list[Any]
            if s.startswith("[") and s.endswith("]"):
                try:
                    loaded = json.loads(s)
                    if not isinstance(loaded, list):
                        raise ValueError("not a list")
                    seq = loaded
                except Exception as e:
                    raise TypeConversionError(field_name, "list", raw, str(e)) from e
            else:
                try:
                    # Use csv to handle quotes/escapes
                    row = next(csv.reader([s]))
                    seq = row
                except Exception as e:  # pragma: no cover - unlikely
                    raise TypeConversionError(field_name, "list", raw, str(e)) from e
            return [_convert_value(v, elem_t, field_name) for v in seq]

    if origin in (dict,) or str(origin).endswith("typing.Dict"):
        key_t, val_t = (get_args(base_target) or (str, Any))[:2]
        if isinstance(raw, dict):
            return {  # best-effort convert values; keys to str-like
                _convert_value(k, key_t, field_name): _convert_value(
                    v, val_t, field_name
                )
                for k, v in raw.items()
            }
        if isinstance(raw, str):
            s = raw.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    loaded = json.loads(s)
                    if not isinstance(loaded, dict):
                        raise ValueError("not a dict")
                except Exception as e:
                    raise TypeConversionError(field_name, "dict", raw, str(e)) from e
                return {
                    _convert_value(k, key_t, field_name): _convert_value(
                        v, val_t, field_name
                    )
                    for k, v in loaded.items()
                }
            # Fallback: parse simple CSV of k=v pairs
            pairs: dict[str, str] = {}
            try:
                for token in next(csv.reader([s])):
                    if "=" in token:
                        k, v = token.split("=", 1)
                    elif ":" in token:
                        k, v = token.split(":", 1)
                    else:
                        continue
                    pairs[k.strip()] = v.strip()
            except Exception as e:  # pragma: no cover - unlikely
                raise TypeConversionError(field_name, "dict", raw, str(e)) from e
            return {
                _convert_value(k, key_t, field_name): _convert_value(
                    v, val_t, field_name
                )
                for k, v in pairs.items()
            }

    if isinstance(base_target, type):
        if isinstance(raw, base_target):  # type: ignore[arg-type]
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


def _is_secret_origin(t: Any) -> bool:
    """Return True if annotation ``t`` is Secret[...] or Secret."""
    try:
        return t is Secret or get_origin(t) is Secret
    except Exception:
        return False
