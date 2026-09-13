"""Unit tests for LicenseExportUtils (issue #878 tranche 1 -- un-omit).

Focuses on the previously-uncovered HTTP error-status paths in
``_handle_async_claim_status`` (401, 403, 400) and the early bail-out
branch in ``export_org_license_async_claim_status`` when the status
handler returns None.
"""

from __future__ import annotations

from unittest.mock import patch

from src.export.license_export_utils import LicenseExportUtils

# ---------- _handle_async_claim_status status-code routing ----------


def test_handle_async_claim_status_401_returns_none() -> None:
    """A 401 auth failure must bail out with None."""
    assert LicenseExportUtils._handle_async_claim_status(401, "org-1", {"any": "payload"}) is None


def test_handle_async_claim_status_403_returns_none() -> None:
    """A 403 permission failure must bail out with None."""
    assert LicenseExportUtils._handle_async_claim_status(403, "org-1", {"any": "payload"}) is None


def test_handle_async_claim_status_400_returns_none() -> None:
    """A 400 invalid-input response must bail out with None."""
    assert LicenseExportUtils._handle_async_claim_status(400, "org-1", {"any": "payload"}) is None


def test_handle_async_claim_status_404_returns_empty_dict() -> None:
    """A 404 no-active-job response normalises to an empty dict."""
    assert LicenseExportUtils._handle_async_claim_status(404, "org-1", {"stale": True}) == {}


def test_handle_async_claim_status_200_passthrough_payload() -> None:
    """A 200 success passes the raw payload through unchanged."""
    payload = {"status": "in_progress", "total": 3}
    assert LicenseExportUtils._handle_async_claim_status(200, "org-1", payload) is payload


# ---------- export_org_license_async_claim_status bail-out branch ----------


def test_export_bails_out_when_status_handler_returns_none() -> None:
    """When _handle_async_claim_status yields None the export writes nothing."""
    with (
        patch.object(LicenseExportUtils, "_is_valid_uuid", return_value=True),
        patch.object(LicenseExportUtils, "_resolve_async_claim_include_detail", return_value=False),
        patch.object(LicenseExportUtils, "_call_async_claim_api", return_value=(401, {})),
        patch.object(LicenseExportUtils, "_handle_async_claim_status", return_value=None),
        patch.object(LicenseExportUtils, "_write_async_claim_summary") as write_summary,
        patch.object(LicenseExportUtils, "_write_async_claim_details") as write_details,
    ):
        LicenseExportUtils.export_org_license_async_claim_status(
            org_id="00000000-0000-0000-0000-000000000001",
        )
    write_summary.assert_not_called()
    write_details.assert_not_called()


def test_export_writes_summary_only_when_detail_false() -> None:
    """A successful summary-only path writes summary, never details."""
    with (
        patch.object(LicenseExportUtils, "_is_valid_uuid", return_value=True),
        patch.object(LicenseExportUtils, "_resolve_async_claim_include_detail", return_value=False),
        patch.object(LicenseExportUtils, "_call_async_claim_api", return_value=(200, {"ok": True})),
        patch.object(
            LicenseExportUtils,
            "_handle_async_claim_status",
            return_value={"ok": True},
        ),
        patch.object(LicenseExportUtils, "_write_async_claim_summary") as write_summary,
        patch.object(LicenseExportUtils, "_write_async_claim_details") as write_details,
    ):
        LicenseExportUtils.export_org_license_async_claim_status(
            org_id="00000000-0000-0000-0000-000000000002",
        )
    write_summary.assert_called_once()
    write_details.assert_not_called()


def test_export_writes_summary_and_details_when_detail_true() -> None:
    """When the detail flag is true the export must fire both writers."""
    with (
        patch.object(LicenseExportUtils, "_is_valid_uuid", return_value=True),
        patch.object(LicenseExportUtils, "_resolve_async_claim_include_detail", return_value=True),
        patch.object(LicenseExportUtils, "_call_async_claim_api", return_value=(200, {"ok": True})),
        patch.object(
            LicenseExportUtils,
            "_handle_async_claim_status",
            return_value={"ok": True},
        ),
        patch.object(LicenseExportUtils, "_write_async_claim_summary") as write_summary,
        patch.object(LicenseExportUtils, "_write_async_claim_details") as write_details,
    ):
        LicenseExportUtils.export_org_license_async_claim_status(
            org_id="00000000-0000-0000-0000-000000000003",
        )
    write_summary.assert_called_once()
    write_details.assert_called_once()


def test_export_bails_out_when_org_id_is_invalid() -> None:
    """An invalid org_id must short-circuit before any API call."""
    with (
        patch.object(LicenseExportUtils, "_call_async_claim_api") as call_api,
        patch.object(LicenseExportUtils, "_write_async_claim_summary") as write_summary,
    ):
        LicenseExportUtils.export_org_license_async_claim_status(org_id="not-a-uuid")
    call_api.assert_not_called()
    write_summary.assert_not_called()


# ---------- _resolve_async_claim_include_detail ----------


def test_resolve_include_detail_returns_true_when_caller_true() -> None:
    """Explicit True flag bypasses the interactive prompt."""
    assert LicenseExportUtils._resolve_async_claim_include_detail(True) is True


def test_resolve_include_detail_returns_false_when_caller_false() -> None:
    """Explicit False flag bypasses the interactive prompt."""
    assert LicenseExportUtils._resolve_async_claim_include_detail(False) is False


def test_resolve_include_detail_prompts_when_caller_none() -> None:
    """A None flag must delegate to the interactive prompt helper."""
    with patch.object(LicenseExportUtils, "_prompt_async_claim_include_detail", return_value=True) as prompter:
        result = LicenseExportUtils._resolve_async_claim_include_detail(None)
    prompter.assert_called_once()
    assert result is True


# ---------- _is_valid_uuid ----------


def test_is_valid_uuid_accepts_canonical_form() -> None:
    """A canonical UUID string is accepted."""
    assert LicenseExportUtils._is_valid_uuid("12345678-1234-1234-1234-123456789012") is True


def test_is_valid_uuid_rejects_malformed_string() -> None:
    """A malformed candidate is rejected without raising."""
    assert LicenseExportUtils._is_valid_uuid("not-a-uuid") is False


def test_is_valid_uuid_rejects_none() -> None:
    """A None candidate is rejected without raising."""
    assert LicenseExportUtils._is_valid_uuid(None) is False  # type: ignore[arg-type]
