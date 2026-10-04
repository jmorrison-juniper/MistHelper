"""Unit tests for PSK hygiene model scoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.mist.intelligence.reports.psk_hygiene import model


def _now() -> datetime:
    """Return a stable test time."""
    return datetime(2026, 9, 29, 12, 0, tzinfo=UTC)  # Keep time math deterministic.


def _base_record(**overrides: object) -> dict[str, object]:
    """Return one PSK record for model tests."""
    record: dict[str, object] = {  # Provide a safe default PSK with no findings.
        "name": "Kitchen sensor",
        "ssid": "Facility",
        "role": "iot",
        "vlan": 20,
        "usage": 1,
        "max_usage": 2,
        "expire_time": None,
        "mac": "aa:bb:cc:dd:ee:ff",
    }
    record.update(overrides)  # Let each test focus on one changed field.
    return record  # Return the assembled fake Mist record.


def _row_for(record: dict[str, object], wlans: list[dict[str, object]] | None = None) -> model.PskHygieneRow:
    """Return the first hygiene row for one fake PSK."""
    psks = model.PskHygieneScorer.psk_inputs_from_records([record])  # Sanitize the fake PSK input.
    refs = None if wlans is None else model.PskHygieneScorer.wlan_references_from_records(wlans, [])
    return model.PskHygieneScorer.build_hygiene_rows(psks, refs, now=_now())[0]  # Score the single PSK.


def test_psk_input_strips_secret_values() -> None:
    """Sanitized PSK input keeps only old passphrase presence."""
    psk = model.PskInput.from_record(
        _base_record(passphrase="secret-value", old_passphrase="old-secret-value")
    )  # Build the sanitized PSK.
    assert not hasattr(psk, "passphrase")  # The current passphrase must not survive sanitization.
    assert not hasattr(psk, "old_passphrase")  # The old passphrase value must not survive sanitization.
    assert psk.old_passphrase_present is True  # The model keeps only the safe presence flag.


def test_normalize_ssid_trims_edges() -> None:
    """SSID normalization trims leading and trailing spaces."""
    psk = model.PskInput.from_record(_base_record(ssid="  Facility  "))  # Build a PSK with padded SSID text.
    assert psk.ssid == "Facility"  # The normalized SSID should match organization WLAN text.


def test_expired_finding() -> None:
    """Past expire time adds the expired finding."""
    expire_time = (_now() - timedelta(days=1)).isoformat()  # Use a past expire time.
    row = _row_for(_base_record(expire_time=expire_time), [{"ssid": "Facility"}])  # Score the PSK.
    assert row.findings == "expired"  # The row should show the expired finding.


def test_expires_soon_finding() -> None:
    """Future expire time inside thirty days adds expires_soon."""
    expire_time = (_now() + timedelta(days=30)).isoformat()  # Use the contract warning boundary.
    row = _row_for(_base_record(expire_time=expire_time), [{"ssid": "Facility"}])  # Score the PSK.
    assert row.findings == "expires_soon"  # The row should show the warning finding.


def test_uncapped_multi_use_finding() -> None:
    """PSK without MAC binding and cap adds uncapped_multi_use."""
    row = _row_for(_base_record(mac=None, macs=[], max_usage=None), [{"ssid": "Facility"}])  # Score the PSK.
    assert row.findings == "uncapped_multi_use"  # The row should show the cap finding.


def test_rotation_pending_finding_uses_presence_only() -> None:
    """Old passphrase presence adds rotation_pending only."""
    row = _row_for(_base_record(old_passphrase="old-secret-value"), [{"ssid": "Facility"}])  # Score the PSK.
    assert row.rotation_pending is True  # The row should show that rotation is pending.
    assert row.old_passphrase_present is True  # The row should show only the presence flag.
    assert "old-secret-value" not in str(row.as_output_row())  # The old passphrase value must not be exported.


def test_orphan_ssid_finding() -> None:
    """Unknown organization SSID adds orphan_ssid."""
    row = _row_for(_base_record(ssid="Guest"), [{"ssid": "Facility"}])  # Score a PSK with no WLAN match.
    assert row.wlan_match is False  # The row should show a known missing match.
    assert row.findings == "orphan_ssid"  # The row should show the orphan finding.


def test_template_wlan_matching() -> None:
    """Template WLANs participate in SSID matching."""
    psks = model.PskHygieneScorer.psk_inputs_from_records([_base_record(ssid="TemplateSSID")])
    refs = model.PskHygieneScorer.wlan_references_from_records(
        [], [{"name": "Campus", "wlans": [{"ssid": "TemplateSSID"}]}]
    )  # Build refs.
    row = model.PskHygieneScorer.build_hygiene_rows(psks, refs, now=_now())[0]  # Score with template references.
    assert row.wlan_match is True  # The template SSID should count as an organization-scope match.
    assert row.findings == ""  # The row should have no orphan finding.


def test_unknown_wlan_scope_does_not_add_orphan_ssid() -> None:
    """Unknown WLAN scope returns unknown match without orphan finding."""
    row = _row_for(_base_record(ssid="Guest"), None)  # Score with unavailable WLAN data.
    assert row.wlan_match == "unknown"  # The row should show unknown scope.
    assert "orphan_ssid" not in row.findings  # The row must not make a false orphan claim.


def test_output_row_redacts_secret_fields() -> None:
    """Output rows never include passphrase or old_passphrase values."""
    row = _row_for(
        _base_record(passphrase="secret-value", old_passphrase="old-secret-value"), [{"ssid": "Facility"}]
    )  # Score a PSK that contains both secret fields.
    output_row = row.as_output_row()  # Convert to the exporter contract.
    assert "passphrase" not in output_row  # The current passphrase column must not exist.
    assert "old_passphrase" not in output_row  # The old passphrase column must not exist.
    assert "secret-value" not in str(output_row)  # The current passphrase value must not be exported.
    assert "old-secret-value" not in str(output_row)  # The old passphrase value must not be exported.


def test_summary_counts_all_findings() -> None:
    """Summary counts match the findings column."""
    rows = [  # Build rows with each finding label.
        _row_for(_base_record(expire_time=(_now() - timedelta(days=1)).isoformat()), [{"ssid": "Facility"}]),
        _row_for(_base_record(expire_time=(_now() + timedelta(days=1)).isoformat()), [{"ssid": "Facility"}]),
        _row_for(_base_record(mac=None, macs=[], max_usage=None), [{"ssid": "Facility"}]),
        _row_for(_base_record(old_passphrase="old-secret-value"), [{"ssid": "Facility"}]),
        _row_for(_base_record(ssid="Guest"), [{"ssid": "Facility"}]),
    ]
    summary = model.HygieneSummary.from_rows(rows)  # Aggregate the row findings.
    assert summary.total_psks == 5  # The total should count every row.
    assert summary.expired == 1  # The expired count should match row labels.
    assert summary.expires_soon == 1  # The soon count should match row labels.
    assert summary.uncapped_multi_use == 1  # The uncapped count should match row labels.
    assert summary.rotation_pending == 1  # The rotation count should match row labels.
    assert summary.orphan_ssid == 1  # The orphan count should match row labels.


def test_zero_finding_summary() -> None:
    """Summary returns zeros when no findings exist."""
    row = _row_for(_base_record(), [{"ssid": "Facility"}])  # Score a clean PSK.
    summary = model.HygieneSummary.from_rows([row])  # Aggregate the clean row.
    assert summary.total_psks == 1  # The total should still count the row.
    assert summary.expired == 0  # No expired finding should exist.
    assert summary.expires_soon == 0  # No soon finding should exist.
    assert summary.uncapped_multi_use == 0  # No uncapped finding should exist.
    assert summary.rotation_pending == 0  # No rotation finding should exist.
    assert summary.orphan_ssid == 0  # No orphan finding should exist.


def test_model_has_no_forbidden_dependency_imports() -> None:
    """The model module stays independent from operation dependencies."""
    source = model.__loader__.get_source(model.__name__)  # Read the loaded model source text.
    assert isinstance(source, str) and "Pure scoring model" in source  # Prove the project source loaded correctly.
    assert "mistapi" not in source  # The model must not import the Mist SDK.
    assert "DataExporter" not in source  # The model must not import the exporter.
    assert "ConfigUtils" not in source  # The model must not import organization prompts.
    assert "SourceDependencyResolver" not in source  # The model must not import runtime dependencies.
