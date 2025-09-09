# Confinit — Project ROADMAP (v0.1 → v1.0)

Confinit is a **lightweight, typed, multi-source configuration loader** with **stdlib-first** design, **deterministic precedence**, and **debug-friendly provenance**. It targets teams who want “**dotenv + settings in one line**,” zero heavy deps, and clean type-checked configs.

---

## 1) Vision & Goals

- **Vision:** Become the **default minimal config loader** for Python apps. Keep it tiny, typed, and predictable.
- **Primary goals**
  - **Zero hard dependencies**; rely on `tomllib` (Py≥3.11) for TOML.
  - **Typed** settings via annotations (dataclasses first-class).
  - **Multi-source** loading with clear order: **CLI > env > `.env` > file > defaults**.
  - **Provenance**: show where each value came from.
- **Non-goals**
  - Not a full validation framework (that’s pydantic/marshmallow territory).
  - Not a remote config service / secrets manager.
  - No magic runtime monkey-patching; explicit code over global side effects.

---

## 2) Target Users & Use Cases

- 12-factor microservices, CLI tools, and research scripts needing **clean, typed settings** without heavy frameworks.
- Teams standardizing on **TOML + `.env` + ENV** with **debuggable merges**.

---

## 3) Design Principles

1. **Stdlib-first:** no heavy deps; keep surface minimal.
2. **Types are the API:** dataclass annotations define shape & conversion.
3. **Deterministic precedence:** last-writer wins according to a **published, per-key** order.
4. **Transparent provenance:** every value can be traced to its source.
5. **Sharp edges over surprises:** explicit errors for missing/invalid config.

---

## 4) Core Concepts

- **Settings schema:** Python `@dataclass` (primary), with support for nested dataclasses, `Enum`, `Path`, `URL` (via simple validators/converters).
- **Sources:**
  - **CLI args** (optional helper that emits key/value overrides).
  - **Environment variables** (with optional prefix & name mapping).
  - **`.env`** (simple parser; no runtime dotenv dependency).
  - **TOML files** via `tomllib`.
- **Merging:** Per key, **CLI > ENV > .env > file > default**; unprovided keys use dataclass defaults.
- **Provenance map:** `{field_name: SourceInfo(path, kind, layer, raw_value)}` for debugging.

---

## 5) Type System & Conversion Rules

- **Built-ins:** `str`, `int`, `float`, `bool`, `list[str|int|float]`, `dict[str, Any]` (JSON/CSV strategies), `Path`, `Enum`, `Optional[T] | T | Union`.
- **Booleans:** case-insensitive `true/false/1/0/yes/no/on/off`.
- **Lists/Dicts:** ENV accepts JSON (`[1,2]`, `{"k":"v"}`) or CSV+escape (`a,b,c`)—configurable.
- **URLs:** parsed & validated with clear error messages.
- **Secrets:** dedicated `Secret[str]` wrapper that **masks** in logs and provenance printouts.
- **Custom decoders:** `Annotated[T, Decoder(fn)]` to plug per-field transforms.

---

## 6) Error Model

- `ConfinitError` (base)
  - `MissingValue(field, source_chain)`
  - `TypeConversionError(field, expected, raw, reason)`
  - `ConfSourceError(source, path, reason)`

All errors **include provenance** and a **one-line fix hint**.

---

## 7) Security & Ops

- **Mask secrets** in logs, dumps, and exceptions.
- **.env hygiene warnings** (e.g., world-readable file).
- **Deterministic, pure load** function to enable reproducible builds.
- Optional **read-only/frozen** settings object post-load.

---

## 8) Public API (initial)

~~~python
from dataclasses import dataclass
from confinit import load, env, file, dotenv, cli

@dataclass
class Settings:
    debug: bool = False
    workers: int = 4
    db_url: str = env("DATABASE_URL")  # required via ENV
    data_dir: str | None = None

cfg = load(
    Settings,
    sources=[
        cli(prefix="APP_"),        # optional CLI key=value or --APP.workers=8
        env(prefix="APP_"),
        dotenv(".env"),
        file("config.toml"),
    ],
)
print(cfg.debug, cfg.workers)
# cfg.__provenance__ -> dict[field, SourceInfo]
~~~

This expands the published **MVP** (`typing`, TOML via `tomllib`, precedence, provenance).

---

## 9) CLI Utilities (optional package `confinit[cli]`)

- `confinit inspect` — print resolved values **with provenance**.
- `confinit dump --format toml|env` — serialize current settings (secrets masked).
- `confinit example` — generate `.env.example` from schema & defaults.
- `confinit doctor` — check `.env` permissions & ENV prefix collisions.

---

## 10) Documentation Plan

- **Quickstart (5 min):** dataclass → load → run.
- **Cookbook:** multi-env overlays, Docker/K8s, secrets, lists via ENV, nested dataclasses.
- **Debugging:** reading provenance; common type errors.
- **Integrations:** FastAPI/Flask/Celery/Uvicorn; systemd units; GitHub Actions.
- **Migration notes:** from `pydantic-settings`/`dynaconf` (scope differences).

---

## 11) Quality, CI/CD, & Support

- **Python:** 3.11–3.13.
- **Type-checking:** mypy + pyright gates.
- **Tests:** pytest with 95%+ coverage on core; property-based tests for parsers.
- **Perf checks:** load 1k fields < 20 ms on CI; zero-alloc hot path where reasonable.
- **Release:** SemVer; `v0.x` for rapid iteration; **`v1.0` freezes public API**.
- **Governance:** MIT license; CONTRIBUTING + CoC.
- **Docs:** MkDocs + examples repo.

---

## 12) Milestones & Timeline

> Dates are indicative, aligned to **Europe/Paris** timezone; adapt as needed.

### **M1 — Core (v0.1.0)** — 3–4 weeks
**Deliverables**
- Dataclass loader (`load()`), field mapping, defaults.
- Sources: `env(prefix=...)`, `dotenv(path)`, `file(toml_path)`.
- Precedence: **CLI > ENV > .env > file > defaults** (documented + tested).
- Type conversions for `str/int/float/bool/Path/Enum/Optional`.
- Provenance map + `cfg.__provenance__`.
- Error classes with helpful messages.

**Acceptance**
- 95%+ coverage on core.
- Docs: Quickstart, Concepts, Precedence, Errors.
- Bench sanity: load of a 50-field schema < 5 ms on CI.

### **M2 — Ergonomics (v0.2.0)** — 3–4 weeks
**Deliverables**
- CLI helper `cli()` (K:V args & `--section.field=value`).
- Collections: list/dict from ENV (JSON & CSV strategies).
- `Annotated` decoders for custom parsing.
- Secrets masking (`Secret[str]`).
- `confinit inspect|dump|example` commands (optional extra).

**Acceptance**
- Provenance shows exact layer & raw text.
- Polished docs (Cookbook + CLI section).
- Example apps: FastAPI & simple worker.

### **M3 — Extensibility (v0.3.0)** — 4–5 weeks
**Deliverables**
- **Source plugin interface** (`Source` protocol) for custom backends.
- Optional extras: `yaml`, `json` sources (no hard deps).
- Nested dataclasses & unions edge-cases hardened.
- Read-only/frozen settings (immutability flag).

**Acceptance**
- Write a custom source in <30 LOC (guide).
- Fuzz tests for nested/unions.
- Perf: ≤10% regression vs v0.2.0.

### **M4 — Ops & DX (v0.4.0)** — 4–5 weeks
**Deliverables**
- Multi-file overlays (e.g., `base.toml`, `dev.toml`).
- Env prefix strategy checks (`APP_` vs collisions).
- `.env` hygiene checks; opt-in file-watch reload via an **extra** (keeps core zero-dep).
- `export_env` helper to emit ENV-style output for shells/containers.

**Acceptance**
- Clear ops runbook in docs.
- Example: containerized service using only ENV & `.env`.

### **GA — Stability (v1.0.0)** — 2–3 weeks
**Deliverables**
- Finalize API; remove deprecations.
- Hardening, docs sweep, website examples.
- Launch blog post & migration guide.

**Acceptance / Launch KPIs**
- Success criteria from proposal:
  - **300+ GitHub stars in 30 days**, mentions in 12-factor blog posts, **pure-stdlib out of the box**.
- At least **5 public dependents** in early weeks (stretch).

---

## 13) Risks & Mitigations

- **Overlap with pydantic-settings/dynaconf:** keep scope **minimal** (loading + light conversion), position as **stdlib-first** alternative. Provide migration notes.
- **Scope creep:** publish a strict **Non-goals** list and guard PRs.
- **OS/env quirks:** thorough tests on Windows/macOS/Linux; normalize case handling on Windows ENV.

---

## 14) Backlog (Post-v1 ideas)

- Field-level validators (lightweight), unit helpers (sizes, durations).
- `.env` encryption helper (openssh-style), keyring integrations (optional).
- Templated configs (Jinja-like) as a **separate** package.
- mypy plugin for stricter Optional checks (optional).
- VS Code snippet/launch templates for Confinit projects.

---

## 15) Example: Real-World Layout

```
project/
  app.py
  conf/
    base.toml
    dev.toml
    prod.toml
  .env.example
  .env          # local only (gitignored)
```

~~~python
# app.py
from dataclasses import dataclass
from confinit import load, env, file, dotenv, cli

@dataclass
class Settings:
    env: str = "dev"
    debug: bool = False
    db_url: str = env("DATABASE_URL")
    cache_ttl: int = 60

cfg = load(Settings, sources=[
    cli(prefix="APP_"),
    env(prefix="APP_"),
    dotenv(".env"),
    file(f"conf/{Settings.env}.toml"),   # overlay after .env by design
    file("conf/base.toml"),
])
~~~

---

### Bottom line

Confinit focuses on **clarity, typing, and provenance** with a **tiny core** and **deterministic precedence**—a deliberately minimal alternative to heavier settings stacks, aligned with the original proposal’s **MVP**, **vision**, and **success metrics**.
