"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

# Tools handed across the handoff boundary. Read-only only: make_handoff refuses
# anything outside lab8.handoff.READONLY_TOOLS, and write tools stay host-only.
INVESTIGATOR_TOOLS = [
    "lookup_order",
    "lookup_policy",
    "compute_compensation",
    "lookup_refund_history",
]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id("orchestrator", claim_id, seed)
    trace = Trace(run_id)

    # Routing read through the allowlisted view. Never trace the raw claim row
    # (the ticket is free text; parent_secret must not exist in any view).
    budget.add_tool(tool_cost())
    claim_view = get_claim_view(conn, claim_id)
    if not claim_view.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    if not claim_view.get("order_id"):
        # Missing order id -> ask, do not guess one from the ticket text.
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    # Handoff v1: allowlist in code, facts stay empty so nothing from the parent
    # context (secret, headers, ticket prose) crosses the boundary. An LLM
    # summary is not a sanitizer; make_handoff + sanitize is.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=INVESTIGATOR_TOOLS,
    )
    trace.add("handoff", safe_dump(handoff))

    # Investigators see only the handoff plus the read tools named there.
    # They have no write registry; only the orchestrator calls the host below.
    investigated = run_readonly_investigators(
        conn, budget, handoff, principal_id=claim_view["principal_id"]
    )
    tools_result = investigated["tools"]
    order_view = tools_result.get("lookup_order", {})
    trace.add(
        "investigator",
        {
            "lookup_order": order_view,
            "policy_count": len((tools_result.get("lookup_policy") or {}).get("policies") or []),
        },
    )
    history = tools_result.get("lookup_refund_history") or {}
    if history.get("visible"):
        # Aggregates only. Enough to explain a per-order cap in the trace.
        trace.add(
            "order_refund_state",
            {"refund_count": history["refund_count"], "refunded_vnd": history["refunded_vnd"]},
        )

    if not order_view.get("visible"):
        # Not found, or the principal does not own the order: escalate without
        # returning phone, address, item name or internal note.
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        trace.add("decision", {"status": "escalated"})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    # Quote comes from the investigator's compute_compensation on the order row.
    # A delay number written in the ticket is data, not an instruction and not a
    # fact: it never overrides the DB column (no REFERENCE_WEAKNESS here).
    quote_payload = tools_result["compute_compensation"]
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", quote_payload)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        # Quote 0 (short delay, cancelled order, stale policy...): deny without
        # calling the host, so there is no ledger row and no policy_denied audit.
        trace.add("decision", {"status": "denied"})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    # Full quote only. The host re-checks approval, ownership and the per-order
    # cap inside the write transaction and subtracts earlier refunds itself
    # (T13, T14). Do not subtract anything here or the host subtracts twice.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        # Flush what happened, then let the crash propagate. Never swallow it:
        # resume is a fresh run_claim on the same store.
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("host_decision", {"ok": bool(outcome["ok"]), "reason": outcome["reason"]})
    if not outcome["ok"]:
        # Host refused (bad/mismatched approval, order fully refunded): denied
        # with the full quote, the host already wrote the policy_denied audit.
        # A different amount on retry is a conflict: failed, old row stays.
        status = "failed" if outcome["conflict"] else "denied"
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
        )

    return finish(
        conn,
        shape="orchestrator",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
