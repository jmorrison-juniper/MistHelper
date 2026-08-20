"""Shared fixtures for the contract tests of the upgrade capture portal.

Why:
    A contract test drives a real route through the Flask test client and
    checks the status code and the response body against the documented
    contract. See ``specs/1823-upgrade-capture-portal/contracts/http-api.md``.
    These fixtures give the application, the test client, a fake Mist cloud
    read surface, and a fake storage surface. No contract test needs a browser,
    a cloud account, an ArangoDB server, or a Redis server.

    No fixture reads the ``.env`` file. Every credential value below is an
    obviously fake string, and no fixture writes a token value into a log
    record.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest

logger = logging.getLogger(__name__)

# WHY: An obviously fake value. FR-009 forbids a real token value anywhere in
# the test suite, and a reader sees at once that this string is not a secret.
FAKE_API_TOKEN = "fake-api-token-for-tests-only"

# WHY: Fixed identifiers keep every canned payload and every route path in
# agreement, so a test reads one identifier and never invents a second one.
FAKE_ORG_ID = "00000000-0000-0000-0000-0000000000aa"
FAKE_SITE_ID = "00000000-0000-0000-0000-0000000000bb"

# WHY: `wiring.install_seams` fills both seams, because a real deployment needs
# them. A contract test drives the routes alone, so `portal_app` empties both.
LAUNCHER_KEY = "RUN_LAUNCHER"  # Hands one prepared record to the run driver.
STOP_RUNNER_KEY = "STOP_RUNNER"  # Performs the cancel work of one stop.

# WHY: The smallest payload that still holds each field a route reads. A
# contract test checks the response shape, so a large payload adds no value.
#
# WHY `listOrgSiteStats` is absent and must stay absent: the three device
# count tests in `test_select.py` divide the work. Two tests set their own
# statistics payload. The third test reads the empty answer that this map
# gives for an absent name. An entry here makes that third test fail. If a
# test needs a statistics record, set the record inside that one test.
# The real read pages by offset with `limit` and `page`. It answers a plain
# array, so any such payload stays a plain list. The read carries no
# `results` envelope and no `search_after` cursor.
DEFAULT_PAYLOADS: dict[str, Any] = {
    "listOrgSites": [{"id": FAKE_SITE_ID, "name": "Test Site", "org_id": FAKE_ORG_ID}],
    "listSiteDevices": [{"mac": "5c5b350e0001", "type": "ap", "model": "AP45", "site_id": FAKE_SITE_ID}],
    "listSiteDevicesStats": [{"mac": "5c5b350e0001", "status": "connected", "uptime": 1200, "version": "0.14.1"}],
}


class FakeMistApi:
    """Canned stand-in for the Mist cloud read surface.

    Why:
        A contract test checks the shape of the portal answer, not the shape
        of the cloud answer. This stub returns one small fixed payload for
        each read and records every call, so a test can assert on the call
        parameters without a network request.
    """

    def __init__(self) -> None:
        """Create the stub with an empty call log."""
        self.calls: list[tuple[str, dict[str, Any]]] = []  # WHY: Records the endpoint name and the parameters.
        self.payloads: dict[str, Any] = dict(DEFAULT_PAYLOADS)  # WHY: A copy lets one test edit one answer.

    def read(self, name: str, **parameters: Any) -> Any:
        """Return the canned payload for one cloud read.

        Args:
            name: The name of the cloud endpoint the route called.
            **parameters: The call parameters the route passed.

        Returns:
            The canned payload, or an empty list for an unknown name.
        """
        self.calls.append((name, dict(parameters)))  # WHY: A copy stops a later edit of the caller dictionary.
        return self.payloads.get(name, [])  # WHY: An unknown read returns empty, never an error.


class FakeCaptureStorage:
    """In-memory stand-in for the capture store and the run store.

    Why:
        A route writes a capture or a run, then reads the key back to prove
        the write. A contract test needs that behavior with no ArangoDB
        server and no comma-separated value fallback file.
    """

    def __init__(self) -> None:
        """Create an empty storage surface."""
        self.captures: dict[str, dict[str, Any]] = {}  # WHY: Holds each capture document by capture identifier.
        self.runs: dict[str, dict[str, Any]] = {}  # WHY: Holds each run document by run identifier.

    def write(self, collection: str, key: str, document: dict[str, Any]) -> bool:
        """Store one document in one collection.

        Args:
            collection: Either ``captures`` or ``runs``.
            key: The natural primary key of the document.
            document: The document body.

        Returns:
            True after a write, or False for an unknown collection.
        """
        target = self.captures if collection == "captures" else self.runs if collection == "runs" else None
        if target is None:  # WHY: An unknown collection is a caller defect, not a storage fault.
            return False
        target[key] = dict(document)  # WHY: A copy stops a later edit of the caller dictionary.
        return True

    def read(self, collection: str, key: str) -> dict[str, Any] | None:
        """Return one stored document.

        Args:
            collection: Either ``captures`` or ``runs``.
            key: The natural primary key of the document.

        Returns:
            The stored document, or None when the key or the collection is absent.
        """
        target = self.captures if collection == "captures" else self.runs if collection == "runs" else {}
        return target.get(key)  # WHY: The read-back check needs the stored copy.


@pytest.fixture
def fake_api_token() -> str:
    """Return an obviously fake cloud token.

    Why:
        A test that builds a signed-in session needs a token shaped value.
        The fixture never reads the ``.env`` file, so no real credential can
        enter a test run or a log record.

    Returns:
        A fake token string.
    """
    return FAKE_API_TOKEN


@pytest.fixture
def fake_org_id() -> str:
    """Return the organization identifier that every canned payload uses.

    Why:
        A route path and a payload must agree on one identifier. One fixture
        gives both, so no test invents a second value.

    Returns:
        The fixed organization identifier.
    """
    return FAKE_ORG_ID


@pytest.fixture
def fake_site_id() -> str:
    """Return the site identifier that every canned payload uses.

    Why:
        A route path and a payload must agree on one identifier. One fixture
        gives both, so no test invents a second value.

    Returns:
        The fixed site identifier.
    """
    return FAKE_SITE_ID


@pytest.fixture
def fake_mist_api() -> FakeMistApi:
    """Return the fake Mist cloud read surface.

    Why:
        Every selection route and every capture route reads the cloud. This
        fixture answers each read with a small fixed payload, so a contract
        test needs no cloud account.

    Returns:
        A fresh stub for one test.
    """
    return FakeMistApi()


@pytest.fixture
def fake_capture_storage() -> FakeCaptureStorage:
    """Return the fake storage surface.

    Why:
        A route writes a capture or a run and then reads the key back. This
        fixture gives that behavior with no ArangoDB server.

    Returns:
        A fresh storage surface for one test.
    """
    return FakeCaptureStorage()


@pytest.fixture
def portal_app() -> Any:
    """Return the capture portal application in test mode.

    Why:
        A contract test drives the real routes, so it needs the real
        application. The factory module does not exist at this phase of the
        work. The guarded import skips the test instead of a collection
        error, so the whole suite still collects.

        The fixture empties the run driver seam and the cancel seam.
        `wiring.install_seams` fills both, because a real deployment needs
        both. `start_upgrade_run` starts a real thread that outlives the test
        and reaches for the Mist cloud. A test that wants either seam injects
        its own recorder, and the injected object then wins.

    Returns:
        The Flask application with the test settings applied.
    """
    factory = pytest.importorskip(  # WHY: The factory arrives at task T027.
        "src.upgrade_portal.app.factory",
        reason="The capture portal application factory is not built yet.",
    )
    logger.info("Build the capture portal application for a contract test")  # WHY: ASCII, %s style, no credential.
    app = factory.create_app()
    app.config.update(TESTING=True)  # WHY: Test mode reports the real exception instead of a 500 page.
    app.config[LAUNCHER_KEY] = None  # WHY: No contract test may start a real run driver thread.
    app.config[STOP_RUNNER_KEY] = None  # WHY: No contract test may send a real cancel to the cloud.
    return app


@pytest.fixture
def portal_client(portal_app: Any) -> Iterator[Any]:
    """Return a Flask test client for the capture portal.

    Why:
        The test client drives a route with no server and no browser, so a
        contract test runs fast and reports a precise failure. The context
        manager keeps the session across the requests of one test.

    Args:
        portal_app: The application from the sibling fixture.

    Yields:
        The Flask test client.
    """
    with portal_app.test_client() as client:  # WHY: The context manager holds the session open.
        yield client
