"""Pytest fixtures for MistHelper E2E browser tests.

Provides two testing strategies:
1. Flask test client (fast, no browser needed, runs in CI)
2. Gunicorn/Playwright (full browser tests, requires playwright install)

The Flask test client approach is preferred for CI reliability.
The Gunicorn approach is available for local Playwright testing.
"""

import os
import socket
import subprocess
import sys
import time

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
    return app


@pytest.fixture(scope="session")
def client(flask_app):
    """Flask test client for fast E2E-style tests without a browser."""
    return flask_app.test_client()


def _find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def gunicorn_server():
    """Start Gunicorn serving the MistHelper web UI on a random port.

    Yields the base URL (e.g., http://127.0.0.1:54321).
    Terminates the server after all tests complete.

    Only used for Playwright browser tests (not Flask test client tests).
    """
    port = _find_free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--bind",
            f"127.0.0.1:{port}",
            "--timeout",
            "30",
            "--workers",
            "1",
            "wsgi:app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"

    # Wait for server to be ready (max 10 seconds)
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.5)
    else:
        process.terminate()
        raise RuntimeError(f"Gunicorn failed to start on port {port}")

    yield base_url

    process.terminate()
    process.wait(timeout=5)
