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

import os

import pytest


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
