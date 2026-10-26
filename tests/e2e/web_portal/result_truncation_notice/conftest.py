"""Serve controlled CSV results through the native portal without Mist access."""

import csv
import logging
import threading
from collections.abc import Iterator

import pytest
from flask import Flask
from playwright.sync_api import Browser, Page
from werkzeug.serving import make_server

from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions

logger = logging.getLogger(__name__)
LONG_VALUE = ("OSPF adjacency detail " + "neighbor reachable " * 12)[:246]


@pytest.fixture(scope="module")
def notice_app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Flask]:
    """Keep all output under a temporary directory for native preview tests."""
    directory = tmp_path_factory.mktemp("notice-output")
    for name, value in (("Adjacency.csv", LONG_VALUE), ("Short.csv", "up")):
        with (directory / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["device_name", "details"])
            writer.writerows([f"switch-{index:02}", value if index < 25 else "up"] for index in range(30))
    logger.info("Creating the local result notice portal")
    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="local-org")
    app.config.update(TESTING=True, DATA_DIR=str(directory))
    logger.debug("Created the result notice portal with two CSV files")
    yield app
    WebPortalApp.shutdown_app(app)


@pytest.fixture(scope="module")
def notice_url(notice_app: Flask) -> Iterator[str]:
    """Serve only the isolated test app and stop its exact server on completion."""
    server = make_server("127.0.0.1", 0, notice_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the local result notice server")
    thread.start()
    logger.debug("Started the result notice server on port %s", server.server_port)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=10)
    server.server_close()


@pytest.fixture
def notice_page(browser: Browser, notice_url: str) -> Iterator[Page]:
    """Use a private context so CI capture options cannot record result artifacts."""
    with browser.new_context() as context:
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{notice_url}/operations", wait_until="networkidle")
        page.wait_for_selector(".op-item", state="attached")
        page.evaluate("OperationResults.showForRun(['Adjacency.csv', 'Short.csv'])")
        page.locator("#resultsBody tr").first.wait_for()
        yield page
        page.evaluate("OperationResults.reset()")
        assert errors == [], errors
