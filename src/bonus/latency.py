"""Simulated latency for bonus B1. Deterministic, offline, no time.sleep.

Each node has a base latency in bonus/latency.yaml plus seeded jitter in
+/-jitter_pct. Same (node, shape, claim, seed) always returns the same value,
so the critical-path comparison is reproducible.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

MODEL_PATH = Path(__file__).with_name("latency.yaml")


@lru_cache(maxsize=1)
def _model() -> dict[str, Any]:
    data = yaml.safe_load(MODEL_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "node_ms" not in data:
        raise ValueError(f"{MODEL_PATH.name} must map node_ms and jitter_pct")
    return data


def node_names() -> list[str]:
    return sorted(_model()["node_ms"])


def step_ms(node: str, *, shape: str, claim_id: str, seed: int) -> float:
    """Latency of one node in this trial, jitter fixed by the seed."""
    model = _model()
    base = float(model["node_ms"][node])
    pct = float(model["jitter_pct"])
    digest = hashlib.sha256(f"{seed}|{shape}|{claim_id}|{node}".encode()).hexdigest()
    frac = int(digest[:8], 16) / 0xFFFFFFFF  # in [0, 1]
    jitter = 1.0 + (frac * 2.0 - 1.0) * (pct / 100.0)
    return round(base * jitter, 3)
