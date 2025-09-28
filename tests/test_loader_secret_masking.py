from __future__ import annotations

from dataclasses import dataclass

import confinit as ci


def test_loader_masks_provenance_for_secret(monkeypatch):
    @dataclass
    class S:
        token: ci.Secret[str]

    monkeypatch.setenv("TOKEN", "super-secret")
    cfg = ci.load(S, sources=[ci.env()])
    assert isinstance(cfg.token, ci.Secret)
    assert str(cfg.token) == "***"
    assert cfg.token.reveal() == "super-secret"
    assert cfg.__provenance__["token"].raw_value == "***"
