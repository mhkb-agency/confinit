from __future__ import annotations

import confinit as ci


def test_secret_wrapper_str_repr_and_reveal():
    s = ci.Secret("super-secret")
    assert str(s) == "***"
    assert "***" in repr(s)
    assert s.reveal() == "super-secret"
