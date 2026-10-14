"""Share complete backup, verified settings writes, and partial reporting between CLI and portal."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .changes import FirmwarePolicy, PolicyChanges
from .recovery.backup import PolicyBackup
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
            "id": self.identifier,
            "name": self.name,
            "policies": policies,
            "sites": [{"id": site.identifier, "name": site.name, "changes": bool(site.body)} for site in self.sites],
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

    def prepare(self, organization: dict[str, Any], policies: list[FirmwarePolicy]) -> OrganizationChange:
        """Read and validate a full organization before preview or confirmation."""
        identifier = PolicyResponse.identifier(organization.get("id", ""))  # Check each selected scope.
        original = self.api.read("org", identifier)  # Retain complete organization settings privately.
        body = PolicyChanges.organization(original, policies)  # Preserve unselected policies and siblings.
        changes: list[SiteChange] = []  # Collect every local site, including already inherited sites.
        seen: set[str] = set()  # Duplicate targets indicate an incomplete or inconsistent site list.
        for site in self.api.sites(identifier):
            site_id = PolicyResponse.identifier(site.get("id", ""))  # Refuse malformed site records.
            if site_id in seen:
                raise PolicyError("The organization site list contains a duplicate identifier.")
            seen.add(site_id)  # Do not send duplicate settings writes.
            settings = self.api.read("site", site_id)  # Capture complete settings before any change.
            changes.append(SiteChange(site_id, str(site.get("name", site_id)), settings, PolicyChanges.site(settings)))
        return OrganizationChange(identifier, str(organization.get("name", identifier)), original, body, changes)

    def apply(self, plans: list[OrganizationChange]) -> PolicyResult:
        """Verify all backups before the first organization or site settings write."""
        if not plans:
            raise PolicyError("No organization policy was selected.")
        records = [  # Back up every complete organization and every complete site across the whole run.
            record
            for plan in plans
            for record in (
                {"scope": "org", "id": plan.identifier, "settings": plan.original},
                *({"scope": "site", "id": site.identifier, "settings": site.original} for site in plan.sites),
            )
        ]
        self._verify_current(plans)  # Refuse a stale preview before creating its backup.
        path = self.backup.save(records)  # No Mist write can run until the complete backup gate succeeds.
        self.backup.verify(path, records)  # Verify the durable bundle again at the apply boundary.
        logger.info("Apply firmware policies after verifying %s settings backups", len(records))
        result = PolicyResult(remaining=[site.identifier for plan in plans for site in plan.sites])
        for plan in plans:
            try:
                self._apply_organization(plan, result)  # Save the new organization policy first.
                self._apply_sites(plan, result)  # Remove overrides only after organization verification.
            except PolicyError as error:
                logger.error("Firmware policy failed for org %s: %s", plan.identifier, error)
                result.failures.append(f"Organization {plan.identifier}: {error} Saved changes can remain.")
                break  # Do not continue a partly failed multi-organization run.
        logger.debug("Verified %s organizations and %s sites", len(result.organizations), len(result.sites))
        return result  # Never count an unverified write as a completed change.

    def _verify_current(self, plans: list[OrganizationChange]) -> None:
        """Refuse concurrent settings changes and cancellation before the backup gate."""
        if self.stopped():
            raise PolicyError("The firmware policy operation was cancelled.")
        for plan in plans:
            if self.api.read("org", plan.identifier) != plan.original:
                raise PolicyError("Organization settings changed after preview. Create a new preview.")
            for site in plan.sites:
                if self.api.read("site", site.identifier) != site.original:
                    raise PolicyError("Site settings changed after preview. Create a new preview.")

    def _apply_organization(self, plan: OrganizationChange, result: PolicyResult) -> None:
        """Check freshness, save the policy, and verify its selected values."""
        if self.stopped():
            raise PolicyError("The firmware policy operation was cancelled.")
        if self.api.read("org", plan.identifier) != plan.original:
            raise PolicyError("Organization settings changed after backup. Create a new preview.")
        self.api.write("org", plan.identifier, plan.body)  # This is a settings write, never a firmware request.
        saved = self.api.read("org", plan.identifier)  # The write response alone does not prove persistence.
        PolicyChanges.verify_org(saved, plan.body)  # Verify model choices and all replaced parent siblings.
        result.organizations.append(plan.identifier)  # Count only a verified organization update.

    def _apply_sites(self, plan: OrganizationChange, result: PolicyResult) -> None:
        """Remove local overrides and stop on the first failed or unverified site."""
        for site in plan.sites:
            if self.stopped():
                raise PolicyError("The firmware policy operation was cancelled.")
            if self.api.read("site", site.identifier) != site.original:
                raise PolicyError(f"Site {site.identifier} changed after backup. Create a new preview.")
            if site.body:
                self.api.write("site", site.identifier, site.body)  # Clear policies without touching devices.
                PolicyChanges.verify_site(self.api.read("site", site.identifier), site.original)
                result.sites.append(site.identifier)  # A verified removal counts as completed.
            else:
                result.unchanged.append(site.identifier)  # Already inherited settings need no write.
            result.remaining.remove(site.identifier)  # Remove only a verified or unchanged site.
