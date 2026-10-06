"""Contract tests for the issue 3210 organization inventory read.

Why:
    The multi-site GET and POST must read organization inventory once. These
    tests drive the real handlers with memory-only seams and no firmware call.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.interfaces.portals.upgrade_portal.app.routes import org_upgrade, select
from src.interfaces.portals.upgrade_portal.runtime import identity
from src.interfaces.portals.upgrade_portal.runtime.cloud_cache import CloudReadCache
from src.interfaces.portals.upgrade_portal.upgrade import options as options_module
from tests.contract.upgrade_portal.test_org_upgrade_routes import (
    AggregateBoundaryStandIn,
    AggregateStoreStandIn,
    VersionReaderStandIn,
)
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

ORG_ID = "00000000-0000-0000-0000-000000003210"
CLOUD_ACCOUNT = "issue-3210-cloud@juniper.net"
OPERATOR_EMAIL = "issue-3210-operator@juniper.net"
OPTIONS_PAGE = "/upgrade/org/options"
OPTIONS_API = "/api/org-upgrades/options"
TARGET_VERSION = "0.15.1"


@dataclass
class Clock:
    """Hold the monotonic time that the inventory cache reads."""

    now: float = 0.0

    def __call__(self) -> float:
        """Return the controlled cache time."""
        return self.now


class InventoryResponse:
    """Answer one complete or partial inventory page without a network call."""

    def __init__(self, rows: list[dict[str, Any]], total: int | None = None) -> None:
        """Store the response payload and its reported total."""
        reported = len(rows) if total is None else total  # A larger total marks a short read.
        self.data = {"results": [dict(row) for row in rows], "total": reported}  # Detach the answer rows.
        self.status_code = 200  # The partial guard compares the body count after a successful first page.
        self.next = None  # One response is enough for these handler contracts.


class InventoryStandIn:
    """Record organization inventory calls and return controlled rows."""

    def __init__(self) -> None:
        """Start with no call and no row."""
        self.calls: list[dict[str, Any]] = []  # Each entry records the endpoint keyword arguments.
        self.rows: list[dict[str, Any]] = []  # The current organization inventory.
        self.total: int | None = None  # A larger value marks a partial read.

    def read(self, session: Any, org_id: str, **kwargs: Any) -> InventoryResponse:
        """Record one organization read and return the current rows."""
        del session  # The stand-in opens no cloud connection.
        self.calls.append({"org_id": org_id, **kwargs})  # Record no credential or device content.
        return InventoryResponse(self.rows, self.total)  # Return a detached memory-only response.


@pytest.fixture
def inventory_clock() -> Clock:
    """Return the controlled cache clock."""
    return Clock()


@pytest.fixture
def inventory() -> InventoryStandIn:
    """Return the organization inventory stand-in."""
    return InventoryStandIn()


@pytest.fixture
def t005_client(
    portal_app: Flask,
    fake_mist_api: Any,
    inventory: InventoryStandIn,
    inventory_clock: Clock,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[FlaskClient]:
    """Return a signed client whose routes use only memory stand-ins."""
    portal_app.config["WTF_CSRF_ENABLED"] = False  # The contract checks inventory behavior, not CSRF.
    portal_app.config["MIST_READER"] = fake_mist_api.read  # The selected-site ownership read stays offline.
    portal_app.config["SITE_LOCK_READER"] = lambda org_id, site_ids: {site_id: None for site_id in site_ids}
    portal_app.config[select.LOCK_CLIENT_KEY] = FakeLockStore()  # No route reaches Redis.
    portal_app.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY] = VersionReaderStandIn()  # No stats read.
    portal_app.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY] = AggregateBoundaryStandIn()  # No firmware call.
    portal_app.config["RUN_STORE"] = AggregateStoreStandIn()  # The proposed plan stays in memory.
    portal_app.config["MIST_SELF_READER"] = lambda cloud_session: {"email": CLOUD_ACCOUNT}  # No account read.
    CascadeSeamStandIn().install(portal_app.config)  # No anchor read and no watch thread.
    monkeypatch.setattr(
        org_upgrade,
        "ORG_INVENTORY_CACHE",
        CloudReadCache(60, 256, inventory_clock),
    )  # No cache state from another test.
    monkeypatch.setattr(
        cast(Any, options_module).mistapi.api.v1.orgs.inventory,
        "getOrgInventory",
        inventory.read,
    )  # No cloud call.
    monkeypatch.setattr(
        options_module,
        "read_model_versions",
        lambda *args: {"AP45": (TARGET_VERSION,)},
    )  # No version service call.
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # One isolated browser owner.
    operator = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=(),
    )
    portal_app.config["T005_OPERATOR"] = operator  # The helper updates the server-side selection outside a request.
    identity.SESSION_REGISTRY.register(operator)
    try:
        with portal_app.test_client() as client:
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
            with client.session_transaction() as browser_session:
                browser_session[identity.SESSION_OWNER_KEY] = owner.key
                browser_session["selected_org_id"] = ORG_ID
                browser_session["selected_upgrade_mode"] = "multi_site"
            yield client
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)


def configure_sites(client: FlaskClient, inventory: InventoryStandIn, count: int) -> list[str]:
    """Give the signed operator and both read seams one selected site set."""
    site_ids = [f"00000000-0000-0000-0001-{index:012d}" for index in range(1, count + 1)]
    reader = client.application.config["MIST_READER"].__self__  # Read the fixture-owned fake Mist API.
    reader.payloads["listOrgSites"] = [
        {"id": site_id, "name": f"Site {index:03d}", "org_id": ORG_ID}
        for index, site_id in enumerate(site_ids, start=1)
    ]  # The ownership read returns every selected site.
    reader.payloads["listOrgSiteStats"] = []  # Device counts do not affect inventory mapping.
    inventory.rows = [
        {
            "mac": f"02{index:010x}",
            "name": f"ap-{index}",
            "type": "ap",
            "model": "AP45",
            "version": "0.14.1",
            "site_id": site_id,
        }
        for index, site_id in enumerate(site_ids, start=1)
    ]  # One logical device per selected site.
    operator = client.application.config["T005_OPERATOR"]  # The signed server-side record owns the site selection.
    operator.selected_site_ids = tuple(site_ids)  # Keep the selected order in the real route context.
    PrecheckAdopterStandIn(tuple(site_ids)).install(client.application.config)  # Keep each plan link offline.
    return site_ids


def options_body(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one valid explicit AP target choice for each inventory row."""
    return {
        "selected_types": ["ap"],
        "strategy": "big_bang",
        "targets": [{"mac": row["mac"], "version_target": TARGET_VERSION} for row in rows],
    }


@pytest.mark.parametrize("site_count", [2, 150])
def test_get_reads_organization_inventory_once(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
    site_count: int,
) -> None:
    """The GET read count stays one when the selected-site count grows."""
    configure_sites(t005_client, inventory, site_count)
    answer = t005_client.get(OPTIONS_PAGE)
    assert answer.status_code == 200
    assert len(inventory.calls) == 1
    assert inventory.calls[0] == {"org_id": ORG_ID, "limit": 1000}


def test_get_and_post_share_one_fresh_inventory_read(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
) -> None:
    """The POST validates the exact complete snapshot that the GET showed."""
    configure_sites(t005_client, inventory, 2)
    assert t005_client.get(OPTIONS_PAGE).status_code == 200
    answer = t005_client.post(OPTIONS_API, json=options_body(inventory.rows))
    assert answer.status_code == 200
    assert answer.get_json() == {"next": "/upgrade/org/confirm"}
    assert len(inventory.calls) == 1


def test_direct_post_reads_organization_inventory_once(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
) -> None:
    """A caller that skips the GET still spends one organization read."""
    configure_sites(t005_client, inventory, 2)
    answer = t005_client.post(OPTIONS_API, json=options_body(inventory.rows))
    assert answer.status_code == 200
    assert len(inventory.calls) == 1


def test_empty_body_returns_http_400_without_a_plan(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
) -> None:
    """An empty JSON body cannot create a plan."""
    configure_sites(t005_client, inventory, 2)
    answer = t005_client.post(OPTIONS_API, data=b"", content_type="application/json")
    assert answer.status_code == 400
    assert len(inventory.calls) == 1
    service = t005_client.application.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY]
    assert service.requests == []


def test_malformed_json_returns_http_400_without_a_plan(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
) -> None:
    """Malformed JSON cannot create a plan."""
    configure_sites(t005_client, inventory, 2)
    answer = t005_client.post(OPTIONS_API, data=b"{not valid JSONDecodeError", content_type="application/json")
    assert answer.status_code == 400
    assert len(inventory.calls) == 1
    service = t005_client.application.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY]
    assert service.requests == []


def test_expired_inventory_refresh_refuses_a_removed_target(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
    inventory_clock: Clock,
) -> None:
    """A stale page choice cannot create a plan after the fresh inventory loses it."""
    configure_sites(t005_client, inventory, 2)
    old_rows = [dict(row) for row in inventory.rows]
    assert t005_client.get(OPTIONS_PAGE).status_code == 200
    inventory_clock.now = 60.5  # Move past the cache boundary.
    inventory.rows = inventory.rows[1:]  # The first selected site now has no device.
    answer = t005_client.post(OPTIONS_API, json=options_body(old_rows))
    assert answer.status_code == 400
    assert len(inventory.calls) == 2
    service = t005_client.application.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY]
    assert service.requests == []


def test_partial_inventory_is_not_cached_and_marks_every_selected_site(
    t005_client: FlaskClient,
    inventory: InventoryStandIn,
) -> None:
    """A short organization read warns on GET and refuses the next POST after another read."""
    configure_sites(t005_client, inventory, 2)
    inventory.total = len(inventory.rows) + 1  # Report one missing organization row.
    page = t005_client.get(OPTIONS_PAGE)
    assert page.status_code == 200
    assert b'data-testid="org-upgrade-partial-inventory"' in page.data
    answer = t005_client.post(OPTIONS_API, json=options_body(inventory.rows))
    assert answer.status_code == 400
    assert len(inventory.calls) == 2
    service = t005_client.application.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY]
    assert service.requests == []
