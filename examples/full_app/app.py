"""Full-fledged usage example application for confinit.

This script loads configuration from CLI, ENV, .env, and a TOML file using
typed fields, secrets, lists/dicts, and an Annotated decoder for custom
duration parsing. It can either "run" a dummy service or "inspect" the
resolved configuration with provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, field
from enum import Enum
from pathlib import Path
from typing import Annotated, Any
import os

import confinit as ci


def parse_duration_to_seconds(v: Any) -> Any:
    """Parse strings like "30s", "5m", "2h" into integer seconds.

    Accepts plain integers as seconds as well. This is used as a custom
    decoder via `typing.Annotated[int, ci.Decoder(parse_duration_to_seconds)]`.
    """
    s = str(v).strip().lower()
    try:
        if s.endswith("s"):
            return int(s[:-1])
        if s.endswith("m"):
            return int(s[:-1]) * 60
        if s.endswith("h"):
            return int(s[:-1]) * 3600
        return int(s)
    except Exception as e:  # pragma: no cover - example script
        raise ValueError(f"invalid duration: {v!r}") from e


class Color(Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Settings:
    # Core
    action: str = "run"  # 'run' or 'inspect'
    debug: bool = False
    env: str = "dev"
    workers: int = 4
    rate: float = 1.5
    color: Color = Color.RED
    data_dir: Path = Path("./data")
    name: str | None = None

    # Collections
    log_levels: list[str] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)

    # Custom-decoded
    timeout: Annotated[int, ci.Decoder(parse_duration_to_seconds)] = 30

    # Secrets
    api_token: ci.Secret[str] = field(default_factory=lambda: ci.Secret("changeme"))


def load_settings() -> Settings:
    root = Path(__file__).resolve().parent
    sources = [
        ci.cli(),
        ci.env(prefix="APP_"),
        ci.dotenv(str(root / ".env"), prefix="APP_"),
        ci.file(str(root / "config.toml")),
    ]
    return ci.load(Settings, sources=sources)


def print_settings(cfg: Settings) -> None:
    print("Resolved settings:")
    for f in fields(cfg):
        val = getattr(cfg, f.name)
        print(f"- {f.name}: {val}")


def inspect_provenance(cfg: Settings) -> None:
    print("\nProvenance:")
    for name, info in cfg.__provenance__.items():
        print(f"- {name}: {info}")


def run_service(cfg: Settings) -> None:  # pragma: no cover - example
    print("Starting service...")
    print(f"env={cfg.env} workers={cfg.workers} port-like-timeout={cfg.timeout}s")
    print(f"data_dir={cfg.data_dir} color={cfg.color.name}")
    print(f"log_levels={cfg.log_levels} features={cfg.features}")
    print(f"api_token(masked)={cfg.api_token}")
    print("Service is running! (demo)")


def main() -> None:
    cfg = load_settings()
    print_settings(cfg)
    if cfg.action == "inspect":
        inspect_provenance(cfg)
    else:
        run_service(cfg)


if __name__ == "__main__":
    # Optionally set an ENV override for demo purposes
    os.environ.setdefault("APP_ENV", "dev")
    main()
