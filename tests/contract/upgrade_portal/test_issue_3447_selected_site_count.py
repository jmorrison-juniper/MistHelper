"""Contract tests of issue #3447: the site noun of the multi-site options page.

Why:
    Issue #3447. The note of the multi-site options page printed the count of
    the selected sites and the fixed word "sites". A plan of one site then
    read "One operation targets 1 selected sites." These tests drive the real
    options route with a signed multi-site session and stand-in cloud reads.
    Each test compares the whole note text, so a change to the count, to the
    noun, or to the second sentence fails the test.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from copy import deepcopy
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from tests.contract.upgrade_portal.test_org_child_controls_routes import (
    AP_ONE,
    AP_TWO,
    CLOUD_ACCOUNT,
    OPERATOR_EMAIL,
    OPTIONS_PAGE,
    RETRY_CLEAR_API,
    RETRY_ID,
    SITE_TWO,
    SWITCH_ONE,
    SWITCH_TWO,
    ControlsHarness,
    ControlsService,
    RecordStore,
    SiteVersionReader,
    inventory_row,
    option_builder,
    post_json,
    settled_record,
)
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

NOTE_ID = "org-upgrade-site-count"  # FR-004: the stable test identifier of the note.
SECOND_SENTENCE = "The portal selects the safe route for each device family."  # FR-003: this text stays.
ONE_SITE_NOTE = f"One operation targets 1 selected site. {SECOND_SENTENCE}"  # FR-001: the singular noun.
TWO_SITES_NOTE = f"One operation targets 2 selected sites. {SECOND_SENTENCE}"  # FR-002: the plural noun.
RETRY_PATH = f"/api/org-upgrades/{RETRY_ID}/retry"  # The retry button of the settled operation.
OPEN_OPTIONS = (200, {"next": OPTIONS_PAGE})  # The answer of a retry or a clear that opens the options page.
NOTE_PATTERN = re.compile(rf'<p[^>]*data-testid="{NOTE_ID}"[^>]*>(.*?)</p>', re.DOTALL)  # The note paragraph.


def install_seams(app: Flask, fake_mist_api: Any, stores: tuple[Any, ...], scope: tuple[str, str]) -> None:
    """Replace each cloud edge and each store of the portal with a stand-in.

    Args:
        app: The portal application.
        fake_mist_api: The shared stub, which answers the site list.
        stores: The record store, the version reader, and the lock store.
        scope: The organization and the first site.
    """
    store, reader, locks = stores  # One name for each store.
    org_id, site_one = scope  # The organization and the first site.
    devices = {  # One access point and one switch at each site.
        site_one: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE)],
        SITE_TWO: [inventory_row(AP_TWO), inventory_row(SWITCH_TWO)],
    }
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds both sites.
        {"id": site_one, "name": "Test Site", "org_id": org_id},
        {"id": SITE_TWO, "name": "Site Two", "org_id": org_id},
    ]
    app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: locks,  # Every lock write stays in memory.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": ControlsService(),  # The production build with no cloud call.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: reader,  # No stats read reaches the cloud.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
    CascadeSeamStandIn().install(app.config)  # Issue #3245: no anchor read and no watch thread.
    PrecheckAdopterStandIn((site_one, SITE_TWO)).install(app.config)  # Issue #3243: each site holds a pre-check.


def register_operator(site_ids: tuple[str, ...]) -> identity.OperatorSession:
    """Register one signed operator with a selected site set.

    Args:
        site_ids: The selected sites, in the order of the selection.

    Returns:
        The server record of the operator. A test changes the selection through this record.
    """
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The operator and a new browser.
    operator = identity.OperatorSession(  # The server record that the session guard reads.
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=site_ids,  # The multi-site selection stays in the server record.
    )
    identity.SESSION_REGISTRY.register(operator)  # The session guard admits a registered owner only.
    return operator  # The caller drops the record after the test.


def sign_in(client: FlaskClient, operator: identity.OperatorSession, org_id: str) -> None:
    """Sign the browser session of one client with the multi-site scope.

    Args:
        client: The test client.
        operator: The registered operator.
        org_id: The selected organization.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, operator.owner.browser_id)  # The browser half of the pair.
    with client.session_transaction() as browser_session:  # The signed half of the pair.
        browser_session[identity.SESSION_OWNER_KEY] = operator.owner.key  # The owner of each operation.
        browser_session["selected_org_id"] = org_id  # The selected organization.
        browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.


@pytest.fixture
def controls(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[ControlsHarness]:
    """Return a signed multi-site client that selects both sites, with no live service."""
    stores = (RecordStore(), SiteVersionReader(), FakeLockStore())  # The store, the version read, and the locks.
    install_seams(portal_app, fake_mist_api, stores, (fake_org_id, fake_site_id))  # No live service.
    operator = register_operator((fake_site_id, SITE_TWO))  # The operator selected both sites.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            sign_in(client, operator, fake_org_id)  # The multi-site scope.
            yield ControlsHarness(client, *stores, operator, fake_org_id, fake_site_id)  # The shared handles.
    finally:
        identity.SESSION_REGISTRY.drop(operator.owner.key)  # No later test finds this operator.


def note_text(page: str) -> str:
    """Return the text of the site count note as a browser shows it.

    Args:
        page: The HTML of the options page.

    Returns:
        The note text with one space between words, or empty text when the page holds no such note.
    """
    match = NOTE_PATTERN.search(page)  # FR-004: the note carries its own test identifier.
    if match is None:  # The page holds no identified note.
        return ""  # The whole-value compare then names the missing note.
    return " ".join(html.unescape(match.group(1)).split())  # A browser folds the white space of the template.


def open_options(harness: ControlsHarness) -> tuple[int, str]:
    """Open the multi-site options page, and return its status and its note text.

    Args:
        harness: The test harness.

    Returns:
        The status code and the note text.
    """
    answer = harness.client.get(OPTIONS_PAGE)  # The real options route with the stand-in reads.
    return answer.status_code, note_text(answer.get_data(as_text=True))  # One value for each compare.


def open_retry(harness: ControlsHarness, switch_status: str) -> tuple[tuple[int, Any], tuple[str, ...]]:
    """Store a settled operation, press its retry button, and return the answer and the new selection.

    Args:
        harness: The test harness.
        switch_status: The state of the switch child job. A completed switch leaves one site to retry.

    Returns:
        The status and the body of the retry answer, and the selected sites after the retry.
    """
    harness.store.write_run(settled_record(harness, switch_status=switch_status))  # The settled operation.
    answer = post_json(harness, RETRY_PATH)  # The operator presses the retry button.
    return (answer.status_code, answer.get_json()), harness.operator.selected_site_ids  # The retry scope.


def test_one_selected_site_reads_as_one_site(controls: ControlsHarness) -> None:
    """FR-001: a plan of one site uses the singular noun."""
    controls.operator.selected_site_ids = (controls.site_one,)  # The operator selected one site only.
    assert open_options(controls) == (200, ONE_SITE_NOTE)  # The whole note, with the singular noun.


def test_two_selected_sites_read_as_sites(controls: ControlsHarness) -> None:
    """FR-002: a plan of two sites uses the plural noun."""
    assert open_options(controls) == (200, TWO_SITES_NOTE)  # The whole note, with the plural noun.


def test_a_retry_of_one_site_reads_as_one_site(controls: ControlsHarness) -> None:
    """FR-005: a retry keeps one site, so the note uses the singular noun."""
    retry = open_retry(controls, switch_status="completed")  # Only the access point of site two failed.
    assert retry == (OPEN_OPTIONS, (SITE_TWO,))  # The healthy site leaves the selection.
    assert open_options(controls) == (200, ONE_SITE_NOTE)  # The retry of one site uses the singular noun.


def test_the_end_of_a_retry_of_one_site_reads_as_one_site(controls: ControlsHarness) -> None:
    """The end of a retry keeps the site of the retry, so the note keeps the singular noun."""
    retry = open_retry(controls, switch_status="completed")  # Only the access point of site two failed.
    cleared = post_json(controls, RETRY_CLEAR_API)  # The operator ends the retry.
    assert (retry, (cleared.status_code, cleared.get_json())) == ((OPEN_OPTIONS, (SITE_TWO,)), OPEN_OPTIONS)
    assert open_options(controls) == (200, ONE_SITE_NOTE)  # The page plans every device of the one site.


def test_a_retry_of_two_sites_reads_as_sites(controls: ControlsHarness) -> None:
    """FR-005: a retry that keeps two sites uses the plural noun."""
    retry = open_retry(controls, switch_status="failed")  # One device failed at each site.
    assert retry == (OPEN_OPTIONS, (controls.site_one, SITE_TWO))  # Each site holds a retry device.
    assert open_options(controls) == (200, TWO_SITES_NOTE)  # The retry of two sites uses the plural noun.


def post_retry_body(harness: ControlsHarness, body: str | bytes) -> tuple[tuple[int, Any], tuple[str, ...]]:
    """Store a settled operation of one failed site, and press its retry button with a raw JSON body.

    Args:
        harness: The test harness.
        body: The raw request body, which a scripted client can send.

    Returns:
        The status and the body of the retry answer, and the selected sites after the retry.
    """
    harness.store.write_run(settled_record(harness, switch_status="completed"))  # Only site two failed.
    answer = harness.client.post(RETRY_PATH, data=body, content_type="application/json")  # The raw body.
    return (answer.status_code, answer.get_json()), harness.operator.selected_site_ids  # The retry scope.


def test_a_retry_with_an_empty_body_reads_as_one_site(controls: ControlsHarness) -> None:
    """The retry reads no body, so a request with an empty body opens the same retry of one site."""
    retry = post_retry_body(controls, b"")  # No body at all.
    assert retry == (OPEN_OPTIONS, (SITE_TWO,))  # The empty body changes nothing in the retry scope.
    assert open_options(controls) == (200, ONE_SITE_NOTE)  # The note keeps the singular noun.


def test_a_retry_with_a_malformed_json_body_reads_as_one_site(controls: ControlsHarness) -> None:
    """The retry reads no body, so a body that is not valid JSON opens the same retry of one site."""
    retry = post_retry_body(controls, "{bad json")  # A damaged body from a scripted client.
    assert retry == (OPEN_OPTIONS, (SITE_TWO,))  # The damaged body changes nothing in the retry scope.
    assert open_options(controls) == (200, ONE_SITE_NOTE)  # The note keeps the singular noun.
