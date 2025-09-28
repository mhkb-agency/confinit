from __future__ import annotations

from dataclasses import dataclass

import confinit as ci


def test_cli_source_overrides_and_provenance():
    @dataclass
    class S:
        workers: int = 1

    cfg = ci.load(S, sources=[ci.cli(["--workers=12"])])
    assert cfg.workers == 12
    prov = cfg.__provenance__["workers"]
    assert prov.kind == "cli" and prov.path == "--workers"
