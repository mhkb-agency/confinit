"""
Minimal performance benchmark scaffold for CI.

This script measures a simple operation many times and enforces
an upper bound on runtime via BENCH_THRESHOLD_SECONDS.

Env vars:
  BENCH_ITER: number of iterations (default: 10000)
  BENCH_THRESHOLD_SECONDS: max allowed seconds (default: 1.0)
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass


def _int(s: str, default: int) -> int:
    try:
        return int(s)
    except Exception:
        return default


def _float(s: str, default: float) -> float:
    try:
        return float(s)
    except Exception:
        return default


ITER = _int(os.getenv("BENCH_ITER", "10000"), 10000)
THRESHOLD = _float(os.getenv("BENCH_THRESHOLD_SECONDS", "1.0"), 1.0)


@dataclass
class _Settings:
    debug: bool = False
    workers: int = 4
    db_url: str = "postgresql://localhost/db"
    data_dir: str | None = None


def micro_op(i: int) -> int:
    # Simulate a tiny amount of work akin to constructing config objects
    s = _Settings(debug=(i % 2 == 0), workers=(i % 8) + 1)
    # Return something to avoid aggressive optimization assumptions
    return (s.workers if s.debug else -s.workers) ^ i


def main() -> int:
    start = time.perf_counter()
    acc = 0
    for i in range(ITER):
        acc ^= micro_op(i)
    dur = time.perf_counter() - start
    ops_per_sec = ITER / dur if dur > 0 else float("inf")

    print(
        f"BENCH: iter={ITER} time={dur:.6f}s ops/s={ops_per_sec:.0f} threshold={THRESHOLD:.3f}s"
    )
    # Ensure we use acc so the loop isn't eliminated
    if acc == 42_4242:  # extremely unlikely; just to keep lints quiet
        print("magic")

    if dur > THRESHOLD:
        print(f"FAIL: exceeded threshold by {dur - THRESHOLD:.6f}s", file=sys.stderr)
        return 1
    print("OK: within threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

