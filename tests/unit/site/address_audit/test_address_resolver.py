"""Unit tests for AddressResolver Tier 1/2 + cache (1003-site-address-audit)."""

from unittest.mock import MagicMock

from src.site.address_audit import address_resolver as resolver_mod
from src.site.address_audit.address_resolver import AddressResolver
from src.site.address_audit.models import ResolveCandidates, ResolverResult

_NO_SUITE = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
_WITH_SUITE = {"address": "100 Main St Suite 5", "city": "Town", "state": "FL", "zip": "33000"}


class _FakeValidator:
    """Stand-in for NominatimValidator that records construction count."""

    count = 0  # Class-level construction counter (reset per test).
    valid = True  # Whether validate() reports a valid comparison.

    def __init__(self, config):
        _FakeValidator.count += 1

    def validate(self, mist, comp):
        return {
            "comparison_validation": {
                "valid": _FakeValidator.valid,
                "confidence": 0.8,
                "display_name": "100 Main St Suite 5, Town, FL",
            }
        }


def _db(tmp_path):
    """Return a temp cache DB path."""
    return str(tmp_path / "mist_data.db")


class TestTier1Internal:
    """Tier 1 internal comparison (no network)."""

    def test_internal_suite_no_network(self, tmp_path, monkeypatch):
        """CSV carrying a suite Mist lacks resolves internally with zero network."""
        # Any attempt to construct the validator would be a network path -> fail the test.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", MagicMock(side_effect=AssertionError("no net")))
        resolver = AddressResolver(db_path=_db(tmp_path))
        candidates = ResolveCandidates(mist_address=_NO_SUITE, csv_address=_WITH_SUITE)
        result = resolver.resolve(candidates)
        assert result.source == "internal"
        assert "Suite 5" in result.canonical_address


class TestTier2Nominatim:
    """Tier 2 Nominatim validation + caching."""

    def test_nominatim_then_cache_hit(self, tmp_path, monkeypatch):
        """First resolve hits Nominatim; an identical rerun is served from cache."""
        _FakeValidator.count = 0
        _FakeValidator.valid = True
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)  # Skip rate-limit sleeps.
        resolver = AddressResolver(db_path=_db(tmp_path))
        candidates = ResolveCandidates(mist_address=_NO_SUITE, csv_address=_NO_SUITE)
        first = resolver.resolve(candidates)
        second = resolver.resolve(candidates)
        assert first.source == "nominatim"
        assert second.source == "cache"
        assert _FakeValidator.count == 1  # Second call made zero external calls.

    def test_nominatim_invalid_is_no_result(self, tmp_path, monkeypatch):
        """An invalid Nominatim comparison yields canonical_address None."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        resolver = AddressResolver(db_path=_db(tmp_path))
        result = resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=_NO_SUITE))
        assert result.canonical_address is None


class TestTier3Gating:
    """Tier 3 UI geocoder must be opt-in only."""

    def test_ui_not_invoked_when_disabled(self, tmp_path, monkeypatch):
        """With ui_geocode False, the injected UI geocoder is never called."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False  # Force Tier 2 to yield nothing.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=_NO_SUITE, ui_geocode=False))
        ui.geocode_via_ui.assert_not_called()

    def test_ui_invoked_when_enabled(self, tmp_path, monkeypatch):
        """With ui_geocode True and Tier 1/2 empty, the UI geocoder is consulted."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        ui.geocode_via_ui.return_value = ResolverResult(query="q", canonical_address="X", source="mist_ui")
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        result = resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=_NO_SUITE, ui_geocode=True))
        ui.geocode_via_ui.assert_called_once()
        assert result.source == "mist_ui"


class TestHelpers:
    """Query-key normalization and rate limiting."""

    def test_query_key_normalized(self):
        """Query keys are lowercased and whitespace-collapsed."""
        assert AddressResolver._build_query_key("  Foo   BAR  ") == "foo bar"

    def test_rate_limit_sleeps_on_rapid_calls(self, monkeypatch):
        """Two back-to-back rate-limit checks trigger at least one sleep."""
        slept = []
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda s: slept.append(s))
        resolver = AddressResolver()
        resolver._respect_rate_limit()
        resolver._respect_rate_limit()
        assert slept  # Second rapid call paused.
