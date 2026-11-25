"""A fake shell and a fake organization for the integration tests of the CLI flow.

Why:
    The integration tests run the real portal batch services: the real picker,
    the real request checker, the real session manager, the real batch runner,
    and the real artifact writer. Only two things are fake: the Mist REST calls
    (the sites, the devices, and the device status) and the shell on a switch.
    The fake shell answers the fixed command with a synthetic reply, so the whole
    path from the menu to the CSV file runs without a network and without a
    credential.
"""

from __future__ import annotations

import logging
import threading
import time
from types import SimpleNamespace
from typing import Any

import mistapi
import pytest

from src.mist.realtime.websocket_streams.live.sessions.manager.factory import RunnerFactory, SharedTransport
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies

PROMPT = "mist@ex>"  # A prompt that the batch runner accepts.
BAD_REPLY = "<rpc-reply><not-a-chassis/></rpc-reply>"  # A reply with no chassis inventory.


def uuid(number: int) -> str:
    """Return an invented identifier that passes the UUID rule of the service."""
    return f"00000000-0000-4000-8000-{number:012d}"


class FakeShells:
    """The scripted behavior of every fake shell, and a record of what the shells did."""

    def __init__(self) -> None:
        """Start with every switch answering well."""
        self.behavior: dict[str, str] = {}  # Device identifier to ok, bad_xml, or silent.
        self.replies: dict[str, str] = {}  # Device identifier to its reply text.
        self.commands: list[tuple[str, str]] = []  # Each command that a shell received, with its device.
        self.opened = 0  # How many shells were opened.
        self.open = 0  # How many shells are open now.
        self.peak = 0  # The most shells that were open at the same time.
        self.hold_seconds = 0.0  # How long a shell takes to answer, to make shells overlap.
        self.lock = threading.Lock()  # The shells run on worker threads.

    def factory(self) -> type[RunnerFactory]:
        """Return a runner factory whose single runners are the fake shells."""
        shells = self  # The class below closes over the script.

        class Factory(RunnerFactory):
            """The production factory, with the fake shell in place of the real shell runner."""

            def __init__(self, apisession: object, profile: object = None, settings: StreamSettings | None = None):
                """Build the parts that the base class builds, without a Mist endpoint."""
                self._settings = settings or StreamSettings.from_environment()
                self._transport = SharedTransport(self._settings.max_sessions)
                self._logger = StructuredTransportLogger(logging.getLogger(__name__))
                self._apisession = apisession

            def _select_single(self, request: Any, sink: Any) -> Any:
                """Return the fake shell for one target."""
                return FakeShellRunner(shells, request, sink)

        return Factory


class FakeShellRunner:
    """One fake shell: it prints a banner and a prompt, then answers the fixed command."""

    def __init__(self, shells: FakeShells, request: Any, sink: Any) -> None:
        """Keep the script, the device, and the sink that receives the bytes."""
        self._shells = shells
        self._device = request.target("device_id")  # The batch checked this identifier.
        self._sink = sink
        self._live = False  # True between start and stop.

    def start(self) -> None:
        """Open the shell and print the banner and the prompt."""
        with self._shells.lock:
            self._shells.opened += 1
            self._shells.open += 1
            self._shells.peak = max(self._shells.peak, self._shells.open)
        self._live = True
        self._sink.mark_live()
        self._sink.add_bytes(f"Welcome to Junos\r\n{{master:0}}\r\n{PROMPT} ".encode())
        self._sink.mark_input_ready()

    def stop(self) -> None:
        """Close the shell once."""
        with self._shells.lock:
            if self._live:
                self._live = False
                self._shells.open -= 1

    def send_input(self, text: str) -> None:
        """Answer a command the way a switch does, or stay silent."""
        command = text.rstrip("\n")
        self._shells.commands.append((self._device, command))
        behavior = self._shells.behavior.get(self._device, "ok")
        if behavior == "silent":  # No answer, so the runner times out on this switch.
            return
        time.sleep(self._shells.hold_seconds)  # Let other shells overlap with this one.
        if behavior == "bad_xml":
            payload = BAD_REPLY
        else:
            payload = self._shells.replies.get(self._device) or HardwareReplies.single_switch(self._device[-6:])
        self._sink.add_bytes(f"{command}\r\n{payload}\r\n\r\n{{master:0}}\r\n{PROMPT} ".encode())


class FakeOrganization:
    """Fake the three Mist REST calls that discovery uses, and record the ledger organization at each call."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, ledger: Any = None) -> None:
        """Patch ``listOrgSites``, ``listSiteDevices``, and ``listSiteDevicesStats``."""
        self.org_sites: dict[str, list[tuple[str, str]]] = {}  # Organization identifier to (site id, site name).
        self.devices: dict[str, list[dict[str, Any]]] = {}  # Site identifier to the device records.
        self.statuses: dict[str, list[str]] = {}  # Device identifier to its statuses in call order.
        self.log: list[tuple[str, str, str | None]] = []  # Each call: name, organization or site, ledger organization.
        self.failures: dict[str, Any] = {}  # A call name, or ``listOrgSites:<org id>``, to a replacement answer.
        self._ledger = ledger
        self._seen: dict[str, int] = {}  # How many status calls each device has had.
        monkeypatch.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", self._list_sites)
        monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", self._list_devices)
        monkeypatch.setattr(mistapi.api.v1.sites.stats, "listSiteDevicesStats", self._list_stats)

    def add(self, org_id: str, site: tuple[str, str], devices: list[tuple[str, str, str, str]]) -> None:
        """Add one site to an organization with its devices, given as (id, name, type, model)."""
        self.org_sites.setdefault(org_id, []).append(site)
        self.devices[site[0]] = [
            {"id": device_id, "name": name, "type": kind, "model": model, "mac": f"5c5b35{index:06x}"}
            for index, (device_id, name, kind, model) in enumerate(devices, start=1)
        ]

    def calls(self, name: str) -> list[tuple[str, str, str | None]]:
        """Return the log entries of one call name."""
        return [entry for entry in self.log if entry[0] == name]

    def _note(self, name: str, key: str, *failure_keys: str) -> Any:
        """Record the call and return the planned failure, if any."""
        self.log.append((name, key, getattr(self._ledger, "org_id", None)))
        for failure_key in (*failure_keys, name):
            if failure_key in self.failures:
                return self.failures[failure_key]
        return None

    @staticmethod
    def _page(rows: list[dict[str, Any]]) -> SimpleNamespace:
        """Return a good SDK page."""
        return SimpleNamespace(status_code=200, data=rows, next=None)

    def _list_sites(self, session: Any, org_id: str, **_kwargs: Any) -> Any:
        """Answer the organization site list."""
        failure = self._note("listOrgSites", org_id, f"listOrgSites:{org_id}")
        return failure or self._page(
            [{"id": site_id, "name": name} for site_id, name in self.org_sites.get(org_id, [])]
        )

    def _list_devices(self, session: Any, site_id: str, **_kwargs: Any) -> Any:
        """Answer the device list of one site."""
        failure = self._note("listSiteDevices", site_id)
        return failure or self._page(list(self.devices.get(site_id, [])))

    def _list_stats(self, session: Any, site_id: str, **_kwargs: Any) -> Any:
        """Answer the device status of one site. Each call advances each device to its next status."""
        failure = self._note("listSiteDevicesStats", site_id)
        if failure:
            return failure
        rows = []
        for device in self.devices.get(site_id, []):
            planned = self.statuses.get(device["id"], ["connected"])
            index = self._seen.get(device["id"], 0)
            rows.append({"id": device["id"], "status": planned[min(index, len(planned) - 1)]})
            self._seen[device["id"]] = index + 1
        return self._page(rows)
