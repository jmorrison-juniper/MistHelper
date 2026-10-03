"""Build the multi-site upgrade section of the history page.

Why:
    Issue #3248. The history page listed the single-site runs only. A
    multi-site upgrade had no history entry. An operator who closed the
    progress page therefore could not find the upgrade again.

    This module turns the operation rows of the capture store into the rows
    that the template prints. The module holds every rule of the section, so
    the template holds no rule. The route gives the module the store reader,
    so a unit test calls the module with no store and no Flask request.

    The job page shows an operation only to the browser session that started
    it. The row therefore carries a link only for that session. The row never
    carries the owner key, so the key never reaches the browser.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each section build with counts only.
from collections.abc import Callable, Mapping  # Accept the store reader and each stored row.
from dataclasses import dataclass  # Freeze the section value that the template reads.
from typing import Any  # The stored row holds JSON values of mixed types.
from urllib.parse import quote  # Keep a stored identifier inside one path segment.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

NOT_RECORDED = "Not recorded"  # The text of a value that an older record does not hold.
UNKNOWN_STATE = "unknown"  # The state word of a record that holds no state.
JOB_PAGE_PREFIX = "/upgrade/org/jobs/"  # The progress page of one multi-site operation.

# The family words of the child jobs, in the order of the options page, with
# the label that the history row shows.
FAMILY_LABELS: tuple[tuple[str, str], ...] = (
    ("ap", "Access points"),
    ("switch", "Switches"),
    ("gateway", "Gateways"),
    ("ssr", "Session Smart Routers"),
)
KNOWN_FAMILIES = frozenset(word for word, _ in FAMILY_LABELS)  # The words that have a label.


@dataclass(frozen=True, slots=True)
class OperationHistorySection:
    """The values that the multi-site section of the history page prints.

    Attributes:
        rows: One row for each operation, newest first.
        org_selected: False when the browser session holds no organization.
        database_available: False when the store did not answer.
    """

    rows: tuple[dict[str, Any], ...]
    org_selected: bool
    database_available: bool


class OrgOperationHistory:
    """Build the multi-site section of the history page for one browser session."""

    def __init__(self, owner_key: str, moment_text: Callable[[Any], str]) -> None:
        """Keep the owner key of the session and the short moment rule of the page.

        Args:
            owner_key: The owner key of the current browser session, or an empty text.
            moment_text: The rule that turns a stored moment into short text.
        """
        self._owner_key = owner_key  # Compare each row against this key, and never show the key.
        self._moment_text = moment_text  # Use the same short moment as the other history sections.

    def section(self, lister: Callable[..., Any], org_id: str, site_id: str, limit: int) -> OperationHistorySection:
        """Read the operations of one organization and build the section.

        Args:
            lister: The store reader. The route passes the injected seam or the store fallback.
            org_id: The selected organization, or an empty text.
            site_id: The site that the page names, or an empty text for every site.
            limit: The page size of the history page.

        Returns:
            The section value.
        """
        if not org_id:  # The job page needs an organization, so a row could lead nowhere.
            logger.info("History: no organization is selected, so the multi-site section reads nothing")
            return OperationHistorySection((), False, True)  # The template asks for an organization.
        logger.info("History: read the multi-site operations of the selected organization")  # Before the read.
        page = lister(org_id, site_id=site_id, limit=limit)  # One store read for the whole section.
        records = getattr(page, "operations", page)  # The store answers a page, and a stand-in may answer a list.
        available = bool(getattr(page, "database_available", True))  # A plain list states no outage.
        rows = tuple(self.row(record) for record in records if self._identifier(record))  # Drop a damaged row.
        logger.debug("History: the multi-site section holds %s row(s)", len(rows))  # Report a safe count.
        return OperationHistorySection(rows, True, available)  # The template prints these values.

    def row(self, record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the template row of one stored operation.

        Args:
            record: One operation row of the store.

        Returns:
            The row. The row holds no owner key.
        """
        operation_id = self._identifier(record)  # The key of the row and of the progress page.
        return {
            "operation_id": operation_id,  # The text of the first cell.
            "progress_path": JOB_PAGE_PREFIX + quote(operation_id, safe=""),  # One path segment.
            "can_open": self._owns(record),  # Only the owner session receives the link.
            "sites_text": self._sites_text(record),  # The site names in the approved order.
            "families_text": self._families_text(record.get("families")),  # The device types.
            "state": str(record.get("state") or UNKNOWN_STATE),  # The badge word.
            "actor_email": str(record.get("actor_email") or NOT_RECORDED),  # The typed operator.
            "cloud_account": str(record.get("cloud_account") or NOT_RECORDED),  # The Mist account.
            "started_text": self._moment(record.get("created_at")),  # The start time in short form.
            "started_raw": str(record.get("created_at") or ""),  # The full stored start time.
            "updated_text": self._moment(record.get("updated_at")),  # The last update in short form.
            "updated_raw": str(record.get("updated_at") or ""),  # The full stored update time.
        }

    def _owns(self, record: Mapping[str, Any]) -> bool:
        """Return True when the current browser session started the operation."""
        return bool(self._owner_key) and record.get("owner") == self._owner_key  # An empty key owns nothing.

    def _moment(self, value: Any) -> str:
        """Return the short form of one stored moment, or the text for a missing value."""
        text = self._moment_text(value) if value else ""  # An older record holds no moment.
        return text or NOT_RECORDED  # A value that the rule cannot read also shows the plain text.

    @staticmethod
    def _identifier(record: Any) -> str:
        """Return the operation identifier of one stored row, or an empty text."""
        if not isinstance(record, Mapping):  # A damaged row holds no identifier.
            return ""  # The caller drops the row.
        return str(record.get("operation_id") or "")  # The store projects this field for each row.

    @staticmethod
    def _sites_text(record: Mapping[str, Any]) -> str:
        """Return the site names of one operation, in the approved site order."""
        site_ids = record.get("site_ids")  # The aggregate service keeps the approved order.
        names = record.get("site_names")  # A map of site identifier to site name.
        known = names if isinstance(names, Mapping) else {}  # An older record holds no name map.
        ordered = [str(site) for site in site_ids if site] if isinstance(site_ids, list) else []  # Keep the order.
        labels = [str(known.get(site) or site) for site in ordered]  # A site with no name shows its identifier.
        return ", ".join(labels) if labels else NOT_RECORDED  # One line of text for the cell.

    @staticmethod
    def _families_text(families: Any) -> str:
        """Return the device types of one operation, in the fixed family order."""
        words = {str(word) for word in families if word} if isinstance(families, list) else set()  # Unique words.
        known = [label for word, label in FAMILY_LABELS if word in words]  # The fixed order of the options page.
        unknown = sorted(words - KNOWN_FAMILIES)  # A family of a later release shows its stored word.
        labels = known + unknown  # The known labels come first.
        return ", ".join(labels) if labels else NOT_RECORDED  # One line of text for the cell.
