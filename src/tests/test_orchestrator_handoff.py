"""Student evidence for the orchestrator (shape C) handoff boundary.

Covers: allowlisted handoff in the trace, read-only investigator tools, and no
secret/PII in the trace or any ``<run_id>*`` side file on resolved, escalated
and needs_info paths.
"""

from __future__ import annotations

import json
from pathlib import Path

from lab8.db import connect, init_store
from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD

FORBIDDEN_ALWAYS = ("parent_secret", "raw_headers", "CANARY_SECRET_", "CANARY_INTERNAL_")


def _store(tmp_path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _run_isolated(monkeypatch, tmp_path, name: str, claim_id: str, seed: int = 11):
    """Run the shape with traces written under tmp_path, not the shared src/traces."""
    monkeypatch.chdir(tmp_path)
    store = _store(tmp_path, name)
    result = SHAPES["orchestrator"](claim_id, seed=seed, store_path=str(store))
    assert Path(result.trace_path).is_file(), "trace must be written in this run"
    return result


def _side_files(trace_path: str, run_id: str) -> list[str]:
    directory = Path(trace_path).parent
    return [p.read_text(encoding="utf-8") for p in sorted(directory.glob(f"{run_id}*"))]


def test_handoff_in_trace_is_allowlisted_and_readonly(tmp_path, monkeypatch):
    result = _run_isolated(monkeypatch, tmp_path, "handoff.sqlite", "C-001")
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    handoffs = [e["payload"] for e in trace["events"] if e["kind"] == "handoff"]
    assert handoffs, "orchestrator must trace the sanitized handoff"
    payload = handoffs[0]
    assert set(payload) <= ALLOWED_FIELDS
    assert payload["allowed_tools"], "handoff must name the investigator tools"
    assert set(payload["allowed_tools"]) <= READONLY_TOOLS
    assert not set(payload["allowed_tools"]) & {"issue_refund", "append_audit"}


def test_resolved_path_trace_leaks_nothing(tmp_path, monkeypatch):
    result = _run_isolated(monkeypatch, tmp_path, "resolved.sqlite", "C-001")
    assert result.status == "resolved"
    forbidden = list(BY_ID["C-001"]["expected"]["forbid_substrings"]) + list(FORBIDDEN_ALWAYS)
    blobs = _side_files(result.trace_path, result.run_id)
    assert blobs, "trace must be written in this run"
    for blob in blobs:
        for needle in forbidden:
            assert needle not in blob


def test_escalated_path_leaks_no_pii(tmp_path, monkeypatch):
    # C-005 (T05): the order belongs to another principal and its row carries a
    # phone, an address, an item name and an internal note. None of that may
    # reach the trace or any side file.
    result = _run_isolated(monkeypatch, tmp_path, "escalated.sqlite", "C-005")
    assert result.status == "escalated"
    assert result.proposal_amount == 0
    forbidden = list(BY_ID["C-005"]["expected"]["forbid_substrings"]) + list(FORBIDDEN_ALWAYS)
    blobs = _side_files(result.trace_path, result.run_id)
    for blob in blobs:
        for needle in forbidden:
            assert needle not in blob


def test_needs_info_path_valid_trace_and_no_ledger_row(tmp_path, monkeypatch):
    result = _run_isolated(monkeypatch, tmp_path, "needs_info.sqlite", "C-004")
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    conn = connect(tmp_path / "needs_info.sqlite")
    try:
        rows = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-004'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert rows == 0
