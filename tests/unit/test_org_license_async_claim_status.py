"""Unit tests for async org license-claim status export wiring and payload mapping."""  # Document unit-test scope for this feature file.

from types import SimpleNamespace  # Use SimpleNamespace to build lightweight fake API responses and call records.

import MistHelper  # Import production module so tests exercise real menu/export wiring.
import pytest  # Use pytest markers to skip when optional runtime deps are unavailable.

_HAS_REQUIRED_EXPORTER_SYMBOLS = all(  # Detect whether MistHelper imported far enough for this feature's symbols.
    hasattr(MistHelper, attr_name)  # Probe each required attribute on the partially loaded module.
    for attr_name in ("LicenseExportUtils", "DataExporter", "InputUtils", "mistapi")  # Require exporter + input + SDK symbols.
)
pytestmark = pytest.mark.skipif(  # Skip this module when optional dependencies prevented full MistHelper import.
    not _HAS_REQUIRED_EXPORTER_SYMBOLS,  # Trigger skip when required symbols were not loaded.
    reason="MistHelper optional dependencies unavailable; async-claim exporter symbols not loaded",  # Explain skip root cause.
)


def test_prompt_parsing_api_call_and_dual_export_writes(monkeypatch):  # Verify prompt flow, SDK call args, and summary/detail writes.
    prompts_seen: list[tuple[str, str, str]] = []  # Capture prompt text/context/default values for deterministic assertions.
    api_calls: list[dict] = []  # Capture SDK invocation kwargs so detail-flag mapping can be validated.
    writes: list[dict] = []  # Capture DataExporter writes to validate filename stems and api_function_name routing.

    def safe_input_stub(prompt, context=None, default=""):  # Stub safe_input so the test can drive interactive branches deterministically.
        prompts_seen.append((prompt, context, default))  # Record each prompt call for downstream assertions.
        if context == "org_license_claim_status:org_id":  # Return a valid org UUID when org prompt is requested.
            return "123e4567-e89b-12d3-a456-426614174000"  # Supply valid UUID to pass input validation guard.
        return "yes"  # Enable detail mode so both summary and detail writes are exercised.

    def api_stub(_session, org_id, detail=None):  # Stub SDK call so no real network calls are made during unit tests.
        api_calls.append({"org_id": org_id, "detail": detail})  # Record resolved org and detail flag for assertion.
        payload = {  # Provide realistic response payload used by flatten helpers.
            "status": "ongoing",  # Include status to test summary field mapping.
            "total": 3,  # Include total count for summary export.
            "processed": 2,  # Include processed count for summary export.
            "succeed": 2,  # Include succeed count for summary export.
            "failed": 0,  # Include failed count for summary export.
            "scheduled_at": 1719600000,  # Include stable job identifier for composite PK mapping.
            "timestamp": 1719603612.123,  # Include server timestamp for summary persistence.
            "completed": ["aabbccddeeff"],  # Include completed list so completed_count can be derived.
            "incompleted": ["112233445566"],  # Include incompleted list so incompleted_count can be derived.
            "details": [  # Include one detail item so detail export path is validated.
                {"mac": "aabbccddeeff", "status": "succeeded", "timestamp": 1719600100.0},
            ],
        }
        return SimpleNamespace(status_code=200, data=payload)  # Return APIResponse-like object with status/data attributes.

    def write_stub(data, filename, api_function_name=None):  # Stub DataExporter write to capture payload routing behavior.
        writes.append({"data": data, "filename": filename, "api_function_name": api_function_name})  # Record write call for assertions.
        return True  # Mimic successful backend write result.

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", safe_input_stub)  # Replace safe_input to avoid interactive blocking in test.
    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim.status, "getOrgLicenseAsyncClaimStatus", api_stub)  # Replace SDK method with deterministic stub.
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)  # Replace backend write with capture stub.

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status()  # Execute exporter through full prompt/api/write flow.

    assert prompts_seen[0][1] == "org_license_claim_status:org_id"  # Confirm first prompt collected org_id with expected context.
    assert prompts_seen[1][1] == "org_license_claim_status:detail"  # Confirm second prompt collected detail flag with expected context.
    assert api_calls == [{"org_id": "123e4567-e89b-12d3-a456-426614174000", "detail": True}]  # Confirm SDK call received parsed detail=True.
    assert writes[0]["api_function_name"] == "getOrgLicenseAsyncClaimStatus"  # Confirm summary write uses summary PK strategy key.
    assert writes[0]["filename"] == "org_123e4567_claim_status_summary"  # Confirm summary filename stem follows short-org convention.
    assert writes[1]["api_function_name"] == "getOrgLicenseAsyncClaimStatusDetails"  # Confirm detail write uses detail PK strategy key.
    assert writes[1]["filename"] == "org_123e4567_claim_status_details"  # Confirm detail filename stem follows short-org convention.
    assert writes[0]["data"][0]["completed_count"] == 1  # Confirm summary flatten derives completed_count from completed array.
    assert writes[1]["data"][0]["mac"] == "aabbccddeeff"  # Confirm detail flatten preserves device MAC from details payload.


def test_invalid_uuid_aborts_before_api_call(monkeypatch):  # Verify invalid org_id returns early before network or write activity.
    sdk_called = {"value": False}  # Track whether SDK function was invoked so early-return behavior can be asserted.
    write_called = {"value": False}  # Track whether DataExporter write was invoked on invalid input.

    def safe_input_stub(_prompt, context=None, default=""):  # Stub prompt answers so exporter receives invalid org identifier.
        if context == "org_license_claim_status:org_id":  # Route org prompt to invalid value branch.
            return "not-a-uuid"  # Return invalid UUID to trigger validation failure path.
        return default  # Return defaults for any other prompt branch.

    def api_stub(*_args, **_kwargs):  # Stub SDK call to detect accidental invocation when validation should block it.
        sdk_called["value"] = True  # Mark SDK as called so assertion can detect contract regression.
        return SimpleNamespace(status_code=200, data={})  # Provide fallback response shape if accidentally called.

    def write_stub(*_args, **_kwargs):  # Stub DataExporter write to detect accidental persistence on invalid input.
        write_called["value"] = True  # Mark write as called for regression detection.
        return True  # Mimic write success if accidentally reached.

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", safe_input_stub)  # Replace safe_input for deterministic invalid input path.
    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim.status, "getOrgLicenseAsyncClaimStatus", api_stub)  # Replace SDK method to detect improper invocation.
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)  # Replace write method to detect improper invocation.

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status()  # Execute exporter with invalid org_id path.

    assert sdk_called["value"] is False  # Confirm exporter did not call SDK when UUID validation failed.
    assert write_called["value"] is False  # Confirm exporter did not write output for invalid input.


def test_404_writes_empty_summary_and_optional_empty_details(monkeypatch):  # Verify 404/no-job path still emits deterministic empty exports.
    writes: list[dict] = []  # Capture write calls to verify summary/detail empty-list behavior.

    def api_stub(_session, org_id, detail=None):  # Stub SDK to emulate 404 no-active-claim-job response.
        return SimpleNamespace(status_code=404, data=None, org_id=org_id, detail=detail)  # Provide APIResponse-like no-body object.

    def write_stub(data, filename, api_function_name=None):  # Capture DataExporter writes so empty payload handling can be asserted.
        writes.append({"data": data, "filename": filename, "api_function_name": api_function_name})  # Persist write arguments for assertions.
        return True  # Mimic successful backend write.

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claim.status, "getOrgLicenseAsyncClaimStatus", api_stub)  # Replace SDK endpoint with 404 stub.
    monkeypatch.setattr(MistHelper.DataExporter, "write_with_format_selection", write_stub)  # Replace exporter writes with capture stub.

    MistHelper.LicenseExportUtils.export_org_license_async_claim_status(  # Run exporter with explicit args to bypass prompts in this test.
        org_id="123e4567-e89b-12d3-a456-426614174000",  # Provide valid UUID so execution reaches API branch.
        include_detail=True,  # Enable detail mode so both summary and detail writes are exercised.
    )

    assert writes[0]["api_function_name"] == "getOrgLicenseAsyncClaimStatus"  # Confirm first write is summary export routing key.
    assert writes[0]["data"] == []  # Confirm 404 path writes empty summary row list.
    assert writes[1]["api_function_name"] == "getOrgLicenseAsyncClaimStatusDetails"  # Confirm second write is detail export routing key.
    assert writes[1]["data"] == []  # Confirm 404 path writes empty detail row list when detail mode is enabled.


def test_flatten_helpers_map_summary_and_detail_fields():  # Verify helper flatten logic maps payload fields to expected output schema.
    payload = {  # Build representative payload with summary and detail fields present.
        "status": "done",  # Include terminal status value for summary mapping assertion.
        "total": 2,  # Include total count used in summary row.
        "processed": 2,  # Include processed count used in summary row.
        "succeed": 1,  # Include succeed count used in summary row.
        "failed": 1,  # Include failed count used in summary row.
        "scheduled_at": 1719600000,  # Include scheduled_at used in composite key mapping.
        "timestamp": 1719603612.123,  # Include server timestamp used in summary persistence.
        "completed": ["aabbccddeeff"],  # Include completed list to validate completed_count derivation.
        "incompleted": ["112233445566"],  # Include incompleted list to validate incompleted_count derivation.
        "details": [  # Include one detail row to validate detail field mapping.
            {"mac": "aabbccddeeff", "status": "succeeded", "timestamp": 1719600100.0},
        ],
    }

    summary_row = MistHelper.LicenseExportUtils._flatten_org_license_async_claim_status_summary(  # Flatten summary row via helper under test.
        "123e4567-e89b-12d3-a456-426614174000",  # Provide org_id so helper can inject missing org context.
        payload,  # Provide payload containing expected summary fields.
    )
    detail_rows = MistHelper.LicenseExportUtils._flatten_org_license_async_claim_status_details(  # Flatten detail rows via helper under test.
        "123e4567-e89b-12d3-a456-426614174000",  # Provide org_id so helper can build composite-key fields.
        payload,  # Provide payload containing details array for flattening.
    )

    assert summary_row["org_id"] == "123e4567-e89b-12d3-a456-426614174000"  # Confirm helper injects org_id into summary row.
    assert summary_row["completed_count"] == 1  # Confirm helper derives completed_count from completed array length.
    assert summary_row["incompleted_count"] == 1  # Confirm helper derives incompleted_count from incompleted array length.
    assert summary_row["scheduled_at"] == 1719600000  # Confirm helper preserves scheduled_at stable key value.
    assert detail_rows[0]["mac"] == "aabbccddeeff"  # Confirm detail helper preserves device MAC field.
    assert detail_rows[0]["device_status"] == "succeeded"  # Confirm detail helper maps status to device_status output field.
    assert detail_rows[0]["scheduled_at"] == 1719600000  # Confirm detail helper carries scheduled_at for summary/detail joinability.
