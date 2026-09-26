"""Contract tests for the site refusals of the multi-site save.

Why:
    Issue #3389. The multi-site save kept the options of the last site only.
    A site with no device answers an empty record, so a canary plan became a
    plan with the default options when that site came last. A failed
    inventory read gave the same empty record, and the save then dropped the
    devices of that site with no message. These tests drive the real Flask
    routes and the production aggregate build. Stand-ins answer only at the
    cloud edge, so no test opens a socket and no test sends a firmware request.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from requests.exceptions import ConnectionError as TransportError

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade import options as option_rules
from src.upgrade_portal.upgrade.org_site_records import SHORT_MESSAGE, UNPLANNED_MESSAGE, UNREAD_MESSAGE
from tests.contract.upgrade_portal.test_org_advanced_options import (
    AP_ONE,
    AP_TARGET,
    AP_TWO,
    GATEWAY_ONE,
    JUNOS_TARGET,
    SWITCH_ONE,
    SWITCH_TWO,
    RecordStore,
    inventory_row,
)
from tests.support.lock_store_double import FakeLockStore

OPERATOR_EMAIL = "org-site-records.operator@juniper.net"  # A reachable address, because a firmware write needs one.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
SITE_TWO = "00000000-0000-0000-0000-0000000000dd"  # A site with an access point and a switch.
EMPTY_SITE = "00000000-0000-0000-0000-0000000000ee"  # A site that holds no device.
GATEWAY_SITE = "00000000-0000-0000-0000-0000000000ff"  # A site that holds only a gateway.
FIRST_NAME = "Test Site"  # The name of the first site in the site list.
SITE_TWO_NAME = "Site Two"  # The name of the second site.
EMPTY_NAME = "Empty Site"  # The name of the site with no device.
GATEWAY_NAME = "Gateway Site"  # The name of the site with only a gateway.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
REFUSAL_CODE = "org_upgrade_options_invalid"  # The error code of each refused save.
UNREAD_START = UNREAD_MESSAGE.split("{names}", maxsplit=1)[0]  # The fixed text before the names.
UNPLANNED_START = UNPLANNED_MESSAGE.split("{names}", maxsplit=1)[0]  # The fixed text before the names.
MALFORMED_BODY = '{"selected_types": ["ap"], "strategy": "canary", bad json'  # No JSON reader accepts it.
OPTIONS_PAGE = "/upgrade/org/options"  # The multi-site options page.
PARTIAL_BANNER_PATTERN = r'data-testid="org-upgrade-partial-inventory">\s*<span>(.*?)</span>'  # Issue #3424.
SHORT_REASON = {"section": "upgrade_inventory", "reason": "page_count_mismatch", "http_status": 200}  # Issue #3424.
CANARY_PHASES = [1, 10, 50, 100]  # The phases of the canary plan below.
CANARY_PLAN = {  # A canary plan of the access points and the switches, as the page script posts it.
    "selected_types": ["ap", "switch"],
    "version_ap": AP_TARGET,
    "version_switch": JUNOS_TARGET,
    "strategy": "canary",
    "canary_phases": "1,10,50,100",
    "max_failure_percentage": "5",
}


@dataclass
class SiteApp:
    """Hold the configured portal and each stand-in of one test."""

    app: Flask  # The portal with each cloud edge replaced.
    org_id: str  # The selected organization.
    first_site: str  # The identifier of the first site.
    store: RecordStore  # The durable store of every operation.
    failed_reads: set[str] = field(default_factory=set)  # The sites whose inventory read fails at the save.
    failed_views: set[str] = field(default_factory=set)  # The sites whose view read fails at the save.
    short_views: set[str] = field(default_factory=set)  # Issue #3424: the sites whose view read is short.
    short_reads: set[str] = field(default_factory=set)  # Issue #3424: the sites whose save read is short.


def empty_aware_builder(
    devices: Mapping[str, list[dict[str, str]]],
    failed_reads: set[str],
    short_reads: set[str],
) -> Any:
    """Return the stand-in of the site option mapper, with the empty-record rule of the shipped mapper.

    Why:
        `build_options_record` returns an empty record when the inventory
        read finds no device. A site with no device and a failed read give
        the same answer, so the stand-in gives that answer for both. Issue
        #3424: the shipped mapper refuses a short read, so the stand-in
        raises the same refusal for a short site.
    """

    def build(cloud_session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        """Build the targets and the options of one site without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        if site_id in short_reads:  # Issue #3424: the save read of this site stopped after the first page.
            raise option_rules.PartialInventoryError(site_id, [dict(SHORT_REASON)])  # The shipped refusal.
        if site_id in failed_reads or not devices[site_id]:  # The shipped mapper found no device.
            return {}  # The shipped empty record, which holds no targets and no options.
        entries = option_rules.build_targets(devices[site_id], list(body["targets"]))  # One entry for each choice.
        return {"targets": entries, "options": asdict(option_rules.build_options(dict(body)))}  # Production shape.

    return build  # The route calls the mapper one time for each site.


@pytest.fixture
def site_app(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> SiteApp:
    """Return the portal with four sites and no live service."""
    store = RecordStore()  # Every operation stays in memory.
    devices = {  # The inventory of each site.
        fake_site_id: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE)],  # An access point and a switch.
        SITE_TWO: [inventory_row(AP_TWO), inventory_row(SWITCH_TWO)],  # An access point and a switch.
        EMPTY_SITE: [],  # No device, as the picker shows zero devices.
        GATEWAY_SITE: [inventory_row(GATEWAY_ONE)],  # A gateway only, so a plan of two other types skips it.
    }
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds each site.
        {"id": fake_site_id, "name": FIRST_NAME, "org_id": fake_org_id},  # The first row of the site list.
        {"id": SITE_TWO, "name": SITE_TWO_NAME, "org_id": fake_org_id},  # The second row.
        {"id": EMPTY_SITE, "name": EMPTY_NAME, "org_id": fake_org_id},  # The site with no device.
        {"id": GATEWAY_SITE, "name": GATEWAY_NAME, "org_id": fake_org_id},  # The site with a gateway only.
    ]
    built = SiteApp(portal_app, fake_org_id, fake_site_id, store)  # The handles that each test reads.

    def options_view(cloud_session: Any, org_id: str, site_id: str) -> dict[str, Any]:
        """Return the inventory of one site for the options page, without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        if site_id in built.failed_views:  # The view read of this site fails.
            return {"targets": [], "versions_by_model": {}}  # The shape of `build_options_view` after a failed read.
        if site_id in built.short_views:  # Issue #3424: the view read of this site stopped after the first page.
            return {"targets": deepcopy(devices[site_id]), "partial_reasons": [dict(SHORT_REASON)]}  # A short view.
        return {"targets": deepcopy(devices[site_id]), "partial_reasons": []}  # A copy, and a complete read.

    portal_app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: FakeLockStore(),  # Every lock write stays in memory.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": AggregateUpgradeService(),  # The production build, which calls no cloud.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: options_view,  # The inventory of the options page.
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: empty_aware_builder(  # The save.
                devices, built.failed_reads, built.short_reads
            ),
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
    return built  # The test posts through the configured portal.


@contextmanager
def signed_client(site_app: SiteApp, site_ids: tuple[str, ...]) -> Iterator[FlaskClient]:
    """Yield a signed client whose operator selected the named sites in the named order."""
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The signed operator.
    operator = identity.OperatorSession(  # The server-side record that the session guard reads.
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=site_ids,
    )
    identity.SESSION_REGISTRY.register(operator)  # The session guard finds the operator record.
    try:  # Drop the operator record after the test, also after a failure.
        with site_app.app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = site_app.org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield client  # The test posts with the signed session.
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def refused_message(client: FlaskClient, plan: Mapping[str, Any]) -> str:
    """Post one plan, and return the refusal text that the flash message shows."""
    answer = client.post(OPTIONS_API, json=dict(plan))  # Save the options through the JSON contract.
    assert answer.status_code == 400, answer.get_data(as_text=True)  # The save must stop before the confirm page.
    payload = answer.get_json()  # Read the structured refusal.
    assert payload["error"]["code"] == REFUSAL_CODE  # Keep the existing route error code.
    return str(payload["error"]["message"])  # Return the text that the operator reads.


def saved_options(client: FlaskClient) -> Any:
    """Return the saved options of the browser session, or None."""
    with client.session_transaction() as browser_session:  # Read the signed cookie.
        return browser_session.get(OPTIONS_SESSION_KEY)  # None when no save succeeded.


def ap_bodies(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the request body of each access point child job of one plan."""
    bodies = [dict(child["body"]) for child in record["children"] if child["device_family"] == "ap"]  # AP jobs.
    assert bodies, "The plan holds no access point child job."  # A missing child makes each later check hollow.
    return bodies  # One body for each access point child job.


def test_an_empty_last_site_stops_the_save_and_names_the_site(site_app: SiteApp) -> None:
    """FR-002: the old save replaced the canary plan with the defaults. The new save names the empty site."""
    with signed_client(site_app, (site_app.first_site, EMPTY_SITE)) as client:  # The empty site comes last.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
        assert message == UNREAD_MESSAGE.format(names=EMPTY_NAME)  # The refusal names the site, not its identifier.
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no child job can start.


def test_an_empty_first_site_stops_the_save_the_same_way(site_app: SiteApp) -> None:
    """FR-002: the old save dropped the empty site with no message. The new save names it in each order."""
    with signed_client(site_app, (EMPTY_SITE, site_app.first_site)) as client:  # The empty site comes first.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
        assert message == UNREAD_MESSAGE.format(names=EMPTY_NAME)  # The order of the selection changes nothing.
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no child job can start.


def test_a_failed_inventory_read_stops_the_save(site_app: SiteApp) -> None:
    """FR-002: a failed read of a site with devices must not drop those devices from the plan."""
    site_app.failed_reads.add(SITE_TWO)  # The page showed the devices, and the read at the save fails.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites that hold devices.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert message == UNREAD_MESSAGE.format(names=SITE_TWO_NAME)  # The refusal names the site of the failed read.
    assert site_app.store.records == {}  # No plan exists, so the devices of the site cannot drop out.


def test_a_failed_view_read_stops_the_save_as_an_unread_site(site_app: SiteApp) -> None:
    """FR-009: a failed view read names the site as unread, also when the next read of the site answers."""
    site_app.failed_views.add(SITE_TWO)  # The page showed the devices, and the view read at the save fails.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites that hold devices.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert message == UNREAD_MESSAGE.format(names=SITE_TWO_NAME)  # Not the refusal for a site of unchecked types.
    assert site_app.store.records == {}  # No plan exists, so the devices of the site cannot drop out.


def test_two_unread_sites_share_one_refusal(site_app: SiteApp) -> None:
    """FR-002: one refusal names each unread site, in the order of the selection."""
    site_app.failed_reads.add(SITE_TWO)  # The second unread site has devices, and its read fails.
    with signed_client(site_app, (EMPTY_SITE, site_app.first_site, SITE_TWO)) as client:  # Two unread sites.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert message == UNREAD_MESSAGE.format(names=f"{EMPTY_NAME}, {SITE_TWO_NAME}")  # One message, both names.


def test_a_site_with_no_checked_device_type_stops_the_save(site_app: SiteApp) -> None:
    """FR-003: a site with only an unchecked device type must not drop out of the plan with no message."""
    with signed_client(site_app, (site_app.first_site, GATEWAY_SITE)) as client:  # The plan checks no gateway.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
        assert message == UNPLANNED_MESSAGE.format(names=GATEWAY_NAME)  # The refusal names the skipped site.
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no child job can start.


def test_no_planned_device_at_any_site_keeps_the_old_refusal(site_app: SiteApp) -> None:
    """FR-004: the old refusal names the device type control when no site holds a planned device."""
    plan = {**CANARY_PLAN, "selected_types": ["gateway"], "version_gateway": "23.4R1.9"}  # Neither site has one.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites with no gateway.
        message = refused_message(client, plan)  # The save must stop before the confirm page.
    assert '"Device types to upgrade"' in message  # The old refusal names the device type control.
    assert not message.startswith((UNREAD_START, UNPLANNED_START))  # No site refusal replaces the old refusal.


@pytest.mark.parametrize("order", ["first-then-second", "second-then-first"])
def test_an_accepted_save_keeps_the_canary_plan_in_each_order(site_app: SiteApp, order: str) -> None:
    """FR-001: each site that answers keeps the choices of the operator in the stored plan."""
    pair = (site_app.first_site, SITE_TWO)  # Two sites that each hold an access point and a switch.
    site_ids = pair if order == "first-then-second" else pair[::-1]  # Each site comes last one time.
    with signed_client(site_app, site_ids) as client:  # The operator selected both sites.
        answer = client.post(OPTIONS_API, json=CANARY_PLAN)  # Save the canary plan.
        assert answer.status_code == 200, answer.get_data(as_text=True)  # The save accepts the plan.
        saved = saved_options(client)  # The options that the confirm page reads.
    record = site_app.store.records[str(saved["operation_id"])]  # The stored plan of the save.
    assert saved["target_count"] == 4  # Two devices at each site.
    for body in ap_bodies(record):  # Each access point child job carries the choices of the operator.
        assert body["strategy"] == "canary"  # The old save sent the default strategy.
        assert body["canary_phases"] == CANARY_PHASES  # The old save sent the default phases.


def test_the_refusal_repeats_no_typed_value(site_app: SiteApp) -> None:
    """The refusal shows the site names from the cloud, and no version text that the operator typed."""
    with signed_client(site_app, (site_app.first_site, EMPTY_SITE)) as client:  # The empty site comes last.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert AP_TARGET not in message  # The flash region shows no typed access point version.
    assert JUNOS_TARGET not in message  # The flash region shows no typed switch version.


@pytest.mark.parametrize("body", [MALFORMED_BODY, b""], ids=["malformed-json", "empty-body"])
def test_a_malformed_or_empty_body_with_an_empty_site_saves_no_plan(site_app: SiteApp, body: str | bytes) -> None:
    """The route reads each body as the empty form, so the site refusal still names the empty site."""
    with signed_client(site_app, (site_app.first_site, EMPTY_SITE)) as client:  # The empty site comes last.
        answer = client.post(OPTIONS_API, data=body, content_type="application/json")  # The page never posts it.
        assert answer.status_code == 400  # The save refuses the body before a plan exists.
        error = answer.get_json()["error"]  # The structured refusal.
        assert error == {"code": REFUSAL_CODE, "message": UNREAD_MESSAGE.format(names=EMPTY_NAME)}  # Site first.
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no child job can start.


def test_a_failed_name_read_names_each_site_by_its_identifier(site_app: SiteApp, fake_mist_api: Any) -> None:
    """FR-006: a transport fault of the name read must not hide the refusal."""

    def reader(name: str, **parameters: Any) -> Any:
        """Fail the site list, and answer every other read from the stand-in."""
        if name == "listOrgSites":  # The name read of the refusal fails.
            raise TransportError("The stand-in site list is not reachable.")  # The fault of the name read.
        return fake_mist_api.read(name, **parameters)  # Every other read answers from the stand-in.

    site_app.app.config["MIST_READER"] = reader  # Only the site list fails.
    with signed_client(site_app, (site_app.first_site, EMPTY_SITE)) as client:  # The empty site comes last.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert message == UNREAD_MESSAGE.format(names=EMPTY_SITE)  # The identifier replaces the unread name.


# ---------------------------------------------------------------------------
# Issue #3424: a site whose inventory read stopped after the first page.
# ---------------------------------------------------------------------------


def partial_banner_text(page: str) -> str | None:
    """Return the text of the partial inventory banner, or None when the page shows no banner."""
    match = re.search(PARTIAL_BANNER_PATTERN, page, flags=re.DOTALL)  # The one banner of the page.
    return " ".join(match.group(1).split()) if match else None  # Join the wrapped template lines.


def test_the_options_page_names_each_short_site(site_app: SiteApp) -> None:
    """FR-006: the page warns the operator before the save, and names only the short site."""
    site_app.short_views.add(SITE_TWO)  # The view read of the second site stopped after the first page.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites that hold devices.
        answer = client.get(OPTIONS_PAGE)  # Open the options page.
    assert answer.status_code == 200  # A short read never refuses the page.
    text = partial_banner_text(answer.get_data(as_text=True))  # The banner above the device tables.
    assert text is not None and SITE_TWO_NAME in text  # The old page showed no warning.
    assert FIRST_NAME not in text  # A site with a complete read stays out of the banner.
    assert "Reload this page before you save the options." in text  # The banner states the next step.


def test_the_options_page_shows_no_banner_after_complete_reads(site_app: SiteApp) -> None:
    """FR-006: complete reads give no warning."""
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites with complete reads.
        answer = client.get(OPTIONS_PAGE)  # Open the options page.
    assert answer.status_code == 200  # The page opens.
    assert partial_banner_text(answer.get_data(as_text=True)) is None  # No banner.


def test_a_short_view_stops_the_save_and_names_the_site(site_app: SiteApp) -> None:
    """FR-007 and FR-010: the old save planned the first page of the site only. The new save names the site."""
    site_app.short_views.add(SITE_TWO)  # The view read of the second site stopped after the first page.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites that hold devices.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
        assert message == SHORT_MESSAGE.format(names=SITE_TWO_NAME)  # The refusal names the short site.
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no device of a lost page can drop out.


def test_a_short_save_read_stops_the_save_and_names_the_site(site_app: SiteApp) -> None:
    """FR-007: a complete view read and a short save read also stop the save, because the save read decides."""
    site_app.short_reads.add(SITE_TWO)  # The page read was complete, and the read at the save is short.
    with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Two sites that hold devices.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
        assert message == SHORT_MESSAGE.format(names=SITE_TWO_NAME)  # Not the single-site text "this site".
        assert saved_options(client) is None  # The confirm page has no options to show.
    assert site_app.store.records == {}  # No plan exists, so no device of a lost page can drop out.


def test_an_unread_site_comes_before_a_short_site(site_app: SiteApp) -> None:
    """FR-008: the unread refusal of issue #3389 comes first, because an unread site hides each device."""
    site_app.short_views.add(SITE_TWO)  # The view read of the second site stopped after the first page.
    with signed_client(site_app, (site_app.first_site, SITE_TWO, EMPTY_SITE)) as client:  # One short, one unread.
        message = refused_message(client, CANARY_PLAN)  # The save must stop before the confirm page.
    assert message == UNREAD_MESSAGE.format(names=EMPTY_NAME)  # The unread site comes first.
