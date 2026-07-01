"""Unit tests for async org license-claim status exporter."""

from types import SimpleNamespace

import pytest

import MistHelper

_HAS_REQUIRED_EXPORTER_SYMBOLS = all(
    hasattr(MistHelper, attr_name) for attr_name in ("LicenseExportUtils", "DataExporter", "InputUtils", "mistapi")
)
pytestmark = pytest.mark.skipif(
    not _HAS_REQUIRED_EXPORTER_SYMBOLS,
    reason="MistHelper optional dependencies unavailable; async-claim exporter symbols not loaded",
)


def test_prompt_parsing_api_call_and_dual_export_writes(monkeypatch):
    prompts_seen: list[tuple[str, str, str]] = []
    api_calls: list[dict] = []
    writes: list[dict] = []

    def safe_input_stub(prompt, context=None, default="", default_value=""):
        prompts_seen.append((prompt, context, default_value or default))
        if context == "org_license_claim_status:org_id":
            return "123e4567-e89b-12d3-a456-426614174000"
        return "yes"

    def api_stub(_session, org_id, detail=None):
        api_calls.append({"org_id": org_id, "detail": detail})
        payload = {
            "status": "ongoing",
            "total": 3,
            "processed": 2,
            "succeed": 2,
            "failed": 0,
            "scheduled_at": 1719600000,
            "timestamp": 1719603612.123,
            "completed": ["aabbccddeeff"],
            "incompleted": ["112233445566"],
            "details": [
                {"mac": "aabbccddeeff", "status": "succeeded", "timestamp": 1719600100.0},
            ],
        }
        return SimpleNamespace(status_code=200, data=payload)

    def write_stub(data, filename, api_function_name=None):
        writes.append({"data": data, "filename": filename, "api_function_name": api_function_name})
        return True

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", safe_input_stub)
    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim, "GetOrgLicenseAsyncClaimStatus", api_stub)
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status()

    assert prompts_seen[0][1] == "org_license_claim_status:org_id"
    assert prompts_seen[1][1] == "org_license_claim_status:detail"
    assert api_calls == [{"org_id": "123e4567-e89b-12d3-a456-426614174000", "detail": True}]
    assert writes[0]["api_function_name"] == "getOrgLicenseAsyncClaimStatus"
    assert writes[0]["filename"] == "org_123e4567_claim_status_summary"
    assert writes[1]["api_function_name"] == "getOrgLicenseAsyncClaimStatusDetails"
    assert writes[1]["filename"] == "org_123e4567_claim_status_details"
    assert writes[0]["data"][0]["completed_count"] == 1
    assert writes[1]["data"][0]["mac"] == "aabbccddeeff"


def test_invalid_uuid_aborts_before_api_call(monkeypatch):
    sdk_called = {"value": False}
    write_called = {"value": False}

    def safe_input_stub(_prompt, context=None, default="", default_value=""):
        if context == "org_license_claim_status:org_id":
            return "not-a-uuid"
        return default_value or default

    def api_stub(*_args, **_kwargs):
        sdk_called["value"] = True
        return SimpleNamespace(status_code=200, data={})

    def write_stub(*_args, **_kwargs):
        write_called["value"] = True
        return True

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", safe_input_stub)
    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim, "GetOrgLicenseAsyncClaimStatus", api_stub)
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status()

    assert sdk_called["value"] is False
    assert write_called["value"] is False


def test_404_writes_empty_summary_and_optional_empty_details(monkeypatch):
    writes: list[dict] = []

    def api_stub(_session, org_id, detail=None):
        return SimpleNamespace(status_code=404, data=None, org_id=org_id, detail=detail)

    def write_stub(data, filename, api_function_name=None):
        writes.append({"data": data, "filename": filename, "api_function_name": api_function_name})
        return True

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim, "GetOrgLicenseAsyncClaimStatus", api_stub)
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status(
        org_id="123e4567-e89b-12d3-a456-426614174000",
        include_detail=True,
    )

    assert writes[0]["api_function_name"] == "getOrgLicenseAsyncClaimStatus"
    assert writes[0]["data"] == []
    assert writes[1]["api_function_name"] == "getOrgLicenseAsyncClaimStatusDetails"
    assert writes[1]["data"] == []


def test_flatten_helpers_map_summary_and_detail_fields():
    payload = {
        "status": "done",
        "total": 2,
        "processed": 2,
        "succeed": 1,
        "failed": 1,
        "scheduled_at": 1719600000,
        "timestamp": 1719603612.123,
        "completed": ["aabbccddeeff"],
        "incompleted": ["112233445566"],
        "details": [
            {"mac": "aabbccddeeff", "status": "succeeded", "timestamp": 1719600100.0},
        ],
    }

    summary_row = MistHelper.LicenseExportUtils._flatten_org_license_async_claim_status_summary(
        "123e4567-e89b-12d3-a456-426614174000",
        payload,
    )
    detail_rows = MistHelper.LicenseExportUtils._flatten_org_license_async_claim_status_details(
        "123e4567-e89b-12d3-a456-426614174000",
        payload,
    )

    assert summary_row["org_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert summary_row["completed_count"] == 1
    assert summary_row["incompleted_count"] == 1
    assert summary_row["scheduled_at"] == 1719600000
    assert detail_rows[0]["mac"] == "aabbccddeeff"
    assert detail_rows[0]["device_status"] == "succeeded"
    assert detail_rows[0]["scheduled_at"] == 1719600000
