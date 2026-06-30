"""Optional site-address write-back for the address-audit feature (1003-site-address-audit).

``AddressCorrector`` is the WRITE surface of menu 195. After the read-only audit
saves its comparison report, the operator may opt in to push corrected addresses
back to their Mist sites. Every push is gated twice: a single opt-in for the whole
batch, then a per-site ``[y/N]`` confirmation showing the BEFORE (current Mist
address) and AFTER (suggested correction) side by side. Nothing is written without
that per-site yes.

Write mechanics (safe, minimal): a Mist site stores its address as a single
formatted string in the ``address`` field (e.g. ``"940 James Bowie Dr, New Boston,
TX 75570, USA"``) alongside ``latlng``, ``country_code``, ``timezone``, and the
various template IDs. To change only the address without disturbing anything else,
we fetch the full current site record, replace ``address``, and PUT the whole
record back. Every Mist call is fail-soft: a permission error (read-only token) or
any API failure is recorded as a failed outcome and never aborts the loop.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
from typing import Any  # Loose typing for the Mist API session/records.

import mistapi  # Mist API SDK (sole Mist interface; hard dependency of MistHelper).

from src.site.address_audit.models import AuditResult, CorrectionOutcome  # Shared dataclasses.
from src.utils.input_utils import InputUtils  # EOF-safe operator prompts.

# Issue states whose suggested address represents a correction worth pushing.
_CORRECTABLE = frozenset({"MISSING_SUITE", "MISSING_NUMBER", "WRONG_STREET", "CSV_BETTER", "AMBIGUOUS"})
_YES = ("y", "yes")  # Accepted affirmative responses (case-insensitive).


class AddressCorrector:
    """Review and push corrected site addresses back to Mist (per-site confirmed)."""

    def __init__(self, apisession: Any) -> None:
        """Store the authenticated Mist API session used for read + write calls."""
        self._api = apisession  # Mist session (its token's role governs write success).

    def correctable(self, results: list[AuditResult]) -> list[AuditResult]:
        """Return the rows whose suggestion is a real, pushable correction."""
        targets: list[AuditResult] = []  # Accumulate correctable rows.
        for result in results:  # Walk every audited row.
            if self._is_correctable(result):  # Has a site, a suggestion, and a correctable state.
                targets.append(result)  # Keep it for review.
        logging.debug("Identified %d correctable row(s) of %d", len(targets), len(results))  # Trace count.
        return targets  # One AuditResult per pushable correction.

    @staticmethod
    def _is_correctable(result: AuditResult) -> bool:
        """Return True when a row has a site, a suggestion, and a correctable state that differs."""
        suggestion = (result.suggested_address or "").strip()  # Suggested correction (may be empty).
        current = (result.matched_site.mist_address.get("address") or "").strip()  # Current Mist address.
        if not result.matched_site.site_id or not suggestion:  # Need a target site and a suggestion.
            return False  # Not pushable.
        if result.issue_type not in _CORRECTABLE:  # State does not call for a correction.
            return False  # Skip matches / Mist-better / no-result.
        return suggestion.lower() != current.lower()  # Only when the suggestion actually differs.

    def review_and_apply(self, results: list[AuditResult]) -> list[CorrectionOutcome]:
        """Per-site BEFORE/AFTER + ``[y/N]``; push the accepted ones; return all outcomes."""
        targets = self.correctable(results)  # Rows eligible for write-back.
        if not targets:  # Nothing to push.
            print("No correctable addresses to push.")  # Inform the operator.
            return []  # Empty outcome list.
        logging.info("Reviewing %d correctable address(es) for write-back", len(targets))  # Action-log start.
        self._print_intro(len(targets))  # Warn that this writes to Mist.
        outcomes = [self._review_one(result) for result in targets]  # Review/push each row.
        self._print_summary(outcomes)  # Show pushed/skipped/failed tally.
        return outcomes  # Outcomes drive the optional before/after report.

    def _review_one(self, result: AuditResult) -> CorrectionOutcome:
        """Show one site's BEFORE/AFTER, prompt, and push when the operator accepts."""
        site = result.matched_site  # Match outcome (site id + current address).
        before = (site.mist_address.get("address") or "").strip()  # Current Mist address string.
        after = result.suggested_address.strip()  # Corrected address to write.
        self._show(site.site_name or "-", before, after)  # Side-by-side display.
        choice = InputUtils.safe_input("Push this corrected address to Mist? [y/N]: ", context="address_writeback")
        if choice.strip().lower() not in _YES:  # Operator declined this site.
            logging.info("Operator skipped write-back for site %s", site.site_id)  # Action-log the skip.
            return CorrectionOutcome(site.site_name or "-", site.site_id or "", before, after, "skipped")
        return self._push(site.site_name or "-", site.site_id or "", before, after)  # Accepted -> push.

    def _push(self, name: str, site_id: str, before: str, after: str) -> CorrectionOutcome:
        """Write the corrected address to one Mist site; never raises."""
        logging.info("Pushing corrected address to site %s (%s)", site_id, name)  # Action-log the write.
        try:
            ok = self._update_site_address(site_id, after)  # Fetch-modify-PUT the site record.
        except Exception as exc:  # noqa: BLE001 -- one failed write must not abort the batch.
            logging.warning("Write-back failed for site %s: %s", site_id, exc)  # Surface the cause.
            print(f"  FAILED: {exc}")  # Inform the operator inline.
            return CorrectionOutcome(name, site_id, before, after, "failed", str(exc))
        if ok:  # Mist accepted the update.
            print("  PUSHED.")  # Confirm inline.
            return CorrectionOutcome(name, site_id, before, after, "pushed")
        print("  FAILED: Mist rejected the update (check token permissions).")  # Read-only / rejected.
        return CorrectionOutcome(name, site_id, before, after, "failed", "update rejected")

    def _update_site_address(self, site_id: str, address: str) -> bool:
        """Fetch the full site, replace only ``address``, and PUT it back; return success."""
        logging.debug("Fetching site %s before write-back", site_id)  # Trace the read.
        current = mistapi.api.v1.sites.sites.getSiteInfo(self._api, site_id)  # Full current site record.
        site = current.data if isinstance(current.data, dict) else {}  # Guard against list/empty payloads.
        if not site:  # No usable site record returned.
            logging.warning("Site %s returned no record; cannot write back", site_id)  # Trace the miss.
            return False  # Treat as a failed update.
        site["address"] = address  # Replace ONLY the address; everything else is preserved.
        updated = mistapi.api.v1.sites.sites.updateSiteInfo(self._api, site_id, site)  # PUT the full record.
        success = updated.status_code in (200, 201)  # 2xx => Mist accepted the change.
        logging.debug("Write-back for site %s status=%s", site_id, updated.status_code)  # Trace the result.
        return success  # True only on a 2xx response.

    @staticmethod
    def _print_intro(count: int) -> None:
        """Print a clear banner before any Mist write occurs."""
        print(f"\n--- Address write-back: {count} site(s) to review ---")  # Section header.
        print("This WRITES to your Mist sites. Confirm each site with y/N (default No).\n")  # Safety note.

    @staticmethod
    def _show(name: str, before: str, after: str) -> None:
        """Display one site's current vs corrected address side by side."""
        print(f"Site: {name}")  # Which site.
        print(f"  BEFORE: {before or '(empty)'}")  # Current Mist address.
        print(f"  AFTER:  {after}")  # Proposed corrected address.

    @staticmethod
    def _print_summary(outcomes: list[CorrectionOutcome]) -> None:
        """Print a pushed/skipped/failed tally after the review loop."""
        pushed = sum(1 for o in outcomes if o.action == "pushed")  # Successful writes.
        skipped = sum(1 for o in outcomes if o.action == "skipped")  # Operator declines.
        failed = sum(1 for o in outcomes if o.action == "failed")  # API failures.
        print(f"\nWrite-back complete: {pushed} pushed, {skipped} skipped, {failed} failed.")  # Tally line.
