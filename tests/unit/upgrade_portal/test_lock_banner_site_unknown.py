"""The lock banner names a fifth state for a page that cannot name its site.

Why:
    Issue #2097 reports that a page with no site identifier showed the same
    sentence as a page that could not reach the lock store. The two causes
    differ. A page with no site holds no lock key, so no read can tell the
    state. A page that names its site but cannot read the store is a store
    fault. FR-118 asks the banner to name the missing site, and FR-119 keeps
    the ``unknown`` sentence for the store fault alone.

    FR-120 asks a test to cover a run page whose run resolves to no run. That
    page names no site, so it reads the fifth state as well.

No network:
    Every test drives a bare application and injects the lock reader through
    the ``SITE_LOCK_READER`` seam. No test opens a socket, reads the ``.env``
    file, or names a real credential.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Callable  # The injected lock reader is a callable seam.

import pytest  # The test framework.
from flask import Flask  # The smallest application that can hold the seam.

from src.upgrade_portal.app.routes import upgrade  # The run page owns ``run_lock_banner``.
from src.upgrade_portal.app.routes.select import (  # The banner builder and the three store words.
    LOCK_READER_KEY,
    LOCK_STATE_FREE,
    LOCK_STATE_UNKNOWN,
    lock_banner_context,
)

# WHY: The identifier shape that the cloud uses. Obviously fake values.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"

# WHY: An obviously fake value. FR-009 forbids a real credential inside the suite.
FAKE_SECRET = "fake-flask-secret-key-for-tests-only"

# WHY: The wire value that Delta S1 fixes for the fifth banner state.
SITE_UNKNOWN = "site_unknown"

STATE_KEY = "lock_state"  # The key that `build_lock_banner` writes the state under.

LockReader = Callable[[str, list[str]], dict[str, str | None]]  # The shape of the injected seam.


def reader_that_raises() -> LockReader:
    """Build a lock reader that fails as an unreachable Redis server does.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Fail as a stopped lock store does.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            Nothing, because this reader always raises.

        Raises:
            RuntimeError: Always, because the store cannot answer.
        """
        raise RuntimeError(f"the lock store cannot answer about {org_id} and {site_ids}")  # The dead store.

    return read  # The test writes this callable into the application configuration.


def reader_that_answers(holders: dict[str, str | None]) -> LockReader:
    """Build a lock reader that answers one fixed index.

    Args:
        holders: The holder of each site that the store knows about.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Return the fixed index, unchanged.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            The index that the test built.
        """
        return dict(holders)  # The organization and the site list play no part in this stand-in.

    return read  # The test writes this callable into the application configuration.


@pytest.fixture
def portal_app() -> Flask:
    """Return a bare application that holds the lock reader seam.

    Returns:
        The application, ready for a request context.
    """
    app = Flask(__name__)  # The smallest application that can read the configuration.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET)  # Test settings alone.
    app.config[LOCK_READER_KEY] = reader_that_answers({})  # A quiet store unless a test says more.
    return app  # Each test drives this application through a request context.


def test_an_empty_site_reads_the_site_unknown_state(portal_app: Flask) -> None:
    """A page with no site identifier reads the fifth state, not a store fault."""
    with portal_app.test_request_context():  # The builder reads the session and the configuration.
        banner = lock_banner_context(ORG_ID, "")  # The page named its organization but no site.

    assert banner[STATE_KEY] == SITE_UNKNOWN  # The banner names the missing site plainly.


def test_a_present_site_with_a_dead_store_still_reads_unknown(portal_app: Flask) -> None:
    """A named site that the store cannot answer keeps the reserved word."""
    portal_app.config[LOCK_READER_KEY] = reader_that_raises()  # The store is unreachable for this test.

    with portal_app.test_request_context():  # The read fails open inside this context.
        banner = lock_banner_context(ORG_ID, SITE_ID)  # The page names its site, so the store fault shows.

    assert banner[STATE_KEY] == LOCK_STATE_UNKNOWN  # A store fault keeps the reserved word.
    assert banner[STATE_KEY] != SITE_UNKNOWN  # The fifth state never covers a store fault.


def test_an_empty_organization_but_named_site_reads_unknown(portal_app: Flask) -> None:
    """A page that names its site reports a store word even without an organization."""
    with portal_app.test_request_context():  # The builder skips the store read without an organization.
        banner = lock_banner_context("", SITE_ID)  # The lock key needs both halves, so the store cannot answer.

    assert banner[STATE_KEY] == LOCK_STATE_UNKNOWN  # A named site never reads the fifth state.
    assert banner[STATE_KEY] != SITE_UNKNOWN  # The fifth state waits for an empty site alone.


def test_a_named_site_with_a_free_store_reads_free(portal_app: Flask) -> None:
    """A named site that the store reports empty reads free, so pages agree."""
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({SITE_ID: None})  # The store answered no lock.

    with portal_app.test_request_context():  # The read reaches the configured store.
        banner = lock_banner_context(ORG_ID, SITE_ID)  # The page names its site and the store answers.

    assert banner[STATE_KEY] == LOCK_STATE_FREE  # The true state agrees with every other page.


def test_a_run_that_resolves_to_no_run_reads_site_unknown(portal_app: Flask) -> None:
    """A run page whose run resolves to no run names the missing site."""
    with portal_app.test_request_context():  # The run banner builder reads the session and the store.
        banner = upgrade.run_lock_banner({})  # An absent run leaves the organization and the site empty.

    assert banner[STATE_KEY] == SITE_UNKNOWN  # The page names the missing site, not a store fault.
