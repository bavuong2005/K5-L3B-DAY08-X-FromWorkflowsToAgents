"""Bonus B1 — simulated critical path: sequential vs parallel investigators.

MockLLM reports latency as unavailable, so this is an analytic model, not a
wall-clock measurement. For every public trial both shapes run for real (same
claims, same seeds, same prices); their dependency DAG is rebuilt from the
resulting status, each node gets its latency from bonus/latency.yaml with
seed-fixed jitter, and the critical path is the longest chain through the DAG.

Amdahl check: with 3 parallel workers the predicted speedup is
1 / (S + P/3), where S is the serial fraction and P the parallelizable reads.

Run from src/:

    python -m bonus.critical_path --out reports/bonus_critical_path.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

from lab8.app import prepare_store
from lab8.config_loader import repo_path
from lab8.console import utf8_stdio
from lab8.db import load_jsonl

from bonus.latency import step_ms
from bonus.orchestrator_parallel import PARALLEL_TOOLS, run_claim as parallel_claim
from lab8.shapes.orchestrator import run_claim as sequential_claim

SEQ_CHAIN = ["lookup_order", "lookup_policy", "compute_compensation", "lookup_refund_history"]
DEFAULT_SEEDS = [11, 22, 33, 44, 55]


def build_plan(shape: str, status: str, proposal_amount: int, error_reason: str | None) -> list[list[str]]:
    """Phases of the run in execution order. Each phase lists nodes that share
    a start time; the sequential shape always has one node per phase."""
    if status == "failed" and error_reason == "unknown_claim":
        return [["get_claim_view"]]
    if status == "needs_info":
        return [["get_claim_view"], ["draft_model"]]
    if status == "escalated":
        reads = [name for name in SEQ_CHAIN if name != "compute_compensation"]
        if shape == "orchestrator_parallel":
            return [["get_claim_view"], list(PARALLEL_TOOLS), ["draft_model"]]
        return [["get_claim_view"]] + [[name] for name in reads] + [["draft_model"]]
    tail: list[list[str]] = [["draft_model"]] + ([["issue_refund"]] if proposal_amount > 0 else [])
    if shape == "orchestrator_parallel":
        return [["get_claim_view"], list(PARALLEL_TOOLS), ["compute_compensation"]] + tail
    return [["get_claim_view"]] + [[name] for name in SEQ_CHAIN] + tail


def critical_path_ms(phases: list[list[str]], *, shape: str, claim_id: str, seed: int) -> float:
    total = 0.0
    for phase in phases:
        total += max(step_ms(node, shape=shape, claim_id=claim_id, seed=seed) for node in phase)
    return round(total, 3)


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = math.ceil(0.95 * len(ordered)) - 1
    return ordered[max(0, index)]


def amdahl_prediction(serial_ms: float, parallel_ms: float, workers: int = 3) -> float:
    total = serial_ms + parallel_ms
    if total <= 0:
        return 1.0
    return total / (serial_ms + parallel_ms / workers)


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="Bonus B1 critical path model")
    parser.add_argument("--cases", default=str(repo_path("data", "public_claims.jsonl")))
    parser.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    claims = load_jsonl(args.cases)
    seeds = [int(seed) for seed in args.seeds.split(",")]
    shapes = {"orchestrator": sequential_claim, "orchestrator_parallel": parallel_claim}

    trials: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="lab8-b1-", ignore_cleanup_errors=True) as tmp:
        original_cwd = os.getcwd()
        os.chdir(tmp)  # traces land in the temp dir, not src/traces
        try:
            for claim in claims:
                claim_id = str(claim["claim_id"])
                for seed in seeds:
                    row: dict[str, Any] = {"claim_id": claim_id, "seed": seed}
                    serial_fraction = 0.0
                    parallel_fraction = 0.0
                    for shape, run_claim in shapes.items():
                        store = os.path.join(tmp, f"{shape}-{claim_id}-{seed}.sqlite")
                        prepare_store(store)
                        result = run_claim(claim_id, seed=seed, store_path=store)
                        phases = build_plan(shape, result.status, result.proposal_amount, result.error_reason)
                        ms = critical_path_ms(phases, shape=shape, claim_id=claim_id, seed=seed)
                        row[shape] = {"status": result.status, "proposal_amount": result.proposal_amount, "critical_path_ms": ms}
                        if shape == "orchestrator_parallel":
                            serial_fraction = sum(
                                step_ms(node, shape=shape, claim_id=claim_id, seed=seed)
                                for phase in phases if len(phase) == 1 for node in phase
                            )
                            parallel_fraction = sum(
                                step_ms(node, shape=shape, claim_id=claim_id, seed=seed)
                                for phase in phases if len(phase) > 1 for node in phase
                            )
                    row["statuses_match"] = (
                        row["orchestrator"]["status"] == row["orchestrator_parallel"]["status"]
                        and row["orchestrator"]["proposal_amount"] == row["orchestrator_parallel"]["proposal_amount"]
                    )
                    row["speedup"] = round(row["orchestrator"]["critical_path_ms"] / row["orchestrator_parallel"]["critical_path_ms"], 4)
                    row["amdahl_predicted_speedup"] = round(amdahl_prediction(serial_fraction, parallel_fraction), 4)
                    trials.append(row)
        finally:
            os.chdir(original_cwd)

    report: dict[str, Any] = {
        "topic": "B1",
        "latency_model": "bonus/latency.yaml",
        "claims": len(claims),
        "seeds": seeds,
        "trials": len(trials),
        "statuses_match": all(row["statuses_match"] for row in trials),
        "per_shape": {},
    }
    for shape in shapes:
        values = [row[shape]["critical_path_ms"] for row in trials]
        report["per_shape"][shape] = {
            "mean_ms": round(sum(values) / len(values), 3),
            "p95_ms": p95(values),
            "min_ms": min(values),
            "max_ms": max(values),
        }
    seq_mean = report["per_shape"]["orchestrator"]["mean_ms"]
    par_mean = report["per_shape"]["orchestrator_parallel"]["mean_ms"]
    report["speedup_mean"] = round(seq_mean / par_mean, 4)
    report["amdahl_predicted_mean_speedup"] = round(
        sum(row["amdahl_predicted_speedup"] for row in trials) / len(trials), 4
    )
    report["trials_detail"] = trials

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"critical path mean: sequential {seq_mean} ms | parallel {par_mean} ms | "
        f"speedup {report['speedup_mean']}x (Amdahl predicts {report['amdahl_predicted_mean_speedup']}x with 3 workers)"
    )
    print(f"statuses_match {report['statuses_match']} | wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
