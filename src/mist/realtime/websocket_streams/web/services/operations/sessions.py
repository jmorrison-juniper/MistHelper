"""Own WebSocket session lifecycle service behavior."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import hashlib  # Preview fingerprints bind exact server snapshots.
import hmac  # Compare preview digests without timing shortcuts.
import json  # Canonical JSON keeps preview digests stable.
import logging  # Structured events use repository handlers.
import secrets  # Preview references must be hard to guess.
import threading  # Web requests share preview records.
import time  # Preview expiry uses monotonic time.
from collections.abc import Mapping  # Request bodies use explicit interfaces.
from dataclasses import dataclass, replace  # Preview records and parent requests are immutable values.
from datetime import UTC, datetime, timedelta  # Preview deadlines use UTC text.
from typing import Any, cast  # Session collaborators use behavior types.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    Safety,
    UtilityDefinition,
)  # Catalog metadata controls targets and safety.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse actions while not ready.
from src.mist.realtime.websocket_streams.intake.identifiers.identity_rules import (
    IdentityIdentifierRules,
)  # Selected site values must be Mist identifiers.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    BatchExecutionPlan,
    BatchTargetRequest,
    StartRequest,
)  # Preview records retain checked requests.
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import MessagePage  # Type message reads.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import (
    BatchArtifactWriter,
    SessionArtifactService,
)  # Store redacted batch output before admission.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep session fields safe and bounded.


@dataclass(slots=True)
class BatchPreviewRecord:
    """Hold one private, expiring batch execution snapshot."""

    preview_id: str  # The browser receives only this opaque reference.
    owner_scope: str  # A process-private value prevents cross-service reuse.
    org_id: str  # The configured organization is part of the snapshot.
    operation: dict[str, object]  # Catalog identity and safe display metadata.
    targets: tuple[BatchTargetRequest, ...]  # Checked requests preserve exact target order.
    excluded: dict[str, int]  # The preview explains candidates that the catalog cannot run.
    parameters: dict[str, object]  # Only validated catalog values remain here.
    commands: tuple[str, ...]  # Shell text stays server-side until execution.
    fingerprint: str  # Canonical digest detects altered stored snapshots.
    scope_revision: int  # The response remains tied to the browser selection revision.
    created_mono: float  # Retention uses a monotonic deadline.
    expires_mono: float  # Admission rejects expired previews.
    expires_at: str  # The browser sees a UTC deadline.
    confirmation: str | None  # Risky batches require one exact server phrase.
    consumed: bool = False  # Admission consumes the snapshot at most once.


class _BatchServiceComponents:
    """Group private collaborators for the batch service in this source module."""

    TARGET_LIMIT = 1000  # A preview cannot admit more targets than this limit.
    PREVIEW_SECONDS = 300.0  # A target snapshot expires after five minutes.
    PREVIEW_KEEP_COUNT = 5  # Keep at most five previews in this portal scope.

    class Input:
        """Validate operator input before discovery or admission."""

        def __init__(self, checker: Any | None, picker: Any | None, reason: str | None) -> None:
            """Store readiness and catalog collaborators."""
            self.checker = checker  # The checker resolves catalog entries and target identities.
            self.picker = picker  # The picker must exist before a preview can read Mist.
            self.reason = reason  # Preserve the production readiness reason.

        def require_ready(self) -> None:
            """Refuse a request when the live collaborators are unavailable."""
            if self.reason is not None or self.checker is None or self.picker is None:  # Guard every live operation.
                raise StreamRequestError("not_ready", self.reason or "The WebSocket engine is not ready.")

        def selection(self, body: object) -> dict[str, object]:
            """Return validated operation, selection, and parameter values."""
            return self.SelectionParser(self).parse(body)  # Keep request parsing separate from target discovery.

        def commands(self, kind: str, definition: object, raw: object) -> tuple[str, ...]:
            """Validate the exact finite command list for a shell preview."""
            return self.CommandValidator().validate(kind, definition, raw)  # Shell limits stay in one validator.

        def start_values(self, body: object) -> tuple[str, str | None, int | None, dict[str, object]]:
            """Validate batch admission fields without execution data."""
            return self.StartFields().parse(body)  # Admission input has a separate boundary.

        class SelectionParser:
            """Resolve the operation and validate the preview request shape."""

            def __init__(self, source: _BatchServiceComponents.Input) -> None:
                """Store the checked catalog collaborators."""
                self.source = source  # Reuse the service input readiness boundary.

            def parse(self, body: object) -> dict[str, object]:
                """Build the server-owned operation selection."""
                values = self._selection_shape(body)  # Validate the browser-owned object shape first.
                kind, key, definition = self._operation(values["operation"])  # Resolve only catalog identities.
                selection, parameters, revision = self._selection_values(values)  # Validate all selector inputs.
                commands = self.source.commands(kind, definition, values.get("commands"))  # Check shell text.
                return {
                    "kind": kind,
                    "key": key,
                    "definition": definition,
                    "selection": selection,
                    "parameters": dict(parameters),
                    "commands": commands,
                    "scope_revision": revision,
                }  # Keep the preview values independent from the caller's dictionaries.

            def _selection_shape(self, body: object) -> Mapping[str, object]:
                """Require the exact set of accepted preview fields."""
                allowed = {"operation", "selection", "parameters", "commands", "scope_revision"}
                if not isinstance(body, Mapping):  # Preview input must be one JSON object.
                    raise StreamRequestError("bad_request", "The preview request must be an object.")
                if set(body) - allowed:  # Refuse browser-supplied execution paths or extra fields.
                    raise StreamRequestError("bad_request", "The preview request has an unknown field.")
                return cast(Mapping[str, object], body)  # Keep the validated request interface explicit.

            def _operation(self, raw: object) -> tuple[str, str, object]:
                """Resolve the catalog identity through the request checker."""
                if not isinstance(raw, Mapping) or set(raw) != {"kind", "key"}:
                    raise StreamRequestError("bad_request", "The preview request needs a catalog operation.")
                kind, key = raw.get("kind"), raw.get("key")
                if not isinstance(kind, str) or not isinstance(key, str):
                    raise StreamRequestError("bad_request", "The catalog operation is not valid.")
                self.source.require_ready()  # The checker is narrowed after the shared readiness check.
                checker = self.source.checker
                if checker is None:  # Keep static type narrowing explicit after the readiness check.
                    raise StreamRequestError("not_ready", self.source.reason or "The WebSocket engine is not ready.")
                return kind, key, checker.resolve_definition(kind, key)  # Apply catalog and lock rules.

            def _selection_values(
                self, values: Mapping[str, object]
            ) -> tuple[Mapping[str, object], Mapping[str, object], int]:
                """Validate selectors, parameters, and selection revision."""
                selection, parameters = values.get("selection"), values.get("parameters")
                if not isinstance(selection, Mapping) or not isinstance(parameters, Mapping):
                    raise StreamRequestError("bad_request", "The preview request needs selectors and parameters.")
                revision = values.get("scope_revision")
                if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
                    raise StreamRequestError("bad_request", "The selection revision is not valid.")
                return selection, parameters, revision  # Preserve the checked JSON mappings.

        class CommandValidator:
            """Enforce shell command type, count, and text limits."""

            def validate(self, kind: str, definition: object, raw: object) -> tuple[str, ...]:
                """Return exact command text or reject an unsupported command field."""
                if kind != "shell":  # Non-shell entries must not carry hidden command input.
                    if raw is not None:
                        raise StreamRequestError("bad_request", "Only shell batches accept commands.")
                    return ()  # Other operations have no command list.
                if not isinstance(definition, UtilityDefinition) or definition.safety is not Safety.SHELL:
                    raise StreamRequestError("bad_request", "The selected operation is not a shell.")
                if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
                    raise StreamRequestError("bad_request", "Enter between one and twenty shell commands.")
                commands = self._text_commands(raw)  # Reject mixed data before encoding command text.
                if any(self._invalid(command) for command in commands) or sum(map(self._size, commands)) > 16384:
                    raise StreamRequestError("bad_request", "The shell command list exceeds its text limits.")
                return commands  # Do not trim or rewrite an accepted command.

            def _text_commands(self, raw: list[object]) -> tuple[str, ...]:
                """Require text for each command while preserving its order."""
                if any(not isinstance(command, str) for command in raw):
                    raise StreamRequestError("bad_request", "Each shell command must be text.")
                return tuple(cast(str, command) for command in raw)  # The previous check narrows each item.

            def _invalid(self, command: str) -> bool:
                """Return whether command text violates per-command limits."""
                return (
                    not command
                    or self._size(command) > 4096
                    or any(ord(character) < 32 or ord(character) == 127 for character in command)
                )  # Keep control characters out of terminal input.

            @staticmethod
            def _size(command: str) -> int:
                """Measure the encoded byte count required by the command limit."""
                return len(command.encode("utf-8"))  # Mist command limits use UTF-8 bytes.

        class StartFields:
            """Validate preview admission and output layout fields."""

            def parse(self, body: object) -> tuple[str, str | None, int | None, dict[str, object]]:
                """Return the checked preview reference and output settings."""
                if not isinstance(body, Mapping) or set(body) - {
                    "preview_id",
                    "confirmation",
                    "concurrency",
                    "output",
                }:
                    raise StreamRequestError("bad_request", "The batch start request has an unknown or invalid field.")
                preview_id, phrase = body.get("preview_id"), body.get("confirmation")
                if not isinstance(preview_id, str) or not preview_id:
                    raise StreamRequestError("bad_request", "The batch start needs a preview identifier.")
                if phrase is not None and not isinstance(phrase, str):
                    raise StreamRequestError("confirmation", "The confirmation phrase is not valid.")
                concurrency = self._concurrency(body.get("concurrency"))
                output = self._output(body.get("output", {"mode": "combined", "group_by": "site"}))
                return preview_id, phrase, concurrency, output

            def _concurrency(self, raw: object) -> int | None:
                """Reject concurrency outside the supported range."""
                if raw is not None and (isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= 5):
                    raise StreamRequestError("bad_request", "Target concurrency must be from one to five.")
                return raw  # The check excludes booleans and other non-integer values.

            def _output(self, raw: object) -> dict[str, object]:
                """Validate the bounded result layout."""
                if not isinstance(raw, Mapping) or set(raw) - {"mode", "group_by"}:
                    raise StreamRequestError("bad_request", "The output layout is not valid.")
                mode, group_by = raw.get("mode"), raw.get("group_by")
                if mode not in {"combined", "grouped", "both"} or group_by not in {
                    "site",
                    "device_type",
                    "device",
                    "client",
                }:
                    raise StreamRequestError("bad_request", "The output layout is not supported.")
                return {"mode": mode, "group_by": group_by}  # Return only supported layout fields.

    class Targets:
        """Discover sites and resources, then build checked target requests."""

        def __init__(self, picker: Any | None, checker: Any | None, reason: str | None) -> None:
            """Store collaborators for complete target discovery."""
            self.picker = picker  # The picker returns complete organization and resource pages.
            self.checker = checker  # The checker validates each final target request.
            self.reason = reason  # Preserve the production readiness reason.
            self.sites = self.SiteResolver(picker, reason)  # Resolve selected sites before resources.
            self.resources = self.ResourceSelector()  # Apply the explicit all or selected resource mode.
            self.requests = self.TargetRequestFactory(checker, reason)  # Build safe request identities.

        def resolve(self, values: dict[str, object]) -> tuple[BatchTargetRequest, ...]:
            """Resolve selectors to complete checked target requests."""
            site_scoped, selector, has_resource = self._shape(values)
            sites = self.sites.resolve(values, site_scoped)  # Resolve all sites before resource expansion.
            rows, excluded = self._discover(sites, values)  # Require complete discovery for each site.
            selected = self.resources.select(rows, selector, has_resource)
            requests = [self.requests.build(values, row, label) for row, label in selected]
            unique = {target.target_key: target for target in requests}
            values["excluded"] = excluded  # Bind discovery explanations to the stored preview.
            return tuple(unique[key] for key in sorted(unique))

        def _shape(self, values: Mapping[str, object]) -> tuple[bool, object, bool]:
            """Validate selection fields and resolve the operation target shape."""
            definition = cast(ChannelDefinition | UtilityDefinition, values["definition"])
            fields = definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
            site_scoped = any(field.name == "site_id" for field in fields)
            selection = values["selection"]
            if not isinstance(selection, Mapping):
                raise StreamRequestError("bad_request", "The target selection is not valid.")
            allowed = {"sites", "resources"} if site_scoped else {"resources"}
            if set(selection) - allowed:
                raise StreamRequestError("bad_request", "The target selection has an unknown field.")
            selector = selection.get("resources")
            has_resource = any(field.name != "site_id" for field in fields)
            if has_resource and not self.resources.valid_selector(selector):
                raise StreamRequestError("bad_request", "The resource selection is not valid.")
            return site_scoped, selector, has_resource

        def _discover(
            self, sites: list[tuple[str | None, str | None]], values: Mapping[str, object]
        ) -> tuple[list[tuple[dict[str, object], str | None]], dict[str, int]]:
            """Collect checked resource rows and exclusion counts across sites."""
            rows: list[tuple[dict[str, object], str | None]] = []
            excluded: dict[str, int] = {}
            for site_id, site_label in sites:
                found_rows, counts = self._site_targets(site_id, values)
                rows.extend((row, site_label) for row in found_rows)
                for reason, count in counts.items():
                    name = str(reason)  # Normalize the controlled reason key for the public preview.
                    excluded[name] = excluded.get(name, 0) + count  # Sum exclusions across selected sites.
            return rows, excluded

        def _site_targets(
            self, site_id: str | None, values: Mapping[str, object]
        ) -> tuple[list[dict[str, object]], Mapping[str, int]]:
            """Require one complete picker response with valid exclusion counts."""
            if self.picker is None:
                raise StreamRequestError("not_ready", self.reason or "The WebSocket engine is not ready.")
            response = self.picker.targets(site_id, str(values["kind"]), str(values["key"]), {})
            rows, counts = response.get("rows"), response.get("excluded", {})
            if response.get("complete") is not True or not isinstance(rows, list):
                raise StreamRequestError("picker_incomplete", "Target discovery did not complete.")
            if not isinstance(counts, Mapping) or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts.values()
            ):
                raise StreamRequestError("picker_incomplete", "Target exclusions are not valid.")
            return [row for row in rows if isinstance(row, dict)], cast(Mapping[str, int], counts)

        class SiteResolver:
            """Resolve all or selected organization sites from complete discovery."""

            def __init__(self, picker: Any | None, reason: str | None) -> None:
                """Store the site discovery collaborator and readiness reason."""
                self.picker = picker  # The picker performs authenticated complete discovery.
                self.reason = reason  # Preserve the production readiness reason.

            def resolve(self, values: Mapping[str, object], site_scoped: bool) -> list[tuple[str | None, str | None]]:
                """Return selected site identifiers and safe display labels."""
                if not site_scoped:
                    return [(None, None)]  # Organization operations do not expand once per site.
                selection = values["selection"]
                selector = selection.get("sites") if isinstance(selection, Mapping) else None
                if (
                    not isinstance(selector, Mapping)
                    or selector.get("mode") not in {"all", "selected"}
                    or set(selector) - {"mode", "ids"}
                ):
                    raise StreamRequestError("bad_request", "The site selection is not valid.")
                rows = self._discover(values)
                chosen = self._choose(rows, cast(Mapping[str, object], selector))
                return [(str(row["id"]), str(row.get("label") or row.get("name") or row["id"])) for row in chosen]

            def _discover(self, values: Mapping[str, object]) -> list[dict[str, object]]:
                """Require complete organization site discovery."""
                if self.picker is None:
                    raise StreamRequestError("not_ready", self.reason or "The WebSocket engine is not ready.")
                response = self.picker.sites(str(values["kind"]), str(values["key"]))
                rows = response.get("rows")
                if response.get("complete") is not True or not isinstance(rows, list):
                    raise StreamRequestError("picker_incomplete", "Site discovery did not complete.")
                return [row for row in rows if isinstance(row, dict)]  # Ignore malformed rows as before.

            def _choose(self, rows: list[dict[str, object]], selector: Mapping[str, object]) -> list[dict[str, object]]:
                """Freeze either every site or the explicit validated site list."""
                mode, ids = selector.get("mode"), selector.get("ids", [])
                if mode == "all":
                    if ids not in ([], None):
                        raise StreamRequestError("bad_request", "All-site selection cannot include site identifiers.")
                    return rows  # Freeze all organization sites once.
                selected_ids = self._selected_ids(ids)
                by_id = {str(row.get("id")): row for row in rows}
                if len(set(selected_ids)) != len(selected_ids) or any(item not in by_id for item in selected_ids):
                    raise StreamRequestError("bad_request", "A selected site is unknown or repeated.")
                return [by_id[item] for item in selected_ids]

            def _selected_ids(self, raw: object) -> list[str]:
                """Require one or more valid unique site identifiers."""
                if (
                    not isinstance(raw, list)
                    or not raw
                    or any(not isinstance(item, str) or not IdentityIdentifierRules.is_uuid(item) for item in raw)
                ):
                    raise StreamRequestError("bad_request", "Select one or more valid site identifiers.")
                return cast(list[str], raw)  # The UUID check requires every item to be a string.

        class ResourceSelector:
            """Apply all or explicit resource selection to verified rows."""

            @staticmethod
            def valid_selector(value: object) -> bool:
                """Return whether a selector has one supported mode and mapping shape."""
                return isinstance(value, Mapping) and value.get("mode") in {"all", "selected"}

            def select(
                self,
                rows: list[tuple[dict[str, object], str | None]],
                selector: object,
                has_resource: bool,
            ) -> list[tuple[dict[str, object], str | None]]:
                """Return verified resources in the operator's selected order."""
                if not has_resource:
                    if selector is not None:
                        raise StreamRequestError("bad_request", "This operation does not accept resource selection.")
                    return rows
                selection = self._selection(selector)
                if selection.get("mode") == "all":
                    if selection.get("targets") not in ([], None):
                        raise StreamRequestError("bad_request", "All-resource selection cannot include targets.")
                    return rows
                return self._selected(rows, selection.get("targets"))

            def _selection(self, raw: object) -> Mapping[str, object]:
                """Validate resource selector fields before reading requested identities."""
                if not isinstance(raw, Mapping) or set(raw) - {"mode", "targets"}:
                    raise StreamRequestError("bad_request", "The resource selection is not valid.")
                return cast(Mapping[str, object], raw)  # The browser input is now a checked mapping.

            def _selected(
                self, rows: list[tuple[dict[str, object], str | None]], raw: object
            ) -> list[tuple[dict[str, object], str | None]]:
                """Resolve requested natural keys and preserve their first occurrence."""
                if not isinstance(raw, list) or not raw or any(not isinstance(item, Mapping) for item in raw):
                    raise StreamRequestError("bad_request", "Select one or more resources.")
                index = {self.natural_key(row): (row, label) for row, label in rows}
                keys = [self.natural_key(cast(Mapping[str, object], item)) for item in raw]
                if any(key not in index for key in keys):
                    raise StreamRequestError("bad_request", "A selected resource is not eligible.")
                unique_keys = tuple(dict.fromkeys(keys))
                return [index[key] for key in unique_keys]

            @staticmethod
            def natural_key(row: Mapping[str, object]) -> str:
                """Return the stable JSON key for one target identity."""
                fields = ("target_type", "site_id", "id", "device_id", "map_id", "mac")
                values = [row.get(field) for field in fields]
                return json.dumps(values, ensure_ascii=True, separators=(",", ":"))

        class TargetRequestFactory:
            """Build checked requests and natural-key target identities."""

            ID_FALLBACKS = {"device_id", "map_id", "asset_id", "mxedge_id", "sdkclient_id"}

            def __init__(self, checker: Any | None, reason: str | None) -> None:
                """Store the request checker and readiness reason."""
                self.checker = checker  # The checker injects organization scope and validates target fields.
                self.reason = reason  # Preserve the production readiness reason.
                self.identities = _BatchServiceComponents.Targets.TargetIdentity()

            def build(
                self, values: Mapping[str, object], row: dict[str, object], site_label: str | None
            ) -> BatchTargetRequest:
                """Check one target and bind its stable display and identity fields."""
                definition = cast(ChannelDefinition | UtilityDefinition, values["definition"])
                fields = definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
                target_values = self._target_values(fields, row)
                if self.checker is None:
                    raise StreamRequestError("not_ready", self.reason or "The WebSocket engine is not ready.")
                request = self.checker.check_batch(
                    {
                        "kind": values["kind"],
                        "key": values["key"],
                        "targets": target_values,
                        "parameters": values["parameters"],
                    }
                )
                identity, key = self.identities.build(request, row, site_label)
                return BatchTargetRequest(key, identity, request)

            def _target_values(self, fields: Any, row: Mapping[str, object]) -> dict[str, object]:
                """Map picker rows to the explicit target identifiers required by the catalog."""
                targets: dict[str, object] = {}
                for field in fields:
                    candidate = self._candidate(field.name, row)
                    if candidate is None:
                        raise StreamRequestError("bad_request", "A target is missing a required identity.")
                    targets[field.name] = candidate
                return targets

            def _candidate(self, name: str, row: Mapping[str, object]) -> object:
                """Resolve one target identifier from supported picker fields."""
                candidate = row.get(name)
                if name == "site_id":
                    return row.get("site_id") or (row.get("id") if row.get("target_type") == "site" else None)
                if candidate is not None:
                    return candidate
                if name in self.ID_FALLBACKS:
                    return row.get("id") if name != "map_id" or row.get("target_type") == "map" else row.get("map_id")
                return row.get("mac") or row.get("client_mac") if name.endswith("_mac") else None

        class TargetIdentity:
            """Build display identity and stable organization-scoped target keys."""

            DISPLAY_FIELDS = (
                ("org_id", None),
                ("site_id", "site_id"),
                ("site_label", None),
                ("target_type", "target_type"),
                ("target_id", "id"),
                ("device_id", "device_id"),
                ("device_type", "family"),
                ("map_id", "map_id"),
                ("client_mac", "mac"),
                ("label", "label"),
            )

            def build(
                self, request: Any, row: Mapping[str, object], site_label: str | None
            ) -> tuple[dict[str, object], str]:
                """Return display identity and its natural key."""
                organization = request.target("org_id")
                identity = self._display_fields(row, organization, site_label)
                identity["target_type"] = identity["target_type"] or "organization"
                return identity, self._key(organization, row)

            def _display_fields(
                self, row: Mapping[str, object], organization: object, site_label: str | None
            ) -> dict[str, object]:
                """Keep display values in the established response order."""
                return {
                    name: (
                        organization
                        if name == "org_id"
                        else site_label if name == "site_label" else row.get(source) if source is not None else None
                    )
                    for name, source in self.DISPLAY_FIELDS
                }

            def _key(self, organization: object, row: Mapping[str, object]) -> str:
                """Encode all target key fields in the established order."""
                fields = ("target_type", "site_id", "id", "device_id", "map_id", "mac")
                values: list[object] = [organization]
                for field in fields:
                    values.append(row.get(field))
                return json.dumps(values, ensure_ascii=True, separators=(",", ":"))

    class SessionLookup:
        """Resolve public sessions and require a batch execution plan."""

        def __init__(self, manager: Any) -> None:
            """Store the session manager used by batch reads."""
            self.manager = manager  # The manager owns every public session.

        def batch(self, session_id: str) -> Any:
            """Return one batch parent or its stable session refusal."""
            session = self.manager.session(session_id)
            if session.request.batch_plan is None:
                raise StreamRequestError("not_batch", "The session is not a Multi Site batch.")
            return session

    class Previews:
        """Create, serialize, retain, and admit immutable batch previews."""

        class Admission:
            """Refuse foreign, expired, consumed, or incorrectly confirmed previews."""

            @staticmethod
            def validate(
                record: BatchPreviewRecord,
                phrase: str | None,
                owner_scope: str,
                records: dict[str, BatchPreviewRecord],
            ) -> None:
                """Check scope, expiry, single-use, and confirmation state."""
                if record.owner_scope != owner_scope:
                    raise StreamRequestError("preview_scope", "The preview belongs to another portal scope.")
                if record.expires_mono <= time.monotonic():
                    records.pop(record.preview_id, None)
                    raise StreamRequestError("preview_expired", "The preview expired.")
                if record.consumed:
                    raise StreamRequestError("preview_consumed", "The preview already started a batch.")
                if record.confirmation is not None and phrase != record.confirmation:
                    raise StreamRequestError("confirmation", "Type the exact batch confirmation phrase.")
                if record.confirmation is None and phrase not in {None, ""}:
                    raise StreamRequestError(
                        "bad_request", "This read-only batch does not accept a confirmation phrase."
                    )

        class Store:
            """Retain private expiring previews and validate admission snapshots."""

            def __init__(
                self,
                checker: Any | None,
                reason: str | None,
                owner_scope: str,
                lock: threading.RLock,
            ) -> None:
                """Store private preview records and shared synchronization."""
                self.checker = checker  # The checker confirms catalog safety again at admission.
                self.reason = reason  # Preserve the production readiness reason.
                self.owner_scope = owner_scope  # Prevent reuse by another service instance.
                self.lock = lock  # Serialize pruning, retention, and admission.
                self.records: dict[str, BatchPreviewRecord] = {}  # Retain only the bounded recent previews.
                self.factory = _BatchServiceComponents.Previews.RecordFactory(owner_scope)

            def save(self, values: Mapping[str, object], targets: tuple[BatchTargetRequest, ...]) -> dict[str, object]:
                """Create and retain one immutable preview snapshot."""
                record, safety = self.factory.create(values, targets)
                self._retain(record)
                return _BatchServiceComponents.Previews.Serializer.preview_payload(record, safety)

            def admission(self, preview_id: str, phrase: str | None) -> BatchPreviewRecord:
                """Return one unexpired preview after scope and confirmation checks."""
                record = self.records.get(preview_id)
                if record is None:
                    raise StreamRequestError("preview_expired", "The preview expired or is unknown.")
                _BatchServiceComponents.Previews.Admission.validate(record, phrase, self.owner_scope, self.records)
                return record

            def validate_fingerprint(self, record: BatchPreviewRecord) -> None:
                """Check the current catalog lock and the stored snapshot digest."""
                operation = record.operation
                if self.checker is None:
                    raise StreamRequestError("not_ready", self.reason or "The WebSocket engine is not ready.")
                definition = self.checker.resolve_definition(str(operation["kind"]), str(operation["key"]))
                safety = definition.safety.value if isinstance(definition, UtilityDefinition) else "read"
                if safety != operation["safety"]:
                    raise StreamRequestError("preview_scope", "The operation safety changed after preview.")
                values = {
                    "kind": operation["kind"],
                    "key": operation["key"],
                    "parameters": record.parameters,
                    "commands": record.commands,
                }
                snapshot = _BatchServiceComponents.Previews.Serializer.fingerprint_payload(
                    values, record.targets, record.org_id
                )
                digest = hashlib.sha256(_BatchServiceComponents.Previews.Serializer.canonical(snapshot)).hexdigest()
                if not hmac.compare_digest(digest, record.fingerprint):
                    raise StreamRequestError("preview_scope", "The preview snapshot changed before admission.")

            def _retain(self, record: BatchPreviewRecord) -> None:
                """Prune expired records and keep only the newest bounded set."""
                now = record.created_mono
                with self.lock:
                    expired = [key for key, item in self.records.items() if item.expires_mono <= now]
                    for key in expired:
                        self.records.pop(key, None)
                    while len(self.records) >= _BatchServiceComponents.PREVIEW_KEEP_COUNT:
                        oldest = min(self.records.values(), key=lambda item: item.created_mono)
                        self.records.pop(oldest.preview_id, None)
                    self.records[record.preview_id] = record

        class RecordFactory:
            """Create expiring records with fingerprints bound to checked target state."""

            def __init__(self, owner_scope: str) -> None:
                """Store the private owner scope for new records."""
                self.owner_scope = owner_scope  # Bind every preview to its service instance.

            def create(
                self, values: Mapping[str, object], targets: tuple[BatchTargetRequest, ...]
            ) -> tuple[BatchPreviewRecord, str]:
                """Build the operation metadata and expiration fields."""
                definition = cast(ChannelDefinition | UtilityDefinition, values["definition"])
                safety = definition.safety.value if isinstance(definition, UtilityDefinition) else "read"
                confirmation = f"RUN {len(targets)} TARGETS" if safety in {"change", "shell"} else None
                org_id = targets[0].request.target("org_id")  # Read the organization injected by the checker.
                payload = _BatchServiceComponents.Previews.Serializer.fingerprint_payload(values, targets, org_id)
                digest = hashlib.sha256(_BatchServiceComponents.Previews.Serializer.canonical(payload)).hexdigest()
                now = time.monotonic()  # Use monotonic time for expiry checks.
                expires_at = self._expires_at()
                details = {
                    "safety": safety,
                    "confirmation": confirmation,
                    "org_id": org_id,
                    "fingerprint": digest,
                    "now": now,
                    "expires_at": expires_at,
                }
                record = BatchPreviewRecord(
                    **self._identity_fields(values, targets, details),
                    **self._state_fields(values, details),
                )
                return record, safety

            def _identity_fields(
                self,
                values: Mapping[str, object],
                targets: tuple[BatchTargetRequest, ...],
                details: Mapping[str, object],
            ) -> dict[str, Any]:
                """Return the checked operation and identity fields for a record."""
                definition = cast(ChannelDefinition | UtilityDefinition, values["definition"])
                safety = cast(str, details["safety"])
                operation = {"kind": values["kind"], "key": values["key"], "name": definition.name, "safety": safety}
                preview_id = secrets.token_urlsafe(24)
                org_id = cast(str, details["org_id"])
                scope_revision = cast(int, values["scope_revision"])
                return {
                    "preview_id": preview_id,
                    "owner_scope": self.owner_scope,
                    "org_id": org_id,
                    "operation": operation,
                    "targets": targets,
                    "scope_revision": scope_revision,
                }

            def _state_fields(
                self,
                values: Mapping[str, object],
                details: Mapping[str, object],
            ) -> dict[str, Any]:
                """Return the checked result, fingerprint, and expiration fields."""
                now = cast(float, details["now"])
                excluded = dict(cast(Mapping[str, int], values.get("excluded", {})))
                parameters = dict(cast(Mapping[str, object], values["parameters"]))
                commands = cast(tuple[str, ...], values["commands"])
                fingerprint = cast(str, details["fingerprint"])
                expires_at = cast(str, details["expires_at"])
                confirmation = cast(str | None, details["confirmation"])
                return {
                    "excluded": excluded,
                    "parameters": parameters,
                    "commands": commands,
                    "fingerprint": fingerprint,
                    "created_mono": now,
                    "expires_mono": now + _BatchServiceComponents.PREVIEW_SECONDS,
                    "expires_at": expires_at,
                    "confirmation": confirmation,
                }

            @staticmethod
            def _expires_at() -> str:
                """Return the browser deadline in UTC ISO 8601 form."""
                return (
                    (datetime.now(UTC) + timedelta(seconds=_BatchServiceComponents.PREVIEW_SECONDS))
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

        class Serializer:
            """Build canonical fingerprint data and safe browser preview payloads."""

            @staticmethod
            def canonical(snapshot: dict[str, object]) -> bytes:
                """Encode stable JSON for a snapshot fingerprint."""
                return json.dumps(snapshot, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")

            @staticmethod
            def fingerprint_payload(
                values: Mapping[str, object], targets: tuple[BatchTargetRequest, ...], org_id: str
            ) -> dict[str, object]:
                """Return canonical execution fields without display labels."""
                identities = [
                    {key: value for key, value in target.identity.items() if key not in {"label", "site_label"}}
                    for target in targets
                ]
                return {
                    "org_id": org_id,
                    "kind": values["kind"],
                    "key": values["key"],
                    "parameters": values["parameters"],
                    "commands": list(cast(tuple[str, ...], values["commands"])),
                    "targets": identities,
                }

            @staticmethod
            def preview_payload(record: BatchPreviewRecord, safety: str) -> dict[str, object]:
                """Return the safe browser view of one stored preview."""
                return {
                    "preview_id": record.preview_id,
                    "expires_at": record.expires_at,
                    "scope_revision": record.scope_revision,
                    "operation": record.operation,
                    "targets": [dict(target.identity, target_key=target.target_key) for target in record.targets],
                    "target_count": len(record.targets),
                    "excluded": record.excluded,
                    "confirmation": {
                        "required": record.confirmation is not None,
                        "phrase": record.confirmation,
                        "safety": safety,
                    },
                    "limits": {
                        "target_count": _BatchServiceComponents.TARGET_LIMIT,
                        "concurrency_min": 1,
                        "concurrency_max": 5,
                        "concurrency": 1 if record.operation["kind"] == "channel" else 3,
                        "shell_command_bytes": 4096,
                        "shell_total_bytes": 16384,
                        "output_bytes": 64 * 1024 * 1024,
                    },
                }

        class ParentRequest:
            """Create the one public request that owns a bounded batch plan."""

            @staticmethod
            def create(
                record: BatchPreviewRecord,
                concurrency: int | None,
                output: dict[str, object],
                writer: BatchArtifactWriter,
            ) -> StartRequest:
                """Build one checked parent request and its progress plan."""
                kind = str(record.operation["kind"])
                effective = _BatchServiceComponents.Previews.ParentRequest._concurrency(kind, concurrency)
                plan = BatchExecutionPlan(
                    record.targets,
                    effective,
                    record.commands,
                    output,
                    writer.artifact_id,
                    writer.write_result,
                    writer.finish,
                )
                title = f"Multi Site: {record.operation['name']} ({len(record.targets)} targets)"
                return replace(record.targets[0].request, title=title, batch_plan=plan)

            @staticmethod
            def _concurrency(kind: str, requested: int | None) -> int:
                """Enforce sequential channel batches and bounded utility batches."""
                effective = requested if requested is not None else (1 if kind == "channel" else 3)
                if kind == "channel" and effective != 1:
                    raise StreamRequestError("bad_request", "Channel batches require concurrency one.")
                if kind != "channel" and not 1 <= effective <= 5:
                    raise StreamRequestError("bad_request", "Target concurrency must be from one to five.")
                return effective


class WebSocketBatchService:
    """Create and retain validated Multi Site previews."""

    TARGET_LIMIT = _BatchServiceComponents.TARGET_LIMIT  # Keep the public target limit stable.
    PREVIEW_SECONDS = _BatchServiceComponents.PREVIEW_SECONDS  # Keep the public expiry stable.
    PREVIEW_KEEP_COUNT = _BatchServiceComponents.PREVIEW_KEEP_COUNT  # Keep retention bounded.

    def __init__(
        self,
        checker: Any | None,
        picker: Any | None,
        manager: Any,
        artifacts: SessionArtifactService,
        reason: str | None,
    ) -> None:
        """Compose batch input, target, and preview collaborators."""
        self._manager = manager  # The manager admits one public parent session.
        self._artifacts = artifacts  # Required output uses a bounded session-owned store.
        self._owner_scope = secrets.token_urlsafe(24)  # Bind previews to this service instance.
        self._lock = threading.RLock()  # Serialize preview retention and later admission.
        self._input = _BatchServiceComponents.Input(checker, picker, reason)
        self._targets = _BatchServiceComponents.Targets(picker, checker, reason)
        self._previews = _BatchServiceComponents.Previews.Store(checker, reason, self._owner_scope, self._lock)
        self._sessions = _BatchServiceComponents.SessionLookup(manager)

    def preview(self, body: object) -> dict[str, object]:
        """Create a complete server-side target snapshot without starting work."""
        self._input.require_ready()  # Refuse before reading Mist or accepting a body.
        values = self._input.selection(body)  # Validate operation, selectors, parameters, and commands.
        targets = self._targets.resolve(values)  # Discover and validate every selected target.
        if not targets:  # An empty preview must never appear startable.
            raise StreamRequestError("bad_request", "The selection has no eligible targets.")
        if len(targets) > self.TARGET_LIMIT:  # Refuse large selections before storing a preview.
            raise StreamRequestError("target_limit", "The selection exceeds the target limit.")
        return self._previews.save(values, targets)  # Store one immutable operation snapshot.

    def start(self, body: object) -> dict[str, object]:
        """Atomically consume one preview and admit one public batch session."""
        self._input.require_ready()  # Refuse before a preview or session can change.
        preview_id, phrase, concurrency, output = self._input.start_values(body)
        with self._lock:
            record = self._previews.admission(preview_id, phrase)
            self._previews.validate_fingerprint(record)
            writer = self._artifacts.prepare_batch(record.targets, output)
            parent = _BatchServiceComponents.Previews.ParentRequest.create(record, concurrency, output, writer)
            try:
                payload = cast(dict[str, object], self._manager.start(parent))
            except StreamRequestError:
                writer.discard()  # A checked admission refusal created no parent session.
                raise
            session_id = payload.get("session_id")
            if not isinstance(session_id, str):
                raise StreamRequestError("output_failed", "The admitted batch has no public session identifier.")
            self._artifacts.bind_batch(session_id, writer)
            record.consumed = True  # Consume only after the manager admits the parent.
        return payload  # Preserve the established public session response.

    def summary(self, session_id: str) -> dict[str, object]:
        """Return one existing public session with its batch summary."""
        session = self._sessions.batch(session_id)
        session.mark_read()  # Parent polling renews the existing idle read time.
        return cast(dict[str, object], session.payload())

    def targets(self, session_id: str, after: int, limit: int) -> dict[str, object]:
        """Return one bounded page of stable target outcomes."""
        if after < 0:
            raise StreamRequestError("bad_request", "The target cursor is not valid.")
        session = self._sessions.batch(session_id)
        plan = session.request.batch_plan
        if plan is None:
            raise StreamRequestError("not_batch", "The session is not a Multi Site batch.")
        return cast(
            dict[str, object],
            plan.progress.summary.target_page(after, min(500, max(1, limit))),
        )


class WebSocketSessionService:
    """Start, list, stop, and shut down sessions."""

    def __init__(self, checker: Any | None, manager: Any, reason: str | None) -> None:
        """Store the request checker, manager, and readiness."""
        self._checker = checker  # A not-ready service has no request checker.
        self._manager = manager  # The fallback manager still lists and shuts down.
        self._reason = reason  # A reason blocks actions that need Mist.

    def start(self, body: object) -> dict[str, object]:
        """Check and start one WebSocket session."""
        if self._reason is not None or self._checker is None:  # Starts need all production collaborators.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        logger.emit(logging.INFO, "web.session.start.begin")  # Record the bounded start action.
        checked = self._checker.check(body)  # Validate identifiers, targets, parameters, and confirmation.
        payload = cast(dict[str, object], self._manager.start(checked))  # Start the selected runner.
        logger.emit(logging.DEBUG, "web.session.start.finish", {"status": "started"})  # Log no identifier.
        return payload  # Return the established session payload.

    def list(self) -> dict[str, object]:
        """Return live and ended session payloads."""
        logger.emit(logging.DEBUG, "web.session.list.start")  # Polling uses debug-level structured events.
        payload = cast(dict[str, object], self._manager.list_payload())  # Read the manager snapshot.
        sessions = payload.get("sessions")  # Read the public session list for a bounded count.
        count = len(sessions) if isinstance(sessions, list) else 0  # Refuse a non-list count shape.
        logger.emit(logging.DEBUG, "web.session.list.finish", {"count": count})  # Report the bounded count.
        return payload  # Preserve limits and session fields.

    def stop(self, session_id: str) -> dict[str, object]:
        """Stop one live session."""
        logger.emit(logging.INFO, "web.session.stop.start")  # Record the bounded stop action.
        payload = cast(dict[str, object], self._manager.stop(session_id))  # Ask the manager to stop the runner.
        logger.emit(logging.DEBUG, "web.session.stop.finish", {"status": "stopped"})  # Log no identifier.
        return payload  # Preserve the stopped session payload.

    def shutdown(self) -> None:
        """Stop all sessions and helper threads."""
        logger.emit(logging.INFO, "web.session.shutdown.start")  # Record shutdown start.
        self._manager.shutdown()  # Stop live runners and the reaper.
        logger.emit(logging.DEBUG, "web.session.shutdown.finish", {"status": "stopped"})  # Confirm shutdown.


class WebSocketMessageService:
    """Read bounded message pages from one session manager."""

    def __init__(self, manager: Any) -> None:
        """Store the session manager."""
        self._manager = manager  # The manager owns each bounded message buffer.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return messages after one sequence number."""
        page = cast(MessagePage, self._manager.read(session_id, after, limit))  # Read the bounded buffer page.
        logger.emit(logging.DEBUG, "web.session.read.finish", {"count": len(page.messages)})  # Report count only.
        return page  # Preserve direct JSON text generation.
