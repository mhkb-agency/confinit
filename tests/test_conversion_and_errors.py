from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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


def test_type_conversions(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("WORKERS", "10")
    monkeypatch.setenv("RATE", "2.75")
    monkeypatch.setenv("COLOR", "BLUE")
    monkeypatch.setenv("DATA_DIR", "/tmp/data")
    monkeypatch.setenv("OPTIONAL_NAME", "")

    cfg = ci.load(Settings, sources=[ci.env()])
    assert cfg.debug is True
    assert cfg.workers == 10
    assert cfg.rate == 2.75
    assert cfg.color is Color.BLUE
    assert cfg.data_dir == Path("/tmp/data")
    assert cfg.optional_name is None


def test_bool_invalid_raises(monkeypatch):
    @dataclass
    class S:
        debug: bool

    monkeypatch.setenv("DEBUG", "maybe")
    try:
        ci.load(S, sources=[ci.env()])
        assert False
    except ci.TypeConversionError as e:
        assert "bool" in str(e)
        assert "maybe" in str(e)


def test_enum_by_value(monkeypatch):
    @dataclass
    class S2:
        color: Color

    monkeypatch.setenv("COLOR", "red")
    cfg = ci.load(S2, sources=[ci.env()])
    assert cfg.color is Color.RED


def test_type_errors_are_clear(monkeypatch):
    @dataclass
    class S:
        count: int

    monkeypatch.setenv("COUNT", "not-an-int")
    try:
        ci.load(S, sources=[ci.env()])
        assert False
    except ci.TypeConversionError as e:
        assert "int" in str(e)
        assert "not-an-int" in str(e)


def test_float_conversion_error(monkeypatch):
    @dataclass
    class S:
        rate: float

    monkeypatch.setenv("RATE", "nope")
    try:
        ci.load(S, sources=[ci.env()])
        assert False
    except ci.TypeConversionError as e:
        assert "float" in str(e)


def test_path_conversion_error_from_toml(tmp_path):
    @dataclass
    class S:
        p: Path

    p = tmp_path / "c.toml"
    p.write_text("p = 123\n")
    try:
        ci.load(S, sources=[ci.file(str(p))])
        assert False
    except ci.TypeConversionError as e:
        assert "Path" in str(e)


def test_bool_false_and_true_variants(monkeypatch):
    @dataclass
    class S:
        a: bool
        b: bool

    monkeypatch.setenv("A", "off")
    monkeypatch.setenv("B", "ON")
    cfg = ci.load(S, sources=[ci.env()])
    assert cfg.a is False and cfg.b is True


def test_enum_invalid(monkeypatch):
    @dataclass
    class S:
        color: Color

    monkeypatch.setenv("COLOR", "green")
    try:
        ci.load(S, sources=[ci.env()])
        assert False
    except ci.TypeConversionError as e:
        assert "no matching enum member" in str(e)


def test_toml_parse_error(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("[not-closed\nkey = 1")
    try:
        ci.load(Settings, sources=[ci.file(str(bad))])
        assert False
    except ci.ConfSourceError as e:
        assert "Failed to parse TOML" in str(e)


def test_invalid_schema_rejected():
    try:
        ci.load(int, sources=[])  # type: ignore[arg-type]
        assert False
    except ci.ConfinitError as e:
        assert "dataclass" in str(e)


def test_unsupported_union_form(monkeypatch):
    @dataclass
    class S3:
        u: int | str

    monkeypatch.setenv("U", "1")
    try:
        ci.load(S3, sources=[ci.env()])
        assert False
    except ci.TypeConversionError as e:
        assert "Union[int, str]" in str(e)


def test_dotenv_export_and_quotes(tmp_path):
    envfile = tmp_path / ".env"
    envfile.write_text('export OPTIONAL_NAME="Alice" # inline comment\n')
    cfg = ci.load(Settings, sources=[ci.dotenv(str(envfile))])
    assert cfg.optional_name == "Alice"


def test_dotenv_read_error_when_directory(tmp_path):
    d = tmp_path / ".env"
    d.mkdir()
    try:
        ci.load(Settings, sources=[ci.dotenv(str(d))])
        assert False
    except ci.ConfSourceError as e:
        assert ".env" in str(e)


def test_str_coercion_from_toml_numeric(tmp_path):
    @dataclass
    class S:
        name: str

    p = tmp_path / "c.toml"
    p.write_text("name = 123\n")
    cfg = ci.load(S, sources=[ci.file(str(p))])
    assert cfg.name == "123"


def test_path_from_toml(tmp_path):
    @dataclass
    class S2:
        data_dir: Path

    p = tmp_path / "c.toml"
    p.write_text('data_dir = "/var/lib/app"\n')
    cfg = ci.load(S2, sources=[ci.file(str(p))])
    assert cfg.data_dir == Path("/var/lib/app")


def test_missing_required_field_raises():
    @dataclass
    class S:
        required: int

    try:
        ci.load(S, sources=[])  # type: ignore[arg-type]
        assert False
    except ci.MissingValue as e:
        assert "required" in str(e)


def test_dict_pass_through_from_toml(tmp_path):
    @dataclass
    class S:
        meta: dict

    p = tmp_path / "c.toml"
    p.write_text('meta = {k="v"}\n')
    cfg = ci.load(S, sources=[ci.file(str(p))])
    assert cfg.meta == {"k": "v"}


def test_bool_from_toml_true(tmp_path):
    @dataclass
    class S:
        debug: bool

    p = tmp_path / "c.toml"
    p.write_text("debug = true\n")
    cfg = ci.load(S, sources=[ci.file(str(p))])
    assert cfg.debug is True


def test_dotenv_line_without_equals_ignored(tmp_path):
    p = tmp_path / ".env"
    p.write_text("NOEQUALS\nworkers=3\n")

    @dataclass
    class S:
        workers: int = 1

    cfg = ci.load(S, sources=[ci.dotenv(str(p))])
    assert cfg.workers == 3
