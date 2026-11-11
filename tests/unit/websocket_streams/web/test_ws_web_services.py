"""Tests for WebSocket web services.

Why:
    Issue #3551 needs one app-scoped service object that shuts down cleanly
    and reports a not-ready portal without leaking Mist details.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

import os  # Inject a deterministic failure between BOTH file renames.
import zipfile  # Check archive entry paths.
from collections.abc import Iterator  # Type the fake download iterator.
from datetime import UTC, datetime  # Artifact tests use one valid ended-session time.
from io import BytesIO  # Inspect bounded ZIP snapshots without a filesystem copy.
from pathlib import Path  # Test output stays under pytest temporary storage.
from types import SimpleNamespace  # Return a checked request with a key attribute.

import pytest  # Assert contract errors from service calls.
from flask import Flask  # Build small app instances for the service tests.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Use production catalog records in eligibility tests.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Not-ready errors use this type.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Preview fixtures return checked requests.
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import (
    MessagePage,
)  # The fake manager returns a read answer.
from src.mist.realtime.websocket_streams.web.blueprint.registry import (
    WebSocketBlueprint,
)  # Verify additive batch picker route registration.
from src.mist.realtime.websocket_streams.web.services.assembly.bundle import (
    WebSocketServiceBundle,
)  # Type the built service set.
from src.mist.realtime.websocket_streams.web.services.assembly.collaborators import (
    WebSocketCollaborators,
)  # Supply explicit test collaborators.
from src.mist.realtime.websocket_streams.web.services.assembly.factory import (
    WebSocketServiceFactory,
)  # Build test bundles.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import (
    SessionArtifactService,
)  # Keep batch test files outside the repository data tree.
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import (
    HardwareOutputError,
    HardwareXmlPreset,
    HardwareXmlSupport,
)  # Exercise the fixed XML and derived JSON boundary.
from src.mist.realtime.websocket_streams.web.services.operations.sessions import (
    WebSocketBatchService,
)  # Test preview validation and snapshots.
from src.mist.realtime.websocket_streams.web.services.pickers.related import (
    BatchTargetPickerService,
)  # Test catalog-scoped target eligibility.
from src.mist.realtime.websocket_streams.web.services.registry import (
    WebSocketServiceRegistry,
)  # Store and stop app bundles.


class FakeCatalog:
    """Fake catalog that records payload reads."""

    def page_payload(self) -> dict[str, object]:
        """Return one safe catalog payload."""
        return {"flags": {}, "channels": [{"key": "site.stats.devices"}], "utilities": []}  # No path leaks.


class FakeSettings:
    """Fake settings that returns small limits."""

    def limits_payload(self) -> dict[str, int]:
        """Return the limits payload."""
        return {"max_sessions": 2, "idle_seconds": 30, "capture_seconds": 60}  # Stable test limits.


class FakeManager:
    """Fake manager for service unit tests."""

    def __init__(self) -> None:
        """Start with no actions."""
        self.shutdown_called = False  # Track shutdown calls.
        self.started = False  # Track start calls.

    def start(self, request: object) -> dict[str, object]:
        """Start one fake session."""
        self.started = True  # Prove that the manager ran.
        return {"session_id": "abc123", "title": "Started"}  # Session payload.

    def list_payload(self) -> dict[str, object]:
        """Return an empty session list."""
        return {"sessions": [], "limits": {"max_sessions": 2, "live_count": 0}}  # Empty list.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return an empty read answer."""
        assert limit > 0  # The service passed the limit through.
        return MessagePage({"session_id": session_id}, [], after, 0, False)  # Read with no new message.

    def stop(self, session_id: str) -> dict[str, object]:
        """Return one stopped session."""
        return {"session_id": session_id, "state": "stopped"}  # Stop payload.

    def session(self, session_id: str) -> object:
        """Refuse each session, because the fake holds no session."""
        raise StreamRequestError("not_found", f"The session {session_id} was not found.")  # Contract error.

    def delete(self, session_id: str) -> None:
        """Accept a delete request."""
        assert session_id  # The service passed the session identifier.

    def download(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return a small download stream."""
        assert session_id  # The service passed the session identifier.
        return "download.jsonl", iter(['{"seq":1}\n'])  # JSON Lines stream.

    def shutdown(self) -> None:
        """Record shutdown."""
        self.shutdown_called = True  # Prove that shutdown reached the manager.


def make_batch_service(
    checker: FakeBatchChecker,
    picker: FakeBatchPicker,
    manager: FakeManager,
    root: Path,
) -> WebSocketBatchService:
    """Build a batch service with isolated artifact storage."""
    artifacts = SessionArtifactService(manager, None, root)  # Keep test files private and temporary.
    return WebSocketBatchService(checker, picker, manager, artifacts, None)  # Share one manager boundary.


class FakeChecker:
    """Fake request checker."""

    def check(self, body: object) -> object:
        """Return a fake checked request."""
        assert isinstance(body, dict)  # The service passed the JSON body through.
        return SimpleNamespace(key="site.stats.devices")  # The service logs the checked key.


class FakeBatchChecker:
    """Return one controlled batch definition and checked target request."""

    def __init__(self, definition: ChannelDefinition | UtilityDefinition) -> None:
        """Store the catalog entry for one preview test."""
        self.definition = definition  # Keep the operation server-owned.

    def resolve_definition(self, kind: str, key: str) -> ChannelDefinition | UtilityDefinition:
        """Return the matching definition or a stable refusal."""
        if key != self.definition.key:
            raise StreamRequestError("unknown_key", "The catalog key is unknown.")
        return self.definition  # A matching key cannot be overridden by the request.

    def check_batch(self, body: object) -> StartRequest:
        """Return a checked request with a trusted organization identifier."""
        values = body if isinstance(body, dict) else {}  # The preview builder sends one validated mapping.
        raw_targets = values.get("targets", {})  # Read only the requested catalog identifiers.
        targets = {"org_id": ("11111111-1111-4111-8111-111111111111",)}  # Mimic checker injection.
        if isinstance(raw_targets, dict):
            targets.update({key: (value,) for key, value in raw_targets.items()})
        return StartRequest(
            str(values.get("kind")), self.definition, targets, {}, "Preview target"
        )  # Keep the fake request shape identical to production.


class FakeBatchPicker:
    """Return complete organization sites and operation targets."""

    def __init__(self, device_target: bool = False) -> None:
        """Build one complete site list and its target rows."""
        self.device_target = device_target  # Tests choose site or device scope.
        self.site_calls: list[tuple[str, str]] = []  # Verify preset discovery stays organization-wide.
        self.target_calls: list[tuple[str | None, str, str]] = []  # Verify one target read per discovered site.
        self.site_complete = True  # Tests can model incomplete paginated organization discovery.
        self.target_complete = True  # Tests can model incomplete resource pagination.
        self.target_rows: list[dict[str, object]] | None = None  # Allow precise EX and VC row fixtures.
        self.site_rows = [
            {"id": "22222222-2222-4222-8222-222222222222", "label": "North"},
            {"id": "33333333-3333-4333-8333-333333333333", "label": "South"},
        ]  # Use source identifiers that pass the production UUID rule.

    def hardware_targets(self, site_id: str | None, kind: str, key: str, parents: dict[str, str]) -> dict[str, object]:
        """Supply explicit running status only for hardware preview fixtures."""
        result = self.targets(site_id, kind, key, parents)
        for row in result["rows"]:
            row.setdefault("status", "connected")
        return result

    def hardware_status(self, identity: object) -> str:
        """Keep fake hardware targets online without external requests."""
        return "connected"

    def sites(self, kind: str, key: str) -> dict[str, object]:
        """Return the complete organization site list."""
        self.site_calls.append((kind, key))  # Keep the server-owned organization operation observable.
        return {"rows": self.site_rows, "complete": self.site_complete}  # No partial site result is accepted.

    def targets(self, site_id: str | None, kind: str, key: str, _parents: dict[str, str]) -> dict[str, object]:
        """Return one site or device row for the requested scope."""
        self.target_calls.append((site_id, kind, key))  # Ensure every organization site is expanded.
        if self.device_target:
            rows = self.target_rows or [
                {
                    "id": "44444444-4444-4444-8444-444444444444",
                    "device_id": "44444444-4444-4444-8444-444444444444",
                    "label": "Switch",
                    "family": "ex",
                    "site_id": site_id,
                    "target_type": "device",
                }
            ]  # Keep the device identity and site association together.
        else:
            rows = [
                {
                    "id": site_id,
                    "label": "Site",
                    "site_id": site_id,
                    "target_type": "site",
                }
            ]  # A site-only operation uses one target per site.
        normalized = [dict(row, site_id=site_id) for row in rows]  # Bind every candidate to the queried site.
        return {"rows": normalized, "complete": self.target_complete}  # Every requested page is complete.


class FakePickers:
    """Fake picker service."""

    def sites(self) -> dict[str, object]:
        """Return one organization site row."""
        return self._payload("org")  # Reuse the stable picker payload.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return one device row."""
        return self._payload(site_id)  # Common picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return one map row."""
        return self._payload(site_id)  # Common picker payload.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return one asset row."""
        return self._payload(site_id)  # Common picker payload.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return one client row."""
        return self._payload(site_id + map_id)  # Common picker payload.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return one Mist Edge row."""
        return self._payload(site_id or "org")  # Common picker payload.

    def _payload(self, value: str) -> dict[str, object]:
        """Return one picker payload."""
        return {"rows": [{"id": value, "label": "Row"}], "total_count": 1, "reason": None}  # Payload.


def make_service(reason: str | None = None) -> tuple[WebSocketServiceBundle, FakeManager]:
    """Build a service with fake parts."""
    manager = FakeManager()  # The test reads this object after the action.
    collaborators = WebSocketCollaborators(
        FakeCatalog(), FakeChecker(), FakePickers(), manager, FakeSettings()
    )  # Supply deterministic collaborators.
    return WebSocketServiceFactory.from_collaborators(collaborators, reason), manager  # Return both objects.


def test_catalog_payload_adds_ready_and_limits() -> None:
    """The service adds readiness and limits to the catalog payload."""
    service, _manager = make_service()  # Build a ready service.
    payload = service.catalog.payload()  # Read the catalog payload.
    assert payload["ready"] is True  # Ready state is true.
    assert payload["limits"]["max_sessions"] == 2  # Limits came from settings.
    assert "path" not in str(payload)  # The payload does not expose a path field.


def test_not_ready_refuses_start_and_picker() -> None:
    """A not-ready service refuses starts and pickers."""
    service, _manager = make_service("The portal has no Mist session or organization.")  # Build not ready.
    with pytest.raises(StreamRequestError) as start_error:  # Start must fail.
        service.sessions.lifecycle.start({"kind": "channel"})  # Attempt a start.
    with pytest.raises(StreamRequestError) as picker_error:  # Picker must fail.
        service.pickers.site.devices("site1")  # Attempt a picker read.
    assert start_error.value.code == "not_ready"  # Start refusal code.
    assert picker_error.value.code == "not_ready"  # Picker refusal code.


def test_not_ready_refuses_the_terminal() -> None:
    """A not-ready service refuses the terminal routes before the gateway runs."""
    service, _manager = make_service("The portal has no Mist session or organization.")  # Build not ready.
    with pytest.raises(StreamRequestError) as terminal_error:  # The terminal must fail.
        service.terminal.read("missing", 0, 0.0)  # Attempt a terminal read.
    assert terminal_error.value.code == "not_ready"  # The refusal uses the contract code.
    assert terminal_error.value.status == 503  # The page shows the not-ready state.


def test_ready_terminal_gateway_reaches_the_manager() -> None:
    """The ready service gives one gateway, and the gateway finds sessions through the manager."""
    service, _manager = make_service()  # Build a ready service.
    terminal = service.terminal  # Read the terminal service.
    with pytest.raises(StreamRequestError) as read_error:  # The fake manager holds no session.
        terminal.read("missing", 0, 0.0)  # Read a session that does not exist.
    assert service.terminal is terminal  # One terminal service owns the process gateway.
    assert read_error.value.code == "not_found"  # The manager refusal reaches the route.


def test_ready_service_delegates_to_manager_and_pickers() -> None:
    """A ready service delegates route work to the built parts."""
    service, manager = make_service()  # Build a ready service.
    started = service.sessions.lifecycle.start({"kind": "channel"})  # Start a fake session.
    listed = service.sessions.lifecycle.list()  # List sessions.
    read = service.sessions.messages.read("abc123", 4, 10)  # Read messages.
    stopped = service.sessions.lifecycle.stop("abc123")  # Stop session.
    deleted = service.artifacts.delete("abc123")  # Delete session.
    filename, lines = service.artifacts.download("abc123")  # Download session.
    picker = service.pickers.related.mxedges(None)  # Read a picker.
    device_picker = service.pickers.site.devices("site1")  # Read devices through the picker service.
    map_picker = service.pickers.site.maps("site1")  # Read maps through the picker service.
    asset_picker = service.pickers.site.assets("site1")  # Read assets through the picker service.
    client_picker = service.pickers.related.sdkclients("site1", "map1")  # Read SDK clients.
    site_picker = service.pickers.site.sites()  # Read sites through the site picker service.
    assert manager.started is True and started["session_id"] == "abc123"  # Manager start ran.
    assert listed["sessions"] == [] and read.next_after == 4  # Manager reads ran.
    assert stopped["state"] == "stopped"  # Stop ran.
    assert deleted == {"ok": True} and filename == "download.jsonl"  # Delete and download ran.
    assert list(lines) == ['{"seq":1}\n'] and picker["rows"][0]["label"] == "Row"  # Streams and picker ran.
    assert device_picker["rows"][0]["label"] == "Row" and map_picker["rows"][0]["label"] == "Row"  # Picker rows.
    assert asset_picker["rows"][0]["label"] == "Row" and client_picker["rows"][0]["label"] == "Row"  # More rows.
    assert site_picker["rows"][0]["id"] == "org"  # Organization sites use the same route-facing service.


def test_for_app_reuses_injected_service() -> None:
    """for_app returns the service that a test injects."""
    app = Flask(__name__)  # Build a small Flask app.
    service, _manager = make_service()  # Build an injected service.
    app.config[WebSocketServiceRegistry.CONFIG_KEY] = service  # Inject the service.
    assert WebSocketServiceRegistry.for_app(app) is service  # The service is reused.


def test_for_app_builds_not_ready_service_without_credentials() -> None:
    """for_app builds a safe service when the portal has no Mist session."""
    app = Flask(__name__)  # Build a small Flask app.
    app.config["APISESSION"] = None  # Simulate a portal with no Mist session.
    app.config["ORG_ID"] = ""  # Simulate a portal with no organization.
    app.register_blueprint(WebSocketBlueprint.create())  # Register the WebSocket picker route.
    service = WebSocketServiceRegistry.for_app(app)  # Build the app-scoped service.
    catalog = service.catalog.payload()  # The catalog route can still answer.
    listed = service.sessions.lifecycle.list()  # The session list can still answer.
    response = app.test_client().get(
        "/api/websockets/batches/sites?kind=channel&key=site.stats.devices"
    )  # Request the additive site picker.
    with pytest.raises(StreamRequestError) as error:  # A start must refuse when not ready.
        service.sessions.lifecycle.start({"kind": "channel"})  # Attempt a start.
    service.sessions.lifecycle.shutdown()  # Shutdown the empty manager safely.
    assert catalog["ready"] is False  # The payload reports not ready.
    assert listed["sessions"] == []  # The empty manager returns no sessions.
    assert response.status_code == 503  # The new picker route preserves not-ready behavior.
    assert error.value.code == "not_ready"  # The refusal uses the contract code.


def test_fallback_not_ready_parts_have_limits() -> None:
    """Fallback parts provide limits when settings cannot import."""
    service = WebSocketServiceFactory.not_ready("The engine is loading.")  # Build fallback services.
    payload = service.catalog.payload()  # Read the safe catalog payload.
    assert payload["limits"]["capture_seconds"] == 3600  # Fallback settings publish the capture maximum.


def test_stop_for_app_calls_shutdown() -> None:
    """stop_for_app shuts down an existing service."""
    app = Flask(__name__)  # Build a small Flask app.
    service, manager = make_service()  # Build an injected service.
    app.config[WebSocketServiceRegistry.CONFIG_KEY] = service  # Inject the service.
    WebSocketServiceRegistry.stop_for_app(app)  # Stop WebSocket services.
    assert manager.shutdown_called is True  # Shutdown reached the manager.


def test_stop_for_app_without_service_is_safe() -> None:
    """stop_for_app does nothing when the app has no service."""
    app = Flask(__name__)  # Build a small Flask app.
    WebSocketServiceRegistry.stop_for_app(app)  # Stop without a configured service.
    assert WebSocketServiceRegistry.CONFIG_KEY not in app.config  # No service was created.


def test_batch_target_picker_filters_families_and_rejects_foreign_sites() -> None:
    """Catalog family and full organization membership constrain target rows."""
    site_id = "11111111-2222-3333-4444-555555555555"  # Keep one site in the fake organization.
    foreign_site_id = "22222222-3333-4444-5555-666666666666"  # Keep one site outside the fake organization.
    site_field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")
    device_field = FieldSpec("device_id", "Device", FieldKind.UUID, required=True, picker="devices")
    definition = UtilityDefinition(
        "ex.retrieveRoutes",
        "ex",
        "retrieveRoutes",
        "Routes",
        "Read routes.",
        (),
        Safety.READ,
        "lines",
        (site_field, device_field),
    )  # Restrict the target list to catalog-approved EX devices.
    calls: list[str] = []  # Prove foreign site rejection occurs before device discovery.
    picker = SimpleNamespace(
        sites=lambda: {"rows": [{"id": site_id, "label": "Site"}]},
        devices=lambda requested_site: (
            calls.append(requested_site)
            or {
                "rows": [
                    {"id": "switch", "label": "Switch", "family": "ex"},
                    {"id": "gateway", "label": "Gateway", "family": "srx"},
                ]
            }
        ),
    )  # Supply complete fake site and device rows.
    catalog = SimpleNamespace(find=lambda _kind, _key: definition)  # Resolve only the fixed operation.
    service = BatchTargetPickerService(picker, catalog, None)  # Build the ready target service.
    result = service.targets(site_id, "utility", "ex.retrieveRoutes", {})  # Discover eligible devices.
    assert [row["id"] for row in result["rows"]] == ["switch"]  # Keep only the catalog family.
    assert result["excluded"] == {"incompatible_family": 1}  # Report excluded families explicitly.
    with pytest.raises(StreamRequestError) as error:  # Reject a foreign site before reading devices.
        service.targets(foreign_site_id, "utility", "ex.retrieveRoutes", {})  # Request the other site.
    assert error.value.code == "bad_request"  # Preserve the safe scope error.
    assert calls == [site_id]  # Do not query device rows for a foreign site.


def test_batch_target_route_rejects_unknown_query_fields() -> None:
    """The Multi Site target route rejects unrecognized query parameters."""
    app = Flask(__name__)  # Build a small Flask app.
    service, _manager = make_service()  # Build a ready service with fake collaborators.
    app.config[WebSocketServiceRegistry.CONFIG_KEY] = service  # Inject the fake service.
    app.register_blueprint(WebSocketBlueprint.create())  # Register the target discovery route.
    response = app.test_client().get(
        "/api/websockets/batches/sites/11111111-2222-3333-4444-555555555555/targets"
        "?kind=channel&key=site.stats.devices&unexpected=value"
    )  # Send an unsupported field through Flask.
    assert response.status_code == 400  # Reject unknown query keys.
    assert response.get_json()["code"] == "bad_request"  # Preserve the route error contract.
    repeated = app.test_client().get(
        "/api/websockets/batches/sites/11111111-2222-3333-4444-555555555555/targets"
        "?kind=channel&kind=utility&key=site.stats.devices"
    )  # Reject duplicate controls before any picker request.
    assert repeated.status_code == 400  # Keep duplicate query fields invalid.
    assert repeated.get_json()["code"] == "bad_request"  # Preserve the checked error contract.


def test_batch_preview_freezes_complete_site_targets(tmp_path: Path) -> None:
    """A preview resolves all sites once and returns the exact safe target list."""
    site_field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")
    definition = ChannelDefinition(
        "site.stats.devices",
        "site",
        "Device statistics",
        "Live data.",
        "/sites/{site_id}",
        (site_field,),
    )  # Build a site-scoped channel definition.
    service = make_batch_service(FakeBatchChecker(definition), FakeBatchPicker(), FakeManager(), tmp_path)
    payload = service.preview(
        {
            "operation": {"kind": "channel", "key": definition.key},
            "selection": {"sites": {"mode": "all"}},
            "parameters": {},
            "scope_revision": 7,
        }
    )  # Ask for one read-only complete preview.
    identifiers = [target["site_id"] for target in payload["targets"]]
    assert payload["target_count"] == 2  # Both organization sites became explicit targets.
    assert identifiers == sorted(identifiers)  # Preview order is deterministic.
    assert payload["scope_revision"] == 7  # The response keeps the browser revision.
    assert payload["confirmation"]["required"] is False  # A read-only channel needs no phrase.
    assert "fingerprint" not in payload and "commands" not in payload  # Private snapshot data stays server-side.


def test_shell_batch_preview_requires_exact_finite_commands(tmp_path: Path) -> None:
    """A shell preview stores commands and returns the batch confirmation phrase."""
    site_field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")
    device_field = FieldSpec("device_id", "Device", FieldKind.UUID, required=True, picker="devices")
    definition = UtilityDefinition(
        "ex.createShellSession",
        "ex",
        "createShellSession",
        "Remote shell",
        "Open a shell.",
        (),
        Safety.SHELL,
        "terminal",
        (site_field, device_field),
    )  # Build a catalog shell definition.
    service = make_batch_service(
        FakeBatchChecker(definition), FakeBatchPicker(device_target=True), FakeManager(), tmp_path
    )
    body = {
        "operation": {"kind": "shell", "key": definition.key},
        "selection": {"sites": {"mode": "all"}, "resources": {"mode": "all"}},
        "parameters": {},
        "commands": ["show version", "show chassis hardware"],
        "scope_revision": 3,
    }  # Keep exact command order in the private preview.
    payload = service.preview(body)  # Create a read-only preview without opening a shell.
    assert payload["target_count"] == 2  # The same device ID in two sites remains two targets.
    assert payload["confirmation"]["phrase"] == "RUN 2 TARGETS"  # Bind confirmation to the exact count.
    assert "commands" not in payload  # Command text is not returned in the preview response.
    with pytest.raises(StreamRequestError) as error:
        service.preview(body | {"commands": ["show version\nconfigure"]})  # Refuse embedded terminal control.
    assert error.value.code == "bad_request"  # Invalid commands fail before any session starts.


def hardware_shell_definition() -> UtilityDefinition:
    """Build the existing server-owned EX shell catalog entry."""
    site_field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")
    device_field = FieldSpec("device_id", "Device", FieldKind.UUID, required=True, picker="devices")
    return UtilityDefinition(
        "ex.createShellSession",
        "ex",
        "createShellSession",
        "Remote shell",
        "Open a shell.",
        (),
        Safety.SHELL,
        "terminal",
        (site_field, device_field),
    )  # Keep the preset bound to the established shell utility.


@pytest.mark.parametrize("selected_format", ["xml", "json", "both"])
def test_ex_hardware_preset_binds_fixed_command_and_org_scope(tmp_path: Path, selected_format: str) -> None:
    """The preset freezes one EX-only command over all sites and the chosen format."""
    checker = FakeBatchChecker(hardware_shell_definition())  # Use the existing shell catalog safety.
    picker = FakeBatchPicker(device_target=True)  # Return one EX device for every configured site.
    service = make_batch_service(checker, picker, FakeManager(), tmp_path)  # Isolate all output.
    payload = service.preview(
        {"preset": "ex-hardware-xml", "format": selected_format, "scope_revision": 5}
    )  # Preview the fixed server-owned preset without browser target data.
    record = next(iter(service._previews.records.values()))  # Read the private snapshot for its fixed command.
    assert payload["preset"] == "ex-hardware-xml"  # Identify the dedicated action in the preview.
    assert payload["format"] == selected_format  # Bind the selected file format to this snapshot.
    assert payload["target_count"] == 2  # Expand both configured organization sites.
    assert picker.site_calls == [("shell", "ex.createShellSession")]  # Resolve sites through the EX shell catalog.
    assert len(picker.target_calls) == 2  # Discover resources once for each complete site row.
    formats = ("xml", "json") if selected_format == "both" else (selected_format,)
    commands = tuple(f"show chassis hardware detail | display {value} | no-more" for value in formats)
    assert record.commands == commands
    assert record.output_format == selected_format  # Prevent format changes after preview.
    assert payload["confirmation"]["phrase"] == "RUN 2 TARGETS"  # Preserve shell admission confirmation.
    assert payload["fixed_commands"] == list(commands)
    assert "commands" not in payload  # Show only the fixed operator-reviewed command.


def test_ex_hardware_preset_defaults_to_xml_and_rejects_browser_command(tmp_path: Path) -> None:
    """The initial format is XML and a browser cannot replace the fixed command."""
    checker = FakeBatchChecker(hardware_shell_definition())  # Keep the shell catalog definition fixed.
    picker = FakeBatchPicker(device_target=True)  # Supply complete organization targets.
    service = make_batch_service(checker, picker, FakeManager(), tmp_path)  # Isolate preview state.
    payload = service.preview({"preset": "ex-hardware-xml", "scope_revision": 0})  # Omit format deliberately.
    assert payload["format"] == "xml"  # Preserve the initial XML-only request.
    with pytest.raises(StreamRequestError) as error:  # Refuse arbitrary shell text.
        service.preview(
            {
                "preset": "ex-hardware-xml",
                "format": "xml",
                "command": "show configuration",
                "scope_revision": 1,
            }
        )  # Do not let the browser supply device commands.
    assert error.value.code == "bad_request"  # Keep request-shape refusal stable.


def test_ex_hardware_preset_rejects_unknown_output_format(tmp_path: Path) -> None:
    """Only XML, JSON, or BOTH can enter the hardware preview snapshot."""
    service = make_batch_service(
        FakeBatchChecker(hardware_shell_definition()),
        FakeBatchPicker(device_target=True),
        FakeManager(),
        tmp_path,
    )  # Build a ready shell batch service.
    with pytest.raises(StreamRequestError) as error:  # Reject unrecognized file extensions.
        service.preview(
            {"preset": "ex-hardware-xml", "format": "yaml", "scope_revision": 2}
        )  # Validate the format before discovery.
    assert error.value.code == "bad_request"  # Keep invalid formats out of preview storage.


def test_ex_hardware_preview_deduplicates_virtual_chassis_and_excludes_non_ex(tmp_path: Path) -> None:
    """Keep one logical EX device even when inventory repeats its member records."""
    picker = FakeBatchPicker(device_target=True)
    picker.site_rows = [{"id": "22222222-2222-4222-8222-222222222222", "label": "North"}]
    picker.target_rows = [
        {
            "id": "44444444-4444-4444-8444-444444444444",
            "device_id": "55555555-5555-4555-8555-555555555555",
            "label": "EX Virtual Chassis",
            "family": "ex",
            "target_type": "device",
        },
        {
            "id": "66666666-6666-4666-8666-666666666666",
            "device_id": "55555555-5555-4555-8555-555555555555",
            "label": "EX Virtual Chassis member",
            "family": "ex",
            "target_type": "device",
        },
        {
            "id": "77777777-7777-4777-8777-777777777777",
            "device_id": "77777777-7777-4777-8777-777777777777",
            "label": "SRX",
            "family": "srx",
            "target_type": "device",
        },
    ]  # Repeat the stable chassis identity and include one ineligible family.
    service = make_batch_service(FakeBatchChecker(hardware_shell_definition()), picker, FakeManager(), tmp_path)
    preview = service.preview({"preset": "ex-hardware-xml", "scope_revision": 1})
    assert preview["target_count"] == 1
    assert preview["targets"][0]["device_id"] == "55555555-5555-4555-8555-555555555555"
    assert preview["excluded"]["duplicate_device"] == 1
    assert preview["excluded"]["incompatible_family"] == 1


@pytest.mark.parametrize("incomplete", ["site", "target"])
def test_ex_hardware_preview_refuses_incomplete_paginated_discovery(tmp_path: Path, incomplete: str) -> None:
    """Never start an organization run from a partial inventory page set."""
    picker = FakeBatchPicker(device_target=True)
    setattr(picker, f"{incomplete}_complete", False)
    service = make_batch_service(FakeBatchChecker(hardware_shell_definition()), picker, FakeManager(), tmp_path)
    with pytest.raises(StreamRequestError) as error:
        service.preview({"preset": "ex-hardware-xml", "scope_revision": 2})
    assert error.value.code == "picker_incomplete"


def test_hardware_output_removes_shell_framing_and_preserves_nested_xml() -> None:
    """Split bytes and a Junos routing-engine marker preserve the original XML."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\r\n'
        '<rpc-reply xmlns="urn:juniper:xml:ns:netconf-base:1.0" xmlns:j="urn:juniper:xml:ns:junos:chassis">'
        "<chassis-inventory><chassis><name>EX-UTF8-ë</name>"
        '<j:chassis-module serial-number="007"><name>FPC 0</name></j:chassis-module>'
        '<j:chassis-module serial-number="008"><name>FPC 1</name></j:chassis-module>'
        "</chassis></chassis-inventory></rpc-reply>"
    )  # Keep repeated namespace-qualified inventory elements and string values.
    framed = (
        "login banner\r\n" f"{HardwareXmlPreset.COMMAND}\r\n" + xml + "\r\n\r\n{master:0}\r\nswitch@site> "
    ).encode("utf-8")
    split = framed.index("ë".encode()) + 1
    result = HardwareXmlSupport.Decoder.decode_output(
        framed[:split] + framed[split:], "switch@site>", HardwareXmlPreset.COMMAND
    )
    assert result.xml == xml  # Save the original device XML, not its terminal framing.
    assert result.json == ""  # An XML command must not manufacture JSON.


@pytest.mark.parametrize(
    "xml",
    [
        "<rpc-reply><chassis-inventory></rpc-reply>",
        "<!DOCTYPE rpc-reply [<!ENTITY x SYSTEM 'file:///secret'>]><rpc-reply><chassis-inventory>&x;</chassis-inventory></rpc-reply>",
        "<rpc-reply><chassis-inventory/></rpc-reply> trailing",
    ],
)
def test_hardware_output_rejects_malformed_entities_and_trailing_content(xml: str) -> None:
    """Never create successful-looking files from incomplete or unsafe XML."""
    framed = (xml + "\nswitch@site>").encode("utf-8")
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(framed, "switch@site>", HardwareXmlPreset.COMMAND)


@pytest.mark.parametrize("payload", [b"", b'{"chassis-inventory": bad json}'])
def test_native_json_rejects_empty_body_and_malformed_response(payload: bytes) -> None:
    """Reject missing or malformed native JSON before artifact publication."""
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(
            payload + b"\r\nswitch@site>", "switch@site>", HardwareXmlPreset.COMMANDS["json"]
        )


def test_hardware_output_rejects_invalid_utf8_and_missing_inventory() -> None:
    """Require a strict complete XML document containing chassis inventory."""
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(
            b"<rpc-reply>\xff</rpc-reply>\nswitch@site>", "switch@site>", HardwareXmlPreset.COMMAND
        )
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(
            b"<rpc-reply><ok/></rpc-reply>\nswitch@site>", "switch@site>", HardwareXmlPreset.COMMAND
        )


@pytest.mark.parametrize(
    "output_format, expected_extensions",
    [("xml", [".xml"]), ("json", [".json"]), ("both", [".json", ".xml"])],
)
def test_hardware_artifact_modes_archive_only_selected_files(
    tmp_path: Path, output_format: str, expected_extensions: list[str]
) -> None:
    """Write distinct safe files and include them in the existing archive and manifest."""
    xml = "<rpc-reply><chassis-inventory><chassis><name>EX-1</name></chassis></chassis-inventory></rpc-reply>"
    document = HardwareXmlSupport.Decoder.decode_output(
        (xml + "\nswitch@site>").encode(), "switch@site>", HardwareXmlPreset.COMMAND
    )
    native_json = '{\r\n  "chassis-inventory": [{"chassis": [{"name": [{"data": "EX-1"}]}]}]\r\n}'
    json_document = HardwareXmlSupport.Decoder.decode_output(
        (native_json + "\n{master:0}\nswitch@site>").encode(),
        "switch@site>",
        HardwareXmlPreset.COMMANDS["json"],
    )
    manager = SimpleNamespace(session=lambda _session_id: SimpleNamespace(live=False))  # Keep archive access local.
    artifacts = SessionArtifactService(manager, None, tmp_path)  # Use only pytest's private temporary directory.
    target = SimpleNamespace(
        target_key='["org","site","device"]',
        identity={"target_id": "device-1", "label": "../EX Switch"},
    )  # Exercise the stable target-id fallback and unsafe hostname normalization.
    writer = artifacts.prepare_batch(
        (target,),
        {"preset": "ex-hardware-xml", "format": output_format, "mode": "combined"},
    )  # Prevent generic JSONL output for this dedicated artifact layout.
    files = ()
    for selected in (("xml", "json") if output_format == "both" else (output_format,)):
        selected_document = document if selected == "xml" else json_document
        files += writer.write_hardware(target.target_key, target.identity, selected_document, selected)
    writer.finish([{"target": dict(target.identity), "state": "completed", "files": list(files)}])
    artifacts.bind_batch("hardware-session", writer)  # Bind only after the output is complete.
    manifest = artifacts.manifest("hardware-session")
    assert sorted(Path(name).suffix for name in manifest["files"]) == expected_extensions
    assert manifest["targets"][0]["files"] == list(files)  # Keep per-device filenames in the outcome record.
    assert all(".." not in Path(name).parts for name in files)  # Keep hostname traversal out of paths.
    archive_name, archive_bytes = artifacts.zip_download("hardware-session")
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        names = archive.namelist()
        output_names = [name for name in names if name.startswith("hardware/")]
        assert sorted(Path(name).suffix for name in output_names) == expected_extensions
        assert "manifest.json" in names
        for name in output_names:
            if name.endswith(".xml"):
                assert archive.read(name).decode("utf-8") == xml  # Keep XML as the complete raw device document.
            if name.endswith(".json"):
                assert archive.read(name).decode("utf-8") == native_json
    assert archive_name.endswith(".zip")


def test_hardware_artifact_names_are_case_insensitive_unique_and_require_device_id() -> None:
    """Use a stable identity suffix when names collide or are unsafe."""
    first = HardwareXmlSupport.ArtifactNames.safe_paths({"label": "EX/Switch", "device_id": "ID:One"}, "xml")
    second = HardwareXmlSupport.ArtifactNames.safe_paths({"label": "ex\\switch", "device_id": "ID:Two"}, "xml")
    assert first[0] != second[0]  # Distinct stable IDs prevent case-insensitive hostname collisions.
    assert "/" not in Path(first[0]).name and "\\" not in Path(first[0]).name
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.ArtifactNames.safe_paths({"label": "Unnamed"}, "xml")


def test_hardware_both_mode_keeps_xml_if_native_json_cannot_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the successful XML file when the independent JSON publication fails."""
    xml = "<rpc-reply><chassis-inventory/></rpc-reply>"
    document = HardwareXmlSupport.Decoder.decode_output(
        (xml + "\nswitch@site>").encode(), "switch@site>", HardwareXmlPreset.COMMAND
    )
    target = SimpleNamespace(
        target_key="target",
        identity={"device_id": "device-1", "label": "EX-1"},
    )
    artifacts = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = artifacts.prepare_batch(
        (target,),
        {"preset": HardwareXmlPreset.NAME, "format": "both", "mode": "combined"},
    )
    xml_files = writer.write_hardware(target.target_key, target.identity, document, "xml")
    native_json = '{"chassis-inventory":[{"chassis":[{"name":[{"data":"EX-1"}]}]}]}'
    json_document = HardwareXmlSupport.Decoder.decode_output(
        (native_json + "\nswitch@site>").encode(), "switch@site>", HardwareXmlPreset.COMMANDS["json"]
    )
    replace_file = os.replace
    renames = 0

    def fail_second_rename(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        """Publish the first format, then simulate an atomic-publish failure."""
        nonlocal renames
        renames += 1
        if renames == 1:
            raise OSError("simulated rename failure")
        replace_file(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_rename)
    with pytest.raises(StreamRequestError):
        writer.write_hardware(target.target_key, target.identity, json_document, "json")
    assert writer._record.files == set(xml_files)
    assert (tmp_path / writer.artifact_id / xml_files[0]).read_text() == xml
    assert list((tmp_path / writer.artifact_id / "hardware").glob("*.json")) == []


@pytest.mark.parametrize("quota", ["file", "run"])
def test_hardware_output_quotas_reject_without_publishing_success_files(tmp_path: Path, quota: str) -> None:
    """Apply the existing file and whole-run quotas to selected raw formats."""
    xml = "<rpc-reply><chassis-inventory/></rpc-reply>"
    document = HardwareXmlSupport.Decoder.decode_output(
        (xml + "\nswitch@site>").encode(), "switch@site>", HardwareXmlPreset.COMMAND
    )
    target = SimpleNamespace(target_key="target", identity={"device_id": "device-1", "label": "EX-1"})
    artifacts = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = artifacts.prepare_batch(
        (target,),
        {"preset": HardwareXmlPreset.NAME, "format": "xml", "mode": "combined"},
    )
    if quota == "file":
        artifacts.RECORD_LIMIT = 4
    else:
        artifacts.OUTPUT_LIMIT = 1
    with pytest.raises(StreamRequestError):
        writer.write_hardware(target.target_key, target.identity, document, "xml")
    assert not list((tmp_path / writer.artifact_id / "hardware").glob("*.xml"))


def test_hardware_output_fails_closed_when_secret_redaction_would_change_xml() -> None:
    """Never redact and save mutated device XML containing a recognized credential."""
    xml = "<rpc-reply><chassis-inventory><note>api_token=private-value</note></chassis-inventory></rpc-reply>"
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(
            (xml + "\nswitch@site>").encode(), "switch@site>", HardwareXmlPreset.COMMAND
        )


def test_batch_start_admits_a_preview_once(tmp_path: Path) -> None:
    """Batch start admits one checked parent and consumes its preview."""
    site_field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")
    definition = ChannelDefinition(
        "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/{site_id}", (site_field,)
    )  # Build a site-scoped read-only channel.
    manager = FakeManager()  # Observe the one public session admission.
    service = make_batch_service(FakeBatchChecker(definition), FakeBatchPicker(), manager, tmp_path)
    preview = service.preview(
        {
            "operation": {"kind": "channel", "key": definition.key},
            "selection": {"sites": {"mode": "all"}},
            "parameters": {},
            "scope_revision": 9,
        }
    )  # Resolve the exact target snapshot before admission.
    result = service.start({"preview_id": preview["preview_id"]})  # Admit the server-owned snapshot.
    assert result["session_id"] == "abc123"  # Preserve the manager response.
    assert manager.started is True  # The manager received the parent request.
    with pytest.raises(StreamRequestError) as error:
        service.start({"preview_id": preview["preview_id"]})  # A second start cannot reuse the snapshot.
    assert error.value.code == "preview_consumed"  # Report reuse with the stable contract error.


def test_batch_artifacts_are_redacted_grouped_pinned_and_deleted(tmp_path: Path) -> None:
    """Batch artifacts keep safe target files and block deletion during download."""
    manager = SimpleNamespace(
        session=lambda _session_id: SimpleNamespace(
            live=False, ended_at=datetime.now(UTC).isoformat().replace("+00:00", "Z")
        ),
        delete=lambda _session_id: None,
    )  # Provide one ended public parent.
    service = SessionArtifactService(manager, None, tmp_path)  # Keep output in the test directory.
    target = SimpleNamespace(
        target_key='["org","device","site","device-1"]',
        identity={"site_id": "site-1", "device_id": "device-1", "label": "Switch"},
    )  # Use one natural target identity.
    writer = service.prepare_batch((target,), {"mode": "both", "group_by": "site"})  # Save both requested layouts.
    writer.write_result(target.target_key, target.identity, "message", "api_token=private-value", None)
    writer.finish([{"target": dict(target.identity), "state": "completed", "result_count": 1}])
    service.bind_batch("parent-1", writer)  # Bind output after public manager admission.
    manifest = service.manifest("parent-1")  # Read safe paths and target outcome.
    assert manifest["status"] == "ready"  # The final output is complete.
    assert len(manifest["files"]) == 2  # Combined and grouped records both exist.
    assert "private-value" not in str(manifest)  # No secret enters metadata.
    filename, lines = service.download("parent-1")  # Pin one combined result snapshot.
    assert filename.endswith(".jsonl")  # Preserve the established parent download type.
    with pytest.raises(StreamRequestError) as error:
        service.delete("parent-1")  # A live response pin blocks removal.
    assert error.value.code == "cleanup_pending"  # Keep cleanup retryable.
    downloaded = "".join(lines)  # Closing the iterator releases its pin.
    assert "private-value" not in downloaded  # Redaction applies before persistence.
    zip_name, archive_bytes = service.zip_download("parent-1")  # Build the saved layout snapshot.
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        names = archive.namelist()  # Inspect only archive-relative names.
        assert "manifest.json" in names  # Include the final target manifest.
        assert all(not name.startswith("/") and ".." not in Path(name).parts for name in names)
        assert "private-value" not in archive.read("results/combined.jsonl").decode("utf-8")
    assert zip_name.endswith(".zip")  # Give the archive a server-created file name.
    service.delete("parent-1")  # Delete only the ended parent and its private tree.
    assert not (tmp_path / writer.artifact_id).exists()  # Confirm exact artifact cleanup.


def test_batch_artifacts_enforce_output_quota_and_symlink_boundary(tmp_path: Path) -> None:
    """Batch artifact writes reject quota overflow and linked output folders."""
    service = SessionArtifactService(SimpleNamespace(), None, tmp_path)  # Use isolated output storage.
    target = SimpleNamespace(target_key="target", identity={"site_id": "site-1"})  # Use one safe target.
    writer = service.prepare_batch((target,), {"mode": "combined", "group_by": "site"})  # Create one result tree.
    service.OUTPUT_LIMIT = 1  # Lower the test limit without changing the global contract.
    with pytest.raises(StreamRequestError) as quota_error:
        writer.write_result("target", target.identity, "message", "output", None)  # Attempt one over-limit row.
    assert quota_error.value.code == "output_failed"  # Report the storage contract failure.
    writer.discard()  # Remove the exact private test tree.
    service.OUTPUT_LIMIT = 63 * 1024 * 1024  # Restore the production output bound for the link check.
    linked_writer = service.prepare_batch((target,), {"mode": "combined", "group_by": "site"})
    outside = tmp_path / "outside"  # The link target must remain untouched.
    outside.mkdir()
    try:
        (tmp_path / linked_writer.artifact_id / "results").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        linked_writer.discard()  # Keep the no-link path clean when Windows has no symlink privilege.
        pytest.skip(f"Symlink creation is unavailable on this host: {error}")
    with pytest.raises(StreamRequestError) as link_error:
        linked_writer.write_result("target", target.identity, "message", "output", None)
    assert link_error.value.code == "output_failed"  # Refuse a linked output directory.
    linked_writer.discard()  # Remove only the private tree and its link.
    assert outside.is_dir()  # The external directory remains unchanged.
