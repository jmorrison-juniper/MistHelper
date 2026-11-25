"""Route the Multi Site hardware action to one organization or to every organization of an MSP.

Why:
    The portal serves one configured organization, but an MSP login can reach
    many. The CLI menu already decides the scope from the profile of the
    credential. The portal action must use the same rules (FR-034), so these
    classes plug the same scope resolver into the portal batch services. They
    change only the hardware preset: the other Multi Site actions keep their
    one-organization behavior. The services of each extra organization are built
    on first use, and the scope decision is cached for a short time, so a repeated
    preview does not read the profile again.
"""

from __future__ import annotations

import logging  # Record each routing decision for the operator trace.
import time  # The scope decision expires after a short time.
from collections.abc import Mapping  # The target identity is a read-only mapping.
from typing import Any, cast  # The picker, the catalog, and the checker have no shared public type.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Refusals of the service.
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # Mist reads.
from src.mist.realtime.websocket_streams.intake.start_request.checker import StartRequestChecker  # Request checks.
from src.mist.realtime.websocket_streams.web.services.pickers.related import BatchTargetPickerService  # Targets.
from src.operations.exporting.ex_hardware_inventory.scope.resolver import (
    ScopeDecision,
    ScopeError,
    ScopeResolver,
)  # The scope detection of the CLI.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class ScopeRouter:
    """Hold the scope of the portal hardware action and the services of each organization."""

    TTL_SECONDS = 300.0  # A scope decision stays valid this long.

    class Discovery:
        """Read the sites of every organization in scope, and remember which organization owns each site."""

        def __init__(self, router: ScopeRouter) -> None:
            """Store the router whose site map and failed list this discovery fills."""
            self._router = router  # Shared with the checker and the status reads.

        def sites(self, kind: str, key: str) -> dict[str, object]:
            """Return the sites of every readable organization.

            Raises:
                StreamRequestError: When the scope is not clear, when the only organization cannot be read, or when
                    every organization of an MSP cannot be read.
            """
            router = self._router  # Short name for the shared state.
            decision = router.decision()  # One organization, or every organization of the MSP.
            router.site_orgs.clear()  # Each preview is a fresh discovery.
            router.failed.clear()  # Nothing has failed yet in this discovery.
            rows: list[dict[str, object]] = []  # The sites of every readable organization.
            errors: dict[str, StreamRequestError] = {}  # The organizations that Mist refused.
            for ref in decision.organizations:  # One organization at a time, so the rate limit holds.
                try:  # An MSP continues when one organization cannot be read.
                    found = cast(list[dict[str, object]], router.services(ref.org_id)[0].sites(kind, key)["rows"])
                except StreamRequestError as error:
                    if decision.mode != "msp":  # The only organization failed, so the preview fails.
                        raise
                    errors[ref.org_id] = error  # Reported in the CSV as one outcome row.
                    continue
                rows.extend(self._claim(ref.org_id, found))  # A complete page is a list.
            if errors and len(errors) == len(decision.organizations):  # Nothing is readable at all.
                raise next(iter(errors.values()))
            router.failed.update({org: self._code(error) for org, error in errors.items()})
            return {"rows": rows, "total_count": len(rows), "complete": True, "reason": None if rows else "No sites."}

        def _claim(self, org_id: str, found: list[dict[str, object]]) -> list[dict[str, object]]:
            """Map each site to its organization and return copies of the rows."""
            for row in found:  # Each site belongs to exactly one organization.
                self._router.site_orgs[str(row["id"])] = org_id  # The route of each later read.
            return [dict(row) for row in found]

        @staticmethod
        def _code(error: StreamRequestError) -> str:
            """Return the reason code of a failed organization for the report."""
            return "rate_limited" if error.code == "rate_limited" else "discovery_failed"

    def __init__(self, picker: Any, catalog: Any) -> None:
        """Store the plain picker of the configured organization and the shared catalog.

        Args:
            picker: The ``StreamPickerService`` of the configured organization.
            catalog: The shared stream catalog.
        """
        self._picker = picker  # The configured organization, and the session for every other organization.
        self._catalog = catalog  # Every organization checks requests against the same catalog.
        self._decision: ScopeDecision | None = None  # The cached decision.
        self._read_at = 0.0  # The monotonic time of the cached decision.
        self._services: dict[str, tuple[BatchTargetPickerService, StartRequestChecker]] = {}  # By organization.
        self.site_orgs: dict[str, str] = {}  # Site identifier to organization, filled by the site discovery.
        self.failed: dict[str, str] = {}  # Organization identifier to the reason code of a failed discovery.

    @classmethod
    def of(cls, picker: Any, catalog: Any) -> ScopeRouter:
        """Return the router of one picker. The targets and the checker of a portal share it."""
        router = getattr(picker, "scope_router", None)  # The first caller attaches one router to the picker.
        if router is None:  # No router exists yet.
            router = cls(picker, catalog)  # Build it once.
            picker.scope_router = router  # The checker finds the same router through the same picker.
        return router  # Shared state for the site map and the failed organizations.

    def decision(self) -> ScopeDecision:
        """Return the scope decision, and read the profile again when it is old.

        Raises:
            StreamRequestError: With the plain sentence of the scope error.
        """
        if self._decision is None or time.monotonic() - self._read_at > self.TTL_SECONDS:  # Old or missing.
            logger.info("Reading the scope of the portal hardware action")  # Log before the external requests.
            try:  # A refused profile must stop the preview with its reason.
                resolver = ScopeResolver(self._picker._apisession, self._picker._org_id)  # The configured organization.
                self._decision = resolver.resolve()  # The same rules as the menu.
            except ScopeError as error:
                raise StreamRequestError("picker_unavailable", str(error)) from None  # The sentence names the fix.
            self._read_at = time.monotonic()  # The decision is fresh.
            logger.debug("Read the scope: mode=%s", self._decision.mode)  # Log the mode only.
        return self._decision  # The cached decision.

    def services(self, org_id: str) -> tuple[BatchTargetPickerService, StartRequestChecker]:
        """Return the target service and the request checker of one organization, built on first use."""
        if org_id not in self._services:  # Build the services of an organization once.
            configured = org_id == self._picker._org_id  # The configured organization reuses the portal picker.
            picker = self._picker if configured else StreamPickerService(self._picker._apisession, org_id)
            self._services[org_id] = (
                BatchTargetPickerService(picker, self._catalog, None),
                StartRequestChecker(self._catalog, picker, org_id),
            )  # The checker injects this organization into each request.
        return self._services[org_id]

    def summary(self, public: bool = False) -> dict[str, object]:
        """Return the scope of the run.

        Args:
            public: True for the counts that the browser shows. False for the full mapping that the report reads.
        """
        decision = self._decision or self.decision()  # The preview just set it, so the start never reads again.
        if public:  # The browser needs counts, not names or identifiers.
            counts = (len(decision.organizations), len(self.failed))  # Organizations in scope and unread ones.
            return {"mode": decision.mode, "organization_count": counts[0], "failed_count": counts[1]}
        return {
            "mode": decision.mode,
            "organizations": {ref.org_id: ref.org_name for ref in decision.organizations},
            "failed": dict(self.failed),
        }  # The report hook reads exactly these three keys.


class ScopeAwareTargets(BatchTargetPickerService):
    """The batch target service of the portal, with scope-aware reads for the hardware preset."""

    def __init__(self, picker: Any | None, catalog: Any | None, reason: str | None) -> None:
        """Build the plain service, and join the router of the picker when the portal is ready."""
        super().__init__(picker, catalog, reason)  # The plain behavior stays for every other action.
        self._router = ScopeRouter.of(picker, catalog) if picker is not None and catalog is not None else None

    def hardware_sites(self, kind: str, key: str) -> dict[str, object]:
        """Return the sites of every organization in scope for the hardware preview."""
        if self._router is None:  # A not-ready portal has no router, and the plain read gives its refusal.
            return self.sites(kind, key)
        return ScopeRouter.Discovery(self._router).sites(kind, key)

    def hardware_targets(self, site_id: str | None, kind: str, key: str, parents: dict[str, str]) -> dict[str, object]:
        """Read the targets of one site through the service of the organization that owns the site."""
        org_id = self._router.site_orgs.get(str(site_id)) if self._router is not None else None
        if org_id and self._router is not None:  # The site discovery found the owner of this site.
            return self._router.services(org_id)[0].hardware_targets(site_id, kind, key, parents)  # Checks membership.
        return super().hardware_targets(site_id, kind, key, parents)  # The configured organization.

    def hardware_status(self, identity: Mapping[str, object]) -> str:
        """Check the status again through the service of the organization of the target."""
        org_id = str(identity.get("org_id") or "")  # The checker injected it into the request.
        if org_id and self._router is not None:  # Status reads are by site, so the owner service answers.
            return self._router.services(org_id)[0].hardware_status(identity)
        return super().hardware_status(identity)  # The configured organization.

    def scope_summary(self, public: bool = False) -> dict[str, object]:
        """Return the scope for the preview line (public) and for the report at the start of the run (full)."""
        return self._router.summary(public) if self._router is not None else {}


class ScopeAwareChecker:
    """The request checker of the portal, with the organization of each hardware target."""

    def __init__(self, checker: Any, router: ScopeRouter) -> None:
        """Keep the plain checker for the configured organization and the shared router."""
        self._checker = checker  # The plain checker serves every action except an MSP hardware target.
        self._router = router  # Knows which organization owns each site.

    def check_batch(self, body: object) -> Any:
        """Check one batch target with the checker of the organization that owns its site."""
        targets = body.get("targets") if isinstance(body, dict) else None  # The preview builds this mapping.
        site_id = targets.get("site_id") if isinstance(targets, dict) else None  # The site of the target.
        org_id = self._router.site_orgs.get(str(site_id)) if site_id else None  # Known after the site discovery.
        checker = self._router.services(org_id)[1] if org_id else self._checker
        return checker.check_batch(body)  # The checker injects its organization into the request.

    def __getattr__(self, name: str) -> Any:
        """Give every other method of the plain checker."""
        return getattr(self._checker, name)
