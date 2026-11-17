"""The reference swarm's weak seed must still respect the host approval gate."""

import json
import time

from lab8.db import connect
from lab8.durability import get_refund
from lab8.metrics import trial_pass
from lab8.shapes.swarm_reference import run_claim
from tests.conftest import BY_ID


def test_expired_approval_is_denied_at_swarm_weak_seed(public_db):
    started_at = time.time()
    result = run_claim("C-007", seed=55, store_path=str(public_db))
    conn = connect(public_db)
    try:
        effect = get_refund(conn, "C-007")
        denials = conn.execute(
            "SELECT details_json FROM audit_events "
            "WHERE claim_id = ? AND event_type = 'policy_denied'",
            ("C-007",),
        ).fetchall()
        passed, reason = trial_pass(
            result.as_dict(), BY_ID["C-007"]["expected"], conn, started_at=started_at
        )
    finally:
        conn.close()

    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert effect is None
    assert any(json.loads(row["details_json"])["reason"] == "approval_expired" for row in denials)
    assert passed, reason
