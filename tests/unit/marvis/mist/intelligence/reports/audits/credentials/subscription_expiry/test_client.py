"""Tests for the subscription expiry client seam."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from types import SimpleNamespace  # Build small SDK response doubles.

import pytest  # Assert exceptions and test outcomes.

from src.mist.intelligence.reports.subscription_expiry import client as client_module  # Patch the module SDK seams.
from src.mist.intelligence.reports.subscription_expiry.client import (
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


def test_client_discovers_direct_and_msp_organizations(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client discovers only profile-granted direct and MSP organizations."""
    monkeypatch.setattr(
        client_module.mistapi.api.v1.self.self,
        "getSelf",
        lambda _session: SimpleNamespace(
            status_code=200,
            data={
                "privileges": [
                    {"org_id": "org-1", "org_name": "Primary", "scope": "org", "role": "read"},
                    {"msp_id": "msp-1", "scope": "msp", "role": "read"},
                ]
            },
        ),
    )  # Return one direct grant and one MSP grant.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.msps.orgs,
        "listMspOrgs",
        lambda _session, _msp_id: SimpleNamespace(
            status_code=200,
            data=[
                {"id": "org-2", "name": "Branch"},
                {"id": "org-1", "name": "Duplicate Name"},
            ],
        ),
    )  # Return one branch org and one duplicate direct org.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client session.
    organizations, failures = client.discover_organizations("org-1", "Primary")  # Discover authorized scopes.
    assert [organization.org_id for organization in organizations] == ["org-1", "org-2"]  # Deduplicate by org ID.
    assert organizations[1].source == "msp"  # The branch org comes from the MSP grant.
    assert failures == []  # Both discovery calls succeed.


def test_client_discovers_msp_organizations_across_continuation_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    """MSP organization discovery follows every SDK continuation page."""
    first_response = SimpleNamespace(
        status_code=200,
        data=[{"id": "org-2", "name": "Branch"}],
        next="/msp-org-page-2",
    )  # Supply the first MSP organization page.
    final_response = SimpleNamespace(
        status_code=200,
        data=[{"id": "org-3", "name": "Retail Partner"}],
        next=None,
    )  # Supply the final MSP organization page.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.self.self,
        "getSelf",
        lambda _session: SimpleNamespace(
            status_code=200,
            data={"privileges": [{"msp_id": "msp-1", "scope": "msp", "role": "read"}]},
        ),
    )  # Grant one MSP scope.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.msps.orgs,
        "listMspOrgs",
        lambda _session, _msp_id: first_response,
    )  # Return the first organization page.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_next",
        lambda mist_session, response: final_response,
    )  # Return the final organization page.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    organizations, failures = client.discover_organizations("org-1", "Primary")  # Discover all MSP pages.
    assert [organization.org_id for organization in organizations] == ["org-1", "org-2", "org-3"]
    assert failures == []  # Both organization pages complete successfully.


def test_client_inventory_expands_logical_vc_into_physical_members(monkeypatch: pytest.MonkeyPatch) -> None:
    """A logical VC inventory row expands to the physical member serials."""
    vc_calls: list[tuple[str, str, str]] = []  # Record VC status API context.

    class FakeInventoryApi:
        """Fake inventory endpoint for one logical VC row."""

        @staticmethod
        def getOrgInventory(
            _session: object,
            _org_id: str,
            limit: int,
            page: int,
            vc: bool,
        ) -> SimpleNamespace:
            return SimpleNamespace(
                status_code=200,
                data=[
                    {
                        "id": "device-1",
                        "serial": "020003135CBF",
                        "mac": "020003135cbf",
                        "vc_mac": "020003135cbf",
                        "model": "EX4100-48MP",
                        "type": "switch",
                        "site_id": "site-1",
                        "name": "VC Stack",
                    }
                ],
                next=None,
            )  # Supply one synthetic logical VC row.

    class FakeSiteDevicesApi:
        """Fake site devices API for one VC status call."""

        @staticmethod
        def getSiteDeviceVirtualChassis(
            _session: object,
            site_id: str,
            device_id: str,
        ) -> SimpleNamespace:
            vc_calls.append(("getSiteDeviceVirtualChassis", site_id, device_id))  # Capture VC context.
            return SimpleNamespace(
                status_code=200,
                data={
                    "mac": "020003135cbf",
                    "members": [
                        {"serial": "MEMBER1", "mac": "member-mac-1", "model": "EX4100-48MP"},
                        {"serial": "MEMBER2", "mac": "member-mac-2", "model": "EX4100-48MP"},
                    ],
                },
            )  # Supply two physical member identities.

    fake_sdk = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=FakeInventoryApi()),
                sites=SimpleNamespace(devices=FakeSiteDevicesApi()),
            )
        ),
        get_next=lambda mist_session, response: None,
    )  # Build a synthetic SDK tree.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call occurs.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    inventory = client.fetch_inventory("org-1")  # Read and expand the logical VC.
    assert [row["serial"] for row in inventory] == ["MEMBER1", "MEMBER2"]  # Preserve both physical serials.
    assert all(row["vc_mac"] == "020003135cbf" for row in inventory)  # Preserve the VC parent MAC.
    assert vc_calls == [("getSiteDeviceVirtualChassis", "site-1", "device-1")]  # Use the site and device IDs.


def test_client_inventory_keeps_logical_vc_when_member_status_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed VC status call leaves no unverified physical count."""

    class FakeInventoryApi:
        """Fake inventory endpoint for one logical VC row."""

        @staticmethod
        def getOrgInventory(
            _session: object,
            _org_id: str,
            limit: int,
            page: int,
            vc: bool,
        ) -> SimpleNamespace:
            return SimpleNamespace(
                status_code=200,
                data=[
                    {
                        "id": "device-1",
                        "serial": "020003135CBF",
                        "mac": "020003135cbf",
                        "vc_mac": "020003135cbf",
                        "model": "EX4100-48MP",
                        "type": "switch",
                        "site_id": "site-1",
                    }
                ],
                next=None,
            )  # Supply one synthetic logical VC row.

    class FakeSiteDevicesApi:
        """Fake site devices API for one VC status failure."""

        @staticmethod
        def getSiteDeviceVirtualChassis(
            _session: object,
            site_id: str,
            device_id: str,
        ) -> SimpleNamespace:
            return SimpleNamespace(status_code=500, data={"error": "failure"})  # Simulate VC status failure.

    fake_sdk = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=FakeInventoryApi()),
                sites=SimpleNamespace(devices=FakeSiteDevicesApi()),
            )
        ),
        get_next=lambda mist_session, response: None,
    )  # Build a synthetic SDK tree.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call occurs.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    inventory = client.fetch_inventory("org-1")  # Read the logical VC with a failed status call.
    assert inventory == [
        {
            "id": "device-1",
            "serial": "020003135CBF",
            "mac": "020003135cbf",
            "vc_mac": "020003135cbf",
            "model": "EX4100-48MP",
            "type": "switch",
            "site_id": "site-1",
        }
    ]  # The synthetic row remains as evidence, but later model logic excludes it.


def test_client_inventory_pagination_uses_sdk_continuation(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client reads every inventory page with SDK continuation and Virtual Chassis."""
    calls: list[tuple[int, bool, int]] = []  # Record inventory limit, VC, and page arguments.

    class FakeInventoryApi:
        """Fake inventory endpoint for two-page pagination."""

        @staticmethod
        def getOrgInventory(
            _session: object,
            _org_id: str,
            limit: int,
            page: int,
            vc: bool,
        ) -> SimpleNamespace:
            calls.append((limit, vc, page))  # Capture pagination and Virtual Chassis arguments.
            return SimpleNamespace(status_code=200, data=[{"serial": "one"}], next="/page-2")

    next_calls: list[object] = []  # Record continuation requests.
    second_response = SimpleNamespace(
        status_code=200,
        data=[{"serial": "two", "site_id": "site-2", "vc_mac": "vc-1"}],
        next=None,
    )  # Supply the final inventory page.

    def get_next(mist_session: object, response: object) -> SimpleNamespace:
        next_calls.append((mist_session, response))  # Capture the SDK continuation call.
        return second_response  # Return the final page once.

    fake_sdk = SimpleNamespace(
        api=SimpleNamespace(v1=SimpleNamespace(orgs=SimpleNamespace(inventory=FakeInventoryApi()))),
        get_next=get_next,
    )  # Build a synthetic SDK tree with SDK continuation.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace SDK access for this test.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    inventory = client.fetch_inventory("org-1")  # Read both pages.
    assert [row["serial"] for row in inventory] == ["one", "two"]  # Preserve continuation order.
    assert calls == [(1000, True, 1)]  # Use the shared page size and VC expansion.
    assert len(next_calls) == 1  # Follow exactly one later page.


def test_client_inventory_later_page_http_failure_remains_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """A denied later inventory page rejects a partial count."""
    calls: list[tuple[int, bool, int]] = []  # Record the first inventory page.

    class FakeInventoryApi:
        """Fake inventory endpoint for a first page with a continuation."""

        @staticmethod
        def getOrgInventory(
            _session: object,
            _org_id: str,
            limit: int,
            page: int,
            vc: bool,
        ) -> SimpleNamespace:
            calls.append((limit, vc, page))  # Capture the first page call.
            return SimpleNamespace(status_code=200, data=[{"serial": "one"}], next="/page-2")  # Return a continuation.

    def get_next(mist_session: object, response: object) -> SimpleNamespace:
        return SimpleNamespace(status_code=500, data={"error": "failure"}, next=None)  # Deny the later page.

    fake_sdk = SimpleNamespace(
        api=SimpleNamespace(v1=SimpleNamespace(orgs=SimpleNamespace(inventory=FakeInventoryApi()))),
        get_next=get_next,
    )  # Build a synthetic SDK tree with a denied continuation.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace the SDK so no network call occurs.
    client = SubscriptionExpiryClient(object())  # Build the synthetic client.
    with pytest.raises(SubscriptionExpiryClientError, match="HTTP 500"):  # Require the later denial.
        client.fetch_inventory("org-1")  # Trigger the inventory continuation failure.


def test_client_transport_failure_sentinel_remains_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A transport status sentinel must not pass as an HTTP 200 response."""
    fake_sdk = FakeMistApi()  # Build a fake SDK tree.
    fake_sdk.api.v1.orgs.licenses.getOrgLicensesSummary = lambda _session, _org_id: SimpleNamespace(
        status_code=0,
        data=None,
    )  # Model a bounded transport failure.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace SDK access for this test.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    with pytest.raises(SubscriptionExpiryClientError, match="HTTP 0"):  # Require visible transport failure.
        client.fetch_license_summary("org-1")  # Trigger the sentinel status.


def test_client_inventory_http_failure_remains_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """An inventory HTTP failure becomes a typed client error."""

    class FakeInventoryApi:
        """Fake inventory endpoint for one HTTP failure."""

        @staticmethod
        def getOrgInventory(
            _session: object,
            _org_id: str,
            limit: int,
            page: int,
            vc: bool,
        ) -> SimpleNamespace:
            return SimpleNamespace(status_code=500, data={"error": "failure"})

    fake_sdk = SimpleNamespace(
        api=SimpleNamespace(v1=SimpleNamespace(orgs=SimpleNamespace(inventory=FakeInventoryApi())))
    )  # Build a synthetic SDK tree.
    monkeypatch.setattr(client_module, "mistapi", fake_sdk)  # Replace SDK access for this test.
    client = SubscriptionExpiryClient(object())  # Build a synthetic client.
    with pytest.raises(SubscriptionExpiryClientError, match="HTTP 500"):  # Require visible HTTP failure.
        client.fetch_inventory("org-1")  # Trigger the inventory failure.
