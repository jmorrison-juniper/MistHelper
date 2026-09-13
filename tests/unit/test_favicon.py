"""Verify that both web portals declare and serve a valid favicon.

Why:
    Browsers request `/favicon.ico` even when the page declares an SVG icon.
    These tests keep that direct path present for both Flask portals.
"""

from __future__ import annotations

import atexit
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask

from src.upgrade_portal.app import factory
from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions


@pytest.fixture
def main_portal() -> Iterator[Flask]:
    """Build and clean up the main portal for the focused favicon test.

    Why:
        The real factory registers the static folder and the favicon route.
        This fixture then proves the shipped route behavior.
    """
    app = WebPortalApp.create_app(  # Build the real main portal with its normal static folder.
        apisession=None,
        menu_actions=build_static_menu_actions(),
        org_id="test-org-id",
    )
    app.config["TESTING"] = True  # Surface unexpected route errors directly during the focused test.
    yield app  # Provide the configured portal to the test.
    event_bus = app.config["EVENT_BUS"]  # Keep the callback reference for test-process cleanup.
    WebPortalApp.shutdown_app(app)  # Stop the portal heartbeat after the test completes.
    atexit.unregister(event_bus.stop)  # Remove the callback that would log after pytest closes its stream.


def _assert_favicon(client: Any, page_path: str) -> None:
    """Check the page declaration and the served favicon response.

    Why:
        The direct route and the declared asset must both answer. This keeps
        older clients and newer browsers on the same shipped icon.
    """
    page = client.get(page_path)  # Render the portal page that must declare its icon.
    assert page.status_code == 200  # Require a complete page before checking its markup.
    assert 'rel="icon"' in page.get_data(as_text=True)  # Confirm the browser has an explicit icon URL.
    assert 'href="/static/favicon.svg"' in page.get_data(as_text=True)  # Confirm the URL uses the shipped asset.

    icon = client.get("/static/favicon.svg")  # Request the declared icon through Flask static handling.
    assert icon.status_code == 200  # Require the asset to exist in the deployed static folder.
    assert icon.content_type.startswith("image/svg+xml")  # Require the browser-compatible SVG MIME type.
    assert icon.data.startswith(b"<svg")  # Confirm the response contains the expected SVG document.

    direct_icon = client.get("/favicon.ico")  # Request the path that clients ask for without reading markup.
    assert direct_icon.status_code == 200  # Require the direct path to stop the repeated 404 log entry.
    assert direct_icon.content_type.startswith("image/svg+xml")  # Require the MIME type of the shipped SVG asset.
    assert "public" in direct_icon.headers["Cache-Control"]  # Permit shared caches to keep the small icon.
    assert "max-age=86400" in direct_icon.headers["Cache-Control"]  # Keep the direct icon cached for one day.
    assert direct_icon.data == icon.data  # Confirm both paths serve the same shipped icon.


def test_main_portal_declares_and_serves_favicon(main_portal: Flask) -> None:
    """The main portal must serve the favicon that its base template declares.

    Why:
        The data browsing portal must stop the automatic favicon 404 entry.
    """
    _assert_favicon(main_portal.test_client(), "/")  # Exercise the main portal through its real test fixture.


def test_upgrade_portal_declares_and_serves_favicon() -> None:
    """The upgrade portal must serve the favicon that its layout declares.

    Why:
        The upgrade capture portal must stop the automatic favicon 404 entry.
    """
    app = factory.create_app()  # Build the production upgrade portal without a network request.
    app.config["TESTING"] = True  # Surface unexpected route errors directly during the focused test.
    _assert_favicon(app.test_client(), "/auth/signin")  # Exercise a public page that extends the layout.
