"""Run actual CLI exporters through native SDK and local CSV boundaries."""

from __future__ import annotations

import csv
import json
import logging
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NoReturn
from unittest.mock import Mock

import pytest
import requests
from mistapi.__api_response import APIResponse

from src.config import runtime_settings
from src.config.config_utils import ConfigUtils
from src.config.source_dependency_resolver import SourceDependencyResolver
from src.export.data_exporter import DataExporter
from src.refactors.main_entrypoint import MainEntrypoint

logger = logging.getLogger(__name__)


class NativeMistSession:
    """Answer native SDK requests without credentials or network access."""

    @dataclass
    class HeldResponse:
        """Hold one real response while the operator changes a target."""

        reply: tuple[int, Any]
        arrived: threading.Event = field(default_factory=threading.Event)
        release: threading.Event = field(default_factory=threading.Event)

        def wait(self) -> tuple[int, Any]:
            """Require an explicit bounded release before the native response returns."""
            self.arrived.set()
            if not self.release.wait(15):
                raise TimeoutError("The controlled selector response did not receive its required release.")
            return self.reply

    def __init__(self) -> None:
        """Keep distinct site, device, client, and endpoint records."""
        self.calls: list[dict[str, Any]] = []
        self.sites = [
            {"id": "site-alpha", "name": "Lab Site", "address": "1 Lab Road"},
            {"id": "site beta%?&", "name": "Recovery <Site>", "address": "2 Lab Road"},
        ]
        self.devices = {
            "site-alpha": [
                dict(id="switch-alpha", mac="001122334455", name="Lab Switch", type="switch", model="EX4400"),
                dict(id="ap-alpha", mac="001122334466", name="Lab AP", type="ap", model="AP45"),
            ],
            "site beta%?&": [
                dict(id="switch-beta", mac="001122334477", name="Recovery <Switch>", type="switch", model="EX4100")
            ],
        }
        self.replies: dict[str, tuple[int, Any] | Exception | NativeMistSession.HeldResponse] = {}

    def mist_get(self, uri: str, query: dict[str, str]) -> APIResponse:
        """Count one real SDK request and return its native response."""
        logger.info("The controlled SDK receives request %d: %s", len(self.calls) + 1, uri)
        self.calls.append({"uri": uri, "query": dict(query)})
        override = self.replies.get(uri)
        if isinstance(override, NativeMistSession.HeldResponse):
            override = override.wait()
        if isinstance(override, Exception):
            logger.debug("The controlled SDK raises %s for %s", type(override).__name__, uri)
            raise override
        status, payload = override if override is not None else (200, self._payload(uri, query))
        response = self.response(uri, payload, status)
        logger.debug("The controlled SDK answered request %d with HTTP %d", len(self.calls), status)
        return response

    def _payload(self, uri: str, query: dict[str, str]) -> Any:
        """Return the native payload for the exact existing endpoint."""
        if uri == "/api/v1/orgs/controlled-org/sites":
            return deepcopy(self.sites)
        if uri.endswith("/devices"):
            site_id = uri.removeprefix("/api/v1/sites/").removesuffix("/devices")
            devices = self.devices.get(site_id, [])
            family = query.get("type", "ap")
            return deepcopy([device for device in devices if family == "all" or device["type"] == family])
        if uri.endswith("/vc"):
            return {"members": [{"serial": "CONTROLLED", "role": "master"}], "preprovisioned": False}
        payloads = {
            "/clients/search": {"results": [{"mac": "aabbccddeeff", "hostname": "Client"}], "total": 1},
            "/clients/sessions/search": {
                "results": [{"mac": "aabbccddeeff", "timestamp": 100, "ssid": "Lab"}],
                "total": 1,
            },
            "/stats/clients": [{"mac": "aabbccddeeff", "hostname": "Client", "rssi": -42}],
        }
        for suffix, payload in payloads.items():
            if uri.endswith(suffix):
                return deepcopy(payload)
        raise AssertionError(f"An unexpected SDK path reached the controlled boundary: {uri}")

    @staticmethod
    def response(uri: str, payload: Any, status: int = 200) -> APIResponse:
        """Construct the shipped SDK response with a real requests response."""
        raw = requests.Response()
        raw.status_code = status
        raw._content = json.dumps(payload).encode("utf-8")
        raw.headers["Content-Type"] = "application/json"
        response = APIResponse(raw, "https://controlled.invalid" + uri)
        assert response.status_code == status, "The native fixture lost its HTTP status."
        assert response.data == payload, "The native fixture did not parse the exact payload."
        assert response.next is None, "This bounded fixture must not request another page."
        return response


class ControlledExportBoundary:
    """Observe real local writes and count metadata without an external store."""

    def __init__(self) -> None:
        """Keep each actual endpoint and row set independently."""
        self.calls: list[dict[str, Any]] = []
        self.format_write = Mock(wraps=DataExporter._dispatch_format_write)
        self.csv_write = Mock(wraps=DataExporter.write_to_csv)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Keep real writer bodies active and replace only external routing."""
        logger.info("Installing 2 real local writer spies and 1 controlled external router")
        for name, value in (
            ("_router_initialized", True),
            ("_router", self),
            ("_dispatch_format_write", self.format_write),
            ("write_to_csv", self.csv_write),
        ):
            monkeypatch.setattr(DataExporter, name, value)
        logger.debug("Installed 2 observed writer boundaries and 1 offline router")

    def write(self, payload: list[dict[str, Any]], api_function_name: str) -> SimpleNamespace:
        """Record the writer boundary while the real local CSV write remains active."""
        logger.info("The controlled router records %d rows for %s", len(payload), api_function_name)
        self.calls.append({"endpoint": api_function_name, "rows": deepcopy(payload)})
        result = SimpleNamespace(
            success=True, records_written=len(payload), records_failed=0, backend="controlled-offline"
        )
        logger.debug("The controlled router recorded write %d without a store connection", len(self.calls))
        return result


class LiveHttpGuard:
    """Fail and count any accidental requests transport call."""

    def __init__(self) -> None:
        """Start the live transport count at zero."""
        self.calls: list[object] = []

    def deny(self, *arguments: Any, **keywords: Any) -> NoReturn:
        """Reject the request before any socket or credential operation."""
        self.calls.append((arguments, keywords))
        raise AssertionError(f"Checked {len(self.calls)} forbidden live HTTP calls. No live request is permitted.")


class NativeScenario:
    """Own the native transport, temporary output, and source runtime seams."""

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bind the proof to one temporary working directory."""
        self.root = root
        self.patch = monkeypatch
        self.session = NativeMistSession()
        self.router = ControlledExportBoundary()
        self.network = LiveHttpGuard()

    def install(self) -> None:
        """Use real source dependencies with controlled runtime state."""
        import MistHelper

        logger.info("Installing the controlled native boundaries for issue 3158")
        self.patch.chdir(self.root)
        for name, value in (
            ("DATA_DIR", str(self.root / "data")),
            ("MISTHELPER_STANDALONE", "false"),
            ("WEBHOOK_ENABLED", "false"),
            ("PORTAL_STREAM_MAX_SECONDS", "1"),
        ):
            self.patch.setenv(name, value)
        self.patch.setattr(SourceDependencyResolver, "_root_module", MistHelper)
        for name, value in (("apisession", self.session), ("org_id", "controlled-org"), ("output_format", "csv")):
            self.patch.setattr(MainEntrypoint.context, name, value)
        self.patch.setattr(ConfigUtils, "_org_id_cache", "controlled-org")
        self.patch.setattr(runtime_settings, "LAST_SELECTED_SITE_ID", None)
        self.router.install(self.patch)
        self.patch.setattr(requests.Session, "send", self.network.deny)
        logger.debug("Installed 1 native transport, 1 local writer, 1 fake router, and 1 live HTTP guard")

    def seed_site_cache(self) -> None:
        """Keep the actual site prompt and CSV reader without a cache-generation substitute."""
        logger.info("Writing the controlled SiteList.csv prompt cache")
        success = DataExporter.write_with_format_selection(
            self.session.sites, "SiteList.csv", api_function_name="listOrgSites"
        )
        assert success is True, "The real local writer did not create the prompt cache."
        assert len(self.router.calls) == 1, "The prompt cache must use exactly one exporter write."
        self.router.calls.clear()
        self.router.format_write.reset_mock()
        self.router.csv_write.reset_mock()
        logger.debug("Wrote 2 controlled site rows and excluded 1 cache write from the run ledger")

    @staticmethod
    def actions() -> dict[str, Any]:
        """Use the exact current CLI menu entries, not handler stand-ins."""
        import MistHelper

        return {number: MistHelper.menu_actions[number] for number in ("63", "64", "65", "11")}

    def read_rows(self, filename: str) -> list[dict[str, str]]:
        """Read the actual owned CSV and refuse a path outside its output directory."""
        root = (self.root / "data").resolve()
        output = (root / filename).resolve()
        assert output.is_relative_to(root), "The observed output escaped the owned data directory."
        logger.info("Reading the actual local output %s", output.name)
        with output.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        logger.debug("Read %d actual output rows from %s", len(rows), output.name)
        return rows
