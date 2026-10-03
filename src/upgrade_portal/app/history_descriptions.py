"""Describe history cards from the existing validated site context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoryCardDescription:
    """Hold the three settled descriptions of one history card."""

    note: str
    empty: str
    caption: str

    @staticmethod
    def scope_subject(site_id: str, site_name: str) -> str:
        """Name a trusted stored site, an unnamed selected site, or the selected organization."""
        if not site_id:
            return "the selected organization"
        return site_name or "the selected site"


@dataclass(frozen=True, slots=True)
class HistoryCardScope:
    """Build three card descriptions without reading another source."""

    site_id: str
    site_name: str

    @property
    def runs(self) -> HistoryCardDescription:
        """Describe single-site runs, including an empty later page."""
        subject = HistoryCardDescription.scope_subject(self.site_id, self.site_name)
        records = f"The single-site upgrade runs of {subject}"
        return HistoryCardDescription(
            note=f"{records}, newest first.",
            empty=f"This page shows no single-site upgrade run for {subject}.",
            caption=f"{records}.",
        )

    @property
    def operations(self) -> HistoryCardDescription:
        """Describe operations that include the site, or operations of the selected organization."""
        subject = HistoryCardDescription.scope_subject(self.site_id, self.site_name)
        relation = "that include" if self.site_id else "of"
        records = f"The multi-site upgrades {relation} {subject}"
        empty_relation = "that includes" if self.site_id else "for"
        return HistoryCardDescription(
            note=f"{records}, newest first.",
            empty=f"This page shows no multi-site upgrade {empty_relation} {subject}.",
            caption=f"{records}.",
        )

    @property
    def audit(self) -> HistoryCardDescription:
        """Describe lock actions inside the same organization and optional site scope."""
        subject = HistoryCardDescription.scope_subject(self.site_id, self.site_name)
        records = f"The site lock actions of {subject}"
        return HistoryCardDescription(
            note=f"{records}, newest first.",
            empty=f"This page shows no site lock action for {subject}.",
            caption=f"{records}.",
        )
