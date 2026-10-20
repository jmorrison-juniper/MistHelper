"""Unit tests for rogue PCI evidence model helpers."""

from src.mist.intelligence.reports.rogue_pci_evidence.model import (  # Import the pure model under test.
    CLASS_HONEYPOT,
    CLASS_NEIGHBOR,
    CLASS_ROGUE,
    SUMMARY_SOURCE_PAGE,
    RoguePciEvidenceModel,
)


def _context():  # Provide a shared context fixture without pytest fixture overhead.
    """Return a deterministic evidence context for model tests."""
    wlans = [{"ssid": "CorpWiFi"}]  # Define one approved organization SSID.
    sites = [{"id": "site-1", "name": "HQ"}]  # Define one site for row labels.
    ap_rows = [{"ap_mac": "aa:bb:cc:dd:ee:ff"}]  # Define one known organization AP radio.
    return RoguePciEvidenceModel.build_context("org-1", wlans, sites, ap_rows)  # Build the lookup context.


def test_honeypot_classification_names_impersonated_ssid():
    """A matching org SSID with an unknown BSSID is a honeypot."""
    row = {"site_id": "site-1", "ssid": "CorpWiFi", "bssid": "11:22:33:44:55:66"}  # Build a honeypot row.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Classify the detection.
    assert evidence["classification"] == CLASS_HONEYPOT  # Verify the honeypot label.
    assert evidence["impersonated_org_ssid"] == "CorpWiFi"  # Verify the copied SSID is named.


def test_approved_org_ap_bssid_prevents_honeypot_classification():
    """A known org AP BSSID prevents a matching SSID from becoming a honeypot."""
    row = {"site_id": "site-1", "ssid": "CorpWiFi", "bssid": "aa:bb:cc:dd:ee:ff"}  # Build an approved AP row.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Classify the approved AP detection.
    assert evidence["classification"] == CLASS_ROGUE  # Verify the honeypot rule excludes known org AP BSSIDs.
    assert evidence["impersonated_org_ssid"] == ""  # Verify approved AP rows do not name an impersonated SSID.


def test_honeypot_classification_takes_precedence_over_neighbor_signal():
    """A copied org SSID with an unknown BSSID remains a honeypot when off LAN."""
    row = {
        "site_id": "site-1",
        "ssid": "CorpWiFi",
        "bssid": "11:22:33:44:55:66",
        "seen_on_lan": False,
    }  # Build a row with both honeypot and neighbor signals.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Classify the precedence case.
    assert evidence["classification"] == CLASS_HONEYPOT  # Verify honeypot takes precedence.
    assert evidence["impersonated_org_ssid"] == "CorpWiFi"  # Verify the copied SSID remains named.


def test_neighbor_classification_uses_off_lan_signal():
    """An off-LAN row is a neighbor when it is not a honeypot."""
    row = {
        "site_id": "site-1",
        "ssid": "Guest",
        "bssid": "11:22:33:44:55:66",
        "seen_on_lan": False,
    }  # Build neighbor row.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Classify the detection.
    assert evidence["classification"] == CLASS_NEIGHBOR  # Verify the neighbor label.


def test_rogue_classification_is_default_for_unknown_on_lan_ap():
    """An unknown AP without the honeypot or neighbor signal is rogue."""
    row = {"site_id": "site-1", "ssid": "Guest", "bssid": "11:22:33:44:55:66", "seen_on_lan": True}  # Build rogue row.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Classify the detection.
    assert evidence["classification"] == CLASS_ROGUE  # Verify the default rogue label.


def test_detection_row_converts_epoch_milliseconds_to_utc_iso_text():
    """Epoch millisecond fields become UTC ISO timestamps."""
    row = {
        "site_id": "site-1",
        "ssid": "Guest",
        "bssid": "11:22:33:44:55:66",
        "first_seen": 1_789_249_851_000,
        "last_seen": 1_789_249_911_000,
    }  # Match the live rogue evidence timestamp shape.
    evidence = RoguePciEvidenceModel.detection_row(row, _context())  # Build the evidence row.
    assert evidence["first_seen"] == "2026-09-12T21:50:51Z"  # Verify first_seen is UTC ISO text.
    assert evidence["last_seen"] == "2026-09-12T21:51:51Z"  # Verify last_seen is UTC ISO text.


def test_detection_off_site_is_counted_in_summary():
    """A site with rogue detection off appears in the summary count."""
    sites = [{"id": "site-1", "name": "HQ"}]  # Define one site for settings output.
    settings = {"site-1": {"rogue": {"enabled": False, "honeypot_enabled": True}}}  # Disable rogue detection.
    rows = RoguePciEvidenceModel.setting_rows(sites, settings, _context())  # Build settings rows.
    counts = RoguePciEvidenceModel.summary_counts([], rows)  # Count the settings evidence.
    assert rows[0]["rogue_enabled"] is False  # Verify the CSV row keeps detection off.
    assert counts["detection_off_site_count"] == 1  # Verify the summary counts the disabled site.


def test_summary_names_required_source_page():
    """The summary cites the Mist wireless PCI source page."""
    summary = RoguePciEvidenceModel.summary_markdown([], [], _context())  # Build an empty-run summary.
    assert SUMMARY_SOURCE_PAGE in summary  # Verify the required source page is named.
    assert "outside the Cardholder Data Environment" in summary  # Verify the PCI boundary statement.
