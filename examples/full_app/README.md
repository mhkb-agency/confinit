Full-fledged usage example for confinit
======================================

This example shows a small application that loads configuration from all
supported sources with clear precedence, typed fields, secrets, lists/dicts,
and an Annotated decoder for custom parsing.

What it demonstrates
- Sources and precedence: CLI > ENV > .env > file > defaults
- Types: bool, int, float, Enum, Path, Optional, list, dict
- Secrets: Secret[str] values are masked in prints and provenance
- Annotated decoder: parse human-friendly duration (e.g., "30s", "5m")
- Provenance inspection: see where each value came from

Files
- app.py: entrypoint that loads and uses the settings
- config.toml: base configuration file
- .env: dotenv with overrides (APP_ prefix)

Run the example
- Default (uses .env and config.toml) — from repo root:
  uv run python examples/full_app/app.py

- With CLI override (highest precedence):
  uv run python examples/full_app/app.py --workers=12 --action=inspect

- With environment variable override:
  APP_WORKERS=9 uv run python examples/full_app/app.py

Outputs
- "inspect" action prints resolved values and provenance per field
- "run" action simulates starting a service with the resolved settings

