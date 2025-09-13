# confinit
Confinit is a lightweight, typed, multi-source configuration loader with stdlib-first design, deterministic precedence, and debug-friendly provenance. It targets teams who want “dotenv + settings in one line,” zero heavy deps, and clean type-checked configs.

## Module Reference

- confinit (package)
  - Public API surface aggregating the modules below. Exposes `load`, `env`, `dotenv`, `file`, error types, `SourceInfo`, `__version__`, and the `main()` CLI entry.

- confinit.loader
  - Dataclass-based loader. `load(schema, sources=None)` merges values from sources with precedence by source order and attaches a per-field provenance map as `cfg.__provenance__`.

- confinit.sources
  - Built-in sources. `env(prefix=None)` reads environment variables; `dotenv(path, prefix=None)` parses dotenv-style key/value files; `file(path)` reads top-level TOML keys using `tomllib`.

- confinit.convert
  - Internal conversion utilities. Converts raw values into annotated field types: `str`, `int`, `float`, `bool` (true/false/1/0/yes/no/on/off), `Path`, `Enum`, and `Optional[T]` via PEP 604 unions.

- confinit.errors
  - Exception hierarchy for clear diagnostics: `ConfinitError` (base), `MissingValue`, `TypeConversionError`, and `ConfSourceError`.

- confinit.types
  - Shared types. `SourceInfo(kind, layer, path, raw_value)` records provenance for each resolved field.

### Typical usage

```python
from dataclasses import dataclass
from confinit import load, env, dotenv, file

@dataclass
class Settings:
    debug: bool = False
    workers: int = 4

cfg = load(Settings, sources=[env(prefix="APP_"), dotenv(".env"), file("config.toml")])
print(cfg.debug, cfg.workers)
print(cfg.__provenance__["workers"])  # -> SourceInfo(...)
```

Precedence is deterministic and source-ordered: later sources in the list do not override earlier ones; instead, the first source that provides a value for a field wins (default order: `env()`, then `dotenv()`, then `file()`, then dataclass defaults).
