"""Keep issue 3158 browser proof local, owned, bounded, and strictly collected."""

import logging
import os
from collections.abc import Iterator

import pytest

from tests.support.wip_target_controls.browser import BrowserCallbacks, BrowserJourney
from tests.support.wip_target_controls.native import NativeScenario
from tests.support.wip_target_controls.portal import ControlledPortal, LocalPortalServer, OwnedOutputLifecycle

try:
    pytest.importorskip(
        "playwright.sync_api", reason="The Playwright package is absent, so browser proof is unavailable."
    )
except pytest.skip.Exception as error:
    if os.environ.get("UPGRADE_PORTAL_E2E_STRICT") == "1":
        raise pytest.UsageError(
            "The Playwright package is absent. Strict browser proof does not permit a skip."
        ) from error
    raise


@pytest.fixture
def wip_server(
    tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[LocalPortalServer]:
    """Start and remove only the owned general portal and its temporary outputs."""
    caplog.set_level(logging.INFO)
    scenario = NativeScenario(tmp_path, monkeypatch)
    scenario.install()
    scenario.seed_site_cache()
    server = LocalPortalServer(ControlledPortal(scenario))
    server.start()
    try:
        yield server
    finally:
        server.close()
        assert all(not thread.is_alive() for thread in server.resources())
        OwnedOutputLifecycle.close(scenario)


@pytest.fixture
def selector_callbacks(page) -> Iterator[BrowserCallbacks]:
    """Use the plugin-owned browser and native coverage without optional artifacts."""
    probe = BrowserCallbacks(page)
    try:
        yield probe
    finally:
        probe.close()


@pytest.fixture
def wip_journey(page, wip_server: LocalPortalServer, selector_callbacks: BrowserCallbacks) -> BrowserJourney:
    """Open the shipped controller after native coverage starts."""
    journey = BrowserJourney(page, wip_server)
    journey.open()
    return journey
