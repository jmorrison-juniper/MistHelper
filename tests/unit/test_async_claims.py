"""Unit tests for async-claim menu handlers (208-210).

Covers:
- list_org_async_claims safe export path
- create_org_async_claim confirmation gate and success path
- get_org_async_claim_status validation and success path
"""

import MistHelper


class _Response:
    """Small response stand-in with status_code/data fields."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code


def test_list_org_async_claims_exports_records(monkeypatch, tmp_path):
    """Menu 208 exports normalized async claim rows on API success."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(MistHelper, "org_id", "org-1")
    monkeypatch.setitem(MistHelper.list_org_async_claims.__globals__, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setitem(MistHelper.list_org_async_claims.__globals__, "safe_input", lambda *args, **kwargs: "n")
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.orgs.claims,
        "listOrgAsyncClaims",
        lambda *_args, **_kwargs: _Response(
            [
                {"id": "claim-1", "status": "pending"},
                {"claim_id": "claim-2", "status": "complete"},
            ]
        ),
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["data"] = data
        captured["filename"] = filename
        captured["api_function_name"] = api_function_name
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper.list_org_async_claims()

    assert captured["filename"] == "OrgAsyncClaims.csv"
    assert captured["api_function_name"] == "listOrgAsyncClaims"
    assert len(captured["data"]) == 2
    assert captured["data"][0]["claim_id"] == "claim-1"
    assert captured["data"][0]["org_id"] == "org-1"
    assert "timestamp" in captured["data"][0]


def test_list_org_async_claims_empty_is_success(monkeypatch, tmp_path, capsys):
    """Menu 208 treats empty list as a valid no-results outcome."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(MistHelper.list_org_async_claims.__globals__, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setitem(MistHelper.list_org_async_claims.__globals__, "safe_input", lambda *args, **kwargs: "n")
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.orgs.claims,
        "listOrgAsyncClaims",
        lambda *_args, **_kwargs: _Response([]),
    )
    called = {"save": False}

    def _save(*_args, **_kwargs):
        called["save"] = True
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper.list_org_async_claims()

    output = capsys.readouterr().out
    assert "No async claims found" in output
    assert called["save"] is False


def test_create_org_async_claim_confirmation_mismatch_skips_api(monkeypatch, tmp_path, capsys):
    """Menu 209 cancels without API call when confirmation is wrong."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper.create_org_async_claim.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    inputs = iter(['{"licenses": []}', "NOPE"])
    monkeypatch.setitem(
        MistHelper.create_org_async_claim.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(inputs),
    )
    called = {"api": False}

    def _api(*_args, **_kwargs):
        called["api"] = True
        return _Response({"id": "claim-1"})

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claims, "createOrgAsyncClaim", _api)

    MistHelper.create_org_async_claim()

    output = capsys.readouterr().out
    assert "Operation cancelled" in output
    assert called["api"] is False


def test_create_org_async_claim_success_exports_response(monkeypatch, tmp_path):
    """Menu 209 submits after exact CREATE confirmation and exports response."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper.create_org_async_claim.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    inputs = iter(['{"licenses": [{"sku": "ABC"}]}', "CREATE"])
    monkeypatch.setitem(
        MistHelper.create_org_async_claim.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(inputs),
    )

    captured = {"body": None, "export": None}

    def _api(_session, org_id, body):
        captured["body"] = (org_id, body)
        return _Response({"id": "claim-1", "status": "submitted"})

    def _save(data, filename, api_function_name=None):
        captured["export"] = (data, filename, api_function_name)
        return True

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claims, "createOrgAsyncClaim", _api)
    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper.create_org_async_claim()

    assert captured["body"][0] == "org-1"
    assert captured["body"][1] == {"licenses": [{"sku": "ABC"}]}
    export_data, export_filename, export_api_name = captured["export"]
    assert export_filename == "OrgAsyncClaimCreate.csv"
    assert export_api_name == "createOrgAsyncClaim"
    assert export_data[0]["claim_id"] == "claim-1"


def test_get_org_async_claim_status_blank_id_rejected(monkeypatch, tmp_path, capsys):
    """Menu 210 rejects empty claim IDs before any API call."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper.get_org_async_claim_status.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    monkeypatch.setitem(
        MistHelper.get_org_async_claim_status.__globals__,
        "safe_input",
        lambda *args, **kwargs: "   ",
    )
    called = {"api": False}

    def _api(*_args, **_kwargs):
        called["api"] = True
        return _Response({"claim_id": "claim-1"})

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claims, "getOrgAsyncClaimStatus", _api)

    MistHelper.get_org_async_claim_status()

    output = capsys.readouterr().out
    assert "Claim ID is required" in output
    assert called["api"] is False


def test_get_org_async_claim_status_success_exports(monkeypatch, tmp_path):
    """Menu 210 exports the requested claim status snapshot."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper.get_org_async_claim_status.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    inputs = iter(["claim-99", "y"])
    monkeypatch.setitem(
        MistHelper.get_org_async_claim_status.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(inputs),
    )

    captured = {"detail": None, "export": None}

    def _api(_session, org_id, claim_id, detail=None):
        captured["detail"] = (org_id, claim_id, detail)
        return _Response({"status": "complete", "items": [{"device_id": "dev-1"}]})

    def _save(data, filename, api_function_name=None):
        captured["export"] = (data, filename, api_function_name)
        return True

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.claims, "getOrgAsyncClaimStatus", _api)
    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper.get_org_async_claim_status()

    assert captured["detail"] == ("org-1", "claim-99", True)
    export_data, export_filename, export_api_name = captured["export"]
    assert export_filename == "OrgAsyncClaimStatus_claim-99.csv"
    assert export_api_name == "getOrgAsyncClaimStatus"
    assert export_data[0]["claim_id"] == "claim-99"
    assert export_data[0]["status"] == "complete"
