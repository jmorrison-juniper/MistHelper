"""Contract tests for the advanced upgrade controls of the multi-site options page.

Why:
    Issue #3383. The single-site options page offers eleven advanced controls
    that the multi-site page did not offer. An operator of a multi-site
    operation could not set a failure count for each canary phase, a peer
    download, a radio batch, the vendor stable build, or the release train of
    a router. These tests drive the real Flask routes, the shipped option
    mapper, and the production aggregate build. Stand-ins answer only at the
    cloud edge, so no test opens a socket and no test sends a firmware request.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade import options as option_rules
from src.upgrade_portal.upgrade.org_advanced_options import OrgAdvancedOptions
from tests.contract.upgrade_portal.test_upgrade_options import ADVANCED_CONTROL_IDS
from tests.support.lock_store_double import FakeLockStore

OPERATOR_EMAIL = "org-advanced.operator@juniper.net"  # A reachable address, because a firmware write needs one.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
SITE_TWO = "00000000-0000-0000-0000-0000000000dd"  # The second selected site of each test.
AP_ONE = "0011223344a1"  # The access point at the first site.
AP_TWO = "0011223344a2"  # The access point at the second site.
SWITCH_ONE = "0011223344b1"  # The switch at the first site.
SWITCH_TWO = "0011223344b2"  # The switch at the second site.
GATEWAY_ONE = "0011223344c1"  # The Junos gateway at the first site.
ROUTER_TWO = "0011223344c2"  # The session smart router at the second site.
DEVICES = {  # The name, the type, the model, and the running version of each device.
    AP_ONE: ("ap-one", "ap", "AP45", "0.14.1"),
    AP_TWO: ("ap-two", "ap", "AP45", "0.14.1"),
    SWITCH_ONE: ("switch-one", "switch", "EX4400", "23.4R1.8"),
    SWITCH_TWO: ("switch-two", "switch", "EX4400", "23.4R1.8"),
    GATEWAY_ONE: ("gateway-one", "gateway", "SRX320", "23.4R1.8"),
    ROUTER_TWO: ("router-two", "gateway", "SSR120", "6.2.0"),
}
AP_TARGET = "0.15.1"  # The access point version that each plan requests.
JUNOS_TARGET = "23.4R1.9"  # The switch version that each plan requests.
GATEWAY_TARGET = "6.3.0"  # The gateway version that each gateway plan requests.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
OPTIONS_PAGE = "/upgrade/org/options"  # The multi-site options page.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
CONFIRM_PAGE = "/upgrade/org/confirm"  # The typed confirmation page.
MALFORMED_BODY = '{"selected_types": ["ap"], "enable_p2p": "yes", bad json'  # No JSON reader accepts it.
BASE_PLAN = {  # The choices of a canary plan of the access points and the switches, as the browser posts them.
    "selected_types": ["ap", "switch"],
    "version_ap": AP_TARGET,
    "version_switch": JUNOS_TARGET,
    "strategy": "canary",
    "canary_phases": "1,10,50,100",
    "max_failure_percentage": "5",
}
PEER_CHOICES = {"max_failures": "0,1,2,3", "enable_p2p": "yes", "p2p_cluster_size": "20", "p2p_parallelism": "4"}
RADIO_CHOICES = {  # One value of each radio batch control, with the radio strategy.
    "strategy": "rrm",
    "rrm_first_batch_percentage": "10",
    "rrm_max_batch_percentage": "30",
    "rrm_node_order": "fringe_to_center",
    "rrm_mesh_upgrade": "sequential",
    "rrm_slow_ramp": "no",
}
DEFAULT_AP_FIELDS = {  # The fields of the access point body of a canary plan before issue #3383.
    "all_sites",
    "device_type",
    "site_ids",
    "versions",
    "strategy",
    "canary_phases",
    "max_failure_percentage",
}
ADVANCED_FIELDS = (  # The eleven cloud fields that issue #3383 adds to the multi-site page.
    "max_failures",
    "stable_version",
    "enable_p2p",
    "p2p_cluster_size",
    "p2p_parallelism",
    "rrm_first_batch_percentage",
    "rrm_max_batch_percentage",
    "rrm_node_order",
    "rrm_mesh_upgrade",
    "rrm_slow_ramp",
    "channel",
)
MULTISITE_CONTROL_OF = {  # The multi-site control of each single-site advanced control.
    "upgrade-advanced-options": "org-upgrade-advanced-options",
    "upgrade-canary-phases": "org-upgrade-canary-phases",
    "upgrade-max-failures": "org-upgrade-max-failures-per-phase",
    "upgrade-max-failure-percentage": "org-upgrade-max-failures",  # This older identifier names the percentage.
    "upgrade-reboot-at": "org-upgrade-reboot-at",
    "upgrade-force-yes": "org-upgrade-force",
    "upgrade-stable-version-yes": "org-upgrade-stable-version-yes",
    "upgrade-enable-p2p-yes": "org-upgrade-enable-p2p-yes",
    "upgrade-p2p-cluster-size": "org-upgrade-p2p-cluster-size",
    "upgrade-p2p-parallelism": "org-upgrade-p2p-parallelism",
    "upgrade-rrm-first-batch-percentage": "org-upgrade-rrm-first-batch-percentage",
    "upgrade-rrm-max-batch-percentage": "org-upgrade-rrm-max-batch-percentage",
    "upgrade-rrm-node-order": "org-upgrade-rrm-node-order",
    "upgrade-rrm-mesh-upgrade": "org-upgrade-rrm-mesh-upgrade",
    "upgrade-rrm-slow-ramp": "org-upgrade-rrm-slow-ramp",
    "upgrade-start-time": "org-upgrade-start-time",
    "upgrade-ssr-channel": "org-upgrade-ssr-channel",
}
REFUSED_CHOICES = (  # One refused value of each advanced control, and the multi-site label that the refusal names.
    ({"max_failures": "1,2"}, "Failures allowed inside each canary phase"),
    ({"max_failures": "0,0,0,2147483648"}, "Failures allowed inside each canary phase"),
    ({"enable_p2p": "perhaps"}, "Let an access point take the firmware from a neighbor"),
    ({"enable_p2p": "yes", "p2p_cluster_size": "1001"}, "Access points of one download group"),
    ({"enable_p2p": "yes", "p2p_parallelism": "-1"}, "Download groups that run together"),
    (
        {"strategy": "rrm", "rrm_first_batch_percentage": "101"},
        "Access points of the first radio batch, as a percentage",
    ),
    ({"strategy": "rrm", "rrm_max_batch_percentage": "half"}, "Largest radio batch after the first, as a percentage"),
    ({"strategy": "rrm", "rrm_node_order": "sideways"}, "Order of the radio batches across each site"),
    ({"strategy": "rrm", "rrm_mesh_upgrade": "random"}, "Order of the mesh access points at the end of the run"),
    ({"strategy": "rrm", "rrm_slow_ramp": "maybe"}, "Growth of each radio batch"),
    ({"stable_version": "perhaps"}, "Firmware version of each switch and each gateway"),
    ({"stable_version": "yes"}, "Firmware version of each switch and each gateway"),  # The plan holds an access point.
    (
        {"selected_types": ["gateway"], "version_gateway": GATEWAY_TARGET, "channel": "gamma"},
        "Release train of each session smart router",
    ),
)


class RecordStore:
    """Keep aggregate records in memory, as the durable store does."""

    def __init__(self) -> None:
        """Start with no record."""
        self.records: dict[str, dict[str, Any]] = {}  # One detached record for each operation.
        self.guard = Lock()  # Serialize each read and each write.

    def write_run(self, record: dict[str, Any]) -> bool:
        """Store one detached record."""
        with self.guard:  # Keep the write atomic.
            self.records[str(record["run_id"])] = deepcopy(record)  # Detach the value of the caller.
        return True  # The memory store accepts every write.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None."""
        with self.guard:  # Keep the read consistent with the writes.
            record = self.records.get(run_id)  # An unknown key reads as None.
            return deepcopy(record) if record is not None else None  # Detach the stored value.


@dataclass
class AdvancedHarness:
    """Hold the signed client and each stand-in of one test."""

    client: FlaskClient  # The signed browser session.
    store: RecordStore  # The durable store of every operation.
    devices: dict[str, list[dict[str, str]]]  # The inventory of each site. A test can change it.


def inventory_row(mac: str) -> dict[str, str]:
    """Build one device row of the site inventory.

    Why:
        The options page reads `device_type` and `gateway_family`, and the
        shipped target builder reads `type` of the raw inventory. The row holds
        each field, and the shipped family rule decides the gateway family.
    """
    name, device_type, model, version = DEVICES[mac]  # The fixed facts of the device.
    row = {
        "mac": mac,
        "name": name,
        "device_type": device_type,
        "type": device_type,
        "model": model,
        "version": version,
    }
    family = option_rules.resolve_family_scope(device_type, row)[0] or ""  # The rule of the production options view.
    return {**row, "gateway_family": family}  # A switch and an access point carry an empty family.


def option_builder(devices: Mapping[str, list[dict[str, str]]]) -> Any:
    """Return the stand-in of the site option mapper, with the production record shape."""

    def build(cloud_session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        """Build the targets and the options of one site without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        entries = option_rules.build_targets(devices[site_id], list(body["targets"]))  # One entry for each choice.
        return {"targets": entries, "options": asdict(option_rules.build_options(dict(body)))}  # Production shape.

    return build  # The route calls the mapper one time for each site.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[AdvancedHarness]:
    """Return a signed client with two selected sites and no live service."""
    store = RecordStore()  # Every operation stays in memory.
    devices = {  # The first site holds a Junos gateway, and the second site holds a router.
        fake_site_id: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE), inventory_row(GATEWAY_ONE)],
        SITE_TWO: [inventory_row(AP_TWO), inventory_row(SWITCH_TWO), inventory_row(ROUTER_TWO)],
    }
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds both selected sites.
        {"id": fake_site_id, "name": "Test Site", "org_id": fake_org_id},
        {"id": SITE_TWO, "name": "Site Two", "org_id": fake_org_id},
    ]
    portal_app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: FakeLockStore(),  # Every lock write stays in memory.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": AggregateUpgradeService(),  # The production build, which calls no cloud.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The signed operator.
    operator = identity.OperatorSession(  # The server-side record that the session guard reads.
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=(fake_site_id, SITE_TWO),
    )
    identity.SESSION_REGISTRY.register(operator)  # The session guard finds the operator record.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = fake_org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield AdvancedHarness(client, store, devices)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def save(harness: AdvancedHarness, **choices: Any) -> Any:
    """Post the base plan with the named choices, as the page script posts it."""
    return harness.client.post(OPTIONS_API, json={**BASE_PLAN, **choices})  # Every value is a text, as in the page.


def saved_plan(harness: AdvancedHarness) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the saved browser options and the durable plan that they name."""
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        saved = dict(browser_session[OPTIONS_SESSION_KEY])  # The options of the last accepted save.
    return saved, harness.store.records[str(saved["operation_id"])]  # The plan that the save wrote.


def child_bodies(record: Mapping[str, Any], family: str) -> list[dict[str, Any]]:
    """Return the request body of each child job of one device family."""
    bodies = [dict(child["body"]) for child in record["children"] if child["device_family"] == family]
    assert bodies, f"The plan holds no {family} child job."  # A missing child makes each later check hollow.
    return bodies  # One body for each child job of the family.


def opening_tag(page: str, test_id: str) -> str:
    """Return the opening tag of the element with one test identifier."""
    match = re.search(rf'<[a-z]+\b[^>]*\bdata-testid="{re.escape(test_id)}"[^>]*>', page)  # One tag.
    assert match is not None, f"The page holds no element {test_id}."  # Name the missing element.
    return match.group(0)  # The tag with every attribute.


def shown_value(page: str, test_id: str) -> str:
    """Return the value attribute of one input."""
    match = re.search(r'\bvalue="([^"]*)"', opening_tag(page, test_id))  # The prefilled text.
    return match.group(1) if match else ""  # An input with no value attribute shows an empty field.


def is_checked(page: str, test_id: str) -> bool:
    """Return true when one radio input renders checked."""
    return re.search(r"\schecked\b", opening_tag(page, test_id)) is not None  # The first paint state.


def is_hidden(page: str, test_id: str) -> bool:
    """Return true when one element renders hidden."""
    return re.search(r"\shidden\b", opening_tag(page, test_id)) is not None  # The first paint state.


def selected_word(page: str, test_id: str) -> str:
    """Return the value of the selected option of one select."""
    pattern = rf'<select\b[^>]*\bdata-testid="{re.escape(test_id)}"[^>]*>(.*?)</select>'  # The whole select.
    match = re.search(pattern, page, re.DOTALL)  # The options span several lines.
    assert match is not None, f"The page holds no select {test_id}."  # Name the missing select.
    chosen = re.search(r'<option value="([^"]*)"\s+selected', match.group(1))  # The prefilled option.
    return chosen.group(1) if chosen else ""  # No selected option means the cloud default.


def element_text(page: str, test_id: str, closing: str = "li") -> str:
    """Return the text of one element of the confirm page.

    Args:
        page: The rendered page.
        test_id: The test identifier of the element.
        closing: The tag name that closes the element.

    Returns:
        The text of the element, without markup and with single spaces.
    """
    pattern = rf'data-testid="{re.escape(test_id)}"[^>]*>(.*?)</{closing}>'  # The element and its text.
    match = re.search(pattern, page, re.DOTALL)  # The text can span several lines.
    assert match is not None, f"The confirm page holds no element {test_id}."  # Name the missing element.
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())  # The text without markup.


def refusal_message(answer: Any) -> str:
    """Return the message of one refused save."""
    assert answer.status_code == 400  # The save refuses the value before a plan exists.
    payload = answer.get_json()  # Read the structured refusal.
    assert payload["error"]["code"] == "org_upgrade_options_invalid"  # Keep the existing route error code.
    return str(payload["error"]["message"])  # The text that the operator reads.


def test_the_canary_and_peer_values_reach_each_child_body(harness: AdvancedHarness) -> None:
    """Each canary count and each peer download value reaches the child job that reads it."""
    answer = save(harness, **PEER_CHOICES)  # A canary plan with a count for each phase and a peer download.
    assert answer.status_code == 200  # The save accepts every value.
    _, record = saved_plan(harness)  # Read the durable plan.
    ap_body = child_bodies(record, "ap")[0]  # The organization access point child.
    assert ap_body["max_failures"] == [0, 1, 2, 3]  # One count for each canary phase.
    assert ap_body["enable_p2p"] is True  # The access points take the firmware from a neighbor.
    assert (ap_body["p2p_cluster_size"], ap_body["p2p_parallelism"]) == (20, 4)  # The two download sizes.
    for body in child_bodies(record, "switch"):  # The site switch child of each site.
        assert body["max_failures"] == [0, 1, 2, 3]  # The switch reads the same canary counts.
        assert "enable_p2p" not in body  # The cloud reads the peer download for an access point only.


def test_the_radio_values_reach_the_access_point_body(harness: AdvancedHarness) -> None:
    """Each radio batch value reaches the organization access point child job."""
    answer = save(harness, **RADIO_CHOICES)  # A radio plan with each radio batch value.
    assert answer.status_code == 200  # The save accepts every value.
    _, record = saved_plan(harness)  # Read the durable plan.
    ap_body = child_bodies(record, "ap")[0]  # The organization access point child.
    assert ap_body["rrm_first_batch_percentage"] == 10  # The share of the first radio batch.
    assert ap_body["rrm_max_batch_percentage"] == 30  # The largest share of a later batch.
    assert ap_body["rrm_node_order"] == "fringe_to_center"  # The order across each site.
    assert ap_body["rrm_mesh_upgrade"] == "sequential"  # The order of the mesh access points.
    assert ap_body["rrm_slow_ramp"] is False  # The growth of each batch.


def test_the_default_form_leaves_each_body_unchanged(harness: AdvancedHarness) -> None:
    """The first paint of the page posts no advanced value, so each body stays as before."""
    answer = save(harness, max_failures="", stable_version="no", enable_p2p="no")  # The default page values.
    assert answer.status_code == 200  # The save accepts the default page.
    _, record = saved_plan(harness)  # Read the durable plan.
    assert set(child_bodies(record, "ap")[0]) == DEFAULT_AP_FIELDS  # No new field reaches the access point body.
    for body in child_bodies(record, "switch"):  # The site switch child of each site.
        assert body["version"] == JUNOS_TARGET  # The typed version, and not the stable word.
        assert "max_failures" not in body  # An empty count list keeps the cloud default.


@pytest.mark.parametrize(("choices", "label"), REFUSED_CHOICES)
def test_a_refused_value_names_the_multisite_control(
    harness: AdvancedHarness,
    choices: dict[str, Any],
    label: str,
) -> None:
    """Each refused advanced value names the multi-site control, and no plan exists.

    Args:
        harness: The test harness.
        choices: The choices that hold one refused value.
        label: The label of the multi-site control that holds the value.
    """
    message = refusal_message(save(harness, **choices))  # The save refuses the value.
    assert f'"{label}"' in message  # The operator reads the label of the control on this page.
    assert harness.store.records == {}  # No plan exists, so no child job can carry the value.


def test_the_stable_build_reaches_each_switch_body(harness: AdvancedHarness) -> None:
    """The vendor stable build reaches each switch child, and the confirm page names it."""
    answer = save(harness, selected_types=["switch"], stable_version="yes")  # A switch plan with the stable build.
    assert answer.status_code == 200  # A plan with no access point accepts the choice.
    _, record = saved_plan(harness)  # Read the durable plan.
    assert [body["version"] for body in child_bodies(record, "switch")] == ["stable", "stable"]  # One for each site.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # Open the typed confirmation page.
    line = element_text(page, "org-upgrade-firmware", closing="p")  # The firmware line of the confirm page.
    assert "Switches the vendor stable build" in line  # The firmware line names the stable build.
    assert JUNOS_TARGET not in line  # The typed version never reaches a switch, so the page never names it.
    assert "the vendor stable build" in element_text(page, "org-upgrade-summary-stable-version")  # The summary.


def test_the_router_channel_reaches_only_the_router_body(harness: AdvancedHarness) -> None:
    """The release train reaches the router child, and the Junos gateway child reads no train."""
    answer = save(  # A gateway plan with the beta train.
        harness, selected_types=["gateway"], version_gateway=GATEWAY_TARGET, strategy="big_bang", channel="beta"
    )
    assert answer.status_code == 200  # The save accepts the train.
    _, record = saved_plan(harness)  # Read the durable plan.
    assert child_bodies(record, "ssr")[0]["channel"] == "beta"  # The router follows the chosen train.
    assert "channel" not in child_bodies(record, "gateway")[0]  # A Junos gateway body holds no train.


def test_the_channel_control_shows_only_for_a_router(harness: AdvancedHarness) -> None:
    """The release train control shows only when a selected site holds a router."""
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The second site holds a router.
    assert 'data-testid="org-upgrade-ssr-channel"' in page  # The page shows the control.
    harness.devices[SITE_TWO] = [inventory_row(AP_TWO), inventory_row(SWITCH_TWO)]  # The router leaves the site.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # Open the page again.
    assert 'data-testid="org-upgrade-ssr-channel"' not in page  # No router, so no control.


def test_the_first_paint_hides_each_control_that_the_plan_does_not_read(harness: AdvancedHarness) -> None:
    """The first paint hides each advanced control that the default canary plan does not read."""
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The default plan: every type, canary.
    assert not is_hidden(page, "org-upgrade-max-failures-per-phase-field")  # The canary plan reads the counts.
    assert not is_hidden(page, "org-upgrade-p2p-group")  # The plan holds access points.
    assert not is_hidden(page, "org-upgrade-stable-version-group")  # The plan holds switches and gateways.
    assert is_hidden(page, "org-upgrade-p2p-cluster-size-field")  # The peer download is off.
    assert is_hidden(page, "org-upgrade-rrm-node-order-field")  # The canary plan reads no radio batch.
    assert is_checked(page, "org-upgrade-stable-version-no")  # The typed versions stay the default.
    assert is_checked(page, "org-upgrade-enable-p2p-no")  # The cloud download stays the default.
    assert "disabled" in opening_tag(page, "org-upgrade-rrm-node-order")  # A hidden control posts no value.


def test_back_shows_each_saved_canary_and_peer_value(harness: AdvancedHarness) -> None:
    """The page shows each saved canary and peer value after Back."""
    assert save(harness, **PEER_CHOICES).status_code == 200  # Save a plan with each value.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # Go back to the options page.
    assert shown_value(page, "org-upgrade-max-failures-per-phase") == "0,1,2,3"  # The counts of each phase.
    assert is_checked(page, "org-upgrade-enable-p2p-yes")  # The peer download stays on.
    assert shown_value(page, "org-upgrade-p2p-cluster-size") == "20"  # The size of one download group.
    assert shown_value(page, "org-upgrade-p2p-parallelism") == "4"  # The count of groups that run together.
    assert not is_hidden(page, "org-upgrade-p2p-cluster-size-field")  # The saved peer choice shows the size.


def test_back_shows_each_saved_radio_value(harness: AdvancedHarness) -> None:
    """The page shows each saved radio batch value after Back."""
    assert save(harness, **RADIO_CHOICES).status_code == 200  # Save a radio plan.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # Go back to the options page.
    assert shown_value(page, "org-upgrade-rrm-first-batch-percentage") == "10"  # The first batch share.
    assert shown_value(page, "org-upgrade-rrm-max-batch-percentage") == "30"  # The largest later share.
    assert selected_word(page, "org-upgrade-rrm-node-order") == "fringe_to_center"  # The order across each site.
    assert selected_word(page, "org-upgrade-rrm-mesh-upgrade") == "sequential"  # The mesh order.
    assert selected_word(page, "org-upgrade-rrm-slow-ramp") == "no"  # The growth of each batch.
    assert not is_hidden(page, "org-upgrade-rrm-node-order-field")  # The radio plan shows its controls.


def test_the_plan_keeps_each_value_for_a_later_retry(harness: AdvancedHarness) -> None:
    """The durable plan keeps each advanced value, so a later retry shows it again."""
    assert save(harness, **PEER_CHOICES).status_code == 200  # Save a plan with each value.
    _, record = saved_plan(harness)  # Read the durable plan.
    shown = org_upgrade.options_view(record["plan_options"])  # The retry prefill reads these stored choices.
    assert shown["max_failures"] == "0,1,2,3"  # The counts of each phase.
    assert shown["enable_p2p"] is True  # The peer download stays on.
    assert (shown["p2p_cluster_size"], shown["p2p_parallelism"]) == ("20", "4")  # The two download sizes.


def test_the_confirm_page_lists_each_advanced_value(harness: AdvancedHarness) -> None:
    """The typed confirmation page lists each advanced value before the operator types the word."""
    assert save(harness, **PEER_CHOICES).status_code == 200  # Save a plan with each value.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # Open the typed confirmation page.
    assert 'data-testid="org-upgrade-advanced-summary"' in page  # The page holds the summary.
    assert "0,1,2,3" in element_text(page, "org-upgrade-summary-max-failures")  # The counts of each phase.
    assert "neighbor" in element_text(page, "org-upgrade-summary-enable-p2p")  # The peer download line.
    assert "20" in element_text(page, "org-upgrade-summary-p2p-cluster-size")  # The size of one group.
    assert "4" in element_text(page, "org-upgrade-summary-p2p-parallelism")  # The groups that run together.


def test_the_confirm_page_names_each_radio_value(harness: AdvancedHarness) -> None:
    """The typed confirmation page names each radio batch choice in words."""
    assert save(harness, **RADIO_CHOICES).status_code == 200  # Save a radio plan.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # Open the typed confirmation page.
    assert "Start at the edge of each site" in element_text(page, "org-upgrade-summary-rrm-node-order")
    assert "One mesh access point at a time" in element_text(page, "org-upgrade-summary-rrm-mesh-upgrade")
    assert "Grow each batch at the usual rate" in element_text(page, "org-upgrade-summary-rrm-slow-ramp")


def test_a_router_plan_confirms_no_failure_count(harness: AdvancedHarness, fake_site_id: str) -> None:
    """A canary plan of one router lists no count, because the router body holds no canary field."""
    harness.devices[fake_site_id] = [inventory_row(AP_ONE), inventory_row(SWITCH_ONE)]  # The Junos gateway leaves.
    answer = save(harness, selected_types=["gateway"], version_gateway=GATEWAY_TARGET, max_failures="0,0,0,0")
    assert answer.status_code == 200  # The save accepts a count for each phase.
    _, record = saved_plan(harness)  # Read the durable plan.
    assert [child["device_family"] for child in record["children"]] == ["ssr"]  # The plan holds one router child.
    assert "max_failures" not in child_bodies(record, "ssr")[0]  # The router body holds no canary count.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # Open the typed confirmation page.
    assert 'data-testid="org-upgrade-summary-max-failures"' not in page  # The page promises no count.


def test_a_per_device_plan_confirms_no_failure_count(harness: AdvancedHarness) -> None:
    """One switch at each site with the reboot off takes the per-device call, so the page lists no count."""
    answer = save(harness, selected_types=["switch"], reboot="no", max_failures="0,0,0,0")  # One switch per site.
    assert answer.status_code == 200  # The save accepts a count for each phase.
    _, record = saved_plan(harness)  # Read the durable plan.
    bodies = child_bodies(record, "switch")  # One child for each site.
    assert len(bodies) == 2  # Each site holds one switch, so each site takes one call.
    assert all("device_ids" not in body for body in bodies)  # The per-device call names the device in its path.
    assert all("max_failures" not in body for body in bodies)  # That schema holds no orchestration field.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # Open the typed confirmation page.
    assert 'data-testid="org-upgrade-summary-max-failures"' not in page  # The page promises no count.


def test_the_legacy_request_reads_no_advanced_field(harness: AdvancedHarness) -> None:
    """An older client that posts no device type keeps the narrow request, with no advanced field."""
    body = {"version": AP_TARGET, "strategy": "canary", "canary_phases": "1,10,50,100", "max_failure_percentage": "5"}
    answer = harness.client.post(OPTIONS_API, json={**body, **PEER_CHOICES})  # The legacy shape.
    assert answer.status_code == 200  # The legacy save still works.
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        saved = dict(browser_session[OPTIONS_SESSION_KEY])  # The legacy options.
    assert set(ADVANCED_FIELDS).isdisjoint(saved)  # The legacy path reads none of the new fields.


def test_every_single_site_advanced_control_has_a_multisite_control(harness: AdvancedHarness) -> None:
    """Each advanced control of the single-site page has one control on the multi-site page."""
    assert set(MULTISITE_CONTROL_OF) == set(ADVANCED_CONTROL_IDS)  # A new single-site control needs a pair here.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The second site holds a router.
    missing = [control for control in MULTISITE_CONTROL_OF.values() if f'data-testid="{control}"' not in page]
    assert not missing, f"The multi-site page holds no control for: {missing}"  # Name each missing pair.


@pytest.mark.parametrize("body", [MALFORMED_BODY, ""], ids=["malformed-json", "empty-body"])
def test_a_malformed_or_empty_body_reads_no_advanced_value(portal_app: Flask, body: str) -> None:
    """A malformed JSON body or an empty body reads as the empty form, and the read does not raise.

    Args:
        portal_app: The shipped portal application.
        body: The text that reaches the save instead of a JSON object.
    """
    with portal_app.test_request_context(OPTIONS_API, method="POST", data=body, content_type="application/json"):
        source = org_upgrade.request_source()  # The shared reader of the save and of the reschedule.
        assert dict(source) == {}  # The text is not a plan, so no field reaches the option reader.
        assert OrgAdvancedOptions.read(source) == {}  # The peer download of the cut text stays off.


def test_an_empty_body_reads_as_the_empty_form(portal_app: Flask) -> None:
    """An empty body with the JSON content type reads as the empty form."""
    with portal_app.test_request_context(OPTIONS_API, method="POST", data="", content_type="application/json"):
        assert dict(org_upgrade.request_source()) == {}  # No JSON object and no form field.


@pytest.mark.parametrize("body", [MALFORMED_BODY, ""], ids=["malformed-json", "empty-body"])
def test_a_malformed_or_empty_body_saves_no_plan(harness: AdvancedHarness, body: str) -> None:
    """The save refuses a malformed JSON body and an empty body, and no plan exists.

    Args:
        harness: The test harness.
        body: The text that reaches the save instead of a JSON object.
    """
    answer = harness.client.post(OPTIONS_API, data=body, content_type="application/json")  # The page never posts it.
    assert answer.status_code == 400  # The save refuses the body before a plan exists.
    assert answer.get_json()["error"]["code"] == "org_upgrade_options_invalid"  # Keep the route error code.
    assert harness.store.records == {}  # No plan exists, so no child job can start.
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        assert OPTIONS_SESSION_KEY not in browser_session  # The confirm page has no options to show.
