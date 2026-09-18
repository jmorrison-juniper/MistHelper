"""Pytest fixtures for the MistHelper end-to-end tests of the legacy web portal.

The fixtures below build a Flask test client, which needs no browser and no
server process. That client is fast and it runs in continuous integration.

Why this file starts no server:
    A server fixture here once started Gunicorn, and no test ever used it.
    Gunicorn imports `fcntl`, which Windows does not hold, so that fixture could
    not run on a developer workstation at all. The upgrade portal tests start
    their own server in `tests/e2e/upgrade_portal/conftest.py`, which selects
    Waitress on Windows and Gunicorn elsewhere.
"""

import logging
import os

import pytest

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

E2E_TIMEOUT_SECONDS = 120  # Bound each E2E test, so one browser wait cannot stop the suite for hours.


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add a per-test timeout to every E2E item.

    Why:
        Browser tests can wait on a page, a browser, or a server. A missing
        boundary can then block a full suite for hours. This hook applies only
        inside the ``tests/e2e`` tree, so unit and contract tests keep their
        existing timing.

    Args:
        config: The active pytest configuration.
        items: The E2E test items that pytest collected under this directory.
    """
    logger.info("Checking the E2E timeout guard")  # Log before the plugin check.
    timeout_is_ready = config.pluginmanager.hasplugin("timeout")  # Confirm that pytest-timeout loaded.
    logger.debug("E2E timeout plugin loaded: %s", timeout_is_ready)  # Log the plugin state.
    if not timeout_is_ready:  # A missing guard must not let browser tests hang.
        logger.info("Adding E2E skip marks because pytest-timeout is missing")  # Log before the skip marks.
        skip_mark = pytest.mark.skip(  # Build one skip mark with the exact missing guard.
            reason="pytest-timeout is not installed, so the E2E timeout guard cannot run."
        )
        for item in items:  # Apply the skip to every collected E2E item.
            item.add_marker(skip_mark)  # Skip unsafe E2E tests instead of letting them run unbounded.
        logger.debug("Added E2E skip marks to %d items", len(items))  # Log the number of skipped items.
        return  # Stop before the timeout mark, because the plugin is not present.
    logger.info("Adding per-test timeout marks to E2E tests")  # Log before the timeout marks.
    timeout_mark = pytest.mark.timeout(E2E_TIMEOUT_SECONDS)  # Use the declared pytest-timeout plugin.
    marked_count = 0  # Count items that this hook protects.
    for item in items:  # Visit each collected E2E item once.
        if any(mark.name == "timeout" for mark in item.iter_markers()):  # Keep a narrower explicit timeout.
            continue  # Preserve an item-specific timeout from a test module.
        item.add_marker(timeout_mark)  # Bound this E2E test with the default guard.
        marked_count += 1  # Count the guard that this hook added.
    logger.debug("Added E2E timeout marks to %d items", marked_count)  # Log the number of protected items.


@pytest.fixture(scope="session")
def flask_app():
    """Create a Flask app instance for testing without API authentication.

    Uses the static menu registry (no MistHelper import needed).
    Returns the Flask app with test config applied.
    """
    os.environ.setdefault("PORTAL_TITLE", "MistHelper Test")
    os.environ.setdefault("PORTAL_THEME", "dark")

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    menu_actions = build_static_menu_actions()
    app = WebPortalApp.create_app(
        apisession=None,
        menu_actions=menu_actions,
        org_id="test-org-id",
    )
    app.config["TESTING"] = True
    yield app  # Hand the app to every test in the session.
    # Stop the heartbeat thread and drain the pool now, while streams are still open.
    # Without this, the atexit hook still runs, but only after pytest closes its
    # own capture streams, so its shutdown log lines fail with a closed-file error.
    WebPortalApp.shutdown_app(app)


@pytest.fixture(scope="session")
def client(flask_app):
    """Flask test client for fast E2E-style tests without a browser."""
    return flask_app.test_client()
