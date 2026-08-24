"""Log-redaction tests for AddressResolver (issue 1733).

CodeQL reported ten ``py/clear-text-logging-sensitive-data`` alerts in
``src/site/address_audit/address_resolver.py``. Every alert wrote a street
address into ``data/script.log``, and that log travels inside the menu-101
support bundle. These tests prove that no street address reaches the log any
more. Each test captures the log with ``caplog`` and asserts that the street
text is absent while the stable digest is present.
"""

import logging  # Set the caplog capture level for DEBUG-level assertions.

import pytest  # Fixtures for temporary paths and log capture.

from src.site.address_audit import address_resolver as resolver_mod  # Patch the Nominatim validator.
from src.site.address_audit.address_resolver import AddressResolver  # Class under test.
from src.site.address_audit.models import ResolveCandidates, ResolverResult  # Resolver input and output.
from src.utils.logger_utils import private_digest  # Expected digest value for each assertion.

_STREET = "742 Evergreen Terrace Suite 12"  # A private street the log must never show.
_CITY = "Springfield"  # City of the test address.
_ADDRESS = {"address": _STREET, "city": _CITY, "state": "OR", "zip": "97475"}  # Full test address dict.


class _MissValidator:
    """Stand-in validator that always reports an invalid comparison."""

    def __init__(self, config):
        """Accept and drop the config so the constructor matches NominatimValidator."""
        self._config = config  # Keep the config so the attribute exists for readers.

    def validate(self, mist, comparison):
        """Return an invalid comparison so the resolver takes the miss path."""
        return {"comparison_validation": {"valid": False}}  # Force the "no result" warning.


class _HitValidator:
    """Stand-in validator that always reports a valid comparison."""

    def __init__(self, config):
        """Accept and drop the config so the constructor matches NominatimValidator."""
        self._config = config  # Keep the config so the attribute exists for readers.

    def validate(self, mist, comparison):
        """Return a valid comparison so the resolver takes the hit path."""
        return {"comparison_validation": {"valid": True, "confidence": 0.9, "display_name": _STREET}}


def _candidates() -> ResolveCandidates:
    """Return a candidate set whose every source carries the private street."""
    return ResolveCandidates(mist_address=dict(_ADDRESS), csv_address=dict(_ADDRESS))  # One street, two sources.


def _log_text(caplog: pytest.LogCaptureFixture) -> str:
    """Return every captured log message joined into one string."""
    return "\n".join(record.getMessage() for record in caplog.records)  # One buffer to search.


class TestResolveLogsNoStreet:
    """The resolve entry point logs a digest, never the street."""

    def test_resolve_start_and_outcome_log_digest_only(
        self, tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """Prove the start log and the outcome log both hide the street."""
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _MissValidator)  # Avoid a real network call.
        monkeypatch.setattr(resolver_mod, "_NOMINATIM_MIN_INTERVAL", 0.0)  # Keep the test fast.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        with caplog.at_level(logging.DEBUG):  # Capture INFO and DEBUG records together.
            resolver.resolve(_candidates())  # Run one full resolution.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert _STREET not in text  # The street must never reach the log.
        assert _CITY not in text  # The city must never reach the log either.
        assert "Resolving address (key=" in text  # The start log still fires.
        assert "Resolved key=" in text  # The outcome log still fires.

    def test_cache_hit_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch) -> None:
        """Prove the cache-hit log hides the street on the second resolve."""
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _MissValidator)  # Avoid a real network call.
        monkeypatch.setattr(resolver_mod, "_NOMINATIM_MIN_INTERVAL", 0.0)  # Keep the test fast.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        resolver.resolve(_candidates())  # First call fills the cache.
        caplog.clear()  # Drop the first call's records so only the hit remains.
        with caplog.at_level(logging.DEBUG):  # The cache-hit log is a DEBUG record.
            resolver.resolve(_candidates())  # Second call hits the cache.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert _STREET not in text  # The street must never reach the log.
        assert "cache hit for key=" in text  # The hit log still fires.
        assert resolver.cache_hits == 1  # The counter proves the cache path ran.

    def test_resolve_failure_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch) -> None:
        """Prove the failure warning hides the street when a tier raises."""

        def _boom(*args, **kwargs):
            """Raise so the resolver takes its fail-soft warning path."""
            raise RuntimeError("tier exploded")  # A generic failure. The message holds no address.

        monkeypatch.setattr(AddressResolver, "_compare_internal", _boom)  # Force the except branch.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        with caplog.at_level(logging.WARNING):  # The failure log is a WARNING record.
            result = resolver.resolve(_candidates())  # Run the failing resolution.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert _STREET not in text  # The street must never reach the log.
        assert "Resolve failed for key=" in text  # The warning still fires.
        assert result.canonical_address is None  # The audit degrades instead of aborting.


class TestTierLogsNoStreet:
    """Every tier log carries a digest instead of the street."""

    def test_tier1_suggestion_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture) -> None:
        """Prove the Tier-1 suggestion log hides both the street and the suite."""
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        mist_without_suite = {"address": "742 Evergreen Terrace", "city": _CITY, "state": "OR", "zip": "97475"}
        candidates = ResolveCandidates(mist_address=mist_without_suite, csv_address=dict(_ADDRESS))  # Suite in CSV.
        with caplog.at_level(logging.DEBUG):  # The Tier-1 log is a DEBUG record.
            result = resolver._compare_internal(candidates)  # Run Tier 1 on its own.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert "Suite 12" not in text  # The suite is part of a private address.
        assert "Evergreen" not in text  # The street name must not reach the log.
        assert "suite_found=True" in text  # The operator still learns that a suite was found.
        assert result is not None  # Tier 1 still returns its suggestion.

    def test_nominatim_miss_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch) -> None:
        """Prove the Nominatim "no result" warning hides the street."""
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _MissValidator)  # Force the miss path.
        monkeypatch.setattr(resolver_mod, "_NOMINATIM_MIN_INTERVAL", 0.0)  # Keep the test fast.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        with caplog.at_level(logging.INFO):  # Capture the start log and the miss warning.
            outcome = resolver._validate_nominatim(_candidates(), _STREET)  # Run Tier 2 on its own.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert _STREET not in text  # The street must never reach the log.
        assert private_digest("742 Evergreen Terrace") in text  # Tier 2 strips the suite before it geocodes.
        assert "Nominatim returned no result for street key=" in text  # The warning still fires.
        assert outcome is None  # A miss defers to the next tier.

    def test_nominatim_hit_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch) -> None:
        """Prove the Nominatim success log hides the canonical street."""
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _HitValidator)  # Force the hit path.
        monkeypatch.setattr(resolver_mod, "_NOMINATIM_MIN_INTERVAL", 0.0)  # Keep the test fast.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        with caplog.at_level(logging.INFO):  # The success log is an INFO record.
            outcome = resolver._validate_nominatim(_candidates(), _STREET)  # Run Tier 2 on its own.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert _STREET not in text  # The street must never reach the log.
        assert "Nominatim validated street (key=" in text  # The success log still fires.
        assert outcome is not None  # Tier 2 still returns its result.

    def test_tier3_retry_logs_digest_only(self, tmp_path, caplog: pytest.LogCaptureFixture) -> None:
        """Prove the Tier-3 retry log hides the plain address."""
        geocoder = _EmptyGeocoder()  # A geocoder that never finds an address forces the retry.
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"), ui_geocoder=geocoder)  # Tier 3 enabled.
        candidates = ResolveCandidates(  # A business name is required before the retry can run.
            mist_address=dict(_ADDRESS), csv_address=dict(_ADDRESS), business_name="Kwik-E-Mart"
        )
        with caplog.at_level(logging.INFO):  # The retry log is an INFO record.
            resolver._ui_lookup_with_fallback(candidates, f"Kwik-E-Mart {_STREET}")  # Run the fallback path.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert "Evergreen" not in text  # The street name must not reach the log.
        assert "Tier 3 retrying without business prefix (key=" in text  # The retry log still fires.
        assert geocoder.calls == 2  # The primary lookup and the retry both ran.


class _EmptyGeocoder:
    """Stand-in UI geocoder that always returns an empty result."""

    def __init__(self) -> None:
        """Start the call counter at zero."""
        self.calls = 0  # Count every geocode call so the test can assert the retry ran.

    def geocode_via_ui(self, query: str) -> ResolverResult:
        """Return an empty result so the caller retries without the business prefix."""
        self.calls += 1  # Record this lookup.
        return ResolverResult(query=query, canonical_address=None)  # No address found.


class TestConflictingHintsLogsNoHouseNumbers:
    """The conflicting-hint log reports a count, never the house numbers."""

    def test_conflict_log_reports_count_only(self, tmp_path, caplog: pytest.LogCaptureFixture) -> None:
        """Prove the conflict log omits every house number."""
        resolver = AddressResolver(db_path=str(tmp_path / "mist_data.db"))  # Isolated cache DB per test.
        candidates = ResolveCandidates(  # Two sources disagree on the house number with no majority.
            mist_address={"address": "742 Evergreen Terrace", "city": _CITY, "state": "OR", "zip": "97475"},
            csv_address={"address": "913 Evergreen Terrace", "city": _CITY, "state": "OR", "zip": "97475"},
        )
        with caplog.at_level(logging.INFO):  # The conflict log is an INFO record.
            conflicted = resolver.has_conflicting_hints(candidates)  # Run the conflict check.
        text = _log_text(caplog)  # Collapse the records into one searchable buffer.
        assert "742" not in text  # The first house number must not reach the log.
        assert "913" not in text  # The second house number must not reach the log.
        assert "2 distinct values" in text  # The operator still learns that two hints disagree.
        assert conflicted is True  # The row is still flagged for manual review.
