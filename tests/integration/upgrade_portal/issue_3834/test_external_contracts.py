"""Prove the external call shapes and startup isolation for issue 3834."""

from __future__ import annotations  # Keep annotations independent from import order.

import importlib  # Load the factory only after external boundaries are trapped.
import inspect  # Bind the production methods instead of permissive mocks.
import socket  # Count every name lookup and outbound connection.
import subprocess  # Prevent container and process startup.
from collections import Counter  # Report the number of trapped external calls.
from functools import partial  # Bind a safe call name to each trap.
from typing import Any  # Hold mixed values from external libraries.

import arango.client  # Patch the supported document-store client constructor.
import dotenv  # Block environment-file loading before WSGI import.
import mistapi.api.v1.orgs.inventory as inventory_api  # Check the current inventory call.
import mistapi.api.v1.sites.devices as devices_api  # Check the current upgrade calls.
import mistapi.api.v1.sites.stats as stats_api  # Check the current statistics call.
import pytest  # Report contract failures through the project test runner.
import redis  # Patch the supported Redis constructor.
from arango.collection import StandardCollection  # Bind the actual Arango collection methods.
from flask import Flask  # The factory contract returns a Flask application.

from src.foundation.persistence.db import DatabaseConfig  # Bind the actual database configuration call.
from src.foundation.persistence.db.router import DatabaseRouter  # Bind the actual router contract.
from src.interfaces.portals.upgrade_portal.audit.logger import AuditLogger  # Bind the real audit contract.
from src.interfaces.portals.upgrade_portal.capture import devices  # Exercise real HTTP-status handling.
from src.operations.exporting.export.data_exporter import DataExporter  # Trap the shared exporter boundary.

SITE_ID = "site-0f3a9c2b7d1e4f5a8b6c0d2e4f6a8b0c"  # A stable non-production site key.
ORG_ID = "org-0f3a9c2b7d1e4f5a8b6c0d2e4f6a8b0c"  # A stable non-production organization key.


class FakeApiResponse:
    """Hold one failed SDK response without creating a network request."""

    def __init__(self, status: int) -> None:
        """Store the status that the SDK reader must refuse."""
        self.status_code = status  # The reader uses this field from mistapi.
        self.headers: dict[str, str] = {}  # A refused response has no page count.
        self.next: None = None  # A refused response has no next page.
        self.data: list[Any] = []  # A refused response contains no device rows.


class PortalStartupTrap:
    """Count attempted network, store, environment, exporter, and process calls."""

    def __init__(self) -> None:
        """Start with no external call attempts."""
        self.attempts: Counter[str] = Counter()  # Each boundary has its own visible count.

    def refuse(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Count and reject one external action."""
        self.attempts[name] += 1  # Count before raising so a swallowed fault stays visible.
        raise AssertionError(f"Startup attempted external action: {name}")  # Keep the error free of secrets.

    def block_dotenv(self, *args: Any, **kwargs: Any) -> bool:
        """Block environment-file reads without failing WSGI startup."""
        self.attempts["dotenv_blocked"] += 1  # A test must never read a local credential file.
        return False  # Keep the process environment as the only test configuration.

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Trap every external action before importing the WSGI factory."""
        monkeypatch.setattr(socket.socket, "connect", partial(self.refuse, "network"))
        monkeypatch.setattr(socket, "create_connection", partial(self.refuse, "network"))
        monkeypatch.setattr(socket, "getaddrinfo", partial(self.refuse, "dns"))
        monkeypatch.setattr(dotenv, "load_dotenv", self.block_dotenv)  # Do not read a credential file.
        monkeypatch.setattr(arango.client, "ArangoClient", partial(self.refuse, "arangodb"))  # Block database clients.
        monkeypatch.setattr(redis, "Redis", partial(self.refuse, "redis"))  # Block Redis clients.
        monkeypatch.setattr(subprocess, "run", partial(self.refuse, "process"))  # Block container startup.
        monkeypatch.setattr(DataExporter, "write_with_format_selection", partial(self.refuse, "exporter"))
        monkeypatch.setattr(inventory_api, "getOrgInventory", partial(self.refuse, "mist"))
        monkeypatch.setattr(stats_api, "listSiteDevicesStats", partial(self.refuse, "mist"))
        monkeypatch.setattr(devices_api, "upgradeSiteDevices", partial(self.refuse, "mist"))
        monkeypatch.setattr(devices_api, "getSiteDeviceUpgrade", partial(self.refuse, "mist"))
        monkeypatch.setattr(devices_api, "cancelSiteDeviceUpgrade", partial(self.refuse, "mist"))


def test_supported_call_signatures_reject_legacy_arguments() -> None:
    """Bind exact Mist, router, and audit arguments to their installed methods."""
    session = object()  # The signature check never calls the cloud.
    config = DatabaseConfig(standalone_mode=True)  # The router constructor never opens a connection here.
    document = {"_key": "run-1"}  # A non-production document proves the write argument shape.
    inspect.signature(inventory_api.getOrgInventory).bind(session, ORG_ID, site_id=SITE_ID, vc=True, limit=1000)
    inspect.signature(stats_api.listSiteDevicesStats).bind(session, SITE_ID, type="all", limit=1000)
    inspect.signature(devices_api.upgradeSiteDevices).bind(session, SITE_ID, body=document)
    inspect.signature(devices_api.getSiteDeviceUpgrade).bind(session, SITE_ID, "upgrade-1")
    inspect.signature(devices_api.cancelSiteDeviceUpgrade).bind(session, SITE_ID, "upgrade-1")
    inspect.signature(DatabaseRouter).bind(config, {"upgrade_runs": {"type": "natural_pk", "primary_key": ["run_id"]}})
    inspect.signature(DatabaseRouter.write).bind(object(), data=[document], api_function_name="upgrade_runs")
    inspect.signature(StandardCollection.insert).bind(object(), document, overwrite=True)
    inspect.signature(StandardCollection.get).bind(object(), "run-1")
    inspect.signature(StandardCollection.update).bind(object(), {"_key": "run-1", "status": "cancelled"})
    inspect.signature(AuditLogger.log_operation).bind(object(), "upgrade_start", "operator@example.com", details={})
    with pytest.raises(TypeError):  # The real router must reject the old keyword-only shape.
        inspect.signature(DatabaseRouter.write).bind(object(), collection="upgrade_runs", document=document)
    with pytest.raises(TypeError):  # The real Arango collection requires one document argument.
        inspect.signature(StandardCollection.insert).bind(object(), collection="upgrade_runs", document=document)


def test_http_client_and_server_errors_remain_failed_reads(monkeypatch: Any) -> None:
    """Reject both HTTP error classes instead of treating their bodies as data."""
    for status in (401, 503):  # Exercise one client refusal and one server failure.
        monkeypatch.setattr(
            stats_api,
            "listSiteDevicesStats",
            lambda *args, code=status, **kwargs: FakeApiResponse(code),
        )
        result = devices.read_device_statistics(object(), SITE_ID, page_limit=10)
        assert result.records == []  # A failed response supplies no device evidence.
        assert result.partial_reasons  # The capture records why its statistics read failed.
        assert result.partial_reasons[0]["http_status"] == status  # The evidence keeps the actual HTTP status.


def test_wsgi_and_factory_startup_make_no_external_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Trap external actions before importing and starting the default app."""
    trap = PortalStartupTrap()  # One counter covers every external boundary.
    trap.install(monkeypatch)  # Install all traps before the WSGI import.
    factory = importlib.import_module("src.interfaces.portals.upgrade_portal.app.factory")
    application = factory.create_app()  # The default path must install construction instructions only.
    wsgi_capture = importlib.import_module("wsgi_capture")  # Import also executes the real WSGI factory path.
    importlib.reload(wsgi_capture)  # Force the WSGI entry point through the active traps.
    assert isinstance(application, Flask)  # The no-argument factory still returns a Flask app.
    assert isinstance(wsgi_capture.app, Flask)  # WSGI startup still exports its application.
    assert trap.attempts["dotenv_blocked"] == 2  # Both WSGI loads use the safe no-op.
    assert sum(trap.attempts.values()) == 2  # Only the two blocked file reads may occur.
