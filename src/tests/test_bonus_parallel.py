"""Bonus B1 tests — parallel investigators must behave exactly like shape C.

pytest -q tests/test_bonus_parallel.py -o addopts=
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS
from tests.conftest import CLAIMS, WORLD
from bonus.orchestrator_parallel import run_claim as parallel
from bonus.orchestrator_parallel import run_readonly_parallel
from lab8.shapes.orchestrator import run_claim as sequential

FORBIDDEN = ("parent_secret", "raw_headers", "CANARY_SECRET_", "CANARY_INTERNAL_")


def _store(tmp_path: Path, name: str) -> str:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_parallel_matches_sequential_on_resolved_claim(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    seq = sequential("C-001", seed=11, store_path=_store(tmp_path, "seq.sqlite"))
    par = parallel("C-001", seed=11, store_path=_store(tmp_path, "par.sqlite"))

    assert seq.status == par.status == "resolved"
    assert par.proposal_amount == seq.proposal_amount == 35000
    assert par.refund_effects == seq.refund_effects
    assert par.committed_audit_count == seq.committed_audit_count == 1
    # Fair comparison: same number of model calls, tool calls, tokens and cost.
    assert par.model_calls == seq.model_calls
    assert par.tool_calls == seq.tool_calls
    assert par.input_tokens == seq.input_tokens
    assert par.output_tokens == seq.output_tokens
    assert par.cost_estimate == seq.cost_estimate
    # Security boundary holds through the thread pool.
    trace_blob = Path(par.trace_path).read_text(encoding="utf-8")
    for needle in FORBIDDEN:
        assert needle not in trace_blob


@pytest.mark.parametrize("claim_id", ["C-002", "C-004", "C-005", "C-013", "C-014"])
def test_parallel_matches_sequential_across_branches(tmp_path, monkeypatch, claim_id):
    _isolate(tmp_path, monkeypatch)
    seq_store = _store(tmp_path, f"seq-{claim_id}.sqlite")
    par_store = _store(tmp_path, f"par-{claim_id}.sqlite")
    seq = sequential(claim_id, seed=11, store_path=seq_store)
    par = parallel(claim_id, seed=11, store_path=par_store)

    assert par.status == seq.status
    assert par.proposal_amount == seq.proposal_amount
    assert par.error_reason == seq.error_reason

    def _ledger_rows(store: str) -> int:
        conn = connect(store)
        try:
            return conn.execute(
                "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)
            ).fetchone()["n"]
        finally:
            conn.close()

    assert _ledger_rows(par_store) == _ledger_rows(seq_store)


def test_join_is_fixed_order_not_completion_order(tmp_path):
    """The slow task is listed first but must finish last; the result mapping
    still follows the spec order, so scheduling is unobservable."""
    started = threading.Event()
    release = threading.Event()

    def slow(*_args):
        started.set()
        release.wait(timeout=5)
        return {"who": "slow"}

    def fast(*_args):
        started.wait(timeout=5)
        release.set()  # fast completes while slow is still blocked
        return {"who": "fast"}

    specs = [("slow", slow), ("fast", fast)]
    outcomes = run_readonly_parallel(str(tmp_path / "fakes.sqlite"), specs)

    assert list(outcomes) == ["slow", "fast"]  # spec order, not completion order
    assert outcomes["slow"][0] == {"who": "slow"}
    assert outcomes["fast"][0] == {"who": "fast"}


def test_parallel_trace_handoff_is_allowlisted_and_pii_free(tmp_path, monkeypatch):
    """C-005 escalates: the order belongs to another principal and its row
    carries phone, address, item name and an internal note. None of it may
    reach the trace, and the handoff must stay inside the allowlist."""
    _isolate(tmp_path, monkeypatch)
    result = parallel("C-005", seed=11, store_path=_store(tmp_path, "escalated.sqlite"))

    assert result.status == "escalated"
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    handoffs = [event["payload"] for event in trace["events"] if event["kind"] == "handoff"]
    assert handoffs, "parallel orchestrator must trace the sanitized handoff"
    payload = handoffs[0]
    assert set(payload) <= ALLOWED_FIELDS
    assert set(payload["allowed_tools"]) <= READONLY_TOOLS
    blob = json.dumps(trace, ensure_ascii=False)
    for needle in FORBIDDEN + ("0901111222", "99 Duong Bi Mat", "SECRET_ITEM_VANG"):
        assert needle not in blob
