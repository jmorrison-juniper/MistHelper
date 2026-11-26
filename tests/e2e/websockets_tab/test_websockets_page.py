"""Browser journey for the WebSockets page.

Why:
    Issue #3551 needs proof that the new tab lets an operator start, view,
    limit, lock, and interact with WebSocket-style sessions in a browser.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import base64  # The fake terminal read route returns base64 terminal bytes.
import json  # The fake keeps JSON message text, like the real buffer.
import logging  # Keep browser test records under this module.
import socket  # Find an unused local port.
import threading  # Serve Flask and fake stream output beside the browser.
import time  # Let fake runners emit messages on a short timer.
from collections.abc import Iterator  # Type fixtures and download streams.
from dataclasses import dataclass, field  # Store fake session state clearly.
from pathlib import Path  # Save screenshots under the test artifact folder.
from types import SimpleNamespace  # Build fake SDK answers.
from typing import Any  # Type Playwright objects without importing private types.

import pytest  # Use fixtures and Playwright integration.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # The fake report can refuse.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message import StreamMessage
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import MessagePage  # The fake keeps real records.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import (
    CsvPreviewer,
    CsvRenderer,
)  # The fake report uses the real renderer and the real page reader.

logger = logging.getLogger(__name__)  # Keep this test module visible in logs.

pytest.importorskip("playwright", reason="playwright is absent, so the browser journey cannot run")  # Browser guard.

READY_TIMEOUT_MS = 15000  # Bound every browser wait.
# The container mounts data/, so the screenshots stay in the test-artifacts/ folder instead.
ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "test-artifacts" / "websockets"  # Git ignores this folder.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # Fake organization identifier.
DEFAULT_HARDWARE_SCOPE = {"mode": "organization", "organization_count": 1, "failed_count": 0}  # One organization.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # First fake site identifier.
SITE_ID_2 = "22222222-3333-4444-5555-666666666666"  # Second fake site identifier.
DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # Fake device identifier.
ROUTE_TABLE_TEXT = (
    '{"columns":[{"id":"Destination","display_name":"Destination"},{"id":"Gateway","display_name":"Gateway"}],'
    '"rows":[{"Destination":"10.0.0.0/24","Gateway":"192.168.1.1"}],"status":"SUCCESS","message":""}'
)  # A route table as the device sends it, as JSON text.
PING_OUTPUT_CHUNKS = (
    "reply from 8.8.8.8\napbr_SL-Only.inet6.0: 1 d",
    "estinations, 1 routes (1 active, 0 holddown, 0 hidden)\nNext ",
    "line stays complete.\n",
)  # The fake cloud splits one word and one line at unstable message boundaries.
CSV_COLUMNS = ["org_name", "site_name", "device_name", "item_type", "item_serial_number"]  # The fake report columns.


def make_csv_report(rows: int = 6) -> bytes:
    """Render a fake combined report with one row for each invented switch."""
    items = [
        {
            "org_name": "Alpha Org",
            "site_name": "HQ" if index % 2 else "Branch",
            "device_name": f"ex-{index:03d}",
            "item_type": ("Chassis", "FPC", "Fan")[index % 3],
            "item_serial_number": f"SN{index:05d}",
        }
        for index in range(1, rows + 1)
    ]
    return CsvRenderer.render(items, CSV_COLUMNS, 50_000_000)  # The same bytes that a real run publishes.


@dataclass
class BrowserSession:
    """One fake browser-visible session."""

    session_id: str  # Stable session identifier.
    kind: str  # channel, utility, or shell.
    key: str  # Catalog key.
    title: str  # Card title.
    output: str  # json, lines, packets, or terminal.
    safety: str  # read, capture, change, or shell.
    messages: list[StreamMessage] = field(default_factory=list)  # Buffered message records.
    state: str = "live"  # Current state.
    live: bool = True  # Live sessions count toward the limit.
    reason: str = ""  # Plain end reason.
    input_ready: bool = True  # Shell input is ready in the fake.


class FakeWebSocketServices:
    """Fake WebSocket service with timer-driven runners."""

    def __init__(self) -> None:
        """Build the fake catalog and empty session store."""
        self._lock = threading.Lock()  # Protect sessions while timer threads write.
        self._sessions: dict[str, BrowserSession] = {}  # Active and ended sessions.
        self.start_bodies: list[dict[str, object]] = []  # Record submitted forms for local browser assertions.
        self._next_id = 1  # Deterministic identifiers make tests easy to read.
        self.shell_inputs: list[dict[str, object]] = []  # Record shell input forms.
        self.terminal_data: dict[str, bytes] = {}  # Store fake terminal byte history by session.
        self.message_gap = False  # Let a browser journey expose a reconnect buffer gap.
        self.batch_target_calls: list[tuple[str | None, str, str]] = []  # Record scoped target reads.
        self.batch_preview_body: dict[str, object] | None = None  # Keep the last safe preview request.
        self.batch_start_body: dict[str, object] | None = None  # Keep the admitted preview-only request.
        self.batch_progress: dict[str, dict[str, object]] = {}  # Store target progress by public parent.
        self.batch_targets_data: dict[str, list[dict[str, object]]] = {}  # Store a frozen target list.
        self.hardware_scope: dict[str, object] = dict(DEFAULT_HARDWARE_SCOPE)  # The scope line of the hardware preview.
        self.hardware_concurrency: int | None = None  # The catalog default for the hardware action.
        self.csv_report: bytes = make_csv_report()  # The combined report that the table preview reads.
        self.csv_error: StreamRequestError | None = None  # A planned refusal of the table preview.
        self.csv_preview_calls: list[dict[str, object]] = []  # Record what the browser asked for.
        self.terminal_reads: list[str] = []  # Record each session that the page reads as a terminal.
        lifecycle = SimpleNamespace(
            start=self.start_session, list=self.list_sessions, stop=self.stop_session, shutdown=self.shutdown
        )  # Group fake session lifecycle behavior.
        self.sessions = SimpleNamespace(
            lifecycle=lifecycle,
            messages=SimpleNamespace(read=self.read_messages),
            batches=SimpleNamespace(
                preview=self.preview_batch,
                start=self.start_batch,
                summary=self.batch_summary,
                targets=self.batch_target_page,
            ),
        )  # Group fake session behavior.
        self.catalog = SimpleNamespace(payload=self.catalog_payload)  # Group fake catalog behavior.
        self.artifacts = SimpleNamespace(
            delete=self.delete_session, download=self.download_session, csv_preview=self.csv_preview
        )  # Group fake artifact behavior.
        self.terminal = self  # Expose direct fake terminal behavior.
        self.pickers = SimpleNamespace(
            site=self, related=self, batch=SimpleNamespace(targets=self.batch_targets, sites=self.batch_sites)
        )  # Group fake picker behavior.

    def reset(self) -> None:
        """Clear sessions before one browser story."""
        with self._lock:  # Timer threads can still be ending.
            self._sessions.clear()  # Remove all prior sessions.
            self.start_bodies.clear()  # Remove prior submitted forms.
            self._next_id = 1  # Reset identifiers.
            self.shell_inputs.clear()  # Remove prior shell input.
            self.terminal_data.clear()  # Remove prior terminal bytes.
            self.message_gap = False  # Start each browser journey without lost buffered messages.
            self.batch_target_calls.clear()  # Remove prior target discovery calls.
            self.batch_preview_body = None  # Remove the previous preview request.
            self.batch_start_body = None  # Remove the previous batch admission request.
            self.batch_progress.clear()  # Remove prior parent progress.
            self.batch_targets_data.clear()  # Remove prior frozen target lists.
            self.hardware_scope = dict(DEFAULT_HARDWARE_SCOPE)  # Restore the one-organization scope line.
            self.hardware_concurrency = None  # Restore the page default.
            self.csv_report = make_csv_report()  # Restore the small default report.
            self.csv_error = None  # Restore a working preview.
            self.csv_preview_calls.clear()  # Remove prior preview requests.
            self.terminal_reads.clear()  # Remove prior terminal reads.

    def catalog_payload(self) -> dict[str, object]:
        """Return the catalog shown by the page."""
        return {
            "ready": True,
            "reason": None,
            "flags": {},
            "limits": {"max_sessions": 2, "idle_seconds": 120, "capture_seconds": 3600}
            | ({"hardware_concurrency": self.hardware_concurrency} if self.hardware_concurrency else {}),
            "channels": [self._channel(), self._device_command_channel()],
            "utilities": self._utilities(),
        }  # Catalog.

    def start_session(self, body: object) -> dict[str, object]:
        """Start one fake session or return a contract-like refusal."""
        if not isinstance(body, dict):  # The page must send a JSON object.
            return {"error": "The request body is not valid.", "code": "bad_request"}  # Defensive answer.
        with self._lock:  # Session limit and identifier allocation must be atomic.
            self.start_bodies.append(dict(body))  # Keep the exact request fields submitted by the browser.
            live = [session.title for session in self._sessions.values() if session.live]  # Current live titles.
            if len(live) >= 2:  # The fake limit is two sessions.
                from src.mist.realtime.websocket_streams.intake.fields.error import (
                    StreamRequestError,
                )  # Import only on refusal.

                raise StreamRequestError(
                    "limit_reached", "The live session limit is reached.", {"live": live}
                )  # Limit.
            session = self._new_session(body)  # Build the fake session.
            self._sessions[session.session_id] = session  # Store it before the runner starts.
            if session.output == "terminal":  # Terminal sessions read through the new terminal route.
                self.terminal_data[session.session_id] = b"Welcome to Fake Mist Shell\r\ndevice> "  # Initial banner.
        self._start_runner(session)  # Start timer output after the session exists.
        return self._payload(session)  # Return the session card payload.

    def list_sessions(self) -> dict[str, object]:
        """Return all fake sessions."""
        with self._lock:  # Copy while no timer mutates the store.
            sessions = [self._payload(session) for session in self._sessions.values()]  # Session payloads.
            live_count = sum(1 for session in self._sessions.values() if session.live)  # Live count.
        return {"sessions": sessions, "limits": {"max_sessions": 2, "live_count": live_count}}  # List payload.

    def read_messages(self, session_id: str, after: int, _limit: int) -> MessagePage:
        """Return messages after the given sequence."""
        with self._lock:  # Copy while timer threads can write.
            session = self._sessions[session_id]  # The test always names a known session.
            messages = [message for message in session.messages if message.seq > after]  # New messages.
            next_after = messages[-1].seq if messages else after  # Highest returned sequence.
            payload = self._payload(session)  # Copy the session card state.
        return MessagePage(payload, messages, next_after, 1, self.message_gap)  # Expose deterministic gap state.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Stop one fake session."""
        with self._lock:  # Update state atomically.
            session = self._sessions[session_id]  # The browser stops a visible session.
            session.state = "stopped"  # Mark stopped.
            session.live = False  # Remove it from the live limit.
            session.reason = "The operator stopped the session."  # Plain reason.
            if session_id in self.batch_progress:
                self._stop_batch_targets(session_id)  # Mark pending work stopped without changing completed work.
            return self._payload(session)  # Return the stopped card.

    def _stop_batch_targets(self, session_id: str) -> None:
        """Stop queued and active fake targets while preserving completed outcomes."""
        rows = self.batch_targets_data[session_id]  # Read the parent target snapshot.
        for item in rows:
            if item["state"] in {"queued", "running"}:
                item["state"] = "stopped"  # Do not rewrite completed or failed outcomes.
        completed = sum(item["state"] == "completed" for item in rows)  # Count preserved terminal work.
        stopped = sum(item["state"] == "stopped" for item in rows)  # Count the stopped remainder.
        previous = self.batch_progress[session_id]  # Preserve the admitted worker limit.
        self.batch_progress[session_id] = {
            "status": "stopped",
            "target_count": len(rows),
            "concurrency": previous["concurrency"],
            "counts": {"queued": 0, "running": 0, "completed": completed, "stopped": stopped, "failed": 0},
            "artifact_status": "ready",
        }  # Return an internally consistent final summary.

    def send_input(self, session_id: str, body: object) -> dict[str, object]:
        """Accept shell input and echo a safe output line."""
        payload = body if isinstance(body, dict) else {}  # Keep only JSON objects.
        self.shell_inputs.append(payload)  # Prove line and key routes were used.
        with self._lock:  # Append output with a sequence number.
            session = self._sessions[session_id]  # The selected shell session.
            self._add_message(session, "text", "device> output accepted", None)  # Echo safe text only.
        return {"ok": True}  # Confirm input.

    def terminal(self) -> FakeWebSocketServices:
        """Return the fake terminal gateway object."""
        return self  # The blueprint calls read, send, and resize on this object.

    def read(self, session_id: str, after: int, _wait_seconds: float) -> dict[str, object]:
        """Return fake terminal bytes after one position."""
        self.terminal_reads.append(session_id)  # A batch parent must never reach this route.
        with self._lock:  # Copy terminal state while the fake runner can append bytes.
            session = self._sessions[session_id]  # The browser names a visible fake session.
            data = self.terminal_data.get(session_id, b"")  # A new terminal can have no bytes.
            chunk = data[after:] if after <= len(data) else b""  # Continue from the browser position.
            next_position = len(data) if after <= len(data) else after  # Keep the browser cursor stable.
        return {
            "data": base64.b64encode(chunk).decode("ascii"),
            "first": 0,
            "next": next_position,
            "gap": 0,
            "state": session.state,
            "reason": session.reason,
            "input_ready": True,
            "read_only": False,
            "expires_at": "2026-10-01T09:30:00Z",
        }  # Terminal read contract.

    def send(self, session_id: str, data: str) -> dict[str, object]:
        """Accept fake terminal input and append visible output."""
        self.shell_inputs.append({"data": data})  # Prove the new terminal body shape was used.
        with self._lock:  # Append output and keep terminal bytes in order.
            current = self.terminal_data.get(session_id, b"")  # Existing terminal bytes.
            self.terminal_data[session_id] = current + b"\r\nran: terminal input\r\n"  # Safe output text.
        return {"accepted": len(data.encode("utf-8")), "queued": False}  # Terminal input contract.

    def resize(self, _session_id: str, cols: int, rows: int) -> dict[str, object]:
        """Accept fake terminal size changes."""
        return {"cols": cols, "rows": rows}  # Terminal resize contract.

    def delete_session(self, _session_id: str) -> dict[str, object]:
        """Confirm delete for ended sessions."""
        return {"ok": True}  # The browser journey does not delete live sessions.

    def download_session(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return the fake session messages as JSON Lines."""
        with self._lock:  # Copy while timer threads can write.
            count = len(self._sessions[session_id].messages)  # Count messages for the stream.
        return "fake-session.jsonl", iter([f'{{"count":{count}}}\n'])  # Safe JSON Lines.

    def csv_preview(self, session_id: str, offset: int, limit: int, text: str) -> dict[str, object]:
        """Return one page of the fake report with the real page reader, or the planned refusal."""
        self.csv_preview_calls.append({"session_id": session_id, "offset": offset, "limit": limit, "text": text})
        if self.csv_error is not None:  # A story can plan a refusal, like a report that is too large.
            raise self.csv_error
        return CsvPreviewer.page(self.csv_report, offset, limit, text)  # The same answer as the portal service.

    def devices(self, _site_id: str) -> dict[str, object]:
        """Return one EX device for utility stories."""
        row = {"id": DEVICE_ID, "label": "EX Switch 1", "family": "ex", "detail": "EX4100"}  # Device row.
        return {"rows": [row], "total_count": 1, "reason": None}  # Picker payload.

    def sites(self) -> dict[str, object]:
        """Return the complete fake organization site list."""
        rows = [{"id": SITE_ID, "label": "HQ"}, {"id": SITE_ID_2, "label": "Branch"}]  # Stable site identities.
        return {"rows": rows, "total_count": len(rows), "reason": None}  # Complete picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return no maps for these stories."""
        return {"rows": [], "total_count": 0, "reason": f"The site {site_id} has no maps."}  # Empty picker.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return no assets for these stories."""
        return {"rows": [], "total_count": 0, "reason": f"The site {site_id} has no assets."}  # Empty picker.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return no SDK clients for these stories."""
        return {
            "rows": [],
            "total_count": 0,
            "reason": f"The map {map_id} in site {site_id} has no SDK clients.",
        }  # Empty.

    def mxedges(self, _site_id: str | None) -> dict[str, object]:
        """Return no Mist Edges for these stories."""
        return {"rows": [], "total_count": 0, "reason": "No Mist Edge is available."}  # Empty picker.

    def batch_targets(self, site_id: str | None, kind: str, key: str, _parents: dict[str, str]) -> dict[str, object]:
        """Return one site-scoped device for browser selection stories."""
        self.batch_target_calls.append((site_id, kind, key))  # Retain only the bounded operation scope.
        row = {
            "id": DEVICE_ID,
            "label": "EX Switch 1",
            "family": "ex",
            "detail": "EX4100",
            "site_id": site_id,
            "target_type": "device",
        }  # Keep one deterministic natural target.
        return {
            "rows": [row],
            "total_count": 1,
            "complete": True,
            "reason": None,
            "excluded": {"incompatible_family": 0},
            "scope": {"site_id": site_id},
        }  # Match the complete discovery response.

    def batch_sites(self, _kind: str, _key: str) -> dict[str, object]:
        """Return the complete organization rows for a selected catalog operation."""
        payload = self.sites()  # Reuse the full fake organization site list.
        payload["complete"] = True  # Mark every fake page as complete.
        payload["scope"] = {"organization": True}  # Preserve the organization target scope.
        return payload  # Match the operation-driven site response.

    def preview_batch(self, body: object) -> dict[str, object]:
        """Return a complete frozen target preview for one browser journey."""
        self.batch_preview_body = body if isinstance(body, dict) else {}  # Retain the request for assertions.
        if self.batch_preview_body.get("preset") == "ex-hardware-xml":
            selected_format = self.batch_preview_body.get("format", "xml")
            xml_only = selected_format in {"csv", "master-xml", "csv-master-xml"}  # A combined report reads XML.
            return {
                "preview_id": "hardware-preview",
                "expires_at": "2026-10-16T12:00:00Z",
                "scope_revision": self.batch_preview_body.get("scope_revision", 0),
                "preset": "ex-hardware-xml",
                "format": selected_format,
                "fixed_commands": [
                    "show chassis hardware detail | display xml | no-more",
                    "show chassis hardware detail | display json | no-more",
                ][: 1 if xml_only else 2],
                "scope": dict(self.hardware_scope),
                "site_selection": (
                    {"mode": "selected", "count": len(self.batch_preview_body["sites"]["ids"])}
                    if isinstance(self.batch_preview_body.get("sites"), dict)
                    else {"mode": "all"}
                ),  # The real service reports a count, so the page can name the site choice.
                "operation": {
                    "kind": "shell",
                    "key": "ex.createShellSession",
                    "name": "EX hardware inventory",
                    "safety": "shell",
                },
                "targets": [
                    {"target_key": "hardware-1", "target_id": "device-1", "label": "EX Switch 1"},
                    {"target_key": "hardware-2", "target_id": "device-2", "label": "EX Switch 2"},
                ],
                "target_count": 2,
                "excluded": {},
                "confirmation": {"required": True, "phrase": "RUN 2 TARGETS", "safety": "shell"},
                "limits": {"target_count": 1000, "concurrency": 3, "output_bytes": 67108864},
            }  # Keep the dedicated preset isolated from generic command controls.
        targets = [
            {
                "target_key": f"target-{index}",
                "target_id": f"device-{index}",
                "target_type": "device",
                "site_id": SITE_ID if index % 2 else SITE_ID_2,
                "site_label": "HQ" if index % 2 else "Branch",
                "label": f"EX Switch {index}",
            }
            for index in range(1, 102)
        ]  # Exercise a target list larger than the earlier display limit.
        return {
            "preview_id": "fake-preview",
            "expires_at": "2026-10-16T12:00:00Z",
            "scope_revision": self.batch_preview_body.get("scope_revision", 0),
            "operation": {
                "kind": "channel",
                "key": "site.stats.devices",
                "name": "Device statistics",
                "safety": "read",
            },
            "targets": targets,
            "target_count": len(targets),
            "excluded": {"incompatible_family": 2},
            "confirmation": {"required": False, "phrase": None, "safety": "read"},
            "limits": {"target_count": 1000, "concurrency": 1, "output_bytes": 67108864},
        }  # Return only safe preview fields.

    def start_batch(self, body: object) -> dict[str, object]:
        """Create one fake parent session and its queued target outcomes."""
        payload = body if isinstance(body, dict) else {}  # Keep the fake request shape bounded.
        self.batch_start_body = dict(payload)  # Verify the start request carries only the preview reference.
        session_id = "batch1"  # Use one stable public parent id.
        preview = self.batch_preview_body or {}  # The real summary names the preset and the format of the run.
        hardware = preview.get("preset") == "ex-hardware-xml"  # The hardware action opens a shell on each switch.
        session = (
            BrowserSession(
                session_id, "shell", "ex.createShellSession", "Multi Site: EX hardware inventory", "terminal", "shell"
            )
            if hardware
            else BrowserSession(
                session_id, "channel", "site.stats.devices", "Multi Site: Device statistics", "json", "read"
            )
        )  # The hardware parent has the public shape of the real one: a shell entry with the terminal output.
        with self._lock:  # Allocate the public session and its target state together.
            self._sessions[session_id] = session  # Store the parent for session list and message reads.
            self.batch_progress[session_id] = self._new_batch_progress(
                int(payload.get("concurrency", 1))
            )  # Model one active worker and a complete queued set.
            if hardware:
                self.batch_progress[session_id].update(preset=preview["preset"], format=preview.get("format", "xml"))
            self.batch_targets_data[session_id] = self._new_batch_targets()  # Keep target order frozen.
        return self._batch_payload(session)  # Return one parent with additive batch state.

    @staticmethod
    def _new_batch_progress(concurrency: int) -> dict[str, object]:
        """Build one running summary with a consistent initial target count."""
        return {
            "status": "running",
            "target_count": 101,
            "concurrency": concurrency,
            "counts": {"queued": 99, "running": 1, "completed": 1, "stopped": 0, "failed": 0},
            "artifact_status": "writing",
        }  # Model a mixed active and queued batch.

    @staticmethod
    def _new_batch_targets() -> list[dict[str, object]]:
        """Build a stable page of targets with one completed and one active result."""
        return [
            {
                "target_key": f"target-{index}",
                "target": {"target_id": f"device-{index}", "label": f"EX Switch {index}"},
                "state": "running" if index == 1 else "completed" if index == 2 else "queued",
                "started_at": None,
                "ended_at": None,
                "reason_code": None,
                "result_count": 0,
                "command_index": None,
                "completion": None,
            }
            for index in range(1, 102)
        ]  # Keep target order equal to the reviewed snapshot.

    def _batch_payload(self, session: BrowserSession) -> dict[str, object]:
        """Return a public session payload with its batch summary."""
        summary = self.batch_progress[session.session_id]  # Read the parent-owned summary.
        return dict(self._payload(session), mode="multi_site", batch=summary)  # Add only batch fields.

    def batch_summary(self, session_id: str) -> dict[str, object]:
        """Return one parent session with its current batch state."""
        with self._lock:  # Copy both values from the same fake snapshot.
            session = self._sessions[session_id]  # The route names the public parent.
            return dict(self._payload(session), mode="multi_site", batch=dict(self.batch_progress[session_id]))

    def batch_target_page(self, session_id: str, after: int, limit: int) -> dict[str, object]:
        """Return one stable target page from the fake parent snapshot."""
        rows = self.batch_targets_data[session_id]  # The frozen target order remains stable.
        page = rows[after : after + limit]  # Apply the server cursor and limit.
        next_after = after + len(page)  # Return the next target position.
        return {
            "targets": page,
            "next_after": next_after,
            "complete": next_after >= len(rows),
            "counts": self.batch_progress[session_id]["counts"],
        }  # Match the batch target-page contract.

    def shutdown(self) -> None:
        """Stop all fake sessions."""
        with self._lock:  # Stop sessions atomically.
            for session in self._sessions.values():  # Visit each fake session.
                session.live = False  # End the fake session.
                session.state = "stopped"  # Mark stopped.

    def _channel(self) -> dict[str, object]:
        """Return one channel catalog entry."""
        site_field = {"name": "site_id", "label": "Site", "kind": "uuid", "required": True, "picker": "sites"}  # Site.
        return {
            "key": "site.stats.devices",
            "scope": "site",
            "name": "Device statistics",
            "description": "Live device statistics.",
            "identifiers": [site_field],
            "repeatable": "site_id",
        }  # Channel.

    def _device_command_channel(self) -> dict[str, object]:
        """Return one channel with a site-scoped device target."""
        site_field = {"name": "site_id", "label": "Site", "kind": "uuid", "required": True, "picker": "sites"}
        device_field = {"name": "device_id", "label": "Device", "kind": "uuid", "required": True, "picker": "devices"}
        return {
            "key": "site.devices.cmd",
            "scope": "site",
            "name": "Device command events",
            "description": "Live command output for each selected device.",
            "identifiers": [site_field, device_field],
            "repeatable": "device_id",
        }  # Catalog metadata drives device choices.

    def _utilities(self) -> list[dict[str, object]]:
        """Return the fake utility catalog entries."""
        targets = [
            self._field("site_id", "Site", "uuid", "sites"),
            self._field("device_id", "Device", "uuid", "devices"),
        ]  # Targets.
        host = {"name": "host", "label": "Host", "kind": "host", "required": True, "default": "8.8.8.8"}  # Host field.
        count = {
            "name": "count",
            "label": "Count",
            "kind": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 100,
            "default": 3,
        }  # Count.
        packets = {
            "name": "num_packets",
            "label": "Packets",
            "kind": "integer",
            "minimum": 1,
            "maximum": 10000,
            "default": 5,
        }  # Packets.
        duration = {
            "name": "duration",
            "label": "Duration",
            "kind": "integer",
            "minimum": 60,
            "maximum": 3600,
            "default": 60,
        }  # Capture duration.
        return [
            self._utility("ex.ping", "Ping", "read", "lines", targets, [host, count], False),
            self._utility("ex.retrieveRoutes", "Routes", "read", "lines", targets, [], False),
            self._utility(
                "ex.remotePcap", "Packet capture", "capture", "packets", targets, [duration, packets], False
            ),  # Capture fields.
            self._utility("ex.bouncePort", "Bounce port", "change", "lines", targets, [], True),
            self._utility("ex.shell", "Remote shell", "shell", "terminal", targets, [], False),
        ]  # Utilities.

    def _field(self, name: str, label: str, kind: str, picker: str) -> dict[str, object]:
        """Return one identifier field."""
        return {"name": name, "label": label, "kind": kind, "required": True, "picker": picker}  # Field.

    def _utility(
        self,
        key: str,
        name: str,
        safety: str,
        output: str,
        targets: list[dict[str, object]],
        fields: list[dict[str, object]],
        locked: bool,
    ) -> dict[str, object]:
        """Return one utility entry."""
        return {
            "key": key,
            "family": "ex",
            "name": name,
            "description": name + " from a switch.",
            "safety": safety,
            "locked": locked,
            "output": output,
            "targets": targets,
            "fields": fields,
            "scope": "site",
        }  # Utility.

    def _new_session(self, body: dict[str, object]) -> BrowserSession:
        """Create one fake session from a start body."""
        session_id = f"fake{self._next_id}"  # Deterministic identifier.
        self._next_id += 1  # Advance for the next session.
        key = str(body.get("key") or "")  # Read the catalog key.
        kind = str(body.get("kind") or "utility")  # Read the request kind.
        output = (
            "json"
            if kind == "channel"
            else {"ex.ping": "lines", "ex.remotePcap": "packets", "ex.shell": "terminal"}.get(key, "lines")
        )  # View.
        safety = "read" if key != "ex.remotePcap" else "capture"  # Safety for the card.
        return BrowserSession(session_id, kind, key, self._title(key), output, safety)  # Session record.

    def _start_runner(self, session: BrowserSession) -> None:
        """Start the fake timer runner for one session."""
        thread = threading.Thread(target=self._run_messages, args=(session.session_id,), daemon=True)  # Runner.
        thread.start()  # Emit messages beside the browser.

    def _run_messages(self, session_id: str) -> None:
        """Emit fake messages for one session."""
        for index in range(3):  # Three messages are enough for the browser waits.
            time.sleep(0.1)  # A short delay proves polling without slowing the suite.
            with self._lock:  # Timer thread writes the session buffer.
                session = self._sessions.get(session_id)  # The session may have stopped.
                if session is None or not session.live:  # A stopped session emits no more messages.
                    return  # End the fake runner.
                self._emit_kind(session, index)  # Add one message by output kind.

    def _emit_kind(self, session: BrowserSession, index: int) -> None:
        """Append one message for the session output type."""
        if session.output == "packets":  # Packet view reads summaries.
            self._add_message(
                session, "packet", {"length": 64 + index}, "12:00 source destination tcp " + str(64 + index)
            )  # Packet.
        elif session.output == "terminal":  # Terminal view reads text.
            self._add_message(session, "text", "device> ready", None)  # Prompt.
        elif session.key == "ex.retrieveRoutes":  # The route utility sends a table as JSON text.
            self._add_message(session, "text", ROUTE_TABLE_TEXT, None)  # Route table.
        elif session.output == "lines":  # Line view reads text lines.
            self._add_message(session, "text", PING_OUTPUT_CHUNKS[index], None)  # Emit unstable command chunks.
        else:  # Channel view reads JSON.
            self._add_message(session, "json", {"site": session.title, "count": index}, None)  # JSON row.

    def _add_message(self, session: BrowserSession, kind: str, content: object, summary: str | None) -> None:
        """Append one message record with the next sequence number, like the real buffer."""
        seq = len(session.messages) + 1  # Sequence numbers start at one.
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"))  # The real buffer keeps JSON text.
        message = StreamMessage(
            seq, "2026-09-29T20:00:00Z", kind, content_json, len(content_json), False, "HQ", summary
        )  # Record.
        session.messages.append(message)  # Add the message to the buffer.

    def _payload(self, session: BrowserSession) -> dict[str, object]:
        """Return one session payload."""
        counters = {"received": len(session.messages), "dropped": 0, "shortened": 0, "bytes": 0}  # Counters.
        payload = {
            "session_id": session.session_id,
            "kind": session.kind,
            "key": session.key,
            "title": session.title,
            "output": session.output,
            "safety": session.safety,
            "state": session.state,
            "live": session.live,
            "reason": session.reason,
            "input_ready": session.input_ready,
            "terminal": session.output == "terminal",
            "started_at": "2026-09-29T20:00:00Z",
            "ended_at": None,
            "counters": counters,
            "rate_per_second": 1.0,
            "last_seq": len(session.messages),
        }  # Payload.
        if session.session_id in self.batch_progress:
            payload["mode"] = "multi_site"  # Mark only batch parents.
            payload["terminal"] = False  # The real service says so: the shells run on the targets, not on the parent.
            payload["batch"] = self.batch_progress[session.session_id]  # Add batch progress to session listings.
        return payload  # Preserve the existing session payload shape.

    def _title(self, key: str) -> str:
        """Return a title for one catalog key."""
        return {
            "site.stats.devices": "Device statistics - HQ and Branch",
            "ex.ping": "Ping - EX Switch 1",
            "ex.retrieveRoutes": "Routes - EX Switch 1",
            "ex.remotePcap": "Packet capture - EX Switch 1",
            "ex.shell": "Remote shell - EX Switch 1",
        }.get(
            key, key
        )  # Title.


@pytest.fixture(scope="module")
def fake_services() -> FakeWebSocketServices:
    """Return the fake services object shared by the server."""
    return FakeWebSocketServices()  # One fake backs the app fixture.


def free_port() -> int:
    """Return an unused local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # Ask the operating system for a port.
        probe.bind(("127.0.0.1", 0))  # Port zero means any free port.
        return int(probe.getsockname()[1])  # Return the selected port.


@pytest.fixture(scope="module")
def websocket_portal(fake_services: FakeWebSocketServices) -> Iterator[str]:
    """Serve the web portal with fake WebSocket services."""
    import mistapi  # Patch the site picker SDK seam.
    from werkzeug.serving import make_server  # Start an in-process server.

    from src.mist.realtime.websocket_streams.web.services.registry import (
        WebSocketServiceRegistry,
    )  # Inject the fake services.
    from web_portal.app import WebPortalApp  # Build the same app as the portal.
    from web_portal.menu_registry import build_static_menu_actions  # Supply normal menu actions.

    def list_sites(_session: object, _org_id: str) -> SimpleNamespace:
        """Return two sites for the multi-site picker."""
        rows = [{"id": SITE_ID, "name": "HQ"}, {"id": SITE_ID_2, "name": "Branch"}]  # Sites.
        return SimpleNamespace(status_code=200, data=rows)  # Model one successful SDK answer.

    with pytest.MonkeyPatch.context() as patcher:  # Undo SDK patches when the server stops.
        patcher.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)  # Patch site picker.
        app = WebPortalApp.create_app(SimpleNamespace(), build_static_menu_actions(), ORG_ID)  # Build app.
        app.config["TESTING"] = True  # Raise route errors during the test.
        app.config[WebSocketServiceRegistry.CONFIG_KEY] = fake_services  # Inject the fake service.
        server = make_server("127.0.0.1", free_port(), app, threaded=True)  # Bind a free port.
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # Serve beside Playwright.
        logger.info("Starting the WebSocket portal on port %d", server.server_port)  # Log server start.
        thread.start()  # Start the server loop.
        try:
            yield f"http://127.0.0.1:{server.server_port}"  # Give tests the base URL.
        finally:
            server.shutdown()  # Stop the server loop.
            thread.join(timeout=10)  # Wait for server thread exit.
            WebPortalApp.shutdown_app(app)  # Stop portal background threads.


@pytest.fixture(autouse=True)
def reset_fake(fake_services: FakeWebSocketServices) -> Iterator[None]:
    """Reset fake state before each story."""
    fake_services.reset()  # Remove prior sessions.
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure screenshot folder exists.
    yield  # Run the browser story.
    fake_services.reset()  # Stop sessions that the story left live.


def screenshot(page: Any, name: str) -> Path:
    """Save one full-page screenshot."""
    path = ARTIFACT_DIR / name  # Build the requested artifact path.
    page.evaluate("window.scrollTo(0, 0)")  # Keep the sticky navigation at the top of full-page shots.
    page.screenshot(path=str(path), full_page=True)  # Save visual evidence.
    return path  # Return the path for assertions and reports.


def open_page(page: Any, portal: str) -> None:
    """Open the WebSockets page and wait for the catalog."""
    page.goto(f"{portal}/websockets", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Open page.
    page.get_by_test_id("nav-websockets").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Nav item.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").wait_for(
        state="visible", timeout=READY_TIMEOUT_MS
    )  # Catalog.


def choose_device(page: Any) -> None:
    """Choose the fake site and device in the start form."""
    page.locator('[data-testid="ws-field-site_id"]').select_option(SITE_ID)  # Choose site.
    page.locator('[data-testid="ws-field-device_id"]').select_option(DEVICE_ID)  # Choose device.


def test_channel_stream_with_multi_site_selection(page: Any, websocket_portal: str) -> None:
    """US1: a channel stream starts with two sites and shows JSON messages."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").click()  # Choose the channel.
    page.locator('[data-testid="ws-field-site_id"]').select_option([SITE_ID, SITE_ID_2])  # Choose two sites.
    page.get_by_test_id("ws-start-button").click()  # Start the stream.
    page.get_by_test_id("ws-session-title").wait_for(timeout=READY_TIMEOUT_MS)  # Session card.
    page.locator('[data-testid="ws-output"]').get_by_text('"count"').nth(0).wait_for(timeout=READY_TIMEOUT_MS)  # JSON.
    shot = screenshot(page, "01-channel-stream.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_channel_reconnect_gap_notice(page: Any, websocket_portal: str, fake_services: FakeWebSocketServices) -> None:
    """Show no warning for a complete reconnect and a warning after a buffer gap."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").click()  # Choose the channel.
    page.locator('[data-testid="ws-field-site_id"]').select_option(SITE_ID)  # Choose one site.
    page.get_by_test_id("ws-start-button").click()  # Start the stream.
    notice = page.get_by_test_id("ws-message-gap")  # Read the accessible reconnect warning.
    notice.wait_for(state="hidden", timeout=READY_TIMEOUT_MS)  # A complete buffer has no gap warning.
    fake_services.message_gap = True  # Simulate a reconnect after the message buffer dropped output.
    notice.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # The next poll must report the gap.
    shot = screenshot(page, "01b-channel-reconnect-gap.png")  # Keep readable warning evidence.
    assert shot.exists()  # The screenshot was written.


def test_read_only_ping_journey(page: Any, websocket_portal: str) -> None:
    """US2: a read-only ping shows output lines."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.ping").click()  # Choose ping.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start ping.
    page.locator('[data-testid="ws-output"]').get_by_text("reply from 8.8.8.8").nth(0).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Output.
    shot = screenshot(page, "02-ping-lines.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_command_output_preserves_boundaries_and_filter_matches(page: Any, websocket_portal: str) -> None:
    """Issue #3723: command chunks show as complete lines and filter as one stream."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.ping").click()  # Choose a line-output utility.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start the split command output.
    output = page.get_by_test_id("ws-output")  # Scope all assertions to the command output.
    output.get_by_text("Next line stays complete.").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for all chunks.
    text = output.inner_text()  # Read the joined command stream.
    assert "1 destinations, 1 routes" in text  # The word boundary survives the cloud split.
    assert "Next line stays complete." in text  # The line boundary survives the cloud split.
    assert "#2 HQ" not in text  # A message header does not interrupt the command line.
    page.get_by_test_id("ws-message-filter").fill("destinations")  # Filter for the word that spans chunks.
    output.get_by_text("apbr_SL-Only.inet6.0: 1 destinations, 1 routes").wait_for(timeout=READY_TIMEOUT_MS)
    filtered = output.inner_text()  # Read the filtered complete line.
    shot = screenshot(page, "08-command-output-boundaries.png")  # Keep UI evidence for the repaired flow.
    assert "Next line stays complete." not in filtered  # The filter hides nonmatching complete lines.
    assert shot.exists()  # The screenshot was written.


def test_packet_capture_journey(page: Any, websocket_portal: str, fake_services: FakeWebSocketServices) -> None:
    """US3: a capture shows packet rows."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.remotePcap").click()  # Choose capture.
    choose_device(page)  # Choose site and device.
    duration = page.get_by_test_id("ws-field-duration")  # Read the capture duration field.
    assert duration.get_attribute("min") == "60"  # Show the minimum duration in the form.
    assert duration.get_attribute("max") == "3600"  # Show the maximum duration in the form.
    duration.fill("120")  # Select a duration above the old fixed limit.
    page.get_by_test_id("ws-start-button").click()  # Start capture.
    page.locator('[data-testid="ws-output"]').get_by_text("source destination tcp").nth(0).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Packet.
    submitted = fake_services.start_bodies[-1]["parameters"]  # Read the local fake request.
    assert isinstance(submitted, dict) and submitted["duration"] == "120"  # HTML submits numeric fields as text.
    shot = screenshot(page, "03-packet-capture.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_session_limit_message(page: Any, websocket_portal: str) -> None:
    """US4: the page shows the live session titles when the limit is reached."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.ping").click()  # Choose ping.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start first session.
    page.get_by_test_id("ws-start-button").click()  # Start second session.
    page.get_by_test_id("ws-start-button").click()  # Ask for one too many.
    page.get_by_text("The live session limit is reached.").wait_for(timeout=READY_TIMEOUT_MS)  # Limit message.
    shot = screenshot(page, "04-session-limit.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_locked_change_utility(page: Any, websocket_portal: str) -> None:
    """US5: a locked change utility shows the lock and disables start."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.bouncePort").click()  # Choose locked utility.
    page.get_by_text("PORTAL_WS_ENABLE_CHANGES").wait_for(timeout=READY_TIMEOUT_MS)  # Lock warning.
    assert page.get_by_test_id("ws-start-button").is_disabled()  # Locked start cannot run.
    shot = screenshot(page, "05-locked-change.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_shell_uses_terminal_panel(page: Any, websocket_portal: str, fake_services: FakeWebSocketServices) -> None:
    """US6: a shell uses the xterm panel and sends the new terminal body shape."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.shell").click()  # Choose shell.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-confirmation-input").fill("EX Switch 1")  # Confirm the shell.
    page.get_by_test_id("ws-start-button").click()  # Start shell.
    page.get_by_test_id("ws-terminal-panel").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Terminal panel.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus the terminal emulator.
    page.keyboard.type("show version")  # Send text through xterm onData.
    page.keyboard.press("Enter")  # Send the carriage return through xterm.
    terminal_output = page.get_by_test_id("ws-terminal-screen")  # Scope the echo check to xterm output.
    terminal_output.get_by_text("ran: terminal input").nth(0).wait_for(timeout=READY_TIMEOUT_MS)  # Output echo.
    shot = screenshot(page, "06-shell-terminal.png")  # Keep evidence.
    has_data = any("data" in record for record in fake_services.shell_inputs)  # Check new terminal body shape.
    has_old_shape = any("line" in record or "key" in record for record in fake_services.shell_inputs)  # Old shape.
    assert has_data is True  # The new body shape reached the fake.
    assert has_old_shape is False  # The old line and key shapes are gone.
    assert shot.exists()  # The screenshot was written.


def test_route_table_shows_columns(page: Any, websocket_portal: str) -> None:
    """US2: a table that the device sends as JSON text shows as aligned columns."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.retrieveRoutes").click()  # Choose the route utility.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start the route read.
    output = page.locator('[data-testid="ws-output"]')  # The message view.
    output.get_by_text("10.0.0.0/24").nth(0).wait_for(timeout=READY_TIMEOUT_MS)  # The table row shows.
    text = output.inner_text()  # Read the drawn view text.
    shot = screenshot(page, "07-route-table.png")  # Keep evidence.
    assert "Destination  Gateway" in text  # The header cells show in aligned columns.
    assert '"columns"' not in text  # The raw JSON text does not show.
    assert shot.exists()  # The screenshot was written.


def test_scope_tabs_preserve_single_site_form(page: Any, websocket_portal: str) -> None:
    """Keep the current form state when the operator changes scope tabs."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    single_tab = page.get_by_test_id("ws-single-site-tab")  # Read the current workflow tab.
    multi_tab = page.get_by_test_id("ws-multi-site-tab")  # Read the new workflow tab.
    assert single_tab.get_attribute("aria-selected") == "true"  # The current workflow starts selected.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").click()  # Select one current operation.
    multi_tab.click()  # Change tabs without submitting or canceling the operation.
    page.get_by_test_id("ws-multi-site-panel").wait_for(state="visible")  # Show the multi-site controls.
    single_tab.click()  # Return to the current workflow.
    page.locator("#wsSingleSitePanel").wait_for(state="visible")  # Restore the single-site panel.
    assert single_tab.get_attribute("aria-selected") == "true"  # Report the selected tab state.
    assert multi_tab.get_attribute("aria-selected") == "false"  # Keep the other tab unselected.
    assert page.locator("#wsSelectedTitle").inner_text() == "Device statistics"  # Preserve the pending selection.


def test_multi_site_operation_loads_complete_site_choices(page: Any, websocket_portal: str) -> None:
    """Derive organization site choices from the selected catalog operation."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-multi-site-tab").click()  # Open the separate Multi Site workflow.
    page.get_by_test_id("ws-batch-operation").select_option("channel:site.stats.devices")  # Choose site scope.
    status = page.get_by_test_id("ws-batch-site-status")  # Read the accessible discovery state.
    status.get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for complete site discovery.
    page.get_by_test_id("ws-batch-sites").select_option("selected")  # Select an explicit site subset.
    options = page.locator("#wsBatchSiteOptions")  # Read the multi-select options.
    options.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Show choices only for selected mode.
    assert options.locator("option").count() == 2  # Keep every discovered natural key.


def test_multi_site_operation_loads_site_scoped_devices(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """Load catalog-driven device targets only for selected organization sites."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-multi-site-tab").click()  # Open the Multi Site workflow.
    page.get_by_test_id("ws-batch-operation").select_option("channel:site.devices.cmd")  # Choose device scope.
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Wait for complete site discovery.
    page.get_by_test_id("ws-batch-sites").select_option("selected")  # Request an explicit site subset.
    page.locator("#wsBatchSiteOptions").select_option(SITE_ID)  # Select one organization site.
    status = page.get_by_test_id("ws-batch-target-status")  # Read the operation target state.
    status.get_by_text("1 eligible resource(s).").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for device discovery.
    options = page.get_by_test_id("ws-batch-target-options")  # Read verified device choices.
    assert options.locator("option").count() == 1  # Do not include devices from the other site.
    assert "HQ" in options.locator("option").first.inner_text()  # Keep site context in the label.
    assert fake_services.batch_target_calls[-1] == (SITE_ID, "channel", "site.devices.cmd")
    # The newest request uses only the selected organization site.


def test_multi_site_preview_reviews_full_target_list_and_stops_batch(page: Any, websocket_portal: str) -> None:
    """Review every resolved target and stop a fake parent without Mist access."""
    open_page(page, websocket_portal)  # Load the local WebSockets test portal.
    page.get_by_test_id("ws-multi-site-tab").click()  # Open the Multi Site workflow.
    page.get_by_test_id("ws-batch-operation").select_option(
        "channel:site.stats.devices"
    )  # Choose a read-only operation.
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Wait for the complete target scope before preview.
    preview_button = page.get_by_test_id("ws-batch-preview")  # Find the safe target snapshot action.
    preview_button.click()  # Request only fake discovery data from the test service.
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    review = page.get_by_test_id("ws-batch-review-summary")  # Read the reviewed snapshot summary.
    review.get_by_text("101 target(s)", exact=True).wait_for(timeout=READY_TIMEOUT_MS)
    targets = page.get_by_test_id("ws-batch-review-targets")  # Read all resolved targets, not a sample.
    target_text = targets.inner_text()  # Read the full accessible target review.
    assert "EX Switch 101 — HQ" in target_text, target_text[:300]  # Verify the final target appears.
    assert target_text.count("\n") == 100  # Require the complete preview before admission.
    assert review.get_by_text("2 excluded: incompatible_family", exact=True).is_visible()  # Explain exclusions.
    page.wait_for_function(
        "() => !document.getElementById('wsBatchStart').disabled", timeout=READY_TIMEOUT_MS
    )  # Wait until the complete preview can be admitted.
    page.get_by_test_id("ws-batch-start").click()  # Admit the reviewed fake batch.
    progress = page.get_by_test_id("ws-batch-progress")  # Find the public parent progress panel.
    progress.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - running").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Confirm the parent is active.
    target_progress = page.get_by_test_id("ws-batch-target-progress")  # Read the server-paged target outcomes.
    assert target_progress.locator("div").count() == 101  # Confirm progress exposes the complete frozen set.
    page.get_by_test_id("ws-batch-stop").click()  # Stop only the fake parent batch.
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - stopped").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Confirm the stop result reaches the browser.


def test_ex_hardware_preset_selects_formats_and_starts_preview_bound_batch(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The dedicated preset offers XML, JSON, and BOTH without a free-form command."""
    open_page(page, websocket_portal)  # Load the local mocked Operations portal.
    page.get_by_test_id("ws-multi-site-tab").click()  # Open the batch workflow.
    page.get_by_test_id("ws-batch-ex-hardware").check()  # Select the named server-owned preset.
    output_format = page.get_by_test_id("ws-batch-hardware-format")  # Read the dedicated format selector.
    assert output_format.input_value() == "xml"  # Keep the original request's XML default.
    assert page.get_by_test_id("ws-batch-hardware-scope").inner_text() == (
        "All sites in the configured organization; EX switches only."
    )  # Make the fixed server scope explicit.
    page.get_by_test_id("ws-batch-preview").click()  # Resolve the selected format through the fake service.
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_preview_body == {
        "preset": "ex-hardware-xml",
        "format": "xml",
        "scope_revision": 1,
    }  # The browser sends no command, site, device, or organization values.
    output_format.select_option("json")  # Select JSON from the same XML source response.
    page.get_by_test_id("ws-batch-preview").click()  # Bind the JSON choice to a new snapshot.
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_preview_body["format"] == "json"  # Keep JSON in the preview, not the command body.
    output_format.select_option("both")  # Request two files from the same one-command run.
    page.get_by_test_id("ws-batch-preview").click()  # Bind BOTH to the final one-use snapshot.
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_preview_body["format"] == "both"  # Confirm the third supported output choice.
    assert page.get_by_test_id("ws-batch-confirmation-phrase").inner_text() == "Type: RUN 2 TARGETS"
    page.get_by_test_id("ws-batch-confirmation").fill("RUN 2 TARGETS")  # Confirm the shell-safe target count.
    page.get_by_test_id("ws-batch-start").click()  # Admit only the reviewed snapshot.
    page.get_by_test_id("ws-batch-progress").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_start_body == {
        "preview_id": "hardware-preview",
        "confirmation": "RUN 2 TARGETS",
        "concurrency": 3,
        "output": {"group_by": "site", "mode": "combined"},
    }  # Start carries the reviewed reference, required phrase, and existing scheduler choices only.


def start_hardware_batch(page: Any, fake_services: FakeWebSocketServices, output: str) -> None:
    """Select the hardware preset with one output, preview it, confirm the phrase, and start the batch."""
    page.get_by_test_id("ws-multi-site-tab").click()  # Open the batch workflow.
    page.get_by_test_id("ws-batch-ex-hardware").check()  # Select the named server-owned preset.
    page.get_by_test_id("ws-batch-hardware-format").select_option(output)  # Choose the output.
    page.get_by_test_id("ws-batch-preview").click()  # Resolve the choice through the fake service.
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-confirmation").fill("RUN 2 TARGETS")  # Confirm the shell-safe target count.
    page.get_by_test_id("ws-batch-start").click()  # Admit only the reviewed snapshot.
    page.get_by_test_id("ws-batch-progress").wait_for(state="visible", timeout=READY_TIMEOUT_MS)


def test_ex_hardware_csv_output_names_the_scope_and_runs_the_fixed_xml_command(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The CSV choice previews one XML command and an MSP scope line with the unread organization count."""
    open_page(page, websocket_portal)  # Load the local mocked Operations portal.
    fake_services.hardware_scope = {"mode": "msp", "organization_count": 3, "failed_count": 1}  # An MSP login.
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-hardware-format").select_option("csv")  # The new output choice.
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_preview_body == {
        "preset": "ex-hardware-xml",
        "format": "csv",
        "scope_revision": 2,
    }  # The browser sends only the preset and the output. The check and the choice each bump the revision.
    assert page.get_by_test_id("ws-batch-scope-summary").inner_text() == (
        "Scope: MSP, 3 organizations; all sites; EX switches only. 1 organization could not be read."
    )  # The scope line shows the decision of the server.
    summary = page.get_by_test_id("ws-batch-review-summary").inner_text()
    assert "Output: One combined CSV report (.csv)" in summary  # The review names the output.
    assert "display xml" in summary and "display json" not in summary  # CSV runs the XML command only.


def test_ex_hardware_one_organization_scope_line(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """An organization token shows the one-organization scope line."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert page.get_by_test_id("ws-batch-scope-summary").inner_text() == (
        "Scope: One organization; all sites; EX switches only."
    )


def test_review_card_lists_the_steps_and_tells_the_operator_to_preview_first(page: Any, websocket_portal: str) -> None:
    """Before any preview, the card shows the four steps, and Start batch says why it is off."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    steps = page.get_by_test_id("ws-batch-steps").inner_text()
    assert "Click Preview targets. Nothing runs yet." in steps and "Click Start batch." in steps
    assert "confirmation word" in steps  # The third step names the word.
    next_step = page.get_by_test_id("ws-batch-next-step")
    assert next_step.inner_text() == "Next: click Preview targets. Start batch stays off until you review the list."
    start = page.get_by_test_id("ws-batch-start")
    assert start.is_disabled() and start.get_attribute("title") == next_step.inner_text()  # The pointer explains it.


def test_the_page_names_the_confirmation_word_and_the_next_step(page: Any, websocket_portal: str) -> None:
    """The label, the empty box, and the next step all show the word. A near miss keeps Start batch off."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    confirmation = page.get_by_test_id("ws-batch-confirmation")
    assert page.get_by_test_id("ws-batch-confirmation-label").inner_text() == "Type RUN 2 TARGETS to confirm."
    assert confirmation.get_attribute("placeholder") == "RUN 2 TARGETS"  # The word shows inside the empty box.
    next_step = page.get_by_test_id("ws-batch-next-step")
    waiting = "Next: type RUN 2 TARGETS in the box, then click Start batch."
    assert next_step.inner_text() == waiting and page.get_by_test_id("ws-batch-start").is_disabled()
    confirmation.fill("RUN 2 TARGET")  # A near miss.
    assert next_step.inner_text() == waiting and page.get_by_test_id("ws-batch-start").is_disabled()
    confirmation.fill("RUN 2 TARGETS")  # The exact word.
    assert next_step.inner_text() == "Next: click Start batch to run on 2 target(s)."
    assert page.get_by_test_id("ws-batch-start").is_enabled()


def test_a_changed_choice_sends_the_operator_back_to_the_preview(page: Any, websocket_portal: str) -> None:
    """Changing the output after a preview voids the preview, the word, and the Start button."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-confirmation").fill("RUN 2 TARGETS")
    assert page.get_by_test_id("ws-batch-start").is_enabled()
    page.get_by_test_id("ws-batch-hardware-format").select_option("csv")  # A different output.
    assert page.get_by_test_id("ws-batch-start").is_disabled()
    assert page.get_by_test_id("ws-batch-next-step").inner_text() == (
        "Next: click Preview targets. Start batch stays off until you review the list."
    )
    assert not page.get_by_test_id("ws-batch-review").is_visible()  # The old list is gone.


def test_a_read_only_preview_needs_no_word_and_says_so(page: Any, websocket_portal: str) -> None:
    """A read-only operation shows no word. The next step goes straight to Start batch."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-operation").select_option("channel:site.stats.devices")
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.wait_for_function("() => !document.getElementById('wsBatchStart').disabled", timeout=READY_TIMEOUT_MS)
    assert page.get_by_test_id("ws-batch-next-step").inner_text() == "Next: click Start batch to run on 101 target(s)."
    assert not page.get_by_test_id("ws-batch-confirmation").is_visible()  # No word is needed.


def test_ex_hardware_preset_keeps_the_site_choice_in_the_targets_card(page: Any, websocket_portal: str) -> None:
    """Checking the action keeps the Sites choice, lists the sites of the organization, and hides only the resources."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    sites = page.get_by_test_id("ws-batch-sites")  # The choice of all sites or some sites.
    sites.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    assert sites.input_value() == "all"  # The whole organization stays the default.
    assert not page.get_by_test_id("ws-batch-targets").is_visible()  # The action finds its own switches.
    assert not page.get_by_test_id("ws-batch-operation").is_visible()  # No catalog operation can replace it.
    sites.select_option("selected")  # Choose some sites.
    options = page.locator("#wsBatchSiteOptions")
    options.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert options.locator("option").count() == 2  # Every site of the organization is a choice.


def test_ex_hardware_preset_sends_the_selected_sites_and_names_them_in_the_scope_line(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A chosen site is the only site in the request, and the review says how many sites the operator chose."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-sites").select_option("selected")
    page.locator("#wsBatchSiteOptions").select_option(SITE_ID)  # One site.
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    body = fake_services.batch_preview_body
    assert body is not None and body["sites"] == {"mode": "selected", "ids": [SITE_ID]}
    assert set(body) == {"preset", "format", "scope_revision", "sites"}  # Still no command or device value.
    assert page.get_by_test_id("ws-batch-scope-summary").inner_text() == (
        "Scope: One organization; 1 selected site; EX switches only."
    )
    page.get_by_test_id("ws-batch-sites").select_option("all")  # Back to the whole organization.
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert "sites" not in (fake_services.batch_preview_body or {})  # All sites sends no selection.


def test_ex_hardware_preset_needs_at_least_one_chosen_site_before_it_asks_the_server(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """Selected-sites mode with no site chosen shows a plain error, and no preview request leaves the page."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-site-status").get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-sites").select_option("selected")  # Choose no site.
    page.get_by_test_id("ws-batch-preview").click()
    error = page.get_by_test_id("ws-batch-error")
    error.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert error.inner_text() == "Select one or more sites."
    assert fake_services.batch_preview_body is None  # The server never saw the request.


def test_leaving_the_ex_hardware_preset_gives_the_catalog_operation_its_sites_back(
    page: Any, websocket_portal: str
) -> None:
    """Unchecking restores the sites of the chosen operation, or the first message when there is no operation."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    status = page.get_by_test_id("ws-batch-site-status")
    page.get_by_test_id("ws-batch-ex-hardware").check()
    status.get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-ex-hardware").uncheck()  # No operation was chosen.
    status.get_by_text("Choose an operation to load eligible sites.").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-operation").select_option("channel:site.stats.devices")
    status.get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-ex-hardware").check()  # The action takes the card.
    status.get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-ex-hardware").uncheck()  # The operation takes it back.
    status.get_by_text("2 eligible site(s).").wait_for(timeout=READY_TIMEOUT_MS)
    assert page.get_by_test_id("ws-batch-operation").input_value() == "channel:site.stats.devices"
    assert page.get_by_test_id("ws-batch-sites").is_visible()


def test_ex_hardware_csv_download_link_appears_only_when_the_report_is_ready(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The link points at the CSV route, stays hidden while the run goes, and hides again when the output failed."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv")
    link = page.get_by_test_id("ws-batch-csv-download")
    assert not link.is_visible()  # The report is published at the end of the run.
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="writing")
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - completed").wait_for(timeout=READY_TIMEOUT_MS)
    assert not link.is_visible()  # The output is not final yet.
    fake_services.batch_progress["batch1"].update(artifact_status="ready")
    link.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert link.get_attribute("href") == "/api/websockets/batches/batch1/download?format=csv"


def test_ex_hardware_csv_download_link_stays_hidden_when_the_output_failed(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A failed output offers no report, and the run keeps its archive."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv")
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="failed")
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - completed").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-zip-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert not page.get_by_test_id("ws-batch-csv-download").is_visible()


def test_ex_hardware_xml_output_never_offers_the_csv_link(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A finished XML run keeps its archive only."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "xml")
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="ready")
    page.get_by_test_id("ws-batch-zip-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert not page.get_by_test_id("ws-batch-csv-download").is_visible()


@pytest.mark.parametrize(
    "output, expected",
    [
        ("master-xml", "Output: One combined XML file (.xml)"),
        ("csv-master-xml", "Output: Combined CSV and XML (.csv + .xml)"),
    ],
)
def test_ex_hardware_master_xml_output_previews_the_one_xml_command_and_names_the_files(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices, output: str, expected: str
) -> None:
    """The page offers both combined XML choices, sends the choice, and the review names the files."""
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    page.get_by_test_id("ws-batch-hardware-format").select_option(output)  # Fails when the option is missing.
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_preview_body is not None and fake_services.batch_preview_body["format"] == output
    summary = page.get_by_test_id("ws-batch-review-summary").inner_text()
    assert expected in summary
    assert "display xml" in summary and "display json" not in summary  # A combined report runs the XML command only.


def test_ex_hardware_master_xml_download_link_appears_only_when_the_file_is_ready(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The link points at the XML route, stays hidden while the run goes, and no CSV link or table appears."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "master-xml")
    link = page.get_by_test_id("ws-batch-xml-download")
    assert not link.is_visible()  # The file is published at the end of the run.
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="writing")
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - completed").wait_for(timeout=READY_TIMEOUT_MS)
    assert not link.is_visible()  # The output is not final yet.
    fake_services.batch_progress["batch1"].update(artifact_status="ready")
    link.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert link.get_attribute("href") == "/api/websockets/batches/batch1/download?format=xml"
    assert link.inner_text() == "Download combined XML"
    assert not page.get_by_test_id("ws-batch-csv-download").is_visible()  # This output holds no CSV report.
    assert not page.get_by_test_id("ws-batch-csv-preview").is_visible() and fake_services.csv_preview_calls == []


def test_ex_hardware_master_xml_download_link_stays_hidden_when_the_output_failed(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A failed output offers no file, and the run keeps its archive."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv-master-xml")
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="failed")
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - completed").wait_for(timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-zip-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert not page.get_by_test_id("ws-batch-xml-download").is_visible()
    assert not page.get_by_test_id("ws-batch-csv-download").is_visible()


@pytest.mark.parametrize("output", ["xml", "json", "both", "csv"])
def test_ex_hardware_other_outputs_never_offer_the_master_xml_link(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices, output: str
) -> None:
    """Only the two combined XML choices publish the file, so no other finished run shows the link."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, output)
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="ready")
    page.get_by_test_id("ws-batch-zip-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.wait_for_timeout(500)  # Give a wrong link time to appear.
    assert not page.get_by_test_id("ws-batch-xml-download").is_visible()


def test_ex_hardware_csv_and_master_xml_output_offers_both_files_and_the_table(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The run publishes two files, so the page shows two links, and the table reads the CSV report."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services, output="csv-master-xml")
    csv_link, xml_link = page.get_by_test_id("ws-batch-csv-download"), page.get_by_test_id("ws-batch-xml-download")
    assert csv_link.is_visible() and xml_link.is_visible()
    assert csv_link.get_attribute("href") == "/api/websockets/batches/batch1/download?format=csv"
    assert xml_link.get_attribute("href") == "/api/websockets/batches/batch1/download?format=xml"
    assert csv_rows(page).count() == 6  # The table still shows the CSV report.
    screenshot(page, "csv-master-xml-links.png")


def test_ex_hardware_master_xml_download_link_returns_after_a_page_reload(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The page restores the last batch, and the link shows again for its ready file."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "master-xml")
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="ready")
    page.get_by_test_id("ws-batch-xml-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.reload(wait_until="networkidle")
    page.get_by_test_id("ws-multi-site-tab").click()  # The page opens on the first tab.
    link = page.get_by_test_id("ws-batch-xml-download")
    link.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert link.get_attribute("href") == "/api/websockets/batches/batch1/download?format=xml"


def finish_csv_run(
    page: Any, fake_services: FakeWebSocketServices, report: bytes | None = None, output: str = "csv"
) -> None:
    """Start a run with a CSV report, end it with a ready report, and wait for the table to show rows."""
    if report is not None:
        fake_services.csv_report = report  # The report that the fake service publishes.
    start_hardware_batch(page, fake_services, output)
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="ready")
    page.get_by_test_id("ws-batch-csv-table").wait_for(state="visible", timeout=READY_TIMEOUT_MS)


def csv_rows(page: Any) -> Any:
    """Return the body rows of the report table."""
    return page.get_by_test_id("ws-batch-csv-table").locator("tbody tr")


def test_ex_hardware_csv_table_shows_the_report_and_keeps_the_download(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """When the report is ready, the table lists its columns and every row, and the page asks for a full page."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    headers = page.get_by_test_id("ws-batch-csv-table").locator("thead th")
    assert headers.all_inner_texts() == CSV_COLUMNS
    assert csv_rows(page).count() == 6
    assert csv_rows(page).first.locator("td").all_inner_texts() == ["Alpha Org", "HQ", "ex-001", "FPC", "SN00001"]
    assert page.get_by_test_id("ws-batch-csv-status").inner_text() == "Rows 1 to 6 of 6."
    assert page.get_by_test_id("ws-batch-csv-download").is_visible()  # The file stays one click away.
    assert page.get_by_test_id("ws-batch-csv-previous").is_disabled()  # One page holds the whole report.
    assert page.get_by_test_id("ws-batch-csv-next").is_disabled()
    assert fake_services.csv_preview_calls == [{"session_id": "batch1", "offset": 0, "limit": 1000, "text": ""}]
    screenshot(page, "csv-table-report.png")


def test_ex_hardware_csv_table_waits_for_the_report(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The table stays hidden, and asks nothing, until the output is ready."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv")
    panel = page.get_by_test_id("ws-batch-csv-preview")
    assert not panel.is_visible()  # The run is still going.
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="writing")
    page.locator("#wsBatchProgressTitle").get_by_text("Batch progress - completed").wait_for(timeout=READY_TIMEOUT_MS)
    page.wait_for_timeout(500)  # Give a wrong request time to arrive.
    assert not panel.is_visible() and fake_services.csv_preview_calls == []  # The report is not final.
    fake_services.batch_progress["batch1"].update(artifact_status="ready")
    panel.wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert len(fake_services.csv_preview_calls) == 1


@pytest.mark.parametrize("output, artifact_status", [("csv", "failed"), ("xml", "ready")])
def test_ex_hardware_csv_table_never_shows_for_a_failed_output_or_another_format(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices, output: str, artifact_status: str
) -> None:
    """A failed CSV output and the XML output have no report, so the page shows no table and asks for none."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, output)
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status=artifact_status)
    page.get_by_test_id("ws-batch-zip-download").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.wait_for_timeout(500)  # Give a wrong request time to arrive.
    assert not page.get_by_test_id("ws-batch-csv-preview").is_visible() and fake_services.csv_preview_calls == []


def test_ex_hardware_csv_filter_asks_the_server_after_a_pause_and_shows_the_matching_rows(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The filter runs on the server over the whole report, and clearing it brings every row back."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    box = page.get_by_test_id("ws-batch-csv-filter")
    status = page.get_by_test_id("ws-batch-csv-status")
    box.press_sequentially("EX-002", delay=30)  # Six keys in a quick row.
    status.get_by_text("that match the filter").wait_for(timeout=READY_TIMEOUT_MS)
    assert status.inner_text() == "Rows 1 to 1 of 1 that match the filter. The report has 6 rows."
    assert csv_rows(page).count() == 1 and csv_rows(page).first.locator("td").nth(2).inner_text() == "ex-002"
    asked = [call["text"] for call in fake_services.csv_preview_calls]
    assert asked[0] == "" and asked[-1] == "EX-002" and len(asked) < 1 + len("EX-002")  # A pause, not each key.
    box.fill("")  # An empty filter shows the whole report again.
    status.get_by_text("Rows 1 to 6 of 6.").wait_for(timeout=READY_TIMEOUT_MS)
    assert csv_rows(page).count() == 6


def test_ex_hardware_csv_filter_with_no_match_says_so(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A filter with no match gives no rows and one plain sentence that names the report size."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    page.get_by_test_id("ws-batch-csv-filter").fill("no-such-switch")
    status = page.get_by_test_id("ws-batch-csv-status")
    status.get_by_text("No row matches the filter.").wait_for(timeout=READY_TIMEOUT_MS)
    assert status.inner_text() == "No row matches the filter. The report has 6 rows."
    assert csv_rows(page).count() == 0


def test_ex_hardware_csv_table_pages_through_a_large_report(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A report of 1500 rows shows 1000 rows, then the last 500 rows, and the buttons follow the position."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services, make_csv_report(1500))
    status = page.get_by_test_id("ws-batch-csv-status")
    previous, following = page.get_by_test_id("ws-batch-csv-previous"), page.get_by_test_id("ws-batch-csv-next")
    assert status.inner_text() == "Rows 1 to 1000 of 1500." and csv_rows(page).count() == 1000
    assert previous.is_disabled() and following.is_enabled()
    following.click()
    status.get_by_text("Rows 1001 to 1500 of 1500.").wait_for(timeout=READY_TIMEOUT_MS)
    assert csv_rows(page).count() == 500 and previous.is_enabled() and following.is_disabled()
    previous.click()
    status.get_by_text("Rows 1 to 1000 of 1500.").wait_for(timeout=READY_TIMEOUT_MS)
    assert [call["offset"] for call in fake_services.csv_preview_calls] == [0, 1000, 0]


def test_ex_hardware_csv_table_shows_markup_in_a_cell_as_text(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A switch controls its text, so a cell with markup must show as text and must not run."""
    hostile = '<img src=x onerror="window.cellScriptRan = 1"><b>bold</b>'
    report = CsvRenderer.render(
        [{"org_name": hostile, "site_name": "HQ", "device_name": "ex-001", "item_type": "Chassis"}],
        CSV_COLUMNS,
        1_000_000,
    )
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services, report)
    table = page.get_by_test_id("ws-batch-csv-table")
    assert csv_rows(page).first.locator("td").first.text_content() == hostile  # The raw text is on the page.
    assert table.locator("img").count() == 0 and table.locator("b").count() == 0  # No element came from the text.
    page.wait_for_timeout(300)  # An image error handler would have run by now.
    assert page.evaluate("window.cellScriptRan") is None


def test_ex_hardware_csv_table_cuts_a_long_cell_and_says_so(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A cell of 1500 characters keeps 1000, and the status line names the cut and the download."""
    report = CsvRenderer.render(
        [{"org_name": "Alpha Org", "site_name": "x" * 1500, "device_name": "ex-001"}], CSV_COLUMNS, 1_000_000
    )
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services, report)
    assert len(csv_rows(page).first.locator("td").nth(1).text_content() or "") == 1000
    status = page.get_by_test_id("ws-batch-csv-status").inner_text()
    assert status == "Rows 1 to 1 of 1. 1 cell is cut at 1000 characters here. The download has the full text."


def test_ex_hardware_csv_table_gives_each_column_a_name_for_a_screen_reader(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The scroll box is a named, focusable region, and each column name is a column header."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    region = page.get_by_role("region", name="Combined CSV report")
    assert region.is_visible() and region.get_attribute("tabindex") == "0"  # A keyboard can scroll it.
    assert page.locator('[data-testid="ws-batch-csv-table"] th[scope="col"]').count() == len(CSV_COLUMNS)


def test_ex_hardware_csv_table_shows_a_refusal_in_plain_words_and_keeps_the_download(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A report that is too large gets the sentence of the server, no rows, and the download stays."""
    message = "The report is too large to show here. Download the CSV report."
    fake_services.csv_error = StreamRequestError("too_large", message)
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv")
    fake_services.batch_progress["batch1"].update(status="completed", artifact_status="ready")
    status = page.get_by_test_id("ws-batch-csv-status")
    status.get_by_text(message).wait_for(timeout=READY_TIMEOUT_MS)
    assert status.evaluate("element => element.classList.contains('text-danger')")  # The refusal stands out.
    assert csv_rows(page).count() == 0 and page.get_by_test_id("ws-batch-csv-next").is_disabled()
    assert page.get_by_test_id("ws-batch-csv-download").is_visible()


def test_ex_hardware_csv_table_recovers_after_a_refusal(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """A refused filter shows the reason. The next filter, after the fault ends, shows the rows again."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    fake_services.csv_error = StreamRequestError("output_failed", "The saved report cannot be shown as a table.")
    box, status = page.get_by_test_id("ws-batch-csv-filter"), page.get_by_test_id("ws-batch-csv-status")
    box.fill("ex")
    status.get_by_text("The saved report cannot be shown as a table.").wait_for(timeout=READY_TIMEOUT_MS)
    fake_services.csv_error = None  # The fault ends.
    box.fill("")
    status.get_by_text("Rows 1 to 6 of 6.").wait_for(timeout=READY_TIMEOUT_MS)
    assert csv_rows(page).count() == 6 and not status.evaluate("element => element.classList.contains('text-danger')")


def test_ex_hardware_csv_table_returns_after_a_page_reload(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The page restores the last batch, and the table loads again for its ready report."""
    open_page(page, websocket_portal)
    finish_csv_run(page, fake_services)
    page.reload(wait_until="networkidle")
    page.get_by_test_id(
        "ws-multi-site-tab"
    ).click()  # The page opens on the first tab, and the batch card is on this one.
    page.get_by_test_id("ws-batch-csv-table").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert csv_rows(page).count() == 6 and len(fake_services.csv_preview_calls) == 2  # One read for each page load.


def test_a_batch_parent_of_a_shell_action_is_not_opened_as_a_terminal(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The hardware parent keeps the terminal output name but owns no shell, so the page reads no terminal (#4932)."""
    open_page(page, websocket_portal)
    start_hardware_batch(page, fake_services, "csv")
    page.wait_for_timeout(1500)  # A terminal read would start at once, and it would repeat each second.
    assert fake_services.terminal_reads == []  # The parent never reaches the terminal route.
    page.get_by_test_id("ws-single-site-tab").click()  # The output panel of the selected session is on the first tab.
    assert page.get_by_test_id("ws-output").is_visible()  # The message view shows the parent, as for a channel batch.
    assert page.get_by_test_id("ws-terminal-panel").is_hidden()  # No dead terminal.
    assert page.get_by_test_id("ws-session-state").inner_text() == "State: Live"  # The state of the session itself.


def test_ex_hardware_concurrency_default_comes_from_the_catalog_setting(
    page: Any, websocket_portal: str, fake_services: FakeWebSocketServices
) -> None:
    """The page takes the shell limit of the hardware action from the catalog, and the start carries it."""
    fake_services.hardware_concurrency = 2  # The server setting in use.
    open_page(page, websocket_portal)
    page.get_by_test_id("ws-multi-site-tab").click()
    page.get_by_test_id("ws-batch-ex-hardware").check()
    assert page.get_by_test_id("ws-batch-concurrency").input_value() == "2"
    page.get_by_test_id("ws-batch-preview").click()
    page.get_by_test_id("ws-batch-review").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    page.get_by_test_id("ws-batch-confirmation").fill("RUN 2 TARGETS")
    page.get_by_test_id("ws-batch-start").click()
    page.get_by_test_id("ws-batch-progress").wait_for(state="visible", timeout=READY_TIMEOUT_MS)
    assert fake_services.batch_start_body is not None and fake_services.batch_start_body["concurrency"] == 2
    page.get_by_test_id("ws-batch-ex-hardware").uncheck()  # Leaving the action restores the generic default.
    assert page.get_by_test_id("ws-batch-concurrency").input_value() == "3"
