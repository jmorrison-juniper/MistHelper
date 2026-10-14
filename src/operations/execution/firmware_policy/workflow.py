"""Share complete backup, verified settings writes, and partial reporting between CLI and portal."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .changes import FirmwarePolicy, PolicyChanges
from .recovery.backup import BackupProof, PolicyBackup
from .sdk import PolicyApi, PolicyError, PolicyResponse

logger = logging.getLogger(__name__)


@dataclass
class SiteChange:
    """Hold a site's original settings privately and its planned override removal."""

    identifier: str
    name: str
    original: dict[str, Any] = field(repr=False)
    body: dict[str, Any] = field(repr=False)


@dataclass
class OrganizationChange:
    """Hold one complete organization and site plan without exposing its settings."""

    identifier: str
    name: str
    original: dict[str, Any] = field(repr=False)
    body: dict[str, Any] = field(repr=False)
    sites: list[SiteChange] = field(repr=False)

    def preview(self) -> dict[str, Any]:
        """Expose only policy choices and target names, never unrelated settings."""
        policies = {  # Keep conductor tokens and other parent siblings outside the preview.
            key: value if key == "auto_upgrade" else value["auto_upgrade"] for key, value in self.body.items()
        }
        return {  # The browser and CLI use the same complete target preview.
            "name": self.name,
            "id": self.identifier,
            "policies": policies,
            "sites": [{"name": site.name, "id": site.identifier, "changes": bool(site.body)} for site in self.sites],
        }


@dataclass
class PolicyResult:
    """Count verified changes separately from failures and remaining work."""

    organizations: list[str] = field(default_factory=list)
    sites: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    remaining: list[str] = field(default_factory=list)


@dataclass
class PolicyWorkflow:
    """Apply only a confirmed complete plan whose complete settings backups verify."""

    api: PolicyApi
    backup: PolicyBackup
    stopped: Callable[[], bool] = lambda: False
    progress: Callable[[dict[str, Any]], None] | None = None

    def __post_init__(self) -> None:
        """Connect workflow progress to the same SDK request and quota-wait events."""
        if self.progress:
            self.api.progress = self.progress
            self.api.guard.progress = self.progress

    def event(self, phase: str, scope: str, identifier: str, details: dict[str, Any]) -> None:
        """Report names and counts without private snapshot values."""
        if self.progress:
            self.progress({"phase": phase, "scope": scope, "id": identifier, **details})

    def prepare(self, organization: dict[str, Any], policies: list[FirmwarePolicy]) -> OrganizationChange:
        """Read and validate a full organization before preview or confirmation."""
        identifier = PolicyResponse.identifier(organization.get("id", ""))  # Check each selected scope.
        original = self.api.read("org", identifier)  # Retain complete organization settings privately.
        body = PolicyChanges.organization(original, policies)  # Preserve unselected policies and siblings.
        changes: list[SiteChange] = []  # Collect every local site, including already inherited sites.
        seen: set[str] = set()  # Duplicate targets indicate an incomplete or inconsistent site list.
        listing = sorted(
            self.api.sites(identifier), key=lambda site: (str(site.get("name", "")).casefold(), site.get("id", ""))
        )
        for site in listing:
            site_id = PolicyResponse.identifier(site.get("id", ""))  # Refuse malformed site records.
            if site_id in seen:
                raise PolicyError("The organization site list contains a duplicate identifier.")
            seen.add(site_id)  # Do not send duplicate settings writes.
            settings = self.api.read("site", site_id)  # Capture complete settings before any change.
            changes.append(SiteChange(site_id, str(site.get("name", site_id)), settings, PolicyChanges.site(settings)))
            self.event(
                "preparing",
                "site",
                site_id,
                {"name": changes[-1].name, "completed": len(changes), "total": len(listing)},
            )
        return OrganizationChange(identifier, str(organization.get("name", identifier)), original, body, changes)

    @staticmethod
    def records(plans: list[OrganizationChange]) -> list[dict[str, Any]]:
        """Project the complete private recovery snapshots from the selected plans."""
        if not plans:
            raise PolicyError("No organization policy was selected.")
        return [  # Back up every complete organization and every complete site across the whole run.
            record
            for plan in plans
            for record in (
                {"scope": "org", "id": plan.identifier, "settings": plan.original},
                *({"scope": "site", "id": site.identifier, "settings": site.original} for site in plan.sites),
            )
        ]

    def back_up(self, plans: list[OrganizationChange]) -> BackupProof:
        """Prepare a durable verified backup before the operator confirms application."""
        records = self.records(plans)  # Include every complete selected snapshot.
        self._verify_current(plans)  # Refuse stale preparation before writing its recovery file.
        self.event("backing_up", "org", plans[0].identifier, {"completed": 0, "total": len(records)})
        path = self.backup.save(records)  # No Mist write can run until the complete backup gate succeeds.
        self.backup.verify(path, records)  # Verify the durable bundle again at the apply boundary.
        self.event("backup_verified", "org", plans[0].identifier, {"completed": len(records), "total": len(records)})
        return BackupProof(path, records, self.binding(plans))  # Bind the exact planned policy and snapshots.

    @staticmethod
    def binding(plans: list[OrganizationChange]) -> str:
        """Bind a recovery proof to the exact selected scopes and write bodies."""
        return PolicyBackup.digest(
            [
                {
                    "id": plan.identifier,
                    "body": plan.body,
                    "sites": [{"id": site.identifier, "body": site.body} for site in plan.sites],
                }
                for plan in plans
            ]
        )

    def apply(self, plans: list[OrganizationChange], proof: BackupProof | None = None) -> PolicyResult:
        """Reverify durable recovery and snapshots before the first organization write."""
        records = self.records(plans)  # Bind the proof to exact complete recovery records.
        proof = proof or self.back_up(plans)  # CLI callers still create and verify every recovery backup.
        proof.verify(self.backup, records, self.binding(plans))  # Recheck durable recovery and consume the proof once.
        self._verify_current(plans)  # Refuse changes after backup preparation.
        logger.info("Apply firmware policies after verifying %s settings backups", len(records))
        result = PolicyResult(remaining=[site.identifier for plan in plans for site in plan.sites])
        self._apply_groups(plans, result, "org", proof)  # Finish every organization before removing any site override.
        if not result.failures:  # All organization writes must finish before the first site write.
            self._apply_groups(plans, result, "site", proof)
        logger.debug("Verified %s organizations and %s sites", len(result.organizations), len(result.sites))
        completed = set(result.sites + result.unchanged)
        result.remaining = [identifier for identifier in result.remaining if identifier not in completed]
        return result  # Never count an unverified write as a completed change.

    def _apply_groups(
        self, plans: list[OrganizationChange], result: PolicyResult, scope: str, proof: BackupProof
    ) -> None:
        """Stop one ordered scope stage at the first uncertain or unverified update."""
        action = self._apply_organization if scope == "org" else self._apply_sites
        for plan in plans:
            try:
                action(plan, result, proof)
            except PolicyError as error:
                logger.error("Firmware policy failed for org %s: %s", plan.identifier, error)
                result.failures.append(f"Organization {plan.identifier}: {error} Saved changes can remain.")
                break  # Never continue a partially failed scope stage.

    def _membership(self, plan: OrganizationChange) -> None:
        """Reject incomplete, duplicate, or changed site memberships."""
        actual = self.api.sites(plan.identifier)
        identifiers = [PolicyResponse.identifier(site.get("id", "")) for site in actual]
        if (
            len(set(identifiers)) != len(identifiers)
            or set(identifiers) != {site.identifier for site in plan.sites}
            or any(site.get("org_id", plan.identifier) != plan.identifier for site in actual)
        ):
            raise PolicyError("Site membership changed after preview. Create a new preview.")

    def _verify_current(self, plans: list[OrganizationChange]) -> None:
        """Refuse concurrent settings changes and cancellation before the backup gate."""
        if self.stopped():
            raise PolicyError("The firmware policy operation was cancelled.")
        for plan in plans:
            self._membership(plan)  # Reject changes before the complete snapshot comparison.
            if self.api.read("org", plan.identifier) != plan.original:
                raise PolicyError("Organization settings changed after preview. Create a new preview.")
            for site in plan.sites:
                if self.stopped():
                    raise PolicyError("The firmware policy operation was cancelled.")
                if self.api.read("site", site.identifier) != site.original:
                    raise PolicyError("Site settings changed after preview. Create a new preview.")

    def _apply_organization(self, plan: OrganizationChange, result: PolicyResult, proof: BackupProof) -> None:
        """Check freshness, save the policy, and verify its selected values."""
        if self.stopped():
            raise PolicyError("The firmware policy operation was cancelled.")
        if self.api.read("org", plan.identifier) != plan.original:
            raise PolicyError("Organization settings changed after backup. Create a new preview.")
        proof.ensure(self.backup)  # Long quota waits must not conceal lost durable recovery.
        self.api.write("org", plan.identifier, plan.body)  # This is a settings write, never a firmware request.
        saved = self.api.read("org", plan.identifier)  # The write response alone does not prove persistence.
        PolicyChanges.verify_org(saved, plan.body)  # Verify model choices and all replaced parent siblings.
        result.organizations.append(plan.identifier)  # Count only a verified organization update.
        self.event("applied", "org", plan.identifier, {"name": plan.name, "completed": len(result.organizations)})

    def _apply_sites(self, plan: OrganizationChange, result: PolicyResult, proof: BackupProof) -> None:
        """Remove local overrides and stop on the first failed or unverified site."""
        for site in plan.sites:
            if self.stopped():
                raise PolicyError("The firmware policy operation was cancelled.")
            if self.api.read("site", site.identifier) != site.original:
                raise PolicyError(f"Site {site.identifier} changed after backup. Create a new preview.")
            if site.body:
                proof.ensure(self.backup)
                self.api.write("site", site.identifier, site.body)  # Clear policies without touching devices.
                PolicyChanges.verify_site(self.api.read("site", site.identifier), site.original)
                result.sites.append(site.identifier)  # A verified removal counts as completed.
            else:
                result.unchanged.append(site.identifier)  # Already inherited settings need no write.
            self.event(
                "applied",
                "site",
                site.identifier,
                {
                    "name": site.name,
                    "completed": len(result.sites) + len(result.unchanged),
                },
            )
