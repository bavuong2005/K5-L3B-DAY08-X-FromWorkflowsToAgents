"""Bonus B1 — orchestrator with parallel read-only investigators. Student work.

Same run_claim contract as shape C, but the three independent reads
(lookup_order, lookup_policy, lookup_refund_history) run in a
ThreadPoolExecutor instead of one after another. Rules respected here:

- Every thread opens its OWN SQLite connection (connections are not shared
  across threads). The main thread keeps the writer connection.
- Every thread goes through lab8.runtime.dispatch(worker=True), so the host
  still refuses any non-read-only tool for investigators.
- Results are joined in the fixed spec order, keyed by tool name, so the
  outcome never depends on which thread finished first.
- compute_compensation depends on the order view, so it runs after the join.
- Only the orchestrator (main thread) calls durability.issue_refund: there is
  exactly one writer, and crash_at passes through untouched.
- Budget totals are merged after the join, so cost stays identical to the
  sequential orchestrator and the benchmark comparison stays fair.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import dispatch
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace

# Reads with no dependency between them: safe to run at the same time.
PARALLEL_TOOLS = ["lookup_order", "lookup_policy", "lookup_refund_history"]
# Dependent read: needs the order view from lookup_order first.
DEPENDENT_TOOLS = ["compute_compensation"]

Reader = Callable[[sqlite3.Connection, Budget], dict[str, Any]]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, store_path=store_path, crash_at=crash_at)
    finally:
        conn.close()


def _with_own_conn(store_path: str, reader: Reader) -> tuple[Any, Budget]:
    """Run one read tool on a dedicated connection. Returns (result, budget)."""
    conn = connect(store_path)
    budget = Budget()
    try:
        return reader(conn, budget), budget
    finally:
        conn.close()


def run_readonly_parallel(
    store_path: str,
    specs: list[tuple[str, Reader]],
) -> dict[str, tuple[Any, Budget]]:
    """Run independent readers concurrently, join in fixed spec order.

    Returns {name: (result, thread_budget)} with the keys in the order the
    specs were given, never in completion order, so downstream code cannot
    observe scheduling.
    """
    with ThreadPoolExecutor(max_workers=max(1, len(specs))) as pool:
        futures = [(name, pool.submit(_with_own_conn, store_path, reader)) for name, reader in specs]
        return {name: future.result() for name, future in futures}


def _merge_budget(budget: Budget, other: Budget) -> None:
    budget.model_calls += other.model_calls
    budget.tool_calls += other.tool_calls
    budget.input_tokens += other.input_tokens
    budget.output_tokens += other.output_tokens
    budget.cost_estimate += other.cost_estimate
    budget.steps += other.steps


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, store_path: str, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id("orchestrator_parallel", claim_id, seed)
    trace = Trace(run_id)

    # Routing read on the writer connection, exactly like shape C.
    budget.add_tool(tool_cost())
    claim_view = get_claim_view(conn, claim_id)
    if not claim_view.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    if not claim_view.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    # Handoff v1, same allowlist and same read-only tool set as shape C.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=PARALLEL_TOOLS + DEPENDENT_TOOLS,
    )
    trace.add("handoff", safe_dump(handoff))

    # The investigator squad reads the claim view once, together, before fanning
    # out (run_readonly_investigators bills the same read for shape C).
    budget.add_tool(tool_cost())

    principal_id = claim_view["principal_id"]
    order_id = claim_view.get("order_id")

    def _lookup_order(reader_conn: sqlite3.Connection, thread_budget: Budget) -> dict[str, Any]:
        return dispatch(
            reader_conn,
            thread_budget,
            "lookup_order",
            {"order_id": order_id, "principal_id": principal_id},
            worker=True,
        )

    def _lookup_policy(reader_conn: sqlite3.Connection, thread_budget: Budget) -> dict[str, Any]:
        return dispatch(reader_conn, thread_budget, "lookup_policy", {}, worker=True)

    def _lookup_refund_history(reader_conn: sqlite3.Connection, thread_budget: Budget) -> dict[str, Any]:
        return dispatch(
            reader_conn,
            thread_budget,
            "lookup_refund_history",
            {"order_id": order_id, "principal_id": principal_id},
            worker=True,
        )

    specs: list[tuple[str, Reader]] = [
        ("lookup_order", _lookup_order),
        ("lookup_policy", _lookup_policy),
        ("lookup_refund_history", _lookup_refund_history),
    ]
    outcomes = run_readonly_parallel(store_path, specs)
    results = {name: outcome[0] for name, outcome in outcomes.items()}
    for name in PARALLEL_TOOLS:  # merge in fixed order, not completion order
        _merge_budget(budget, outcomes[name][1])

    order_view = results["lookup_order"]
    policy_result = results["lookup_policy"] or {}
    trace.add(
        "investigator",
        {
            "lookup_order": order_view,
            "policy_count": len(policy_result.get("policies") or []),
        },
    )
    history = results["lookup_refund_history"] or {}
    if history.get("visible"):
        trace.add(
            "order_refund_state",
            {"refund_count": history["refund_count"], "refunded_vnd": history["refunded_vnd"]},
        )

    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        trace.add("decision", {"status": "escalated"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    # Dependent read: needs the order view, so it runs after the join, on the
    # writer connection, like shape C.
    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, dict(order_view["order"]))
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", quote_payload)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        trace.add("decision", {"status": "denied"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("host_decision", {"ok": bool(outcome["ok"]), "reason": outcome["reason"]})
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return finish(
            conn,
            shape="orchestrator_parallel",
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
        shape="orchestrator_parallel",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
