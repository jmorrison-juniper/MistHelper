"""Verify authoritative bulk run previews."""

from datetime import UTC, datetime, timedelta

import pytest

from src.upgrade_portal.api.run_controls.models import BulkPreviewRequest
from src.upgrade_portal.api.run_controls.services import BulkActionPreviewService, PreviewError

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)


def _records() -> dict[str, dict[str, str]]:
    return {
        "run-a": {"run_id": "run-a", "organization_id": "org-a", "site_id": "site-a"},
        "run-b": {"run_id": "run-b", "organization_id": "org-a", "site_id": "site-a"},
        "run-c": {"run_id": "run-c", "organization_id": "org-a", "site_id": "site-b"},
        "run-hidden": {"run_id": "run-hidden", "organization_id": "org-b", "site_id": "site-c"},
    }


def _service(clock=lambda: NOW) -> BulkActionPreviewService:
    records = _records()
    return BulkActionPreviewService(
        run_reader=lambda run_id: records.get(run_id),
        visibility_reader=lambda row, org_id, scope: (
            row.get("organization_id") == org_id
            and (scope == "all-sites" or row.get("site_id") == scope.removeprefix("site:"))
        ),
        signing_key="unit-test-preview-key",
        clock=clock,
    )


def test_request_rejects_duplicate_identifiers_without_deduplication() -> None:
    with pytest.raises(ValueError, match="duplicate_run_id"):
        BulkPreviewRequest.from_mapping(
            {
                "action": "cancel",
                "organization_id": "org-a",
                "history_scope": "all-sites",
                "run_ids": ["run-a", "run-a"],
            }
        )


@pytest.mark.parametrize("run_ids", [[], [f"run-{index}" for index in range(51)]])
def test_request_rejects_an_unsafe_batch_size(run_ids: list[str]) -> None:
    with pytest.raises(ValueError, match="batch_size_invalid"):
        BulkPreviewRequest.from_mapping(
            {
                "action": "retry",
                "organization_id": "org-a",
                "history_scope": "all-sites",
                "run_ids": run_ids,
            }
        )


def test_preview_removes_hidden_and_absent_identifiers_and_returns_exact_counts() -> None:
    request = BulkPreviewRequest.from_mapping(
        {
            "action": "cancel",
            "organization_id": "org-a",
            "history_scope": "all-sites",
            "run_ids": ["run-a", "run-hidden", "missing", "run-b", "run-c"],
        }
    )

    result = _service().preview(request, "actor-scope-a").to_mapping()

    assert result["run_ids"] == ["run-a", "run-b", "run-c"]
    assert result["removed_run_ids"] == ["run-hidden", "missing"]
    assert result["run_count"] == 3
    assert result["site_count"] == 2
    assert result["site_counts"] == {"site-a": 2, "site-b": 1}
    assert result["confirmation"] == "CANCEL 3 RUNS"
    assert result["expires_at"] == "2026-09-11T08:10:00Z"


def test_preview_applies_the_current_history_scope() -> None:
    request = BulkPreviewRequest.from_mapping(
        {
            "action": "retry",
            "organization_id": "org-a",
            "history_scope": "site:site-b",
            "run_ids": ["run-a", "run-c"],
        }
    )

    result = _service().preview(request, "actor-scope-a").to_mapping()

    assert result["run_ids"] == ["run-c"]
    assert result["removed_run_ids"] == ["run-a"]
    assert result["confirmation"] == "RETRY 1 RUNS"


def test_preview_refuses_an_empty_authoritative_selection() -> None:
    request = BulkPreviewRequest.from_mapping(
        {
            "action": "cancel",
            "organization_id": "org-a",
            "history_scope": "all-sites",
            "run_ids": ["run-hidden", "missing"],
        }
    )

    with pytest.raises(PreviewError, match="preview_empty"):
        _service().preview(request, "actor-scope-a")


def test_token_verification_binds_actor_action_scope_order_and_counts() -> None:
    service = _service()
    request = BulkPreviewRequest.from_mapping(
        {
            "action": "cancel",
            "organization_id": "org-a",
            "history_scope": "all-sites",
            "run_ids": ["run-a", "run-c"],
        }
    )
    preview = service.preview(request, "actor-scope-a")

    payload = service.verify(
        preview.preview_token,
        actor_scope="actor-scope-a",
        action="cancel",
        organization_id="org-a",
        history_scope="all-sites",
        run_ids=("run-a", "run-c"),
    )

    assert payload["run_count"] == 2
    assert payload["site_counts"] == {"site-a": 1, "site-b": 1}
    for changed in (
        {"actor_scope": "actor-scope-b"},
        {"action": "retry"},
        {"organization_id": "org-b"},
        {"history_scope": "site:site-a"},
        {"run_ids": ("run-c", "run-a")},
    ):
        arguments = {
            "actor_scope": "actor-scope-a",
            "action": "cancel",
            "organization_id": "org-a",
            "history_scope": "all-sites",
            "run_ids": ("run-a", "run-c"),
        }
        arguments.update(changed)
        with pytest.raises(PreviewError, match="preview_mismatch"):
            service.verify(preview.preview_token, **arguments)


def test_token_refuses_tampering_and_expiry() -> None:
    now = [NOW]
    service = _service(clock=lambda: now[0])
    request = BulkPreviewRequest.from_mapping(
        {
            "action": "cancel",
            "organization_id": "org-a",
            "history_scope": "all-sites",
            "run_ids": ["run-a"],
        }
    )
    preview = service.preview(request, "actor-scope-a")

    with pytest.raises(PreviewError, match="preview_invalid"):
        service.verify(
            preview.preview_token[:-1] + ("0" if preview.preview_token[-1] != "0" else "1"),
            actor_scope="actor-scope-a",
            action="cancel",
            organization_id="org-a",
            history_scope="all-sites",
            run_ids=("run-a",),
        )

    now[0] += timedelta(minutes=10)
    with pytest.raises(PreviewError, match="preview_expired"):
        service.verify(
            preview.preview_token,
            actor_scope="actor-scope-a",
            action="cancel",
            organization_id="org-a",
            history_scope="all-sites",
            run_ids=("run-a",),
        )
