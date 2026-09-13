"""Prove that the history and run pages share the stale view contract."""

from __future__ import annotations  # Keep annotations independent from import order.

from collections.abc import Iterator  # Type the signed-in client fixture.
from datetime import UTC, datetime, timedelta  # Build stable old and invalid run records.
from typing import Any  # Run records contain different JSON-compatible values.

import pytest  # Build the route fixtures.
from flask import Flask  # Type the real portal application.
from flask.testing import FlaskClient  # Type the signed-in route client.

from src.upgrade_portal.runtime import identity  # Use the real signed-session guard.

RUN_ID = "run-stale-contract"  # Keep both page requests on one exact record.
TERMINAL_RUN_ID = "run-terminal-contract"  # Prove that an old final run has no stale badge.
UNKNOWN_RUN_ID = "run-unknown-time-contract"  # Prove that malformed time stays unknown.
ORG_ID = "org-stale-contract"  # Give the run page one organization scope.
SITE_ID = "site-stale-contract"  # Give the history and lock reads one site scope.
PROBE_EMAIL = "stale.contract@example.invalid"  # Use a reserved address that reaches no mail service.


class ContractRunStore:  # Hold the exact records that both real page routes read.
    """Hold isolated run records for stale view contract tests."""

    def __init__(self, records: list[dict[str, Any]]) -> None:  # Index records by run identifier.
        """Store copies of the supplied run records."""
        self.records = {str(record["run_id"]): dict(record) for record in records}  # Protect fixture values.

    def read_run(self, run_id: str) -> dict[str, Any] | None:  # Read one run for the run page.
        """Return a copy of one run record."""
        record = self.records.get(run_id)  # An absent identifier gives no record.
        return dict(record) if record is not None else None  # Protect the stored value from route edits.

    def write_run(self, run: dict[str, Any]) -> bool:  # Match the store interface used by stop controls.
        """Store a copy of one run record."""
        self.records[str(run["run_id"])] = dict(run)  # Preserve a complete route write inside this test.
        return True  # The isolated store accepts each valid write.

    def list_runs(  # List the same records for the history page.
        self, site_id: str = "", limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Return one ordered page of run records."""
        rows = list(self.records.values())  # Preserve the insertion order of the fixture.
        scoped = [row for row in rows if not site_id or row.get("site_id") == site_id]  # Apply page scope.
        return [dict(row) for row in scoped[offset : offset + limit]]  # Return isolated row copies.


@pytest.fixture
def stale_app(portal_app: Flask) -> Flask:  # Install isolated run and lock seams on the real application.
    """Return the portal with fixed stale-view records."""
    old_time = datetime.now(tz=UTC) - timedelta(days=1, hours=1, minutes=30)  # Avoid a display boundary.
    base = {  # Supply every field that the run status view and page controls read.
        "org_id": ORG_ID,  # Bind the records to one organization.
        "site_id": SITE_ID,  # Bind the records to one site.
        "site_name": "Stale contract site",  # Give the page readable site text.
        "created_at": (old_time - timedelta(hours=1)).isoformat(),  # Give the history a start moment.
        "targets": [],  # Keep device rendering empty and deterministic.
        "phases": [],  # Let the status view build the default phase rows.
        "stop_request": None,  # Give the stop partial no prior outcome.
        "pre_capture_id": "",  # Keep capture links absent from this focused contract.
        "post_capture_id": "",  # Keep capture links absent from this focused contract.
    }
    stale = {**base, "run_id": RUN_ID, "state": "created", "updated_at": old_time.isoformat()}  # Eligible record.
    terminal = {**base, "run_id": TERMINAL_RUN_ID, "state": "failed", "updated_at": old_time.isoformat()}  # Final.
    unknown = {**base, "run_id": UNKNOWN_RUN_ID, "state": "created", "updated_at": "bad-time"}  # Unsafe time.
    store = ContractRunStore([stale, terminal, unknown])  # Give both routes the same record source.
    portal_app.config["RUN_STORE"] = store  # Keep the run page away from persistent storage.
    portal_app.config["RUN_LISTER"] = store.list_runs  # Keep the history page on the same records.
    portal_app.config["CAPTURE_LISTER"] = lambda *_arguments, **_options: []  # Keep capture reads in memory.
    portal_app.config["SITE_LOCK_READER"] = lambda _org, sites: {site: None for site in sites}  # Avoid Redis.
    return portal_app  # The shared factory already registered the real route blueprints.


@pytest.fixture
def stale_client(stale_app: Flask) -> Iterator[FlaskClient]:  # Sign in one isolated operator for both pages.
    """Return a signed-in client for the stale view routes."""
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # Build the pair that the guard checks.
    session_record = identity.OperatorSession(  # Register a safe session with no cloud client.
        owner=owner,  # Bind the record to the browser cookie pair.
        cloud_session=object(),  # A plain object can make no cloud request.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,  # Use the existing session kind.
    )
    identity.SESSION_REGISTRY.register(session_record)  # Add the record before the first page request.
    try:  # Keep cleanup active when an assertion fails.
        with stale_app.test_client() as client:  # Hold one browser session across both page reads.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Supply the cookie half of the guard.
            with client.session_transaction() as browser_session:  # Write the signed server-side session.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Supply the session half of the guard.
            yield client  # Let each contract test read the real rendered pages.
    finally:  # The process-wide registry must not affect a later test.
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the isolated operator record.


class TestStaleViewContract:  # Group the three page-agreement cases under one contract owner.
    """Verify the stale, terminal, and unknown page contracts."""

    def test_stale_run_has_matching_age_and_badges(self, stale_client: FlaskClient) -> None:
        """Both pages show the same age and the exact stale test identifiers."""
        history = stale_client.get("/history").get_data(as_text=True)  # Render the real history page.
        run_page = stale_client.get(f"/runs/{RUN_ID}").get_data(as_text=True)  # Render the real run page.
        assert f'data-testid="history-run-age-{RUN_ID}"' in history  # Use the exact history age identifier.
        assert f'data-testid="history-run-stale-{RUN_ID}"' in history  # Use the exact history stale identifier.
        assert 'data-testid="run-last-update-age"' in run_page  # Use the exact run page age identifier.
        assert 'data-testid="run-stale-badge"' in run_page  # Use the exact run page stale identifier.
        assert "1d 1h" in history  # Show the same short age on the history page.
        assert "1d 1h" in run_page  # Show the same short age on the run page.

    def test_terminal_run_has_age_without_stale_badges(self, stale_client: FlaskClient) -> None:
        """Both pages show an old terminal age without a stale badge."""
        history = stale_client.get("/history").get_data(as_text=True)  # Render all run rows.
        run_page = stale_client.get(f"/runs/{TERMINAL_RUN_ID}").get_data(as_text=True)  # Render the final run.
        assert f'data-testid="history-run-age-{TERMINAL_RUN_ID}"' in history  # Keep the age visible.
        assert f'data-testid="history-run-stale-{TERMINAL_RUN_ID}"' not in history  # Never mark a final row stale.
        assert 'data-testid="run-last-update-age"' in run_page  # Keep the final age visible on the run page.
        assert 'data-testid="run-stale-badge"' not in run_page  # Never mark a final run page stale.

    def test_malformed_time_is_unknown_on_both_pages(self, stale_client: FlaskClient) -> None:
        """Both pages show unknown and no stale badge for malformed time."""
        history = stale_client.get("/history").get_data(as_text=True)  # Render the malformed history row.
        run_page = stale_client.get(f"/runs/{UNKNOWN_RUN_ID}").get_data(as_text=True)  # Render the same run.
        assert f'data-testid="history-run-age-{UNKNOWN_RUN_ID}"' in history  # Keep the history age hook present.
        assert f'data-testid="history-run-stale-{UNKNOWN_RUN_ID}"' not in history  # Fail closed on history.
        assert 'data-testid="run-last-update-age"' in run_page  # Keep the run age hook present.
        assert 'data-testid="run-stale-badge"' not in run_page  # Fail closed on the run page.
        assert ">unknown</span>" in history  # Show the required unknown history text.
        assert ">unknown</span>" in run_page  # Show the required unknown run page text.
