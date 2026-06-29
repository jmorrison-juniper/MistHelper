"""Unit tests for AddressAuditEngine classification + assembly (1003-site-address-audit)."""

from src.site.address_audit.audit_engine import AddressAuditEngine
from src.site.address_audit.models import AddressRow, MatchedSite, ResolverResult

_MIST_NO_SUITE = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}
_MIST_WITH_SUITE = {"address": "100 Main St Suite 5", "city": "Town", "state": "FL", "zip": "33000"}
_CSV = {"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"}


def _rr(canonical, ambiguous=False, source="nominatim"):
    """Build a ResolverResult for classification tests."""
    return ResolverResult(query="q", canonical_address=canonical, source=source, ambiguous=ambiguous)


class TestClassify:
    """AddressAuditEngine._classify covers all eight states."""

    def setup_method(self):
        """Fresh engine per test."""
        self.engine = AddressAuditEngine()

    def test_no_result(self):
        """No canonical address -> NO_RESULT."""
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, _rr(None)) == "NO_RESULT"

    def test_no_result_when_rr_none(self):
        """A None resolver result -> NO_RESULT."""
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, None) == "NO_RESULT"

    def test_internal_fallback_missing_suite(self):
        """No external result but SNMP adds a suite Mist lacks -> MISSING_SUITE."""
        snmp = "08095 - 100 Main St Suite 9"
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, snmp, _rr(None)) == "MISSING_SUITE"

    def test_ambiguous(self):
        """An ambiguous result -> AMBIGUOUS."""
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, _rr("X", ambiguous=True)) == "AMBIGUOUS"

    def test_address_match(self):
        """Identical base + suite -> ADDRESS_MATCH."""
        rr = _rr("100 Main St Town FL 33000")
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, rr) == "ADDRESS_MATCH"

    def test_wrong_street(self):
        """Different base street -> WRONG_STREET."""
        rr = _rr("200 Oak Ave Town FL 33000")
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, rr) == "WRONG_STREET"

    def test_missing_suite(self):
        """Candidate adds a suite Mist lacks -> MISSING_SUITE."""
        rr = _rr("100 Main St Suite 5 Town FL 33000")
        assert self.engine._classify(_MIST_NO_SUITE, _CSV, None, rr) == "MISSING_SUITE"

    def test_mist_better(self):
        """Mist carries a suite the candidate lacks -> MIST_BETTER."""
        rr = _rr("100 Main St Town FL 33000")
        assert self.engine._classify(_MIST_WITH_SUITE, _CSV, None, rr) == "MIST_BETTER"

    def test_csv_better(self):
        """Both specify suites that differ -> CSV_BETTER."""
        rr = _rr("100 Main St Suite 7 Town FL 33000")
        assert self.engine._classify(_MIST_WITH_SUITE, _CSV, None, rr) == "CSV_BETTER"


class TestBuildAuditResult:
    """Unmatched rows short-circuit to UNMATCHED without resolution."""

    def test_unmatched_row(self):
        """An unmatched site yields UNMATCHED and never calls the resolver."""
        engine = AddressAuditEngine()
        row = AddressRow(serial="9999999999", model="SSR130", address="1 A St", city="T", state="FL", zip_code="1")
        site = MatchedSite(match_strategy="unmatched")

        class _Boom:
            def resolve(self, *_):
                raise AssertionError("resolver must not be called for unmatched rows")

        result = engine._build_audit_result(row, site, _Boom(), "", False)
        assert result.issue_type == "UNMATCHED"
        assert result.source == "-"


class TestResolveAndClassify:
    """Row-accountability invariant."""

    def test_zero_rows_yields_empty(self):
        """An empty input produces an empty result list (no exception)."""
        engine = AddressAuditEngine()
        assert engine._resolve_and_classify([], [], None, "", False) == []


class TestEnvConfig:
    """Environment-driven configuration helpers."""

    def test_env_float_default_when_unset(self, monkeypatch):
        """An unset env var returns the supplied default."""
        monkeypatch.delenv("UI_GEOCODE_MAX_LOOKUPS", raising=False)
        assert AddressAuditEngine._env_float("UI_GEOCODE_MAX_LOOKUPS", 50.0) == 50.0

    def test_env_float_parses_value(self, monkeypatch):
        """A valid env value is parsed as a float."""
        monkeypatch.setenv("FUZZY_MATCH_THRESHOLD", "92")
        assert AddressAuditEngine._fuzzy_threshold() == 92.0

    def test_env_float_invalid_falls_back(self, monkeypatch):
        """A malformed env value falls back to the default without raising."""
        monkeypatch.setenv("FUZZY_MATCH_THRESHOLD", "not-a-number")
        assert AddressAuditEngine._fuzzy_threshold() == 85.0

    def test_ui_config_reads_env(self, monkeypatch):
        """UI config merges dashboard URL and bounds from the environment."""
        monkeypatch.setenv("MIST_DASHBOARD_URL", "https://manage.eu.mist.com/")
        monkeypatch.setenv("UI_GEOCODE_TIMEOUT_SECONDS", "30")
        monkeypatch.setenv("UI_GEOCODE_MAX_LOOKUPS", "10")
        config = AddressAuditEngine._ui_config()
        assert config.dashboard_url == "https://manage.eu.mist.com/"
        assert config.per_lookup_timeout_s == 30.0
        assert config.max_lookups == 10
