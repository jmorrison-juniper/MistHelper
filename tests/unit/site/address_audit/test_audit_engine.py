"""Unit tests for AddressAuditEngine classification + assembly (1003-site-address-audit)."""

from unittest.mock import MagicMock

from src.site.address_audit import audit_engine as eng_mod
from src.site.address_audit.audit_engine import AddressAuditEngine
from src.site.address_audit.business_authority_ingester import BusinessAuthorityRow
from src.site.address_audit.models import AddressRow, AuditResult, MatchedSite, ResolverResult

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

    def test_directional_conflict_is_wrong_street(self):
        """Mist 'E Jefferson' vs web 'West Jefferson' is a different street, not a match."""
        mist = {"address": "1606 E Jefferson St", "city": "Quincy", "state": "FL", "zip": "32351"}
        rr = _rr("1606 West Jefferson Street, Quincy, FL 32351")
        assert self.engine._classify(mist, _CSV, None, rr) == "WRONG_STREET"

    def test_missing_house_number_not_match(self):
        """Mist street with no house number + a numbered suggestion -> MISSING_NUMBER, not ADDRESS_MATCH."""
        mist = {"address": "S Federal Hwy, Fort Pierce, FL 34982, USA", "city": "", "state": "", "zip": ""}
        rr = _rr("2315 S Federal Hwy Fort Pierce, FL 34982")
        assert self.engine._classify(mist, _CSV, None, rr) == "MISSING_NUMBER"

    def test_missing_house_number_helper(self):
        """The helper inspects the leading street segment, ignoring a trailing ZIP."""
        # Full Mist string: street has no leading number even though the ZIP has digits.
        assert (
            self.engine._missing_house_number("S Federal Hwy, Fort Pierce, FL 34982, USA", "2315 S Federal Hwy") is True
        )
        assert (
            self.engine._missing_house_number("1606 E Jefferson St, Quincy, FL 32351", "1606 W Jefferson St") is False
        )
        assert self.engine._missing_house_number("S Federal Hwy, Fort Pierce, FL 34982", "S Federal Hwy") is False

    def test_abbreviated_directional_still_matches(self):
        """Mist 'NW 107th Ave' vs web 'Northwest 107th Avenue' is the same street."""
        mist = {"address": "1455 NW 107th Ave", "city": "Miami", "state": "FL", "zip": "33172"}
        rr = _rr("1455 Northwest 107th Avenue #410, Miami, FL 33172")
        assert self.engine._classify(mist, _CSV, None, rr) == "MISSING_SUITE"

    def test_city_directional_does_not_cause_false_mismatch(self):
        """A directional inside the city (West Palm Beach) does not break the street match."""
        mist = {"address": "940 S Military Trail", "city": "West Palm Beach", "state": "FL", "zip": "33415"}
        rr = _rr("940 South Military Trail #3, West Palm Beach, FL 33415")
        assert self.engine._classify(mist, _CSV, None, rr) == "MISSING_SUITE"


class TestSameStreet:
    """Street-equality helper: directionals, ordinals, and abbreviations."""

    def setup_method(self):
        """Fresh engine per test."""
        self.engine = AddressAuditEngine()

    def test_opposite_directionals_differ(self):
        """East vs West on the same street name are different streets."""
        assert self.engine._same_street("1606 E Jefferson St", "1606 West Jefferson Street, Quincy, FL") is False

    def test_abbrev_vs_spelled_directional_same(self):
        """NW and Northwest are the same directional."""
        assert self.engine._same_street("1455 NW 107th Ave", "1455 Northwest 107th Avenue #410, Miami, FL") is True

    def test_directional_S_vs_South_same(self):
        """S and South are the same directional (no false mismatch)."""
        assert self.engine._same_street("1671 US 41 Bypass S", "1671 U.S. 41 Bypass South Unit 100, Venice, FL") is True

    def test_same_house_number_different_street_differs(self):
        """The same house number on a different street is not a match."""
        assert self.engine._same_street("100 Main St", "100 Oak Ave, Town, FL") is False

    def test_leading_directional_ignores_city(self):
        """Only the directional after the house number counts, not one inside the city."""
        assert self.engine._leading_directional("940 South Military Trail #3, West Palm Beach, FL") == "S"


class TestWriteBackWiring:
    """The optional write-back flow is correctly gated and wired into _finish."""

    def _engine_with_mocks(self):
        """Build an engine whose renderer/reporter/corrector are mocks."""
        engine = AddressAuditEngine(renderer=MagicMock(), reporter=MagicMock())
        corrector = MagicMock()
        engine._make_corrector = staticmethod(lambda _api: corrector)  # Inject the mock corrector.
        return engine, corrector

    def test_quit_skips_save_and_writeback(self):
        """Choosing quit saves nothing and never offers write-back."""
        engine, corrector = self._engine_with_mocks()
        engine._renderer.prompt_post_table.return_value = "quit"
        engine._finish([], MagicMock())
        engine._reporter.save.assert_not_called()
        corrector.correctable.assert_not_called()

    def test_save_then_offers_writeback(self):
        """Choosing save writes the report and then offers write-back."""
        engine, corrector = self._engine_with_mocks()
        engine._renderer.prompt_post_table.return_value = "save"
        engine._reporter.save.return_value = "data/x.csv"
        corrector.correctable.return_value = []  # No targets -> offer ends quietly.
        engine._finish([], MagicMock())
        engine._reporter.save.assert_called_once()
        corrector.correctable.assert_called_once()

    def test_gate_no_skips_review(self, monkeypatch):
        """Declining the batch gate means review_and_apply is never called."""
        engine, corrector = self._engine_with_mocks()
        corrector.correctable.return_value = [object()]  # One target exists.
        monkeypatch.setattr(eng_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "n"))
        engine._offer_write_back([], MagicMock())
        corrector.review_and_apply.assert_not_called()

    def test_gate_yes_runs_review_and_report(self, monkeypatch):
        """Accepting the batch gate runs review_and_apply and then offers the report."""
        engine, corrector = self._engine_with_mocks()
        corrector.correctable.return_value = [object()]
        corrector.review_and_apply.return_value = [object()]
        answers = iter(["y", "y"])  # Gate yes, then save-report yes.
        monkeypatch.setattr(eng_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: next(answers)))
        engine._offer_write_back([], MagicMock())
        corrector.review_and_apply.assert_called_once()
        engine._reporter.save_corrections.assert_called_once()


class TestConsoleLogSuppression:
    """Address-audit logs are routed off the console (kept in the file) during a run."""

    def _filter(self):
        """Return a fresh console filter."""
        return eng_mod._AddressAuditConsoleFilter()

    def _record(self, pathname):
        """Build a log record as if emitted from ``pathname``."""
        import logging

        return logging.LogRecord("root", logging.WARNING, pathname, 1, "msg", None, None)

    def test_filter_drops_address_audit_records(self):
        """A record emitted from the address_audit package is dropped from console."""
        rec = self._record("/x/src/site/address_audit/address_resolver.py")
        assert self._filter().filter(rec) is False

    def test_filter_keeps_other_records(self):
        """A record from elsewhere is kept on console."""
        rec = self._record("/x/src/utils/address_utils.py")
        assert self._filter().filter(rec) is True

    def test_filter_is_separator_portable(self):
        """Windows-style backslash paths are matched too."""
        rec = self._record("C:\\x\\src\\site\\address_audit\\ui_geocoder.py")
        assert self._filter().filter(rec) is False

    def test_context_attaches_console_only_and_removes(self):
        """The context manager filters console handlers (not file) and detaches afterwards."""
        import io
        import logging

        root = logging.getLogger()
        saved = list(root.handlers)
        for handler in saved:
            root.removeHandler(handler)
        console = logging.StreamHandler(io.StringIO())

        class _FakeFile(logging.FileHandler):
            def __init__(self, stream):
                logging.Handler.__init__(self)
                self.stream = stream
                self.baseFilename = "x"

            def _open(self):
                return self.stream

        file_handler = _FakeFile(io.StringIO())
        root.addHandler(console)
        root.addHandler(file_handler)
        try:
            with AddressAuditEngine()._console_logs_to_file_only():
                assert len(console.filters) == 1  # Console handler filtered.
                assert len(file_handler.filters) == 0  # File handler untouched.
            assert len(console.filters) == 0  # Filter removed after the run.
        finally:
            root.removeHandler(console)
            root.removeHandler(file_handler)
            for handler in saved:
                root.addHandler(handler)


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

        ctx = eng_mod._AuditContext(  # WHY: Bundle collapses six-param helper into ctx form.
            business="",  # WHY: No business prefix influences suite fallbacks.
            ui_geocode=False,  # WHY: Tier-3 disabled so resolver is never invoked.
            authoritative_index={"by_name": {}, "by_full": {}, "by_no_suite": {}},  # WHY: Empty index -> no authority.
        )
        result = engine._build_audit_result(row, site, _Boom(), ctx)  # WHY: Unmatched short-circuit skips resolver.
        assert result.issue_type == "UNMATCHED"
        assert result.source == "-"


class TestBusinessAuthorityPrompt:
    """Second CSV prompt for optional business-authoritative data."""

    def test_prompt_business_csv_skip(self, monkeypatch):
        """Entering 'q' skips authoritative CSV selection cleanly."""
        engine = AddressAuditEngine()  # Real engine; prompt path is pure input logic.
        monkeypatch.setattr(
            eng_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "q")
        )  # Simulate operator skip.
        picked = engine._prompt_business_csv_choice(["data\\Book1.csv", "data\\T-Builder.csv"], "data\\Book1.csv")
        assert picked is None  # Skip returns None so pipeline remains backward-compatible.

    def test_prompt_business_csv_selects_index(self, monkeypatch):
        """A valid index returns the selected business CSV path."""
        engine = AddressAuditEngine()  # Real engine; prompt path is pure input logic.
        monkeypatch.setattr(
            eng_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "2")
        )  # Simulate index selection.
        picked = engine._prompt_business_csv_choice(["data\\Book1.csv", "data\\T-Builder.csv"], "data\\Book1.csv")
        assert picked == "data\\T-Builder.csv"  # Selected index maps to the expected candidate path.


class TestBusinessAuthorityIntegration:
    """Business-authoritative rows are fed into ResolveCandidates when uniquely matched."""

    def test_build_audit_result_passes_authoritative_address(self):
        """A unique authoritative match is forwarded to the resolver candidates payload."""
        engine = AddressAuditEngine()  # Real engine with injectable resolver stub below.
        row = AddressRow(  # Primary row from the customer CSV.
            serial="1234567890",
            model="SSR130",
            address="100 Main St Suite 9",
            city="Town",
            state="FL",
            zip_code="33000",
        )
        site = MatchedSite(  # Matched site required for resolution path.
            site_id="site-1",
            site_name="Store A",
            mist_address={"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"},
            match_strategy="serial",
        )

        class _ResolverStub:
            """Capture resolver candidates so test can assert authoritative wiring."""

            captured = None  # Last resolve() candidates argument.

            def has_conflicting_hints(self, *_):
                return False  # Keep flow on the normal resolve path.

            def resolve(self, candidates):
                _ResolverStub.captured = candidates  # Capture payload for assertion.
                return ResolverResult(
                    query="q", canonical_address="100 Main St Suite 9, Town, FL 33000", source="internal"
                )

        authoritative_index = {  # Minimal index with one unique address match.
            "by_name": {},
            "by_full": {
                "100 main st suite 9 town fl 33000": [
                    BusinessAuthorityRow(  # Simulate one parsed authoritative row.
                        site_name="Store A",
                        address="100 Main St Suite 9",
                        city="Town",
                        state="FL",
                        zip_code="33000",
                    )
                ]
            },
            "by_no_suite": {},
        }
        ctx = eng_mod._AuditContext(  # WHY: Bundle context for the refactored builder API.
            business="",  # WHY: No business prefix in this path.
            ui_geocode=False,  # WHY: Tier-3 web geocoding stays off in the unit.
            authoritative_index=authoritative_index,  # WHY: Feed the constructed authority index.
        )
        result = engine._build_audit_result(row, site, _ResolverStub(), ctx)  # WHY: Build one row via stub.
        assert result.issue_type in {
            "ADDRESS_MATCH",
            "MISSING_SUITE",
            "CSV_BETTER",
            "MIST_BETTER",
            "NO_RESULT",
            "WRONG_STREET",
        }  # Flow completed.
        assert _ResolverStub.captured is not None  # Resolver was invoked.
        assert (
            _ResolverStub.captured.authoritative_address.get("address") == "100 Main St Suite 9"
        )  # Authority address wired in.


class TestResolveAndClassify:
    """Row-accountability invariant."""

    def test_zero_rows_yields_empty(self):
        """An empty input produces an empty result list (no exception)."""
        engine = AddressAuditEngine()
        ctx = eng_mod._AuditContext(  # WHY: Bundle context for the refactored resolver helper.
            business="",  # WHY: Empty business string keeps prefix logic inert.
            ui_geocode=False,  # WHY: Tier-3 disabled so no external geocode occurs.
            authoritative_index={"by_name": {}, "by_full": {}, "by_no_suite": {}},  # WHY: Empty index for zero-row.
        )
        assert engine._resolve_and_classify([], [], None, ctx) == []  # WHY: Empty input must produce empty output.


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

    def test_skip_ssl_verify_defaults_false(self, monkeypatch):
        """Certificate verification stays on by default. See issue #1914."""
        monkeypatch.delenv("MIST_SKIP_SSL_VERIFY", raising=False)
        assert AddressAuditEngine._skip_ssl_verify() is False

    def test_skip_ssl_verify_env_opt_out(self, monkeypatch):
        """Setting MIST_SKIP_SSL_VERIFY=true turns the check off, and only then."""
        monkeypatch.setenv("MIST_SKIP_SSL_VERIFY", "true")
        assert AddressAuditEngine._skip_ssl_verify() is True

    def test_skip_ssl_verify_unknown_value_stays_secure(self, monkeypatch):
        """An unrecognized value keeps the check on, so a typo fails secure."""
        monkeypatch.setenv("MIST_SKIP_SSL_VERIFY", "flase")
        assert AddressAuditEngine._skip_ssl_verify() is False

    def test_ui_geocode_enabled_defaults_true(self, monkeypatch):
        """Tier-3 web geocoding is permitted by default (no CLI flag required)."""
        monkeypatch.delenv("ADDRESS_AUDIT_GEOCODE", raising=False)
        assert AddressAuditEngine._ui_geocode_enabled() is True

    def test_ui_geocode_enabled_env_off(self, monkeypatch):
        """Setting ADDRESS_AUDIT_GEOCODE=off disables the Tier-3 attempt."""
        monkeypatch.setenv("ADDRESS_AUDIT_GEOCODE", "off")
        assert AddressAuditEngine._ui_geocode_enabled() is False

    def test_ui_geocode_enabled_env_auto(self, monkeypatch):
        """An explicit 'auto' value keeps Tier-3 enabled."""
        monkeypatch.setenv("ADDRESS_AUDIT_GEOCODE", "auto")
        assert AddressAuditEngine._ui_geocode_enabled() is True

    def test_geocode_mode_default_auto(self, monkeypatch):
        """Unset ADDRESS_AUDIT_GEOCODE defaults to auto (take over else spawn)."""
        monkeypatch.delenv("ADDRESS_AUDIT_GEOCODE", raising=False)
        assert AddressAuditEngine._geocode_mode() == "auto"

    def test_geocode_mode_off(self, monkeypatch):
        """'off' disables Tier 3 entirely."""
        monkeypatch.setenv("ADDRESS_AUDIT_GEOCODE", "off")
        assert AddressAuditEngine._geocode_mode() == "off"
        assert AddressAuditEngine._ui_geocode_enabled() is False

    def test_geocode_mode_launch(self, monkeypatch):
        """'launch' selects the Playwright-launch strategy."""
        monkeypatch.setenv("ADDRESS_AUDIT_GEOCODE", "launch")
        assert AddressAuditEngine._geocode_mode() == "launch"

    def test_geocode_mode_unknown_falls_back_auto(self, monkeypatch):
        """An unrecognized value falls back to auto so a typo never disables Tier 3."""
        monkeypatch.setenv("ADDRESS_AUDIT_GEOCODE", "banana")
        assert AddressAuditEngine._geocode_mode() == "auto"


class TestSourceLabel:
    """Source-column labelling, including OSM street-validation."""

    def test_internal_with_osm_confirmation(self):
        """An internal suite whose street OSM confirmed is labelled Internal+OSM."""
        rr = ResolverResult(query="q", canonical_address="X Suite 5", source="internal", street_validated=True)
        assert AddressAuditEngine._source_label(rr) == "Internal+OSM"

    def test_internal_without_osm(self):
        """An internal suite OSM could not confirm is labelled plain Internal."""
        rr = ResolverResult(query="q", canonical_address="X Suite 5", source="internal", street_validated=False)
        assert AddressAuditEngine._source_label(rr) == "Internal"

    def test_nominatim_label(self):
        """A Nominatim-sourced result is labelled Nominatim."""
        rr = ResolverResult(query="q", canonical_address="X", source="nominatim")
        assert AddressAuditEngine._source_label(rr) == "Nominatim"

    def test_mist_ui_label_names_google(self):
        """A Tier-3 result is labelled to make the Google authority explicit."""
        rr = ResolverResult(query="q", canonical_address="X #5", source="mist_ui")  # Tier-3 (Google-via-Mist).
        assert AddressAuditEngine._source_label(rr) == "Google (Mist UI)"  # Label must name Google, not just "Mist UI".

    def test_no_result_label(self):
        """A result with no canonical address is labelled '-'."""
        rr = ResolverResult(query="q", canonical_address=None, source="internal")
        assert AddressAuditEngine._source_label(rr) == "-"


class TestConflictingHints:
    """A no-majority hint disagreement short-circuits to CONFLICTING_HINTS without resolving."""

    def test_conflicting_hints_short_circuits(self):
        """When the resolver reports conflicting hints, the row is review-only and resolve() never runs."""
        engine = AddressAuditEngine()  # Real engine; resolver is a guard stub below.
        row = AddressRow(
            serial="111", model="SSR130", address="2825 Crossroads Blvd", city="Waterloo", state="IA", zip_code="50702"
        )  # CSV hint.
        site = MatchedSite(
            site_id="s1",
            site_name="IAS0252F",
            mist_address={"address": "1523 E San Marnan Dr", "city": "Waterloo", "state": "IA", "zip": "50702"},
            snmp_location="100 Mall Dr Waterloo IA 50702",
            match_strategy="serial",
        )  # Three divergent hints.

        class _Guard:
            def has_conflicting_hints(self, _candidates):
                return True  # Force the conflict path.

            def resolve(self, *_):
                raise AssertionError("resolver must not run on a conflict row")  # Must be skipped.

        ctx = eng_mod._AuditContext(  # WHY: Wrap params for the refactored builder API.
            business="",  # WHY: No business prefix in this path.
            ui_geocode=False,  # WHY: Tier-3 disabled for this test.
            authoritative_index={"by_name": {}, "by_full": {}, "by_no_suite": {}},  # WHY: No authority index required.
        )
        result = engine._build_audit_result(row, site, _Guard(), ctx)  # WHY: Drive the conflicting-hints short-circuit.
        assert result.issue_type == "CONFLICTING_HINTS"  # Flagged review-only.
        assert result.suggested_address == ""  # No recommendation offered.
        assert result.source == "-"  # No single trustworthy source.


class TestFlagDuplicateAddresses:
    """Cross-row collision: one address shared by 2+ distinct sites -> DUPLICATE_ADDRESS."""

    @staticmethod
    def _result(site_id, name, suggested="", mist_addr=None, issue="ADDRESS_MATCH", source="Google (Mist UI)"):
        """Build a minimal AuditResult for the collision pass."""
        row = AddressRow(serial=site_id, model="M", address="x", city="c", state="s", zip_code="z")  # Stub row.
        site = MatchedSite(site_id=site_id, site_name=name, mist_address=mist_addr or {}, match_strategy="serial")
        return AuditResult(
            address_row=row, matched_site=site, issue_type=issue, suggested_address=suggested, source=source
        )

    def test_two_sites_same_suggested_are_flagged(self):
        """Two different sites with the identical suggested address -> both DUPLICATE_ADDRESS."""
        a = self._result("s1", "A", suggested="100 Main St, Town, FL 33000")  # Site A.
        b = self._result("s2", "B", suggested="100 Main St, Town, FL 33000")  # Site B, same address.
        AddressAuditEngine._flag_duplicate_addresses([a, b])  # Run the post-pass.
        assert a.issue_type == "DUPLICATE_ADDRESS" and b.issue_type == "DUPLICATE_ADDRESS"  # Both flagged.
        assert a.suggested_address == "" and a.source == "-"  # No push, no credited source.

    def test_strip_mall_different_suites_untouched(self):
        """Same street but different suites are distinct full addresses -> not a collision."""
        a = self._result("s1", "A", suggested="100 Main St Ste 100, Town, FL 33000")  # Unit 100.
        b = self._result("s2", "B", suggested="100 Main St Ste 200, Town, FL 33000")  # Unit 200.
        AddressAuditEngine._flag_duplicate_addresses([a, b])  # Run the post-pass.
        assert a.issue_type == "ADDRESS_MATCH" and b.issue_type == "ADDRESS_MATCH"  # Strip-mall case preserved.

    def test_single_site_not_flagged(self):
        """A lone site is never a collision."""
        a = self._result("s1", "A", suggested="100 Main St, Town, FL 33000")  # Only one site.
        AddressAuditEngine._flag_duplicate_addresses([a])  # Run the post-pass.
        assert a.issue_type == "ADDRESS_MATCH"  # Untouched.

    def test_same_site_twice_not_flagged(self):
        """Two rows for the SAME site (same id) are not a cross-site collision."""
        a = self._result("s1", "A", suggested="100 Main St, Town, FL 33000")  # Same site_id ...
        b = self._result("s1", "A", suggested="100 Main St, Town, FL 33000")  # ... appearing twice.
        AddressAuditEngine._flag_duplicate_addresses([a, b])  # Run the post-pass.
        assert a.issue_type == "ADDRESS_MATCH" and b.issue_type == "ADDRESS_MATCH"  # Not flagged.

    def test_conflicting_hints_row_is_preserved(self):
        """A CONFLICTING_HINTS row keeps its (more specific) reason and is skipped by the pass."""
        a = self._result(
            "s1",
            "A",
            suggested="",
            mist_addr={"address": "100 Main St, Town, FL 33000"},
            issue="CONFLICTING_HINTS",
            source="-",
        )  # Already review-only.
        b = self._result("s2", "B", suggested="100 Main St, Town, FL 33000")  # Different site, same address.
        AddressAuditEngine._flag_duplicate_addresses([a, b])  # Run the post-pass.
        assert a.issue_type == "CONFLICTING_HINTS"  # Preserved (skipped).
        assert b.issue_type == "ADDRESS_MATCH"  # Alone in its bucket -> not flagged.

    def test_collision_detected_via_mist_fallback_and_country_strip(self):
        """Suite-less ADDRESS_MATCH rows collide via the Mist address even when one carries a ', USA' suffix."""
        a = self._result(
            "s1", "A", suggested="", mist_addr={"address": "100 Main St, Town, FL 33000, USA"}, issue="ADDRESS_MATCH"
        )  # Country suffix.
        b = self._result(
            "s2", "B", suggested="", mist_addr={"address": "100 Main St, Town, FL 33000"}, issue="ADDRESS_MATCH"
        )  # No suffix.
        AddressAuditEngine._flag_duplicate_addresses([a, b])  # Run the post-pass.
        assert a.issue_type == "DUPLICATE_ADDRESS" and b.issue_type == "DUPLICATE_ADDRESS"  # Normalized to one key.
