"""Dataclass-based configuration loader.

Key function
- load(schema, sources=None): Resolve a dataclass ``schema`` by merging values
  from ``sources`` (default: ``env()``, ``dotenv('.env')``, ``file('config.toml')``)
  with precedence by source order. Attaches per-field provenance map as
  ``instance.__provenance__`` using ``SourceInfo``.
"""

from __future__ import annotations

from dataclasses import MISSING, Field, fields, is_dataclass
from typing import Any, Dict, Iterable, Tuple, Type, TypeVar, get_type_hints, cast

from .convert import _convert_value
from .errors import ConfinitError, MissingValue, TypeConversionError
from .sources import dotenv, env, file
from .types import SourceInfo

Collect = Dict[str, Tuple[Any, SourceInfo]]
T = TypeVar("T")


def load(schema: Type[T], sources: Iterable[object] | None = None) -> T:
    """Load a dataclass ``schema`` from multiple sources.

    - Applies sources in order and takes the first value found per field.
    - Default sources: ``env()``, ``dotenv('.env')``, ``file('config.toml')``.
    - Performs basic type conversions (str/int/float/bool/Path/Enum/Optional).
    - Attaches a provenance map at ``instance.__provenance__`` for debugging.

    Args:
        schema: A dataclass type defining the settings schema.
        sources: Iterable of source objects with a ``collect(schema)`` method.

    Returns:
        An instance of ``schema`` populated from the configured sources.

    Raises:
        ConfinitError: If ``schema`` is not a dataclass or a source is invalid.
        MissingValue: If a required field has no value in any source.
        TypeConversionError: If converting a raw value to a target type fails.
    """
    if not is_dataclass(schema):
        raise ConfinitError("load() expects a dataclass type as schema")
    # Narrow for static analyzers: we only proceed with dataclass types
    schema_type = cast(type[Any], schema)

    srcs: list[object] = (
        list(sources)
        if sources is not None
        else [env(), dotenv(".env"), file("config.toml")]
    )

    merged: Collect = {}
    source_names: list[str] = []
    for s in srcs:
        if hasattr(s, "collect") and callable(getattr(s, "collect")):
            collected = s.collect(schema_type)
            source_names.append(type(s).__name__)
            for k, v in collected.items():
                if k not in merged:
                    merged[k] = v
        else:  # pragma: no cover
            raise ConfinitError(f"Invalid source provided: {s!r}")

    kwargs: Dict[str, Any] = {}
    provenance: Dict[str, SourceInfo] = {}
    type_hints = get_type_hints(schema_type, include_extras=True)
    for f in _iter_fields(schema_type):
        if f.name in merged:
            raw, info = merged[f.name]
            try:
                target = type_hints.get(f.name, f.type)
                kwargs[f.name] = _convert_value(raw, target, f.name)
            except TypeConversionError:
                provenance[f.name] = info
                raise
            provenance[f.name] = info
        else:
            if f.default is not MISSING or f.default_factory is not MISSING:  # type: ignore[attr-defined]
                provenance[f.name] = SourceInfo(
                    kind="default", layer=99, path=None, raw_value=f.default
                )
            else:
                raise MissingValue(f.name, source_chain=source_names)

    instance: T = schema(**kwargs)  # type: ignore[misc]
    setattr(instance, "__provenance__", provenance)
    return instance


def _iter_fields(schema: object) -> Iterable[Field[Any]]:
    """Iterate dataclass fields for ``schema``.

    Assumes the caller has already validated that ``schema`` is a dataclass
    type. Uses a local cast to keep static analyzers satisfied.
    """
    return fields(cast(Any, schema))
