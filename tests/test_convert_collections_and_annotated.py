from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

import confinit as ci


def test_list_from_env_json_and_csv(monkeypatch):
    @dataclass
    class S:
        tags: list[str]
        nums: list[int]

    monkeypatch.setenv("TAGS", '"a b",c,d')
    monkeypatch.setenv("NUMS", "[1,2,3]")
    cfg = ci.load(S, sources=[ci.env()])
    assert cfg.tags == ["a b", "c", "d"]
    assert cfg.nums == [1, 2, 3]


def test_dict_from_env_json(monkeypatch):
    @dataclass
    class S:
        meta: dict[str, Any]

    monkeypatch.setenv("META", '{"x": 1, "y": "z"}')
    cfg = ci.load(S, sources=[ci.env()])
    assert cfg.meta == {"x": 1, "y": "z"}


def test_annotated_decoder_custom(monkeypatch):
    @dataclass
    class S:
        port: Annotated[int, ci.Decoder(lambda s: int(str(s), 16))]

    monkeypatch.setenv("PORT", "FF")
    cfg = ci.load(S, sources=[ci.env()])
    assert cfg.port == 255
