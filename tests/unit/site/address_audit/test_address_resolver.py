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


class TestCleanSuggestion:
    """Tier 1 builds a clean Mist-base + suite suggestion, free of SAP/zip pollution."""

    def test_suggestion_uses_mist_base_and_zip(self):
        """Suggestion = Mist street + CSV suite + Mist city/state/zip (not the SNMP zip)."""
        res = AddressResolver()
        mist = {"address": "5550 N Military Trl", "city": "Boca Raton", "state": "FL", "zip": "33431"}
        csv = {"address": "5550 N Military Trail Unit 200", "city": "Boca Raton", "state": "FL", "zip": "33431"}
        # SNMP carries a different (wrong) zip; it must not leak into the suggestion.
        cand = ResolveCandidates(
            mist_address=mist, csv_address=csv, snmp_location="5550 N Military Trl Unit 200 FL 33496"
        )
        result = res._compare_internal(cand)
        assert result is not None
        assert result.canonical_address == "5550 N Military Trl Unit 200, Boca Raton, FL 33431"

    def test_hash_suite_detected(self):
        """A bare '#3' suite is detected and appended cleanly."""
        res = AddressResolver()
        mist = {"address": "940 S Military Trail", "city": "West Palm Beach", "state": "FL", "zip": "33415"}
        csv = {"address": "940 S Military Trail #3", "city": "West Palm Beach", "state": "FL", "zip": "33415"}
        result = res._compare_internal(ResolveCandidates(mist_address=mist, csv_address=csv))
        assert result.canonical_address == "940 S Military Trail #3, West Palm Beach, FL 33415"

    def test_space_suite_detected(self):
        """A 'Space P239' suite is detected (broadened keyword set)."""
        res = AddressResolver()
        mist = {"address": "3101 PGA Boulevard", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        csv = {"address": "3101 PGA Boulevard Space P239", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        result = res._compare_internal(ResolveCandidates(mist_address=mist, csv_address=csv))
        assert result.canonical_address == "3101 PGA Boulevard Space P239, Palm Beach Gardens, FL 33410"

    def test_prefers_csv_suite_over_bad_snmp(self):
        """When SNMP holds a different (stale) address, the CSV suite is used on the Mist base."""
        res = AddressResolver()
        mist = {"address": "3101 PGA Boulevard", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        csv = {"address": "3101 PGA Boulevard Space P239", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        cand = ResolveCandidates(
            mist_address=mist, csv_address=csv, snmp_location="1520 Route 38 Bldg 4 Hainesport NJ 08060"
        )
        result = res._compare_internal(cand)
        assert result.canonical_address == "3101 PGA Boulevard Space P239, Palm Beach Gardens, FL 33410"

    def test_prefers_authoritative_suite_over_csv(self):
        """When business-authoritative suite differs, Tier 1 prefers authoritative over CSV."""
        res = AddressResolver()
        mist = {"address": "4200 Conroy Rd", "city": "Orlando", "state": "FL", "zip": "32839"}
        csv = {"address": "4200 Conroy Rd Suite H200", "city": "Orlando", "state": "FL", "zip": "32839"}
        authority = {"address": "4200 Conroy Rd #204", "city": "Orlando", "state": "FL", "zip": "32839"}
        cand = ResolveCandidates(mist_address=mist, csv_address=csv, authoritative_address=authority)
        result = res._compare_internal(cand)
        assert result is not None
        assert result.canonical_address == "4200 Conroy Rd #204, Orlando, FL 32839"

    def test_no_suite_anywhere_defers(self):
        """With no suite in CSV or SNMP, Tier 1 returns None (defers to OSM)."""
        res = AddressResolver()
        mist = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
        csv = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
        assert res._compare_internal(ResolveCandidates(mist_address=mist, csv_address=csv)) is None

    def test_mist_already_has_suite_defers(self):
        """If Mist already carries a suite, Tier 1 does not flag MISSING_SUITE."""
        res = AddressResolver()
        mist = {"address": "100 Main St Suite 9", "city": "Town", "state": "FL", "zip": "33000"}
        csv = {"address": "100 Main St Suite 5", "city": "Town", "state": "FL", "zip": "33000"}
        assert res._compare_internal(ResolveCandidates(mist_address=mist, csv_address=csv)) is None


class TestTier1Internal:
    """Tier 1 internal comparison (no network)."""

    def test_internal_suite_with_osm_street_validation(self, tmp_path, monkeypatch):
        """CSV suite resolves internally; OSM additionally confirms the street."""
        _FakeValidator.count = 0
        _FakeValidator.valid = True  # OSM validates the street successfully.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)  # Skip rate-limit sleeps.
        resolver = AddressResolver(db_path=_db(tmp_path))
        candidates = ResolveCandidates(mist_address=_NO_SUITE, csv_address=_WITH_SUITE)
        result = resolver.resolve(candidates)
        assert result.source == "internal"  # Suite came from the internal CSV candidate.
        assert "Suite 5" in result.canonical_address
        assert result.street_validated is True  # OSM externally confirmed the base street.

    def test_internal_suite_osm_unconfirmed(self, tmp_path, monkeypatch):
        """When OSM cannot confirm the street, the internal suite still resolves, unflagged."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False  # OSM returns nothing.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        resolver = AddressResolver(db_path=_db(tmp_path))
        candidates = ResolveCandidates(mist_address=_NO_SUITE, csv_address=_WITH_SUITE)
        result = resolver.resolve(candidates)
        assert result.source == "internal"
        assert result.street_validated is False  # OSM did not confirm the street.


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

    def test_nominatim_canonical_cleans_display_name(self):
        """An OSM-validated row surfaces Mist's clean address, not the noisy display_name."""
        resolver = AddressResolver()
        # Real Mist structure: 'address' is the full formatted string (no separate city/state/zip).
        cand = ResolveCandidates(
            mist_address={"address": "1200 NW 87th Ave #1st, Doral, FL 33172, USA", "city": "", "state": "", "zip": ""},
            csv_address={"address": "1200 NW 87th Ave", "city": "Doral", "state": "FL", "zip": "33172"},
        )
        comparison = {
            "valid": True,
            "confidence": 0.82,
            "display_name": "T-Mobile, 1200, Northwest 87th Avenue, Doral, Miami-Dade County, Florida, 33172, USA",
        }
        # Trailing country dropped, suite preserved, county/business noise gone.
        assert resolver._nominatim_canonical(cand, comparison) == "1200 NW 87th Ave #1st, Doral, FL 33172"

    def test_nominatim_canonical_falls_back_to_display_name(self):
        """With no usable Mist address, the raw display_name is the last resort."""
        resolver = AddressResolver()
        cand = ResolveCandidates(mist_address={"address": ""}, csv_address={})
        comparison = {"display_name": "5 Main St, Town, FL"}
        assert resolver._nominatim_canonical(cand, comparison) == "5 Main St, Town, FL"


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

    def test_ui_wins_over_internal_and_osm(self, tmp_path, monkeypatch):
        """Tier 3 (web authority) overrides internal + OSM when Mist lacks a suite."""
        _FakeValidator.count = 0
        _FakeValidator.valid = True  # OSM also validates -> proves Tier 3 still wins.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        ui.geocode_via_ui.return_value = ResolverResult(
            query="q", canonical_address="100 Main St #200, Town, FL 33000", source="mist_ui", confidence=0.9
        )
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        csv = {"address": "100 Main St Unit 200", "city": "Town", "state": "FL", "zip": "33000"}  # Internal suite.
        result = resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=csv, ui_geocode=True))
        ui.geocode_via_ui.assert_called_once()
        assert result.source == "mist_ui"  # Web authority wins over the internal suggestion.
        assert result.canonical_address == "100 Main St #200, Town, FL 33000"
        assert result.street_validated is True  # OSM cross-checked the street.

    def test_ui_skipped_when_mist_has_suite(self, tmp_path, monkeypatch):
        """No Tier-3 lookup when Mist already carries a suite that matches the CSV."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        resolver.resolve(ResolveCandidates(mist_address=_WITH_SUITE, csv_address=_WITH_SUITE, ui_geocode=True))
        ui.geocode_via_ui.assert_not_called()  # Mist suite matches the CSV -> skip the slow lookup.

    def test_ui_consulted_when_suite_conflicts(self, tmp_path, monkeypatch):
        """Tier 3 runs to adjudicate when Mist's suite differs from the CSV's."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        ui.geocode_via_ui.return_value = ResolverResult(
            query="q", canonical_address="4200 Conroy Rd Suite H200, Orlando, FL", source="mist_ui"
        )
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        mist = {"address": "4200 Conroy Rd #204", "city": "Orlando", "state": "FL", "zip": "32839"}
        csv = {"address": "4200 Conroy Rd Suite H200", "city": "Orlando", "state": "FL", "zip": "32839"}
        resolver.resolve(ResolveCandidates(mist_address=mist, csv_address=csv, ui_geocode=True))
        ui.geocode_via_ui.assert_called()  # Conflicting suites -> adjudicate via the web.

    def test_suite_unit_extracts_identifier(self):
        """The bare unit identifier is extracted for conflict comparison."""
        assert AddressResolver._suite_unit("4200 Conroy Rd #204") == "204"
        assert AddressResolver._suite_unit("4200 Conroy Rd Suite H200") == "h200"
        assert AddressResolver._suite_unit("100 Main St Ste 100") == "100"
        assert AddressResolver._suite_unit("100 Main St") == ""

    def test_should_consult_ui_matrix(self):
        """The Tier-3 gate: run on missing or conflicting suites, skip on a match."""
        res = AddressResolver()

        def gate(mist, csv, authority=""):
            cand = ResolveCandidates(
                mist_address={"address": mist},
                csv_address={"address": csv},
                authoritative_address={"address": authority},
            )
            return res._should_consult_ui(cand)

        assert gate("100 Main St", "100 Main St Suite 5") is True  # Mist missing -> discover.
        assert gate("100 Main St #204", "100 Main St Suite H200") is True  # Conflict -> adjudicate.
        assert gate("100 Main St Suite 100", "100 Main St Ste 100") is False  # Same unit -> skip.
        assert gate("100 Main St #1st", "100 Main St") is False  # CSV claims no unit -> skip.
        assert gate("100 Main St #204", "100 Main St #204", "100 Main St Suite H200") is True  # Authority conflict.

    def test_internal_used_when_ui_returns_none(self, tmp_path, monkeypatch):
        """When Tier 3 returns None, the internal suite suggestion is used (no worse than before)."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        ui.geocode_via_ui.return_value = None  # Selectors/login failed -> fail-soft.
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        csv = {"address": "100 Main St Unit 200", "city": "Town", "state": "FL", "zip": "33000"}
        result = resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=csv, ui_geocode=True))
        ui.geocode_via_ui.assert_called_once()
        assert result.source == "internal"  # Graceful fallback to the internal suggestion.
        assert "Unit 200" in result.canonical_address  # Internal suite preserved.


class TestConsensusQuery:
    """The geocoding query is built by house-number consensus, not blind SNMP-first."""

    def test_out_of_state_snmp_does_not_hijack(self):
        """When SNMP points to another state, Mist+CSV consensus wins the query."""
        res = AddressResolver()
        mist = {"address": "3101 PGA Boulevard", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        csv = {"address": "3101 PGA Boulevard Space P239", "city": "Palm Beach Gardens", "state": "FL", "zip": "33410"}
        cand = ResolveCandidates(
            mist_address=mist, csv_address=csv, snmp_location="1520 Route 38 Bldg 4 Hainesport NJ 08060"
        )
        query = res._build_query(cand)
        assert "3101 PGA Boulevard Space P239" in query  # FL consensus address.
        assert "1520" not in query and "NJ" not in query  # The NJ SNMP outlier is rejected.

    def test_csv_outlier_uses_mist_snmp_consensus(self):
        """When the CSV house number is the lone outlier, Mist+SNMP consensus wins."""
        res = AddressResolver()
        mist = {"address": "1701 Ohio Ave N", "city": "Live Oak", "state": "FL", "zip": "32064"}
        csv = {"address": "6670 US Highway 129, Suite 1", "city": "Live Oak", "state": "FL", "zip": "32060"}
        cand = ResolveCandidates(mist_address=mist, csv_address=csv, snmp_location="1701 Ohio Ave N Live Oak FL 32064")
        query = res._build_query(cand)
        assert "1701 Ohio Ave N" in query  # Mist+SNMP agree on 1701.
        assert "6670" not in query  # The CSV outlier is rejected.

    def test_business_name_prefixes_query(self):
        """A configured business name is prepended to the consensus address."""
        res = AddressResolver()
        addr = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
        query = res._build_query(ResolveCandidates(mist_address=addr, csv_address=addr, business_name="T-Mobile"))
        assert query.startswith("T-Mobile 100 Main St")

    def test_normalize_glue_splits_directional(self):
        """Directional/US glue from SNMP is repaired before voting."""
        assert AddressResolver._normalize_glue("2315 SFederal Hwy") == "2315 S Federal Hwy"
        assert AddressResolver._normalize_glue("931 USHighway 331") == "931 US Highway 331"
        assert AddressResolver._normalize_glue("5550 NMilitary Trl") == "5550 N Military Trl"

    def test_leading_house_number_ignores_zip(self):
        """A street with no leading number yields '' (the trailing ZIP is not a house number)."""
        assert AddressResolver._leading_house_number("S Federal Hwy Fort Pierce FL 34982") == ""
        assert AddressResolver._leading_house_number("2315 S Federal Hwy") == "2315"

    def test_consensus_prefers_suite_bearing_source(self):
        """Within the winning house-number group, a suite-bearing source is preferred."""
        res = AddressResolver()
        mist = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
        csv = {"address": "100 Main St Suite 7", "city": "Town", "state": "FL", "zip": "33000"}
        assert "Suite 7" in res._consensus_address(ResolveCandidates(mist_address=mist, csv_address=csv))

    def test_consensus_prefers_authority_when_house_number_ties(self):
        """Authority hint outranks CSV when both agree on house number and carry suites."""
        res = AddressResolver()
        mist = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
        csv = {"address": "100 Main St Suite 7", "city": "Town", "state": "FL", "zip": "33000"}
        authority = {"address": "100 Main St #204", "city": "Town", "state": "FL", "zip": "33000"}
        query = res._consensus_address(
            ResolveCandidates(mist_address=mist, csv_address=csv, authoritative_address=authority)
        )
        assert "#204" in query


class TestUiBusinessFallback:
    """Tier 3 retries without the business prefix when the prefixed query finds nothing."""

    def test_retry_plain_when_business_query_empty(self, tmp_path, monkeypatch):
        """An empty business-prefixed result triggers one plain-address retry."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False  # Tier 2 yields nothing so Tier 3 is consulted.
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        empty = ResolverResult(query="q", canonical_address=None, source="mist_ui")  # No fresh suggestion.
        found = ResolverResult(query="q", canonical_address="2315 S Federal Hwy, Fort Pierce, FL", source="mist_ui")
        ui.geocode_via_ui.side_effect = [empty, found]  # First (business) empty, then (plain) hit.
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        mist = {"address": "S Federal Hwy", "city": "Fort Pierce", "state": "FL", "zip": "34982"}
        csv = {"address": "2315 S Federal Hwy", "city": "Fort Pierce", "state": "FL", "zip": "34982"}
        result = resolver.resolve(
            ResolveCandidates(mist_address=mist, csv_address=csv, business_name="T-Mobile", ui_geocode=True)
        )
        assert ui.geocode_via_ui.call_count == 2  # Business query, then plain retry.
        assert "T-Mobile" not in ui.geocode_via_ui.call_args_list[1].args[0]  # Retry had no business prefix.
        assert result.canonical_address == "2315 S Federal Hwy, Fort Pierce, FL"

    def test_no_retry_without_business_name(self, tmp_path, monkeypatch):
        """Without a business name there is nothing to strip, so no second lookup."""
        _FakeValidator.count = 0
        _FakeValidator.valid = False
        monkeypatch.setattr(resolver_mod, "NominatimValidator", _FakeValidator)
        monkeypatch.setattr(resolver_mod.time, "sleep", lambda *_: None)
        ui = MagicMock()
        ui.geocode_via_ui.return_value = ResolverResult(query="q", canonical_address=None, source="mist_ui")
        resolver = AddressResolver(db_path=_db(tmp_path), ui_geocoder=ui)
        resolver.resolve(ResolveCandidates(mist_address=_NO_SUITE, csv_address=_NO_SUITE, ui_geocode=True))
        assert ui.geocode_via_ui.call_count == 1  # No business prefix -> no fallback.


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


class TestHasConflictingHints:
    """has_conflicting_hints flags only genuine no-majority house-number disagreement."""

    def test_all_three_differ_is_conflict(self):
        """Three distinct house numbers with no majority -> conflict (three different stores)."""
        cand = ResolveCandidates(
            mist_address={"address": "1523 E San Marnan Dr", "city": "Waterloo", "state": "IA", "zip": "50702"},
            csv_address={"address": "2825 Crossroads Blvd", "city": "Waterloo", "state": "IA", "zip": "50702"},
            snmp_location="100 Mall Dr Waterloo IA 50702",
        )
        assert AddressResolver().has_conflicting_hints(cand) is True

    def test_two_agree_one_differs_is_not_conflict(self):
        """A 2-vs-1 split has a clear majority -> not a conflict (the outlier is trusted away)."""
        cand = ResolveCandidates(
            mist_address={"address": "100 Main St", "city": "T", "state": "FL", "zip": "1"},
            csv_address={"address": "100 Main St", "city": "T", "state": "FL", "zip": "1"},
            snmp_location="456 Oak Ave Ste 200 T FL 1",
        )
        assert AddressResolver().has_conflicting_hints(cand) is False

    def test_all_same_number_is_not_conflict(self):
        """All hints on the same house number -> consensus, never a conflict."""
        cand = ResolveCandidates(
            mist_address={"address": "100 Main St", "city": "T", "state": "FL", "zip": "1"},
            csv_address={"address": "100 Main St Suite 5", "city": "T", "state": "FL", "zip": "1"},
            snmp_location="100 Main St T FL 1",
        )
        assert AddressResolver().has_conflicting_hints(cand) is False

    def test_suite_on_dissenter_does_not_rescue(self):
        """A suite-bearing dissenter on a different number is still a conflict (suite is irrelevant off-street)."""
        cand = ResolveCandidates(
            mist_address={"address": "100 Main St", "city": "T", "state": "FL", "zip": "1"},
            csv_address={"address": "200 Oak Ave", "city": "T", "state": "FL", "zip": "1"},
            snmp_location="300 Pine Rd Ste 9 T FL 1",
        )
        assert AddressResolver().has_conflicting_hints(cand) is True

    def test_mist_missing_number_others_agree_is_not_conflict(self):
        """Mist lacks a house number but CSV+SNMP agree -> majority, not a conflict."""
        cand = ResolveCandidates(
            mist_address={"address": "S Federal Hwy", "city": "Ft Pierce", "state": "FL", "zip": "34982"},
            csv_address={"address": "2315 S Federal Hwy", "city": "Ft Pierce", "state": "FL", "zip": "34982"},
            snmp_location="2315 S Federal Hwy Ft Pierce FL 34982",
        )
        assert AddressResolver().has_conflicting_hints(cand) is False

    def test_mist_missing_number_others_differ_is_conflict(self):
        """Mist lacks a number and CSV/SNMP disagree -> no tiebreaker -> conflict."""
        cand = ResolveCandidates(
            mist_address={"address": "S Federal Hwy", "city": "Ft Pierce", "state": "FL", "zip": "34982"},
            csv_address={"address": "2315 S Federal Hwy", "city": "Ft Pierce", "state": "FL", "zip": "34982"},
            snmp_location="2400 S Federal Hwy Ft Pierce FL 34982",
        )
        assert AddressResolver().has_conflicting_hints(cand) is True
