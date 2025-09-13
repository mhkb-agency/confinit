from __future__ import annotations

from pathlib import Path
import tomllib

import confinit


def test_detect_version_fallback_reads_pyproject(monkeypatch):
    # Force PackageNotFoundError to exercise the fallback path
    def _raise(_name: str) -> str:  # type: ignore[return-type]
        raise confinit.PackageNotFoundError

    monkeypatch.setattr(confinit, "_pkg_version", _raise)

    root = Path(__file__).resolve().parents[1]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    expected = data.get("project", {}).get("version")
    assert confinit._detect_version() == expected


def test_detect_version_prefers_pkg_metadata(monkeypatch):
    monkeypatch.setattr(confinit, "_pkg_version", lambda _name: "9.9.9")
    assert confinit._detect_version() == "9.9.9"


def test_detect_version_default_when_no_pyproject(monkeypatch):
    class Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def resolve(self):
            return self

        @property
        def parents(self):
            return [self]

        def __truediv__(self, _other):
            return self

        def exists(self) -> bool:
            return False

        def read_text(self, *args, **kwargs):  # pragma: no cover - not reached
            raise AssertionError("should not read text when file does not exist")

    monkeypatch.setattr(confinit, "Path", Dummy)

    # Also ensure importlib metadata path is not taken
    def _raise(_name: str) -> str:  # type: ignore[return-type]
        raise confinit.PackageNotFoundError

    monkeypatch.setattr(confinit, "_pkg_version", _raise)
    assert confinit._detect_version() == "0.0.0"


def test_main_prints_greeting(capsys):
    confinit.main()
    out = capsys.readouterr().out.strip()
    assert out == "Hello from confinit!"


def test_version_matches_pyproject() -> None:
    # Locate repository root from this test file
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found at repository root"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    assert isinstance(version, str)
    assert confinit.__version__ == version
