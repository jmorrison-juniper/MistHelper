"""Pure model helpers for the rogue wireless PCI evidence pack."""

from __future__ import annotations  # Enable modern annotation syntax.

from dataclasses import dataclass  # Define small immutable records for the evidence pack.
from datetime import UTC, datetime  # Build one UTC run timestamp for audit evidence.
from typing import Any  # Type Mist API rows without binding to SDK classes.

CLASS_HONEYPOT = "honeypot"  # Name the SSID impersonation classification.
CLASS_ROGUE = "rogue"  # Name the unauthorized wired-network classification.
CLASS_NEIGHBOR = "neighbor"  # Name the nearby external AP classification.
SUMMARY_SOURCE_PAGE = "05-wlan-threat-client-and-pci-controls.md"  # Cite the source required by issue #3562.

EVIDENCE_COLUMNS = [  # Keep the CSV field order stable for assessors.
    "org_id",
    "site_id",
    "site_name",
    "classification",
    "ssid",
    "bssid",
    "channel",
    "band",
    "rssi",
    "first_seen",
    "last_seen",
    "client_count",
    "impersonated_org_ssid",
]

SETTINGS_COLUMNS = [  # Keep the settings CSV field order stable for assessors.
    "org_id",
    "site_id",
    "site_name",
    "rogue_enabled",
    "honeypot_enabled",
    "neighbor_rssi_threshold",
    "approved_ssid_count",
    "approved_bssid_count",
    "read_status",
    "run_started_at",
]


@dataclass(frozen=True)
class EvidenceContext:
    """Hold shared values that all evidence rows need."""

    org_id: str  # Identify the Mist organization that the run covers.
    run_started_at: str  # Use one audit timestamp across all output rows.
    org_ssids: frozenset[str]  # Store normalized organization WLAN SSIDs.
    org_ap_bssids: frozenset[str]  # Store normalized organization AP BSSIDs.
    site_names: dict[str, str]  # Map site identifiers to readable site names.


class RoguePciEvidenceModel:
    """Build classified rogue evidence rows, site setting rows, and a summary."""

    @staticmethod
    def run_timestamp() -> str:
        """Return the UTC timestamp used by one evidence run."""
        return datetime.now(UTC).isoformat(timespec="seconds")  # Keep the audit timestamp precise and readable.

    @staticmethod
    def normalize_text(value: Any) -> str:
        """Return a stripped string for display and comparison."""
        if value is None:  # Treat absent Mist fields as blank fields.
            return ""  # Preserve the row while leaving the missing field empty.
        return str(value).strip()  # Normalize whitespace without changing identifiers.

    @classmethod
    def normalize_mac(cls, value: Any) -> str:
        """Return a lowercase MAC string with common separators removed."""
        text = cls.normalize_text(value).lower()  # Compare MAC addresses case-insensitively.
        return text.replace(":", "").replace("-", "").replace(".", "")  # Remove common separators for matching.

    @classmethod
    def build_context(
        cls, org_id: str, wlans: list[dict[str, Any]], sites: list[dict[str, Any]], rows: list[dict[str, Any]]
    ) -> EvidenceContext:
        """Return shared lookup values for one evidence run."""
        org_ssids = frozenset(
            cls.normalize_text(row.get("ssid")) for row in wlans if cls.normalize_text(row.get("ssid"))
        )  # Keep named WLANs only.
        site_names = {
            cls.normalize_text(site.get("id")): cls.normalize_text(site.get("name")) for site in sites
        }  # Map site ids to names.
        org_ap_bssids = frozenset(
            cls.normalize_mac(row.get("ap_mac")) for row in rows if cls.normalize_mac(row.get("ap_mac"))
        )  # Use observer AP MACs as known org radios.
        return EvidenceContext(str(org_id), cls.run_timestamp(), org_ssids, org_ap_bssids, site_names)  # Share lookups.

    @classmethod
    def classify(cls, row: dict[str, Any], context: EvidenceContext) -> tuple[str, str]:
        """Return the classification and impersonated SSID for one detection."""
        ssid = cls.normalize_text(row.get("ssid"))  # Read the detected SSID for matching.
        bssid = cls.normalize_mac(row.get("bssid"))  # Read the detected BSSID for matching.
        if ssid in context.org_ssids and bssid not in context.org_ap_bssids:  # Detect an evil twin rule match.
            return CLASS_HONEYPOT, ssid  # Name the copied organization SSID.
        if row.get("seen_on_lan") is False or row.get("is_rogue") is False:  # Mist marks nearby APs as off-LAN.
            return CLASS_NEIGHBOR, ""  # Neighbor APs impersonate no org SSID in this model.
        return CLASS_ROGUE, ""  # Treat remaining unknown AP detections as rogue evidence.

    @classmethod
    def detection_row(cls, row: dict[str, Any], context: EvidenceContext) -> dict[str, Any]:
        """Return one flat evidence row from one Mist detection."""
        classification, impersonated_ssid = cls.classify(row, context)  # Classify before building the CSV row.
        site_id = cls.normalize_text(row.get("site_id"))  # Preserve the site identifier for joins.
        return {  # Build the stable CSV row for one detection.
            "org_id": context.org_id,
            "site_id": site_id,
            "site_name": context.site_names.get(site_id, cls.normalize_text(row.get("site_name")) or "Unknown Site"),
            "classification": classification,
            "ssid": cls.normalize_text(row.get("ssid")),
            "bssid": cls.normalize_text(row.get("bssid")),
            "channel": cls.normalize_text(row.get("channel")),
            "band": cls.normalize_text(row.get("band")),
            "rssi": cls.normalize_text(row.get("rssi", row.get("avg_rssi"))),
            "first_seen": cls.normalize_text(row.get("first_seen", row.get("timestamp"))),
            "last_seen": cls.normalize_text(row.get("last_seen", row.get("timestamp"))),
            "client_count": int(row.get("num_clients") or row.get("client_count") or 0),
            "impersonated_org_ssid": impersonated_ssid,
        }

    @classmethod
    def detection_rows(cls, rows: list[dict[str, Any]], context: EvidenceContext) -> list[dict[str, Any]]:
        """Return all flat detection rows."""
        return [cls.detection_row(row, context) for row in rows]  # Convert every source row with one rule path.

    @staticmethod
    def _count_list(value: Any) -> int:
        """Return the count of a list-like setting value."""
        if isinstance(value, list):  # Mist returns approved values as arrays in the site setting.
            return len(value)  # Count approved entries.
        if isinstance(value, str) and value.strip():  # Some fixtures or older exports can hold comma strings.
            return len([item for item in value.split(",") if item.strip()])  # Count nonblank comma entries.
        return 0  # Treat missing values as no approvals.

    @classmethod
    def setting_row(
        cls, site: dict[str, Any], setting: dict[str, Any] | None, context: EvidenceContext
    ) -> dict[str, Any]:
        """Return one flat site settings row."""
        site_id = cls.normalize_text(site.get("id"))  # Preserve the site identifier in every settings row.
        rogue = (
            (setting or {}).get("rogue", {}) if isinstance(setting or {}, dict) else {}
        )  # Read rogue settings safely.
        return {  # Build one row even when the settings read failed.
            "org_id": context.org_id,
            "site_id": site_id,
            "site_name": cls.normalize_text(site.get("name")) or "Unknown Site",
            "rogue_enabled": bool(rogue.get("enabled")) if setting else False,
            "honeypot_enabled": bool(rogue.get("honeypot_enabled")) if setting else False,
            "neighbor_rssi_threshold": rogue.get("min_rssi", ""),
            "approved_ssid_count": cls._count_list(rogue.get("whitelisted_ssids")),
            "approved_bssid_count": cls._count_list(rogue.get("whitelisted_bssids")),
            "read_status": "ok" if setting else "error",
            "run_started_at": context.run_started_at,
        }

    @classmethod
    def setting_rows(
        cls, sites: list[dict[str, Any]], settings: dict[str, dict[str, Any]], context: EvidenceContext
    ) -> list[dict[str, Any]]:
        """Return one settings row for each site."""
        return [
            cls.setting_row(site, settings.get(cls.normalize_text(site.get("id"))), context) for site in sites
        ]  # Keep every site.

    @staticmethod
    def _classification_count(rows: list[dict[str, Any]], classification: str) -> int:
        """Return how many detection rows use one classification."""
        return sum(1 for row in rows if row["classification"] == classification)  # Count one classification value.

    @staticmethod
    def _settings_status_counts(settings: list[dict[str, Any]]) -> dict[str, int]:
        """Return settings status counts for the summary."""
        return {  # Keep site status counts grouped away from detection counts.
            "site_count": len(settings),
            "detection_off_site_count": sum(1 for row in settings if not row["rogue_enabled"]),
            "incomplete_site_count": sum(1 for row in settings if row["read_status"] != "ok"),
        }

    @classmethod
    def summary_counts(cls, detections: list[dict[str, Any]], settings: list[dict[str, Any]]) -> dict[str, int]:
        """Return summary counts for the Markdown evidence statement."""
        counts = {  # Keep detection count names stable for tests and summary rendering.
            "detection_count": len(detections),
            "honeypot_count": cls._classification_count(detections, CLASS_HONEYPOT),
            "rogue_count": cls._classification_count(detections, CLASS_ROGUE),
            "neighbor_count": cls._classification_count(detections, CLASS_NEIGHBOR),
        }
        counts.update(cls._settings_status_counts(settings))  # Add site counts without extra branches.
        return counts  # Return all summary counts.

    @classmethod
    def summary_markdown(
        cls, detections: list[dict[str, Any]], settings: list[dict[str, Any]], context: EvidenceContext
    ) -> str:
        """Return the Markdown evidence summary."""
        counts = cls.summary_counts(detections, settings)  # Compute all counts from the written rows.
        lines = ["# Rogue and PCI Evidence Summary", ""]  # Start with a short assessor-facing heading.
        lines.append(f"- Run time: `{context.run_started_at}`")  # State when the evidence was collected.
        lines.append(f"- Organization ID: `{context.org_id}`")  # State the organization that the evidence covers.
        for key, value in counts.items():  # Render each measured count.
            lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")  # Keep a readable label and exact value.
        lines.append("")  # Separate counts from the PCI statement.
        lines.append(
            "The Mist cloud sits outside the Cardholder Data Environment "
            "because it does not carry wireless packet data."
        )  # Required PCI statement.
        lines.append(f"Source page: `{SUMMARY_SOURCE_PAGE}`.")  # Cite the required source page.
        return "\n".join(lines) + "\n"  # End the Markdown file with a newline.
