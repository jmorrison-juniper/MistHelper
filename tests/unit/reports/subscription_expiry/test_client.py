"""Tests for the subscription expiry client seam."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from types import SimpleNamespace  # Build small SDK response doubles.

import pytest  # Assert exceptions and test outcomes.

from src.reports.subscription_expiry import client as client_module  # Patch the module SDK seams.
from src.reports.subscription_expiry.client import (
    JsiAccountNotLinkedError,
    SubscriptionExpiryClient,
    SubscriptionExpiryClientError,
)


class FakeLicensesApi:
    """Fake Mist licenses API used without network calls."""

    def getOrgLicensesSummary(self, apisession: object, org_id: str) -> SimpleNamespace:
        """Return a wrapped license summary payload."""
        return SimpleNamespace(data={"entitled": {"SUB": 5}, "licenses": [{"type": "SUB"}], "summary": {}})  # Fake.

    def getOrgLicensesBySite(self, apisession: object, org_id: str) -> list[dict[str, object]]:
        """Return a plain license usage payload."""
        return [{"site_id": "site-1", "num_devices": 2, "usages": {"SUB": 2}, "fully_loaded": {"SUB": True}}]  # Fake.


class FakeJsiApi:
    """Fake Mist JSI API used without network calls."""

    def searchOrgJsiAssetsAndContracts(self, apisession: object, org_id: str, limit: int) -> SimpleNamespace:
        """Return a wrapped search payload that the fake paginator consumes."""
        return SimpleNamespace(
            data={"results": [{"serial": "ABC", "model": "AP", "status": "Active", "end_date": "2027-01-01"}]}
        )  # Fake contract fields.


class FakeMistApi:
    """Fake Mist SDK tree with only the report endpoints."""

    def __init__(self) -> None:
        """Create the nested SDK path used by the report client."""
        self.api = SimpleNamespace(
            v1=SimpleNamespace(orgs=SimpleNamespace(licenses=FakeLicensesApi(), jsi=FakeJsiApi()))
        )  # Provide the dotted SDK path.

    @staticmethod
    def get_all(response: SimpleNamespace, mist_session: object) -> list[dict[str, object]]:
        """Return paginated rows from the wrapped response."""
        return list(response.data["results"])  # Simulate mistapi pagination output.


def test_client_converts_plain_and_wrapped_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client converts SDK wrappers and plain containers to dataclasses."""
    monkeypatch.setattr(client_module, "mistapi", FakeMistApi())  # Replace the SDK so no network call can occur.
    client = SubscriptionExpiryClient(object())  # Build the client with a fake session.
    summary = client.fetch_license_summary("org-1")  # Fetch the fake license summary.
    usages = client.fetch_license_usage_by_site("org-1")  # Fetch the fake usage rows.
    assert summary.entitled == {"SUB": 5}  # Entitlement map must survive conversion.
    assert summary.licenses == [{"type": "SUB"}]  # License rows must survive conversion.
    assert usages[0].site_id == "site-1"  # Site ID must survive conversion.
    assert usages[0].usages == {"SUB": 2}  # Usage map must survive conversion.


def test_client_uses_mistapi_pagination_for_jsi(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client uses mistapi.get_all for the JSI search endpoint."""
    fake_sdk = FakeMistApi()  # Build a fake SDK with a paginator.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call can occur.
    client = SubscriptionExpiryClient(object())  # Build the client with a fake session.
    contracts = client.search_jsi_assets_and_contracts("org-1")  # Fetch fake JSI rows.
    assert len(contracts) == 1  # The paginated row must become one contract source.
    assert contracts[0].serial == "ABC"  # The device serial must survive conversion.
    assert contracts[0].status == "Active"  # The contract status must survive conversion.
    assert contracts[0].end_date == "2027-01-01"  # The contract end date must survive conversion.


def test_client_raises_clear_error_for_jsi_400(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client signals the no-linked-account JSI response without network calls."""
    fake_sdk = FakeMistApi()  # Build a fake SDK tree.
    fake_sdk.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts = lambda apisession, org_id, limit: SimpleNamespace(
        status_code=400,
        data={"detail": "no account"},
    )  # Return the expected 400 response.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call can occur.
    client = SubscriptionExpiryClient(object())  # Build the client with a fake session.
    with pytest.raises(JsiAccountNotLinkedError):  # The operation layer handles this one expected case.
        client.search_jsi_assets_and_contracts("org-1")  # Trigger the fake 400 path.


def test_client_raises_clear_error_for_jsi_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client stops pagination when the JSI endpoint returns HTTP 500."""
    fake_sdk = FakeMistApi()  # Build a fake SDK tree.
    fake_sdk.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts = lambda apisession, org_id, limit: SimpleNamespace(
        status_code=500,
        data={"detail": "server error"},
    )  # Return the expected 500 response.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call can occur.
    client = SubscriptionExpiryClient(object())  # Build the client with a fake session.
    with pytest.raises(SubscriptionExpiryClientError, match="HTTP 500"):  # The caller receives the HTTP failure.
        client.search_jsi_assets_and_contracts("org-1")  # Trigger the fake 500 path.
