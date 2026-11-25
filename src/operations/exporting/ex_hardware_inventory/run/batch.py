"""Drive the portal batch service layer from the command line, one organization at a time.

Why:
    The Multi Site tab already discovers the connected EX switches, re-checks
    their status, opens bounded shells, and saves each reply under a private run
    folder. The CLI needs the same work without a browser. This module builds
    that service stack without Flask for one organization, previews the targets,
    starts the batch with the confirmed preview, and returns one result for each
    target. A preview expires after five minutes, so a long run previews each
    organization again just before it starts, and it refuses to run a target
    that the operator did not confirm.
"""

from __future__ import annotations

import logging  # Record each preview, start, and read for the operator trace.
from collections.abc import Iterable, Mapping  # Targets are read-only identity mappings.
from dataclasses import dataclass, replace  # Keep each value immutable.
from datetime import UTC, datetime, timedelta  # Preview expiry uses UTC ISO 8601 text.
from pathlib import Path  # The run folder root is a path.
from typing import Any  # The SDK session has no public type.

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Channel definitions.
from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import StreamCatalog  # The joined catalog.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog  # Utilities.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Refusals of the service.
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # Mist reads.
from src.mist.realtime.websocket_streams.intake.start_request.checker import StartRequestChecker  # Request checks.
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import RunnerFactory  # Shell runners.
from src.mist.realtime.websocket_streams.live.sessions.manager.lifecycle import StreamSessionManager  # Sessions.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # Limits and flags.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import SessionArtifactService  # Folders.
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import HardwareXmlPreset  # The preset.
from src.mist.realtime.websocket_streams.web.services.operations.sessions import WebSocketBatchService  # Batches.
from src.mist.realtime.websocket_streams.web.services.pickers.related import BatchTargetPickerService  # Targets.
from src.operations.exporting.ex_hardware_inventory.report.builder import TargetResult  # One result for each target.
from src.operations.exporting.ex_hardware_inventory.run.watch import BatchWatcher, RunFolder  # Wait and read.
from src.operations.exporting.ex_hardware_inventory.scope.session import AdmissionBinding  # Ledger organization.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


@dataclass(frozen=True)
class BatchPreview:
    """What the preview of one organization found.

    Attributes:
        org_id: The organization identifier.
        org_name: The organization name.
        preview_id: The opaque reference of the stored preview, empty when no target exists.
        phrase: The confirmation phrase of the service for this organization, empty when no target exists.
        expires_at: The preview deadline in UTC ISO 8601 text, empty when no target exists.
        targets: One identity for each target. Each identity holds a ``target_key``.
        excluded: The count of each left-out reason: offline, unknown_status, incompatible_family, duplicate_device.
    """

    org_id: str  # The natural key of the organization.
    org_name: str  # Shown to the operator.
    preview_id: str  # Needed to start the batch.
    phrase: str  # The service checks it at the start.
    expires_at: str  # The service refuses an expired preview.
    targets: tuple[Mapping[str, object], ...]  # The confirmed switches.
    excluded: Mapping[str, int]  # Why a device is not a target.

    @property
    def target_keys(self) -> frozenset[str]:
        """Return the stable key of each target."""
        return frozenset(str(item["target_key"]) for item in self.targets)  # The service builds one key each.

    def expired(self, margin_seconds: float = 20.0) -> bool:
        """Return True when the preview is expired or expires within the margin."""
        if not self.expires_at:  # A preview with no target stores nothing, so nothing can expire.
            return True  # It cannot start a batch.
        deadline = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))  # The service writes UTC text.
        return datetime.now(UTC) >= deadline - timedelta(seconds=margin_seconds)  # The start needs a live preview.

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], org_id: str, org_name: str) -> BatchPreview:
        """Build the preview from the payload of the service."""
        confirmation = payload.get("confirmation") or {}  # The service names the phrase for a shell batch.
        return cls(
            org_id,
            org_name,
            str(payload["preview_id"]),
            str(confirmation.get("phrase") or ""),
            str(payload["expires_at"]),
            tuple(dict(item) for item in payload["targets"]),
            {str(key): int(value) for key, value in dict(payload.get("excluded") or {}).items()},
        )  # Copy every value, so a later change of the payload cannot reach the preview.

    @classmethod
    def empty(cls, org_id: str, org_name: str, excluded: Mapping[str, int]) -> BatchPreview:
        """Build the preview of an organization that has no connected EX switch."""
        return cls(org_id, org_name, "", "", "", (), {str(key): int(value) for key, value in excluded.items()})


@dataclass(frozen=True)
class BatchRunResult:
    """What one organization run produced.

    Attributes:
        run_id: The run folder name, empty when no batch started.
        cancelled: True when the batch was stopped before it ended by itself.
        results: One result for each confirmed target.
        reason: ``new_targets`` or ``no_longer_connected`` when the organization was not run, otherwise empty.
    """

    run_id: str  # The folder under data/websocket-streams.
    cancelled: bool  # Marks the run partial.
    results: tuple[TargetResult, ...]  # One for each confirmed target.
    reason: str = ""  # Empty when the batch ran.

    @classmethod
    def skipped(
        cls, targets: Iterable[Mapping[str, object]], org_name: str, reason: str, state: str = "skipped"
    ) -> BatchRunResult:
        """Build the result of targets that did not run, one result for each.

        Args:
            targets: The identities of the targets.
            org_name: The organization name for the report rows.
            reason: The reason code of each result.
            state: ``skipped`` for a target that was not attempted, or ``stopped`` for a cancelled run.
        """
        return cls(
            "", state == "stopped", tuple(TargetResult(item, org_name, state, reason, None) for item in targets), reason
        )


class BatchStack:
    """The portal batch services for one organization, built without Flask."""

    def __init__(self, apisession: Any, org_id: str, root: Path, settings: StreamSettings | None = None) -> None:
        """Build the services for one organization.

        Args:
            apisession: The Mist API session of the CLI.
            org_id: The organization to read.
            root: The folder that holds the run folders, ``data/websocket-streams`` in production.
            settings: The WebSocket limits, or None to read the environment.
        """
        self.settings = replace(settings or StreamSettings.from_environment(), shell_enabled=True)  # CLI shells.
        self.apisession, self.org_id, self.root = apisession, org_id, root  # What the run helpers need.
        catalog = StreamCatalog(ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=True)
        picker = StreamPickerService(apisession, org_id)  # Discovery and the status re-check.
        checker = StartRequestChecker(catalog, picker, org_id)  # Builds each target request for the organization.
        self.manager = StreamSessionManager(self.settings, RunnerFactory(apisession, settings=self.settings))
        self.artifacts = SessionArtifactService(self.manager, None, root)  # The private run folders.
        self.manager.set_artifact_cleanup(self.artifacts.cleanup_expired)  # Retention removes only expired trees.
        targets = BatchTargetPickerService(picker, catalog, None)  # The catalog decides which targets exist.
        self.service = WebSocketBatchService(checker, targets, self.manager, self.artifacts, None)  # The batch API.

    @property
    def concurrency(self) -> int:
        """Return the most shells open at the same time: the setting, capped by the shared transport capacity."""
        return min(self.settings.hardware_concurrency, self.settings.max_sessions)

    def shutdown(self) -> None:
        """Stop every session and helper thread of the stack."""
        logger.info("Shutting down the batch services")  # Log before the stop.
        self.manager.shutdown()  # Stops live runners and the reaper, and is safe to repeat.
        logger.debug("Shut down the batch services")  # Log the result.


class OrganizationBatchRun:
    """Run the hardware batch of one organization through the portal service layer."""

    REQUEST = {"preset": HardwareXmlPreset.NAME, "format": "xml", "scope_revision": 0}  # Fixed, the CLI has no page.

    def __init__(self, stack: BatchStack, org_name: str) -> None:
        """Store the services and the organization name.

        Args:
            stack: The batch services of the organization.
            org_name: The organization name for the report rows and the console.
        """
        self._stack = stack  # The service, the manager, and the folder root.
        self._org_name = org_name  # The batch identity holds the organization identifier only.

    def preview(self) -> BatchPreview:
        """Find the connected EX switches of the organization.

        Returns:
            The preview. It holds no target when no connected EX switch exists.

        Raises:
            StreamRequestError: When discovery fails or the organization has more than 1000 targets.
        """
        logger.info("Previewing the connected EX switches of one organization")  # Log before the reads.
        try:  # An organization with no connected switch is a normal answer, not an error.
            with AdmissionBinding(self._stack.apisession, self._stack.org_id):  # Site reads need the organization.
                payload = self._stack.service.preview(dict(self.REQUEST))  # Discovery, filter, and snapshot.
        except StreamRequestError as error:  # The service refuses an empty selection with its counts.
            excluded = error.extra.get("excluded")  # Only the empty-selection refusal carries the counts.
            if error.code != "bad_request" or not isinstance(excluded, dict):  # Any other refusal is a failure.
                raise  # The operation reports it for this organization.
            logger.debug("The preview found no connected EX switch")  # Log the result.
            return BatchPreview.empty(self._stack.org_id, self._org_name, excluded)
        preview = BatchPreview.from_payload(payload, self._stack.org_id, self._org_name)  # Copy the payload.
        logger.debug("Previewed %d targets", len(preview.targets))  # Log the count only.
        return preview  # The operator confirms this snapshot.

    def run(self, confirmed: BatchPreview) -> BatchRunResult:
        """Start the confirmed organization and wait for the batch to end.

        Args:
            confirmed: The preview that the operator confirmed.

        Returns:
            One result for each confirmed target. A target that did not run has a skipped result.
        """
        logger.info("Starting the hardware batch of one organization")  # Log before the start.
        with AdmissionBinding(self._stack.apisession, self._stack.org_id):  # Worker threads read site paths.
            current = self.preview() if confirmed.expired() else confirmed  # A preview lasts five minutes.
            if not current.target_keys <= confirmed.target_keys:  # A switch that the operator never saw.
                return BatchRunResult.skipped(confirmed.targets, self._org_name, "new_targets")
            if not current.targets:  # Every confirmed switch went offline.
                return BatchRunResult.skipped(confirmed.targets, self._org_name, "no_longer_connected")
            session_id = self._start(current)  # Admit the batch with the preview phrase.
            cancelled = BatchWatcher(self._stack, session_id).wait(len(current.targets))  # Ctrl+C stops it.
            run_id, results = RunFolder(self._stack, self._org_name).collect(session_id, cancelled)  # Outcomes.
        gone = [item for item in confirmed.targets if str(item["target_key"]) not in current.target_keys]
        extra = BatchRunResult.skipped(gone, self._org_name, "no_longer_connected").results  # Left out.
        logger.debug("Finished the batch with %d results and %d left out", len(results), len(extra))  # Log.
        return BatchRunResult(run_id, cancelled, results + extra)  # One result for each confirmed target.

    def _start(self, preview: BatchPreview) -> str:
        """Admit the batch and return its public session identifier."""
        body = {
            "preview_id": preview.preview_id,
            "confirmation": preview.phrase or None,  # The operator already confirmed the total.
            "concurrency": self._stack.concurrency,  # The setting that both front ends read.
            "output": {"mode": "combined", "group_by": "site"},  # The hardware preset saves files, not a layout.
        }  # The exact fields that the service accepts.
        payload = self._stack.service.start(body)  # Consumes the preview and starts the worker threads.
        return str(payload["session_id"])  # The public identifier of the parent session.
