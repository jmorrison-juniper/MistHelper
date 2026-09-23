"""Unit tests of the site lock release rule of a multi-site operation (issue #3220)."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.app.routes import org_upgrade


def operation(*states: str, state: str = "running", cancelled: bool = False) -> dict[str, Any]:
    """Build one aggregate operation with one child for each state.

    Args:
        *states: The status of each child.
        state: The aggregate state.
        cancelled: True when the operator requested a cancel.

    Returns:
        The operation record.
    """
    children = [{"child_id": f"child-{index}", "status": value} for index, value in enumerate(states)]  # One row each.
    return {"state": state, "children": children, "cancellation": {"requested": cancelled, "results": []}}


@pytest.mark.parametrize("child_state", ["running", "accepted", "partial", "read_unknown", "submission_unknown"])
def test_a_child_that_can_still_write_keeps_the_sites(child_state: str) -> None:
    """A running or uncertain child keeps every site lock, even when the aggregate reads attention_required."""
    record = operation("completed", child_state, state="attention_required")  # One child is not past the write.
    assert org_upgrade._operation_is_settled(record) is False  # The sites stay held.


def test_a_cancel_request_alone_keeps_the_sites() -> None:
    """A cancel does not stop a device that already writes firmware."""
    record = operation("running", "running", cancelled=True)  # The cloud still runs both children.
    assert org_upgrade._operation_is_settled(record) is False  # The sites stay held until the children end.


def test_every_final_child_releases_the_sites() -> None:
    """Each known final child state lets the portal release the sites."""
    record = operation("completed", "failed", "cancelled", "rejected", "not_submitted", state="failed")  # All final.
    assert org_upgrade._operation_is_settled(record) is True  # No firmware write can follow.


@pytest.mark.parametrize(("state", "settled"), [("completed", True), ("failed", True), ("attention_required", False)])
def test_a_record_without_children_keeps_the_conservative_state_rule(state: str, settled: bool) -> None:
    """A damaged record with no child releases the sites only for a final aggregate state."""
    record = {"state": state, "children": []}  # No child row survived.
    assert org_upgrade._operation_is_settled(record) is settled  # attention_required never releases the sites.
