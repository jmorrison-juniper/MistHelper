"""Prove that site transport failures refuse planning without losing operator choices."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from requests.exceptions import ConnectionError as TransportError
from requests.exceptions import RequestException, Timeout

from src.interfaces.portals.upgrade_portal.app.routes import org_upgrade
from tests.contract.upgrade_portal.test_org_site_records_routes import (
    CANARY_PLAN,
    OPTIONS_API,
    OPTIONS_PAGE,
    SITE_TWO,
    SiteApp,
    signed_client,
)
from tests.contract.upgrade_portal.test_org_site_records_routes import (
    site_app as site_app,
)

REFUSAL = {  # Keep the response contract independent of the production constants.
    "error": {
        "code": "org_upgrade_site_read_failed",
        "message": "The Mist cloud site read failed. Try again.",
    }
}


def _failing_reader(fake_mist_api: Any, error_type: type[RequestException]) -> Any:
    """Fail only the site-list endpoint so the save reaches its site ownership read."""

    def read(name: str, **parameters: Any) -> Any:
        """Keep inventory and site statistics available while the site list fails."""
        if name == "listOrgSites":  # The ownership read, not the separate device-family validation.
            raise error_type("private-transport-detail")  # Raw transport text must not reach the operator.
        return fake_mist_api.read(name, **parameters)  # Preserve every other local cloud answer.

    return read  # The configured cloud seam performs no network request.


class TestSiteReadRefusal:
    """Exercise the actual route and site reader with only the cloud boundary replaced."""

    @pytest.mark.parametrize("error_type", [TransportError, Timeout, RequestException])
    def test_failed_save_creates_no_plan(
        self, site_app: SiteApp, fake_mist_api: Any, error_type: type[RequestException]
    ) -> None:
        """FR-001 and FR-003: a failed ownership read cannot persist a new plan or nonce."""
        with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Both sites hold devices.
            site_app.app.config["MIST_READER"] = _failing_reader(fake_mist_api, error_type)  # Fail at the edge.
            with client.session_transaction() as browser_session:  # Capture all signed fields before the refusal.
                previous = dict(browser_session)  # A refusal must change no saved option or nonce.
            answer = client.post(OPTIONS_API, json=CANARY_PLAN)  # Exercise aggregation before the site-list failure.
            assert answer.status_code == 503  # The previous unhandled transport failure produced status 500.
            assert answer.get_json() == REFUSAL  # Explain the cloud cause without private transport text.
            with client.session_transaction() as browser_session:  # Read the state after the refused save.
                assert dict(browser_session) == previous  # No saved option, organization binding, or nonce.
        assert site_app.store.records == {}  # No durable operation can reach firmware submission.

    def test_failed_replacement_preserves_the_previous_plan(self, site_app: SiteApp, fake_mist_api: Any) -> None:
        """FR-005: a refused replacement must not corrupt an earlier confirmed choice."""
        with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Plan both populated sites.
            assert client.post(OPTIONS_API, json=CANARY_PLAN).status_code == 200  # Establish the earlier plan.
            records = deepcopy(site_app.store.records)  # Preserve each durable field for comparison.
            with client.session_transaction() as browser_session:  # Preserve every earlier signed field.
                previous = dict(browser_session)  # The old options remain valid after a refused replacement.
            site_app.app.config["MIST_READER"] = _failing_reader(fake_mist_api, Timeout)  # Fail the new read.
            answer = client.post(OPTIONS_API, json={**CANARY_PLAN, "max_failure_percentage": "7"})  # New choice.
            assert answer.status_code == 503  # Do not report success for the unsaved replacement.
            assert answer.get_json() == REFUSAL  # Use the same recovery contract.
            with client.session_transaction() as browser_session:  # The old plan must remain bound.
                assert dict(browser_session) == previous  # Preserve the nonce and the earlier options.
        assert site_app.store.records == records  # Preserve every field of the existing operation.

    @pytest.mark.parametrize("path", [OPTIONS_PAGE, "/upgrade/org/confirm"])
    @pytest.mark.parametrize("error_type", [TransportError, Timeout])
    def test_failed_page_read_preserves_the_plan(
        self, site_app: SiteApp, fake_mist_api: Any, path: str, error_type: type[RequestException]
    ) -> None:
        """FR-001 and FR-005: both pages name the failed cloud read without modifying the saved plan."""
        with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Use a complete signed selection.
            assert client.post(OPTIONS_API, json=CANARY_PLAN).status_code == 200  # Make confirmation accessible.
            records = deepcopy(site_app.store.records)  # A page read must not rewrite the existing plan.
            with client.session_transaction() as browser_session:  # Preserve each signed saved option.
                previous = dict(browser_session)  # Compare the full state rather than one selected field.
            site_app.app.config["MIST_READER"] = _failing_reader(fake_mist_api, error_type)  # Cloud edge only.
            answer = client.get(path)  # Exercise the actual page call to selected_rows.
            assert answer.status_code == 503  # Neither page may expose the generic unexpected-fault response.
            assert answer.get_json() == REFUSAL  # Both reads explain the same temporary cloud failure.
            with client.session_transaction() as browser_session:  # A read failure must preserve its inputs.
                assert dict(browser_session) == previous  # No navigation or option reset occurs.
        assert site_app.store.records == records  # No page read creates or removes an operation.

    def test_a_repeated_save_succeeds_after_recovery(self, site_app: SiteApp, fake_mist_api: Any) -> None:
        """SC-004: the same choices can reach confirmation after the cloud answers again."""
        with signed_client(site_app, (site_app.first_site, SITE_TWO)) as client:  # Keep the same browser selection.
            site_app.app.config["MIST_READER"] = _failing_reader(fake_mist_api, TransportError)  # First failure.
            assert client.post(OPTIONS_API, json=CANARY_PLAN).status_code == 503  # Refuse without saving.
            site_app.app.config["MIST_READER"] = fake_mist_api.read  # Restore the local site-list response.
            answer = client.post(OPTIONS_API, json=CANARY_PLAN)  # Repeat exactly the entered choices.
            assert answer.status_code == 200  # Recovery must not require a different request.
            assert answer.get_json() == {"next": "/upgrade/org/confirm"}  # Keep the successful response.
            with client.session_transaction() as browser_session:  # Inspect only validated saved options.
                options = browser_session[org_upgrade.OPTIONS_SESSION_KEY]  # A successful save binds the plan.
                assert options["canary_phases"] == [1, 10, 50, 100]  # Preserve the original phases.
                assert options["max_failure_percentage"] == 5  # Preserve the original failure limit.
        assert len(site_app.store.records) == 1  # Only the successful repeated save creates a plan.

    def test_empty_selection_keeps_the_validation_refusal(self, site_app: SiteApp, fake_mist_api: Any) -> None:
        """FR-006: an empty selection must fail validation before a site transport read is necessary."""
        site_app.app.config["MIST_READER"] = _failing_reader(fake_mist_api, TransportError)  # The cloud is unavailable.
        with signed_client(site_app, ()) as client:  # No selected site can define a valid operation.
            answer = client.post(OPTIONS_API, json=CANARY_PLAN)  # Valid choices cannot replace the missing scope.
            assert answer.status_code == 400  # Preserve the existing input refusal, not the new 503.
            assert answer.get_json()["error"]["code"] == org_upgrade.MODE_REQUIRED  # Keep the selection refusal.
            with client.session_transaction() as browser_session:  # No empty choice may become saved options.
                assert org_upgrade.OPTIONS_SESSION_KEY not in browser_session  # No confirmation can start.
        assert site_app.store.records == {}  # Invalid empty input creates no durable plan.
