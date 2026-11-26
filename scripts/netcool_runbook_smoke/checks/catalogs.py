"""Catalog check SMK-05: the six definition catalogs, and the runbook names that they must hold.

Why: each runbook name is a Mist key. A key that the catalog no longer holds would make the runbook point at an
event that does not exist. The catalogs also feed the evidence record, so the operator sees what the run compared.
"""

from __future__ import annotations  # Postpone annotation evaluation.

from collections.abc import Sequence  # Type the runbook name lists of each catalog.
from dataclasses import replace  # Copy the result with the confirmed catalog field names.
from typing import Any, ClassVar  # Type the catalog values and the class constants.

import structlog  # Structured logging of each catalog request and each name comparison.

from scripts.netcool_runbook_smoke.checks import (  # Import the run state, result, and status types for SMK-05.
    CheckContext,
    CheckResult,
    CheckStatus,
)
from scripts.netcool_runbook_smoke.client import CallRecord  # Import the attempt type that each catalog request uses.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class CatalogStore:  # Keep each catalog entry, and judge the defects of its request.
    """Store the catalog entries of SMK-05, and name the defects of each catalog request.

    Why: the evidence needs each catalog with its status and its items, and a defect of a request must be named once.
    The storage and the defect rules live together, so each catalog is judged where it is stored.
    """

    @staticmethod
    def store(  # Store one catalog entry, and return its request defects.
        catalogs: dict[str, dict[str, Any]], key: str, final: CallRecord
    ) -> list[str]:
        """Store one catalog entry in the run context, and return the defects of its request.

        Why: the evidence needs each catalog with its status and its items, and a defect must be named once.

        Args:
            catalogs: Catalog entries of the run, updated in place.
            key: Catalog key, for example alarm_defs.
            final: Final attempt of the catalog request.

        Returns:
            The defect texts. An empty list means that the catalog is a non-empty JSON array.
        """
        is_array = isinstance(final.data, list)  # A catalog is a top-level JSON array.
        items: list[dict[str, Any]] = (  # Keep the object items, so each item key can be compared.
            [item for item in final.data if isinstance(item, dict)] if is_array else []
        )  # Objects.
        catalogs[key] = {  # Store the status and items for the evidence record.
            "status_code": final.status_code,
            "item_count": len(items),
            "items": items,
        }
        logger.debug("Catalog %s holds %s items", key, len(items))  # Log the item count of the catalog.
        return CatalogStore.describe(key, final, is_array, items)  # Name each defect of the request.

    @staticmethod
    def describe(  # Name the defect of one catalog request, if it has one.
        key: str, final: CallRecord, is_array: bool, items: list[dict[str, Any]]
    ) -> list[str]:
        """Return the defect texts of one catalog request, in the order of the contract.

        Why: a failed request, a body that is not an array, and an empty array each fail the catalog.
        Each of the three fails for a different reason.
        Each reason therefore has its own text for the operator.

        Args:
            key: Catalog key, for example alarm_defs.
            final: Final attempt of the catalog request.
            is_array: True when the response body is a top-level JSON array.
            items: Object items of the array, or an empty list.

        Returns:
            The defect texts. An empty list means that the catalog is a non-empty JSON array.
        """
        if final.error_class is not None:  # The request failed, so the catalog has no usable items.
            return [f"{key} returned {final.error_class.value}"]  # Name the error class.
        if not is_array:  # A catalog body that is not an array is unusable.
            return [f"{key} is not a JSON array"]  # Name the defect.
        if not items:  # An empty catalog cannot prove any runbook name.
            return [f"{key} is empty"]  # Name the defect.
        return []  # The catalog is a non-empty array.

    @staticmethod
    def summary(problems: Sequence[str], catalog_count: int) -> tuple[CheckStatus, str]:  # Judge the catalog part.
        """Return the status and the text of the catalog part of SMK-05.

        Why: any catalog defect fails the part, and the text names each defect. A part with no defect reports the
        count of its catalogs.

        Args:
            problems: Defect texts of the six catalog requests.
            catalog_count: Number of catalogs that the check requests.

        Returns:
            The status and the text of the catalog part.
        """
        if problems:  # Any catalog defect fails the catalog part.
            return CheckStatus.FAIL, "; ".join(problems)  # Name each defect in one text.
        return CheckStatus.PASS, f"{catalog_count} catalogs not empty"  # Count the catalogs that passed.


class NameComparison:  # Compare the runbook names with the live catalog keys.
    """Compare each Appendix B name with the keys of its catalog, and judge the name part of SMK-05.

    Why: a runbook name that the catalog does not hold is a finding. Without the runbook, the comparison is skipped,
    and the catalog requests still count. The judgment is kept apart from the request code, so each rule reads alone.
    """

    @staticmethod
    def missing_names(  # Return each runbook name that its catalog lacks, as catalog key and name.
        catalogs: dict[str, dict[str, Any]], catalog_names: dict[str, tuple[str, ...]]
    ) -> list[str]:
        """Return each runbook name that its catalog does not hold, as catalog key and name.

        Why: a name is a finding only when the live catalog lacks its key.
        The catalog keys are read from the entries that the requests stored.

        Args:
            catalogs: Catalog entries that the requests stored.
            catalog_names: Runbook names of each Appendix B table, keyed by catalog key.

        Returns:
            The missing names, each written as its catalog key and its name.
        """
        missing: list[str] = []  # Each runbook name that the catalog does not hold.
        for key, names in catalog_names.items():  # Each Appendix B table with its catalog key.
            entry = catalogs.get(key, {})  # The catalog entry that the request stored.
            held = {  # Collect the catalog keys for the name comparison.
                item.get("key") for item in entry.get("items", []) if isinstance(item, dict)
            }  # Keys of the catalog.
            missing.extend(f"{key} {name}" for name in names if name not in held)  # Names that the catalog lacks.
        return missing  # Every missing name, in table order.

    @staticmethod
    def verdict(missing: Sequence[str], has_system_events: bool) -> tuple[CheckStatus, str]:  # Judge the name part.
        """Return the status and the text of the name part of SMK-05.

        Why: a missing name fails the part, and an absent optional Appendix B.4 is only an observation.

        Args:
            missing: Each runbook name that its catalog does not hold.
            has_system_events: True when Appendix B.4 holds at least one name.

        Returns:
            The status and the text of the name part.
        """
        if missing:  # At least one runbook name is not a live key.
            return CheckStatus.FAIL, "missing runbook names: " + "; ".join(missing)  # Name each missing value.
        if not has_system_events:  # Appendix B.4 is optional, so its absence is only an observation.
            return CheckStatus.INFO, "all runbook names found, and Appendix B.4 is absent"  # Observation text.
        return CheckStatus.PASS, "all runbook names found"  # Every runbook name is a live key.


class CatalogChecks:  # Hold the SMK-05 requests and comparisons in one class.
    """Request the six definition catalogs, and compare each Appendix B name with its catalog key.

    Why: the comparison proves that the runbook names are live Mist keys. The evidence keeps each catalog item without
    its example member, so the file shows the definitions that were compared.
    """

    CATALOG_PATHS: ClassVar[tuple[tuple[str, str], ...]] = (  # Catalog key and path, in the contract order.
        ("alarm_defs", "/api/v1/const/alarm_defs"),
        ("device_events", "/api/v1/const/device_events"),
        ("mxedge_events", "/api/v1/const/mxedge_events"),
        ("system_events", "/api/v1/const/system_events"),
        ("ap_led_status", "/api/v1/const/ap_led_status"),
        ("webhook_topics", "/api/v1/const/webhook_topics"),
    )

    def __init__(self, context: CheckContext) -> None:  # Store the run state that receives the catalog entries.
        """Keep the run context that the check shares.

        Args:
            context: Run state of the smoke test.
        """
        self._context: CheckContext = context  # Run state that receives the catalog entries.

    def smk_05(self) -> CheckResult:  # Run SMK-05, so a missing runbook name becomes a finding.
        """Request the six catalogs, and compare the Appendix B names with the catalog keys.

        Why: a catalog that is empty, unreadable, or missing a runbook name is a finding for the operator.
        Each finding is named in the detail.

        Returns:
            The result of SMK-05. SKIP for the name part when the runbook is absent.
        """
        attempts, (catalogs_status, catalogs_text) = self._request_catalogs()  # The six requests and their part.
        names_status, names_text = self._compare_names()  # The runbook names against the catalog keys.
        status = CheckStatus.most_severe([catalogs_status, names_status])  # Roll-up of the two parts.
        result = CheckResult.from_calls("SMK-05", status, f"{catalogs_text}, {names_text}.", attempts)  # Request facts.
        return replace(result, field_names=self._field_names())  # Confirmed catalog field names, never values.

    def _request_catalogs(  # Request the six catalogs in order, and judge their entries.
        self,
    ) -> tuple[list[CallRecord], tuple[CheckStatus, str]]:
        """Request the six catalogs in the contract order, store each entry, and judge the catalog part.

        Why: each catalog is one request that the budget counts, and each defect of a request is named once.

        Returns:
            The attempts of the six requests, and the status and text of the catalog part.
        """
        attempts: list[CallRecord] = []  # Every attempt of the six catalog requests.
        problems: list[str] = []  # Catalog defects, one text each.
        for key, path in self.CATALOG_PATHS:  # Request the catalogs in the contract order.
            calls = self._context.get(path, {}, {})  # One request per catalog, counted by the budget.
            attempts.extend(calls)  # Keep the attempts for the request counts.
            problems.extend(CatalogStore.store(self._context.catalogs, key, calls[-1]))  # Store and name defects.
        return attempts, CatalogStore.summary(problems, len(self.CATALOG_PATHS))  # The catalog part of SMK-05.

    def _compare_names(self) -> tuple[CheckStatus, str]:  # Compare each runbook name with its live catalog key.
        """Compare each Appendix B name with the keys of its catalog.

        Why: a runbook name that the catalog does not hold is a finding. Without the runbook, the comparison
        is skipped, and the catalog requests still count.

        Returns:
            The status and the text of the name part.
        """
        claims = self._context.claims  # Runbook facts, or None when the default runbook is absent.
        if claims is None:  # Without the runbook, there are no names to compare.
            return CheckStatus.SKIP, "runbook not found, so the runbook names were not compared"  # Skip cause.
        missing = NameComparison.missing_names(self._context.catalogs, claims.catalog_names)  # Names the catalog lacks.
        has_system_events = bool(claims.catalog_names.get("system_events"))  # Appendix B.4 holds at least one name.
        return NameComparison.verdict(missing, has_system_events)  # Status and text of the name part.

    def _field_names(self) -> tuple[str, ...]:  # List catalog field names, never values, for the evidence.
        """Return the sorted names of the catalog fields that the run confirmed, never their values.

        Why: the check item lists the field names of the catalogs, so the operator sees the shape of each catalog.

        Returns:
            The sorted field names, without the example member.
        """
        names = {  # Field names of every catalog item, without the example member.
            key
            for entry in self._context.catalogs.values()
            for item in entry.get("items", [])
            for key in item
            if key != "example"
        }
        return tuple(sorted(names))  # Sort the names, because a set has no stable order between runs.
