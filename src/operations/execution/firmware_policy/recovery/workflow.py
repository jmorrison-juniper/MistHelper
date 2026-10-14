"""Share guarded complete restoration between the CLI and the protected graphical portal."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from ..sdk import PolicyApi, PolicyError
from .backup import BackupProof, PolicyBackup
from .bundle import BundleFiles, RestoreBundle, RestoreSelection
from .schema import RestoreSchema

logger = logging.getLogger(__name__)


@dataclass
class RestoreTarget:
    """Keep complete snapshots and settings bodies outside public representations."""

    scope: Literal["org", "site"]
    identifier: str
    organization: str
    original: dict[str, Any] = field(repr=False)
    body: dict[str, Any] = field(repr=False)
    name: str = ""
    organization_name: str = ""

    @property
    def key(self) -> str:
        """Give each result an unambiguous scope identifier."""
        return f"{self.scope}:{self.identifier}"

    def preview(self) -> dict[str, Any]:
        """Count writable effects without comparing excluded server-managed metadata."""
        changed = sum(
            key[1:] in self.original if key.startswith("-") else key not in self.original or self.original[key] != value
            for key, value in self.body.items()
        )
        return {
            "name": self.name,
            "scope": self.scope,
            "id": self.identifier,
            "organization_name": self.organization_name,
            "organization": self.organization,
            "fields": len(self.body),
            "deletions": sum(key.startswith("-") for key in self.body),
            "changed_fields": changed,
            "changed": changed > 0,
        }


@dataclass
class RestorePlan:
    """Bind one unchanged source bundle to a current cloud and complete selection."""

    cloud: str
    bundle: RestoreBundle = field(repr=False)
    targets: list[RestoreTarget] = field(repr=False)
    membership: dict[str, list[str]] = field(repr=False)
    exclusions: dict[str, list[str]]

    def preview(self) -> dict[str, Any]:
        """Show effects and exclusions without saved values or historical names."""
        return {
            "cloud": self.cloud,
            "targets": [target.preview() for target in self.targets],
            "excluded": self.exclusions,
            "writes": 0,
            "warning": (
                "Warning: restoration replaces complete writable settings, including changes made after the backup. "
                "Missing fields without proven deletion support stop restoration. "
                "A checksum is not an authentic signature. Verify the backup source and selected cloud. "
                "Organization settings are restored before sites. No firmware execution request is sent."
            ),
        }


@dataclass
class RestoreResult:
    """Separate verified completion from failed and unattempted targets."""

    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    remaining: list[str] = field(default_factory=list)
    error: str | None = None
    backups_verified: int = 0


@dataclass
class RestoreWorkflow:
    """Require source validation, freshness, recovery backups, and saved-state checks."""

    api: PolicyApi
    files: BundleFiles
    schema: RestoreSchema = field(default_factory=RestoreSchema)
    stopped: Callable[[], bool] = lambda: False
    progress: Callable[[dict[str, Any]], None] | None = None

    def __post_init__(self) -> None:
        """Connect restoration progress to the same SDK admission and quota waits."""
        if self.progress:
            self.api.progress = self.progress
            self.api.guard.progress = self.progress

    def event(self, phase: str, target: RestoreTarget | None, completed: int, total: int) -> None:
        """Send names and counts without saved or current settings values."""
        if self.progress:
            self.progress(
                {
                    "phase": phase,
                    "completed": completed,
                    "total": total,
                    **({"scope": target.scope, "id": target.identifier, "name": target.name} if target else {}),
                }
            )

    def prepare(self, token: str, selected: Any, cloud: str) -> RestorePlan:
        """Validate every selected record and dependency before producing a preview."""
        if cloud != RestoreSelection.cloud(self.api):
            raise PolicyError("Explicitly select the active Mist cloud for this legacy backup.")
        bundle = self.files.read(token)
        records = RestoreSelection.records(bundle, selected)
        organizations = {record["id"] for record in records if record["scope"] == "org"}
        listings = {organization: self.api.sites(organization) for organization in organizations}
        membership = RestoreSelection.membership(self.api, organizations, listings)
        names = self._names(organizations, listings)
        projected = self._project(bundle, records, membership, names)
        targets = [target for target, excluded in projected]
        exclusions = {target.key: excluded for target, excluded in projected}
        return RestorePlan(cloud, bundle, targets, membership, exclusions)

    def _names(self, organizations: set[str], listings: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
        """Resolve actual identity names once from admitted organization and site lists."""
        names = {organization: self.api.organization(organization)["name"] for organization in organizations}
        names.update(
            {site["id"]: str(site.get("name", site["id"])) for listing in listings.values() for site in listing}
        )
        return names

    def _project(
        self,
        bundle: RestoreBundle,
        records: list[dict[str, Any]],
        membership: dict[str, list[str]],
        names: dict[str, str],
    ) -> list[tuple[RestoreTarget, list[str]]]:
        """Build named private targets with constant-time membership tests."""
        indexed = {key: set(value) for key, value in membership.items()}
        projected = []
        for record in records:  # Use indexed memberships instead of scanning the source per selected site.
            target, excluded = self._target(bundle, record, indexed)
            target.organization_name = names[target.organization]
            target.name = names[target.identifier]
            projected.append((target, excluded))
            self.event("preparing", target, len(projected), len(records))
        projected.sort(key=lambda item: (item[0].scope, item[0].name.casefold(), item[0].identifier))
        return projected

    def _target(
        self, bundle: RestoreBundle, record: dict[str, Any], membership: dict[str, set[str]]
    ) -> tuple[RestoreTarget, list[str]]:
        """Bind a selected record to proven ownership and complete writable effects."""
        owner = RestoreSelection.ownership(bundle, record)
        if owner not in membership or (record["scope"] == "site" and record["id"] not in membership[owner]):
            raise PolicyError("Select the saved organization and only its current member sites.")
        original = self.api.read(record["scope"], record["id"])
        if original.get("org_id", owner) != owner or original.get("site_id", record["id"]) != record["id"]:
            raise PolicyError("The current settings ownership does not match the selected backup.")
        body, excluded = self.schema.body(record["scope"], record["settings"], original)
        return RestoreTarget(record["scope"], record["id"], owner, original, body), excluded

    def current(self, plan: RestorePlan) -> list[dict[str, Any]]:
        """Verify the source, cloud, memberships, and every current complete snapshot."""
        if self.stopped():
            raise PolicyError("The restoration was cancelled.")
        source = self.files.read(plan.bundle.token)
        if source != plan.bundle or RestoreSelection.cloud(self.api) != plan.cloud:
            raise PolicyError("The source backup or active cloud changed. Create a new preview.")
        if RestoreSelection.membership(self.api, set(plan.membership)) != plan.membership:
            raise PolicyError("Site membership changed. Create a new preview.")
        records = []
        for target in plan.targets:
            if self.stopped():
                raise PolicyError("The restoration was cancelled.")
            if self.api.read(target.scope, target.identifier) != target.original:
                raise PolicyError("Settings changed after preview. Create a new preview.")
            records.append({"scope": target.scope, "id": target.identifier, "settings": target.original})
        return records

    def back_up(self, plan: RestorePlan) -> BackupProof:
        """Save and verify every current snapshot before restoration confirmation."""
        if not plan.targets:
            raise PolicyError("The restoration has no selected target.")
        records = self.current(plan)
        self.event("backing_up", None, 0, len(records))
        path = self.files.backup.save(records)
        self.files.backup.verify(path, records)
        self.files.read(path.stem)
        self.event("backup_verified", None, len(records), len(records))
        return BackupProof(path, records, self.binding(plan))

    @staticmethod
    def binding(plan: RestorePlan) -> str:
        """Bind recovery to one cloud, source checksum, and exact selected write bodies."""
        return PolicyBackup.digest(
            [
                {
                    "cloud": plan.cloud,
                    "source": plan.bundle.checksum,
                    "targets": [
                        {"scope": target.scope, "id": target.identifier, "body": target.body} for target in plan.targets
                    ],
                }
            ]
        )

    def apply(self, plan: RestorePlan, confirmation: str, proof: BackupProof | None = None) -> RestoreResult:
        """Reverify private recovery, source integrity, and freshness before any write."""
        if confirmation != "RESTORE":
            raise PolicyError("Type RESTORE exactly to confirm this restoration.")
        if not plan.targets:
            raise PolicyError("The restoration has no selected target.")
        proof = proof or self.back_up(plan)  # CLI callers retain the complete recovery backup gate.
        records = [
            {"scope": target.scope, "id": target.identifier, "settings": target.original} for target in plan.targets
        ]
        proof.verify(self.files.backup, records, self.binding(plan))  # Bind complete recovery to the exact operation.
        self.current(plan)
        result = RestoreResult(remaining=[target.key for target in plan.targets], backups_verified=len(records))
        logger.info("Restore settings after verifying %s complete recovery records", len(records))
        self._restore_targets(plan, result, proof)
        attempted = set(result.completed + result.failed)  # Keep remaining outcomes linear in selected record count.
        result.remaining = [key for key in result.remaining if key not in attempted]
        logger.debug("Restoration verified %s scopes with %s failures", len(result.completed), len(result.failed))
        return result

    def _restore_targets(self, plan: RestorePlan, result: RestoreResult, proof: BackupProof) -> None:
        """Write one ordered run and retain exact verified, failed, and remaining outcomes."""
        targets = sorted(plan.targets, key=lambda target: (target.scope, target.name.casefold(), target.identifier))
        checked_membership = False
        for target in targets:
            try:
                if target.scope == "site" and not checked_membership:
                    if RestoreSelection.membership(self.api, set(plan.membership)) != plan.membership:
                        raise PolicyError("Site membership changed during restoration. Changes can remain.")
                    checked_membership = True
                self._write(plan, target, proof)
            except PolicyError as error:
                result.failed.append(target.key)
                result.error = str(error)
                logger.error("Restoration stopped for %s: %s", target.key, error)
                break
            result.completed.append(target.key)
            self.event("applied", target, len(result.completed), len(targets))

    def _write(self, plan: RestorePlan, target: RestoreTarget, proof: BackupProof) -> None:
        """Refresh each target and stop on the first failed write or saved-state check."""
        if self.stopped() or RestoreSelection.cloud(self.api) != plan.cloud:
            raise PolicyError("Restoration cancelled or cloud context changed. Changes can remain.")
        self.files.unchanged(plan.bundle)  # Detect source replacement without repeated complete parsing.
        if self.api.read(target.scope, target.identifier) != target.original:
            raise PolicyError("Settings changed after recovery backup. Changes can remain.")
        self.files.unchanged(plan.bundle)  # Recheck source freshness after any settings-read admission wait.
        proof.ensure(self.files.backup)  # Keep complete durable recovery available throughout the run.
        self.api.write(target.scope, target.identifier, target.body)
        saved = self.api.read(target.scope, target.identifier)
        if any(saved.get(key) != target.original[key] for key in ("id", "org_id", "site_id") if key in target.original):
            raise PolicyError("Saved settings ownership verification failed. Changes can remain.")
        self.schema.verify(target.scope, saved, target.body)
