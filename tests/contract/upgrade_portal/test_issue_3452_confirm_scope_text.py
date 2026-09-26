"""Contract tests of issue #3452: the scope text of the multi-site confirm page.

Why:
    Issue #3452. The multi-site confirm page stated a plural scope for a plan
    of one site. The Warning said "at all selected sites", and the button of a
    full pre-check said "Take new pre-checks for all sites". These tests drive
    the real options save and the real confirm route with stand-in cloud
    reads. Each test compares the whole text of the Warning and of each
    pre-check button, so a change to the scope or to the second sentence of
    the Warning fails the test.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterator, Mapping
from typing import Any

import pytest
from flask import Flask

from src.upgrade_portal.runtime import identity
from tests.contract.upgrade_portal.test_issue_3447_selected_site_count import (
    install_seams,
    register_operator,
    sign_in,
)
from tests.contract.upgrade_portal.test_org_child_controls_routes import (
    CONFIRM_PAGE,
    OPTIONS_API,
    PLAN_CHOICES,
    RETRY_ID,
    SITE_TWO,
    ControlsHarness,
    RecordStore,
    SiteVersionReader,
    error_code,
    post_json,
    settled_record,
)
from tests.support.lock_store_double import FakeLockStore

WARNING_ID = "org-upgrade-scope-warning"  # FR-005: the new test identifier of the Warning.
SCOPE_IDS = (WARNING_ID, "org-upgrade-precheck-all", "org-upgrade-precheck-missing")  # The three scope texts.
SECOND_SENTENCE = "Cancellation does not restore upgraded devices."  # The second sentence of the Warning stays.
ONE_SITE_TEXTS = (  # FR-001, FR-003, and FR-004: the texts of a plan of one site.
    f"Warning: the upgrade can interrupt network service at the selected site. {SECOND_SENTENCE}",
    "Take a new pre-check for the site",
    "Take the missing pre-check",
)
SITES_TEXTS = (  # FR-002, FR-003, and FR-004: the texts of a plan of two or more sites.
    f"Warning: the upgrade can interrupt network service at each selected site. {SECOND_SENTENCE}",
    "Take a new pre-check for each site",
    "Take the missing pre-checks",
)
NO_SCOPE = ("", "", "")  # A page that shows no confirm card shows no scope text.
REFUSED_CONFIRM = (400, "org_upgrade_options_invalid")  # The confirm page of a session with no saved plan.
AP_CHOICES = {**PLAN_CHOICES, "selected_types": ["ap"]}  # A retry of one failed access point.


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


def element_text(page: str, test_id: str) -> str:
    """Return the text of one element as a browser shows it.

    Args:
        page: The HTML of the page.
        test_id: The test identifier of the element.

    Returns:
        The text with one space between words, or empty text when the page holds no such element.
    """
    pattern = re.compile(rf'<(\w+)[^>]*data-testid="{test_id}"[^>]*>(.*?)</\1>', re.DOTALL)  # One element.
    match = pattern.search(page)  # The first element with this identifier.
    if match is None:  # The page holds no such element.
        return ""  # The whole-value compare then names the missing element.
    return " ".join(html.unescape(match.group(2)).split())  # A browser folds the white space of the template.


def save_and_confirm(harness: ControlsHarness, choices: Mapping[str, Any]) -> tuple[int, int, str]:
    """Save one plan, and open the confirm page.

    Args:
        harness: The test harness.
        choices: The choices of the options form.

    Returns:
        The status of the save, the status of the confirm page, and the HTML of the confirm page.
    """
    saved = post_json(harness, OPTIONS_API, dict(choices))  # The real options save with the stand-in reads.
    answer = harness.client.get(CONFIRM_PAGE)  # The real confirm route.
    return saved.status_code, answer.status_code, answer.get_data(as_text=True)  # One value for each compare.


def scope_texts(page: str) -> tuple[str, ...]:
    """Return the Warning, the text of the full pre-check button, and the text of the missing button."""
    return tuple(element_text(page, test_id) for test_id in SCOPE_IDS)  # The page order of the three texts.


def test_a_plan_of_one_site_names_one_site(controls: ControlsHarness) -> None:
    """FR-001, FR-003, and FR-004: a plan of one site names one site in each scope text."""
    controls.operator.selected_site_ids = (controls.site_one,)  # The operator selected one site only.
    saved, status, page = save_and_confirm(controls, PLAN_CHOICES)  # Save the plan, and open the confirm page.
    assert (saved, status) == (200, 200)  # The save accepted the plan, and the confirm page opened.
    assert scope_texts(page) == ONE_SITE_TEXTS  # Each whole text names one site.
    assert "<strong>Sites:</strong> 1</p>" in page  # FR-006: the line "Sites" states the same count.


def test_a_plan_of_two_sites_keeps_a_plural_scope(controls: ControlsHarness) -> None:
    """FR-002, FR-003, and FR-004: a plan of two sites keeps a plural scope in each text."""
    saved, status, page = save_and_confirm(controls, PLAN_CHOICES)  # Save the plan of both sites.
    assert (saved, status) == (200, 200)  # The save accepted the plan, and the confirm page opened.
    assert scope_texts(page) == SITES_TEXTS  # Each whole text keeps the plural scope.
    assert "<strong>Sites:</strong> 2</p>" in page  # FR-006: the line "Sites" states the same count.


def test_a_retry_of_one_site_names_one_site(controls: ControlsHarness) -> None:
    """A retry that keeps one site of an earlier plan names one site on its confirm page."""
    controls.store.write_run(settled_record(controls, switch_status="completed"))  # Only site two failed.
    retry = post_json(controls, f"/api/org-upgrades/{RETRY_ID}/retry")  # The operator presses the retry button.
    saved, status, page = save_and_confirm(controls, AP_CHOICES)  # Save the retry of the failed access point.
    assert (retry.status_code, controls.operator.selected_site_ids) == (200, (SITE_TWO,))  # One site stays.
    assert (saved, status) == (200, 200)  # The save accepted the retry, and the confirm page opened.
    assert scope_texts(page) == ONE_SITE_TEXTS  # The retry of one site names one site.


def post_raw_save(harness: ControlsHarness, body: str | bytes) -> tuple[int, tuple[int, str], tuple[str, ...]]:
    """Send one raw body to the options save, and read the confirm page after the save.

    Args:
        harness: The test harness.
        body: The raw request body, which a scripted client can send.

    Returns:
        The status of the save, the status and the error code of the confirm page, and its scope texts.
    """
    saved = harness.client.post(OPTIONS_API, data=body, content_type="application/json")  # The raw body.
    answer = harness.client.get(CONFIRM_PAGE)  # The confirm route after the refused save.
    confirm = (answer.status_code, error_code(answer))  # The refusal of a page with no saved plan.
    return saved.status_code, confirm, scope_texts(answer.get_data(as_text=True))  # One value for each compare.


def test_an_empty_save_body_shows_no_scope(controls: ControlsHarness) -> None:
    """A save with an empty body stores no plan, so no confirm page states a scope."""
    saved, confirm, texts = post_raw_save(controls, b"")  # No body at all.
    assert saved == 400  # The save refuses a body with no choice.
    assert (confirm, texts) == (REFUSED_CONFIRM, NO_SCOPE)  # The confirm route shows no scope text.


def test_a_malformed_save_body_shows_no_scope(controls: ControlsHarness) -> None:
    """A save with a body that is not valid JSON stores no plan, so no confirm page states a scope."""
    saved, confirm, texts = post_raw_save(controls, "{bad json")  # A damaged body from a scripted client.
    assert saved == 400  # The save refuses a body that it cannot read.
    assert (confirm, texts) == (REFUSED_CONFIRM, NO_SCOPE)  # The confirm route shows no scope text.
