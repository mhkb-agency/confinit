from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import textwrap

import confinit as ci


class Color(Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Settings:
    debug: bool = False
    workers: int = 4
    rate: float = 1.5
    data_dir: Path | None = None
    color: Color = Color.RED
    optional_name: str | None = None


def test_file_and_defaults(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        textwrap.dedent(
            """
            workers = 8
            rate = 2.25
            color = "blue"
            """
        ).strip()
    )

    cfg = ci.load(Settings, sources=[ci.file(str(cfg_path))])
    assert cfg.debug is False
    assert cfg.workers == 8
    assert cfg.rate == 2.25
    assert cfg.color is Color.BLUE
    assert cfg.optional_name is None
    prov = cfg.__provenance__
    assert prov["debug"].kind == "default"
    assert prov["workers"].kind == "file"


def test_dotenv_overrides_file(tmp_path):
    envfile = tmp_path / ".env"
    envfile.write_text("WORKERS=6\n# comment\nrate=3.5\n")
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("workers = 2\nrate = 1.0\n")

    cfg = ci.load(Settings, sources=[ci.dotenv(str(envfile)), ci.file(str(cfg_path))])
    assert cfg.workers == 6
    assert cfg.rate == 3.5
    assert cfg.__provenance__["workers"].kind == "dotenv"


def test_env_overrides_all(monkeypatch, tmp_path):
    envfile = tmp_path / ".env"
    envfile.write_text("APP_WORKERS=7\n")
    toml_path = tmp_path / "config.toml"
    toml_path.write_text("workers = 1\n")

    monkeypatch.setenv("APP_WORKERS", "9")
    cfg = ci.load(
        Settings,
        sources=[
            ci.env(prefix="APP_"),
            ci.dotenv(str(envfile), prefix="APP_"),
            ci.file(str(toml_path)),
        ],
    )
    assert cfg.workers == 9
    assert cfg.__provenance__["workers"].kind == "env"
    assert cfg.__provenance__["workers"].path == "APP_WORKERS"


def test_dotenv_missing_file_no_effect(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("workers = 5\n")
    cfg = ci.load(
        Settings, sources=[ci.dotenv(str(tmp_path / ".env")), ci.file(str(cfg_path))]
    )
    assert cfg.workers == 5


def test_nonexistent_toml_uses_defaults(tmp_path):
    cfg = ci.load(Settings, sources=[ci.file(str(tmp_path / "missing.toml"))])
    assert cfg.workers == 4
