"""Workflow-owned checks. The public matrix covers every shape; these lock the workflow contract."""

from __future__ import annotations

from pathlib import Path

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.shapes.workflow import run_claim
from tests.conftest import CLAIMS, WORLD


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def test_workflow_ignores_ticket_delay_on_the_swarm_weak_seed(tmp_path: Path):
    store = _store(tmp_path, "t02.sqlite")
    result = run_claim("C-002", seed=55, store_path=str(store))
    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-002'").fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert count == 0


def test_workflow_keeps_the_full_quote_when_the_host_pays_the_difference(tmp_path: Path):
    store = _store(tmp_path, "t14.sqlite")
    result = run_claim("C-014", seed=11, store_path=str(store))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000
    assert len(result.refund_effects) == 1
    assert int(result.refund_effects[0]["amount_vnd"]) == 120000
    assert result.committed_audit_count == 1
    trace = Path(result.trace_path).read_text(encoding="utf-8")
    assert "CANARY_SECRET_" not in trace


def test_workflow_lets_the_injected_crash_escape_and_retries_once(tmp_path: Path):
    store = _store(tmp_path, "t12.sqlite")
    try:
        run_claim(
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )
    except InjectedCrash:
        pass
    else:
        raise AssertionError("crash did not leave run_claim")
    result = run_claim("C-012", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'").fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert count == 1
