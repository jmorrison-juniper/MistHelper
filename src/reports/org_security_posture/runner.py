"""Runner for the organization security posture checklist."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from typing import Any

from src.config.source_dependency_resolver import SourceDependencyResolver
from src.reports.org_security_posture.checks.registry import OrgSecurityPostureCheckRegistry
from src.reports.org_security_posture.io.exporter import OrgSecurityPostureExporter
from src.reports.org_security_posture.io.sources import OrgSecurityPostureSourceClient
from src.reports.org_security_posture.models import OrganizationSecuritySourceData, SecurityPostureCheckResult

logger = logging.getLogger(__name__)


class OrgSecurityPostureChecklist:
    """Static menu handler for the organization security posture checklist."""

    @staticmethod
    def run(
        *,
        api_session: Any | None = None,
        org_id: str | None = None,
        test_mode: bool = False,
        source_data: OrganizationSecuritySourceData | None = None,
        write_fn: Callable[..., bool] | None = None,
    ) -> dict[str, int]:
        """Run the checklist and return the summary counts."""
        logging.info("Starting organization security posture checklist")  # Log the operator action start.
        runner = OrgSecurityPostureRunner(
            api_session, org_id, test_mode, source_data, write_fn
        )  # Build the coordinator.
        summary = runner.run()  # Execute the same flow for normal mode and test mode.
        logging.debug("Finished organization security posture checklist with summary %s", summary)  # Log result counts.
        return summary  # Return counts for tests and deferred integration.


class OrgSecurityPostureRunner:
    """Coordinate source collection, evaluation, export, and summary."""

    def __init__(
        self,
        api_session: Any | None,
        org_id: str | None,
        test_mode: bool,
        source_data: OrganizationSecuritySourceData | None,
        write_fn: Callable[..., bool] | None,
    ) -> None:
        """Store dependencies for one checklist run."""
        self.api_session = api_session  # Store the optional Mist API session for normal mode.
        self.org_id = org_id  # Store the optional organization ID for normal mode.
        self.test_mode = test_mode  # Store whether fixture data must be used.
        self.source_data = source_data  # Store injected source data for tests.
        self.exporter = OrgSecurityPostureExporter(write_fn)  # Store the exporter dependency.

    def run(self) -> dict[str, int]:
        """Run all checklist phases."""
        logging.info("Preparing organization security posture source data")  # Log before source data resolution.
        source_data = self._build_source_data()  # Resolve fixture, injected, or live API data.
        logging.debug("Prepared organization security posture source data")  # Log after source data resolution.
        logging.info("Evaluating organization security posture checks")  # Log before check evaluation.
        results = self._evaluate(source_data)  # Run all registered checks.
        logging.debug("Evaluated %s organization security posture checks", len(results))  # Log result count.
        rows = [result.to_row() for result in results]  # Convert result objects into CSV rows.
        logging.info("Exporting organization security posture rows")  # Log before export.
        exported = self.exporter.export(rows)  # Persist rows through DataExporter.
        logging.debug("Exported organization security posture rows: %s", exported)  # Log export status.
        if not exported:  # A successful run must not claim success when the CSV write fails.
            raise RuntimeError("Organization security posture export failed.")
        logging.info("Summarizing organization security posture verdicts")  # Log before summary aggregation.
        summary = self._summarize(rows)  # Count pass, fail, and review rows.
        logging.debug("Organization security posture summary counts: %s", summary)  # Log summary counts.
        self._print_summary(summary)  # Print operator-facing counts.
        return summary  # Return counts for tests and callers.

    def _build_source_data(self) -> OrganizationSecuritySourceData:
        """Return source data for this run."""
        if self.source_data is not None:  # Tests can inject source data without network access.
            return self.source_data
        if self.test_mode:  # Test mode must not prompt or call the network.
            return self._fixture_source_data()
        api_session = self.api_session or SourceDependencyResolver.apisession  # Read the shared menu API session.
        org_id = self.org_id or self._resolve_org_id()  # Read the shared organization context when needed.
        if not api_session or not org_id:  # Normal mode needs both context values.
            raise ValueError("Organization security posture requires an API session and organization ID.")
        client = OrgSecurityPostureSourceClient(api_session, str(org_id))  # Build the live source client.
        return client.collect()  # Collect each required Mist source once.

    def _evaluate(self, source_data: OrganizationSecuritySourceData) -> list[SecurityPostureCheckResult]:
        """Evaluate every registered check against one source bundle."""
        checks = OrgSecurityPostureCheckRegistry.checks()  # Load the stable registry.
        return [check.run(source_data) for check in checks]  # Evaluate each check once.

    @staticmethod
    def _summarize(rows: list[dict[str, str]]) -> dict[str, int]:
        """Return pass, fail, and review counts that match exported rows."""
        counts = Counter(row["verdict"] for row in rows)  # Count the actual exported verdict values.
        return {verdict: counts.get(verdict, 0) for verdict in ("pass", "fail", "review")}  # Include zero counts.

    @staticmethod
    def _print_summary(summary: dict[str, int]) -> None:
        """Print the operator-facing summary."""
        print("Organization security posture summary")  # Give the operator a clear section heading.
        print(f"pass: {summary['pass']}")  # Print pass count from exported rows.
        print(f"fail: {summary['fail']}")  # Print fail count from exported rows.
        print(f"review: {summary['review']}")  # Print review count from exported rows.

    @staticmethod
    def _fixture_source_data() -> OrganizationSecuritySourceData:
        """Return representative source data for safe test mode."""
        settings = {  # Keep fixture data local so --test does not call the network.
            "password_policy": {
                "enabled": True,
                "min_length": 12,
                "requires_uppercase": True,
                "requires_lowercase": True,
                "requires_number": True,
                "requires_special_char": True,
                "requires_two_factor_auth": True,
                "reuse_history": 5,
                "expiry_in_days": 90,
            },
            "ui_idle_timeout": 30,
            "session_policy": {"max_lifetime_hours": 12},
            "api_policy": {"access": "restricted"},
            "disable_remote_shell": True,
            "disable_pcap": True,
            "junos_shell_access": {"admin": "none", "helpdesk": "none", "read": "none", "write": "none"},
            "pcap_bucket_verified": True,
            "switch_mgmt": {"remove_existing_configs": True},
        }
        tokens = [{"created_time": 1_700_000_000, "expire_time": 1_731_536_000}]  # Use a one-year token lifespan.
        webhooks = [{"url": "https://example.invalid/mist-webhook"}]  # Use HTTPS so the fixture can pass.
        return OrganizationSecuritySourceData(settings, [{"enabled": True}], [{"role": "admin"}], tokens, webhooks)

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the organization ID from the shared MistHelper context."""
        logging.info("Resolving organization ID for security posture checklist")  # Log before shared lookup.
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()  # Use existing safe helper.
        logging.debug("Resolved organization ID for security posture checklist: %s", org_id)  # Log lookup result.
        return str(org_id)  # Normalize organization identifiers to text for the source client.
