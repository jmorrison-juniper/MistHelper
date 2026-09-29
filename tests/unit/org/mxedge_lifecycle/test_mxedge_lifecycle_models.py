"""Contract tests for Mist Edge lifecycle request models."""

from __future__ import annotations  # WHY: match package type syntax.

import pytest  # WHY: validate model refusal paths.

from src.org.mxedge_lifecycle.models import (  # WHY: pure builders are the contract surface.
    REDACTED_VALUE,
    STEP_ASSIGN,
    STEP_BOUNCE,
    STEP_CLAIM,
    STEP_UNASSIGN,
    STEP_UPGRADE,
    MxEdgeLifecycleModels,
    UpgradeStatusReader,
)


def test_mxedge_lifecycle_claim_body_matches_openapi() -> None:
    """The claim body must use the OpenAPI `code` field."""
    request = MxEdgeLifecycleModels.claim("135-546-673")  # WHY: sample code from OpenAPI.
    assert request.step == STEP_CLAIM  # WHY: row and dispatch key must be stable.
    assert request.confirmation_word == "CLAIM"  # WHY: destructive claim guard word.
    assert request.body == {"code": "135-546-673"}  # WHY: OpenAPI `code_string` shape.
    assert request.target_summary == REDACTED_VALUE  # WHY: claim code must not reach logs or CSV.


def test_mxedge_lifecycle_assign_body_matches_openapi() -> None:
    """The assign body must use `mxedge_ids` and `site_id`."""
    request = MxEdgeLifecycleModels.assign(["mx-1"], "site-1")  # WHY: single-target assignment.
    assert request.step == STEP_ASSIGN  # WHY: row and dispatch key must be stable.
    assert request.confirmation_word == "ASSIGN"  # WHY: destructive assign guard word.
    assert request.body == {"mxedge_ids": ["mx-1"], "site_id": "site-1"}  # WHY: OpenAPI shape.


def test_mxedge_lifecycle_unassign_body_matches_openapi() -> None:
    """The unassign body must use only `mxedge_ids`."""
    request = MxEdgeLifecycleModels.unassign(["mx-1", "mx-2"])  # WHY: bulk unassign is supported.
    assert request.step == STEP_UNASSIGN  # WHY: row and dispatch key must be stable.
    assert request.confirmation_word == "UNASSIGN"  # WHY: destructive unassign guard word.
    assert request.body == {"mxedge_ids": ["mx-1", "mx-2"]}  # WHY: OpenAPI shape.


def test_mxedge_lifecycle_bounce_body_matches_openapi() -> None:
    """The bounce body must use the OpenAPI `ports` field."""
    request = MxEdgeLifecycleModels.bounce("mx-1", ["0", "2"])  # WHY: sample ports from OpenAPI.
    assert request.step == STEP_BOUNCE  # WHY: row and dispatch key must be stable.
    assert request.confirmation_word == "BOUNCE"  # WHY: destructive bounce guard word.
    assert request.body == {"ports": ["0", "2"]}  # WHY: OpenAPI `utils_tunterm_bounce_port` shape.


def test_mxedge_lifecycle_upgrade_body_matches_openapi() -> None:
    """The upgrade body must include targets, strategy, and versions."""
    request = MxEdgeLifecycleModels.upgrade(["mx-1"], "default")  # WHY: default tunnel service target.
    assert request.step == STEP_UPGRADE  # WHY: row and dispatch key must be stable.
    assert request.confirmation_word == "UPGRADE"  # WHY: destructive upgrade guard word.
    assert request.body == {"mxedge_ids": ["mx-1"], "strategy": "serial", "versions": {"tunterm": "default"}}


def test_mxedge_lifecycle_empty_targets_are_refused() -> None:
    """Empty target lists must stop before an API body exists."""
    with pytest.raises(ValueError, match="ports"):  # WHY: empty bounce would target nothing.
        MxEdgeLifecycleModels.bounce("mx-1", [])  # WHY: validate the refusal path.


def test_mxedge_lifecycle_terminal_status_detection() -> None:
    """Terminal upgrade statuses must stop polling."""
    assert UpgradeStatusReader.status_from({"state": "Completed"}) == "completed"  # WHY: state field fallback.
    assert UpgradeStatusReader.is_terminal("completed") is True  # WHY: completed is terminal.
    assert UpgradeStatusReader.is_terminal("running") is False  # WHY: running must continue polling.
