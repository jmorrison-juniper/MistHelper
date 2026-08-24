"""Unit tests for MistUIGeocoder (Tier-3 browser geocoder).

All tests are fully mocked -- no real browser is launched -- so they run
offline in milliseconds and stay deterministic in CI. They cover:
  * graceful degradation when Playwright is absent,
  * the fail-soft guards (lookup before connect, max-lookups cap),
  * the CDP attach/launch connection logic (mocked Playwright),
  * the result-builder ranking/ambiguity logic,
  * the selector-candidate fallthrough and Edge-discovery helpers.
"""

from unittest.mock import MagicMock

import pytest

from src.site.address_audit import MistUIGeocoder, ResolverResult, UIGeocoderConfig
from src.site.address_audit import ui_geocoder as ui_mod


def _fake_playwright(browser):
    """Return a callable mimicking sync_playwright() whose start() yields a driver."""
    driver = MagicMock()
    driver.chromium.connect_over_cdp.return_value = browser
    driver.chromium.launch.return_value = browser
    factory = MagicMock()
    factory.return_value.start.return_value = driver
    return factory, driver


class TestCapabilityAndGuards:
    """is_available() and the fail-soft guards."""

    def test_is_available_false_without_playwright(self, monkeypatch):
        """When Playwright is not importable, the tier is unavailable."""
        monkeypatch.setattr(ui_mod, "sync_playwright", None)
        geo = MistUIGeocoder()
        assert geo.is_available() is False
        assert geo.connect() is False
        assert geo.geocode_via_ui("x") is None

    def test_is_available_true_with_playwright(self, monkeypatch):
        """When the sentinel is set, the tier reports available."""
        monkeypatch.setattr(ui_mod, "sync_playwright", MagicMock())
        assert MistUIGeocoder().is_available() is True

    def test_lookup_before_connect_returns_none(self):
        """geocode_via_ui must fail soft if connect() never succeeded."""
        assert MistUIGeocoder().geocode_via_ui("anything") is None

    def test_max_lookups_cap_blocks_further_lookups(self):
        """Reaching the per-run cap returns None without driving the browser."""
        geo = MistUIGeocoder(UIGeocoderConfig(max_lookups=0))
        geo._connected = True  # simulate a successful connect()
        geo._active_page = MagicMock(side_effect=AssertionError("must not be called"))
        assert geo.geocode_via_ui("x") is None


class TestConnect:
    """CDP attach and launch connection paths (mocked Playwright)."""

    def test_attach_success_sets_context(self, monkeypatch):
        """Attach reuses the first existing context of the debuggable browser."""
        browser = MagicMock()
        ctx = MagicMock()
        browser.contexts = [ctx]
        factory, driver = _fake_playwright(browser)
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)

        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="attach"))
        assert geo.connect() is True
        assert geo._context is ctx
        driver.chromium.connect_over_cdp.assert_called_once()

    def test_attach_no_context_returns_false(self, monkeypatch):
        """A debuggable browser with zero contexts cannot be driven."""
        browser = MagicMock()
        browser.contexts = []
        factory, _ = _fake_playwright(browser)
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)

        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="attach"))
        assert geo.connect() is False

    def test_launch_mode_waits_for_login(self, monkeypatch):
        """Launch mode opens a context and passes the interactive-login gate."""
        browser = MagicMock()
        browser.new_context.return_value = MagicMock()
        factory, driver = _fake_playwright(browser)
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)
        monkeypatch.setattr(ui_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: ""))

        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="launch"))
        assert geo.connect() is True
        driver.chromium.launch.assert_called_once()

    def test_connect_failure_is_swallowed(self, monkeypatch):
        """Any exception during connect() degrades to False, never raises."""
        factory = MagicMock()
        factory.return_value.start.side_effect = RuntimeError("boom")
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)
        assert MistUIGeocoder().connect() is False


class TestBuildResult:
    """Result-builder ranking and ambiguity logic."""

    def test_empty_is_no_result(self):
        """No suggestions => canonical_address None (NO_RESULT)."""
        result = MistUIGeocoder()._build_result("q", [])
        assert isinstance(result, ResolverResult)
        assert result.canonical_address is None
        assert result.source == "mist_ui"

    def test_single_suggestion_high_confidence(self):
        """A lone suggestion is unambiguous with high confidence."""
        result = MistUIGeocoder()._build_result("q", ["123 Main St Suite 4"])
        assert result.canonical_address == "123 Main St Suite 4"
        assert result.confidence == pytest.approx(0.9)
        assert result.raw_response["ambiguous"] is False

    def test_multiple_suggestions_ambiguous_top_ranked(self):
        """Multiple suggestions => ambiguous, top one wins, lower confidence."""
        result = MistUIGeocoder()._build_result("q", ["A Suite 1", "B Suite 2"])
        assert result.canonical_address == "A Suite 1"
        assert result.raw_response["ambiguous"] is True
        assert result.confidence == pytest.approx(0.6)


class TestTypingJitter:
    """Human-like, randomized typing cadence into the Google autocomplete box."""

    def test_types_each_char_with_randomized_delay(self, monkeypatch):
        """Each character is typed individually with a randomized sleep between keys."""
        sleeps: list[float] = []
        monkeypatch.setattr(ui_mod.time, "sleep", lambda s: sleeps.append(s))
        geo = MistUIGeocoder(UIGeocoderConfig(min_key_delay_s=0.05, max_key_delay_s=0.15))
        field = MagicMock()
        geo._type_humanlike(field, "940 Main")
        assert field.type.call_count == len("940 Main")  # One keystroke per character.
        assert len(sleeps) == len("940 Main")  # One delay per character.
        assert all(s >= 0.05 for s in sleeps)  # Never below the configured floor.
        assert len(set(round(s, 5) for s in sleeps)) > 1  # Delays vary (not a fixed cadence).

    def test_key_delay_within_bounds(self):
        """A normal keystroke delay stays within [min, max]."""
        geo = MistUIGeocoder(UIGeocoderConfig(min_key_delay_s=0.05, max_key_delay_s=0.15))
        for index in range(1, 7):  # Indices that do not trigger the thinking pause.
            assert 0.05 <= geo._key_delay(index) <= 0.15

    def test_thinking_pause_extends_delay(self):
        """Every Nth character adds an extra 'thinking' pause, so the delay can exceed max."""
        geo = MistUIGeocoder(UIGeocoderConfig(min_key_delay_s=0.10, max_key_delay_s=0.10))
        # min==max==0.10 -> base is exactly 0.10; the thinking pause at index 7 doubles it.
        assert geo._key_delay(1) == pytest.approx(0.10)
        assert geo._key_delay(7) == pytest.approx(0.20)

    def test_key_delay_guards_inverted_bounds(self):
        """If max < min, the upper bound is clamped to min (never negative range)."""
        geo = MistUIGeocoder(UIGeocoderConfig(min_key_delay_s=0.20, max_key_delay_s=0.05))
        assert geo._key_delay(1) == pytest.approx(0.20)


class TestHelpers:
    """Selector fallthrough, item-text safety, and Edge discovery."""

    def test_locate_input_falls_through_candidates(self):
        """The first matching selector wins; earlier misses are tried in order."""
        page = MagicMock()
        sentinel = object()
        page.wait_for_selector.side_effect = [RuntimeError("miss"), sentinel]
        assert MistUIGeocoder()._locate_input(page, 6000) is sentinel
        assert page.wait_for_selector.call_count == 2

    def test_item_text_handles_stale_node(self):
        """A node that raises on inner_text yields an empty string, not an error."""
        element = MagicMock()
        element.inner_text.side_effect = RuntimeError("stale")
        assert MistUIGeocoder._item_text(element) == ""

    def test_spawn_returns_none_when_edge_absent(self, monkeypatch):
        """No Edge binary => spawn_debuggable_browser returns None gracefully."""
        monkeypatch.setattr(MistUIGeocoder, "_edge_executable", staticmethod(lambda: None))
        assert MistUIGeocoder.spawn_debuggable_browser() is None


class TestStaleGuard:
    """The autocomplete lag race: never read the previous query's suggestion."""

    def test_house_number_extracts_first_digits(self):
        """The first digit-run of the query is the house-number anchor."""
        assert MistUIGeocoder._house_number("T-Mobile 931 US Highway 331") == "931"
        assert MistUIGeocoder._house_number("No digits here") == ""

    def test_matches_house_number_is_glue_safe(self):
        """House-number match works even when the name is glued to the number."""
        assert MistUIGeocoder._matches_house_number("T-Mobile931 US Highway 331", "931") is True
        assert MistUIGeocoder._matches_house_number("T-Mobile7535 Kendall Dr", "931") is False

    def test_read_fresh_returns_when_top_matches(self):
        """A top row containing the query's house number is returned immediately."""
        geo = MistUIGeocoder()
        page = MagicMock()
        item = MagicMock()
        item.inner_text.return_value = "T-Mobile931 US Highway 331 Ste A2, DeFuniak Springs, FL"
        page.query_selector_all.return_value = [item]
        out = geo._read_fresh_suggestions(page, "931", 5000)
        assert out and out[0].startswith("T-Mobile931")

    def test_read_fresh_skips_stale_then_returns(self):
        """A stale top row (wrong house number) is skipped until the fresh one appears."""
        geo = MistUIGeocoder()
        page = MagicMock()
        stale = MagicMock()
        stale.inner_text.return_value = "T-Mobile7535 North Kendall Drive #1515b, Miami, FL"
        fresh = MagicMock()
        fresh.inner_text.return_value = "T-Mobile1701 Ohio Ave N, Live Oak, FL"
        page.query_selector_all.side_effect = [[stale], [fresh]]  # First poll stale, second fresh.
        out = geo._read_fresh_suggestions(page, "1701", 5000)
        assert out[0].startswith("T-Mobile1701")
        assert page.query_selector_all.call_count == 2

    def test_read_fresh_times_out_to_empty(self):
        """Persistent stale (never the right house number) fails soft to [] (NO_RESULT)."""
        geo = MistUIGeocoder()
        page = MagicMock()
        stale = MagicMock()
        stale.inner_text.return_value = "T-Mobile7535 North Kendall Drive, Miami, FL"
        page.query_selector_all.return_value = [stale]
        assert geo._read_fresh_suggestions(page, "9999", 0) == []  # Zero budget -> immediate timeout.

    def test_read_fresh_waits_for_lagging_suite(self):
        """When a suite is expected, a suite-bearing row that arrives late is preferred."""
        geo = MistUIGeocoder()
        page = MagicMock()
        base = MagicMock()  # First poll: correct house number but no unit yet (suite lag).
        base.inner_text.return_value = "5550 North Military Trail, Boca Raton, FL 33431"
        withunit = MagicMock()  # Second poll: the unit has landed.
        withunit.inner_text.return_value = "5550 North Military Trail #200, Boca Raton, FL 33431"
        page.query_selector_all.side_effect = [[base], [withunit]]  # Suite appears on the 2nd poll.
        out = geo._read_fresh_suggestions(page, "5550", 5000, expected_suite="200")
        assert out[0].endswith("#200, Boca Raton, FL 33431")  # Captured the suite-bearing row.
        assert page.query_selector_all.call_count == 2  # Waited one extra poll for the suite.

    def test_read_fresh_accepts_base_after_suite_grace(self, monkeypatch):
        """If the suite never appears within the grace, the base street is accepted (not hung)."""
        monkeypatch.setattr(ui_mod, "_SUITE_GRACE_S", 0.0)  # Collapse the grace so the test is instant.
        geo = MistUIGeocoder()
        page = MagicMock()
        base = MagicMock()  # House number matches, unit never shows.
        base.inner_text.return_value = "5550 North Military Trail, Boca Raton, FL 33431"
        page.query_selector_all.return_value = [base]  # Always the suite-less base street.
        out = geo._read_fresh_suggestions(page, "5550", 5000, expected_suite="200")
        assert out and out[0].startswith("5550 North Military Trail")  # Falls back to the base street.

    def test_read_fresh_no_suite_returns_immediately(self):
        """With no expected suite the first house-number-fresh row returns at once (unchanged)."""
        geo = MistUIGeocoder()
        page = MagicMock()
        item = MagicMock()
        item.inner_text.return_value = "5550 North Military Trail, Boca Raton, FL 33431"
        page.query_selector_all.return_value = [item]
        out = geo._read_fresh_suggestions(page, "5550", 5000)  # No expected_suite.
        assert out and page.query_selector_all.call_count == 1  # No extra suite wait.


class TestSuitePreservation:
    """Tier-3 keeps a customer-supplied unit that Google's autocomplete drops."""

    def test_suite_id_and_phrase_extraction(self):
        """Keyword and hash unit forms are extracted from a full query string."""
        g = MistUIGeocoder()
        assert g._suite_phrase("5550 N Military Traill Unit 200 Boca Raton FL 33431") == "Unit 200"
        assert g._suite_id("5550 N Military Traill Unit 200 Boca Raton FL 33431") == "200"
        assert g._suite_phrase("940 S Military Trail #3 West Palm Beach FL 33415") == "#3"
        assert g._suite_id("940 S Military Trail #3 West Palm Beach FL 33415") == "3"
        assert g._suite_phrase("1200 NW 87th Ave Doral FL 33172") == ""  # No unit present.

    def test_reflects_suite_excludes_leading_house_number(self):
        """A unit id equal to the house number is not falsely 'reflected' by the base street."""
        assert MistUIGeocoder._reflects_suite("100 Main St, Town, FL 33000", "100") is False
        assert MistUIGeocoder._reflects_suite("100 Main St Suite 100, Town, FL", "100") is True
        assert MistUIGeocoder._reflects_suite("5550 N Military Trl #200, Boca, FL", "200") is True

    def test_preserves_dropped_unit_from_query(self):
        """Google returned the bare street; the unit we typed is restored to it."""
        g = MistUIGeocoder()
        query = "T-Mobile 5550 N Military Traill Unit 200 Boca Raton FL 33431"
        sugg = "5550 North Military Trail, Boca Raton, FL 33431"
        assert g._preserve_query_suite(query, sugg) == "5550 North Military Trail Unit 200, Boca Raton, FL 33431"

    def test_build_result_preserves_dropped_unit(self):
        """End-to-end: _build_result restores the dropped unit into the canonical address."""
        g = MistUIGeocoder()
        query = "T-Mobile 6798 Bird Rd Suite 98 Miami FL 33155"
        result = g._build_result(query, ["6798 Bird Road, Miami, FL 33155, USA"])
        assert result.canonical_address == "6798 Bird Road Suite 98, Miami, FL 33155"

    def test_keeps_googles_different_unit(self):
        """A DIFFERENT unit from Google is authoritative -- our unit is not grafted on."""
        g = MistUIGeocoder()
        query = "T-Mobile 4200 Conroy Rd #204 Orlando FL 32839"
        sugg = "4200 Conroy Rd Suite H200, Orlando, FL 32839"
        assert g._preserve_query_suite(query, sugg) == sugg  # Google's H200 wins.

    def test_never_grafts_across_buildings(self):
        """A different house number means a different building -- never move the unit."""
        g = MistUIGeocoder()
        query = "T-Mobile 901 W Indiantown Rd Suite 101 Jupiter FL 33458"
        sugg = "903 W Indiantown Rd, Jupiter, FL 33458"
        assert g._preserve_query_suite(query, sugg) == sugg  # 901 != 903 -> untouched.

    def test_no_unit_typed_is_noop(self):
        """When we typed no unit there is nothing to preserve."""
        g = MistUIGeocoder()
        assert g._preserve_query_suite("1200 NW 87th Ave Doral FL", "1200 NW 87th Ave, Doral, FL") == (
            "1200 NW 87th Ave, Doral, FL"
        )


class TestCleanAddress:
    """The captured Google suggestion is reduced to a clean shippable street line."""

    def test_strips_business_prefix_and_country(self):
        """A glued business name and trailing ', USA' are removed."""
        raw = "T-Mobile931 US Highway 331 Ste A2, DeFuniak Springs, FL 32435, USA"
        assert MistUIGeocoder._clean_address(raw) == "931 US Highway 331 Ste A2, DeFuniak Springs, FL 32435"

    def test_keeps_plain_address_unchanged(self):
        """An already-clean address is returned as-is."""
        assert MistUIGeocoder._clean_address("123 Main St Suite 4") == "123 Main St Suite 4"

    def test_keeps_numberless_address(self):
        """A place with no house number is preserved (cannot safely split)."""
        assert MistUIGeocoder._clean_address("Brandon Town Center Mall, Brandon, FL") == (
            "Brandon Town Center Mall, Brandon, FL"
        )

    def test_build_result_cleans_top_suggestion(self):
        """_build_result returns the cleaned address, not the raw glued text."""
        raw = "T-Mobile7535 North Kendall Drive #1515b, Miami, FL 33156, USA"
        result = MistUIGeocoder()._build_result("q", [raw])
        assert result.canonical_address == "7535 North Kendall Drive #1515b, Miami, FL 33156"

    def test_strips_business_when_street_starts_with_number(self):
        """The business prefix is stripped even when the street name starts with a digit."""
        raw = "T-Mobile4103 14th St W, Bradenton, FL 34205, USA"
        assert MistUIGeocoder._clean_address(raw) == "4103 14th St W, Bradenton, FL 34205"

    def test_splits_directional_glued_to_city(self):
        """A directional fused to the city is split (NLive Oak -> N Live Oak)."""
        raw = "1701 Ohio Ave NLive Oak, FL 32064"
        assert MistUIGeocoder._clean_address(raw) == "1701 Ohio Ave N Live Oak, FL 32064"

    def test_splits_street_suffix_glued_to_city(self):
        """A street suffix fused to the city is split (HwyFort Pierce -> Hwy Fort Pierce)."""
        raw = "2315 S Federal HwyFort Pierce, FL 34982"
        assert MistUIGeocoder._clean_address(raw) == "2315 S Federal Hwy Fort Pierce, FL 34982"

    def test_splits_number_glued_to_city(self):
        """A suite number fused to the city is split (330Brandon -> 330 Brandon)."""
        raw = "459 Brandon Town Center Drive suite 330Brandon, FL 33511"
        assert MistUIGeocoder._clean_address(raw) == "459 Brandon Town Center Drive suite 330 Brandon, FL 33511"

    def test_camelcase_city_is_preserved(self):
        """A legitimately camel-cased city (DeFuniak) is never split."""
        raw = "931 US Highway 331 Ste A2, DeFuniak Springs, FL 32435, USA"
        assert MistUIGeocoder._clean_address(raw) == "931 US Highway 331 Ste A2, DeFuniak Springs, FL 32435"

    def test_alphanumeric_street_name_preserved(self):
        """An alphanumeric street name (A1A) is not split by the number-glue rule."""
        raw = "1015 A1A Beach Blvd Unit 4, St. Augustine Beach, FL 32080"
        assert MistUIGeocoder._clean_address(raw) == "1015 A1A Beach Blvd Unit 4, St. Augustine Beach, FL 32080"

    def test_hyphenated_house_number_strips_business_prefix(self):
        """A Hawaii hyphenated house number (74-5450) still sheds the glued business name."""
        raw = "T-Mobile74-5450 Makala Blvd #107, Kailua-Kona, HI 96740, USA"  # Business name glued to 74-5450.
        assert MistUIGeocoder._clean_address(raw) == "74-5450 Makala Blvd #107, Kailua-Kona, HI 96740"

    def test_hyphenated_house_number_without_prefix_preserved(self):
        """A hyphenated house number with no business prefix is returned intact."""
        raw = "46-047 Kamehameha Hwy Suite E5, Kaneohe, HI 96744, USA"  # Leading 46-047 is the house number.
        assert MistUIGeocoder._clean_address(raw) == "46-047 Kamehameha Hwy Suite E5, Kaneohe, HI 96744"


class TestAutoConnect:
    """The default 'auto' mode: take over an existing browser, else spawn one."""

    def test_auto_attaches_when_browser_present(self, monkeypatch):
        """Auto reuses a running debuggable browser without spawning."""
        browser = MagicMock()
        ctx = MagicMock()
        browser.contexts = [ctx]
        factory, _ = _fake_playwright(browser)
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)
        spy = MagicMock()
        monkeypatch.setattr(MistUIGeocoder, "spawn_debuggable_browser", staticmethod(spy))
        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="auto"))
        assert geo.connect() is True
        assert geo._context is ctx
        spy.assert_not_called()  # Existing browser taken over; no spawn needed.

    def test_auto_spawns_when_no_browser(self, monkeypatch):
        """Auto spawns Edge, waits for login, then takes it over via CDP."""
        browser = MagicMock()
        ctx = MagicMock()
        browser.contexts = [ctx]
        driver = MagicMock()
        driver.chromium.connect_over_cdp.side_effect = [RuntimeError("no endpoint"), browser]  # miss, then hit.
        factory = MagicMock()
        factory.return_value.start.return_value = driver
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)
        proc = MagicMock()
        spawned = ui_mod.SpawnedBrowser(process=proc, profile_dir="C:\\temp\\misthelper-edge-test")  # Issue #1862.
        monkeypatch.setattr(MistUIGeocoder, "spawn_debuggable_browser", staticmethod(lambda *a, **k: spawned))
        monkeypatch.setattr(ui_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: ""))
        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="auto"))
        assert geo.connect() is True
        assert geo._spawned_proc is proc
        assert geo._spawned_profile_dir == spawned.profile_dir  # The caller owns the profile for the teardown.
        assert driver.chromium.connect_over_cdp.call_count == 2  # Attach-miss, then attach-after-spawn.

    def test_auto_falls_back_to_launch_when_no_edge(self, monkeypatch):
        """Auto falls back to Playwright launch when Edge cannot be spawned."""
        browser = MagicMock()
        browser.new_context.return_value = MagicMock()
        driver = MagicMock()
        driver.chromium.connect_over_cdp.side_effect = RuntimeError("no endpoint")  # No browser to attach.
        driver.chromium.launch.return_value = browser
        factory = MagicMock()
        factory.return_value.start.return_value = driver
        monkeypatch.setattr(ui_mod, "sync_playwright", factory)
        monkeypatch.setattr(MistUIGeocoder, "spawn_debuggable_browser", staticmethod(lambda *a, **k: None))
        monkeypatch.setattr(ui_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: ""))
        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="auto"))
        assert geo.connect() is True
        driver.chromium.launch.assert_called_once()


class TestPortAndReadiness:
    """CDP port parsing, the Location Search readiness probe, and spawned teardown."""

    def test_cdp_port_parses_endpoint(self):
        """A port in the CDP endpoint is parsed correctly."""
        geo = MistUIGeocoder(UIGeocoderConfig(cdp_endpoint="http://127.0.0.1:9333"))
        assert geo._cdp_port() == 9333

    def test_cdp_port_defaults_when_no_digits(self):
        """An endpoint without a port falls back to the documented 9222 default."""
        geo = MistUIGeocoder(UIGeocoderConfig(cdp_endpoint="http://localhost"))
        assert geo._cdp_port() == 9222

    def test_ensure_ready_false_when_disconnected(self):
        """The readiness probe returns False without a connection."""
        assert MistUIGeocoder().ensure_location_field_ready() is False

    def test_ensure_ready_detects_field(self):
        """A present Location Search field is detected without prompting."""
        geo = MistUIGeocoder()
        geo._connected = True  # Simulate a successful connect().
        page = MagicMock()
        page.query_selector.return_value = object()  # Field present on first probe.
        geo._active_page = MagicMock(return_value=page)
        assert geo.ensure_location_field_ready() is True

    def test_ensure_ready_guides_then_finds(self, monkeypatch):
        """When the field is missing, the operator is prompted, then it's found."""
        geo = MistUIGeocoder()
        geo._connected = True  # Simulate a successful connect().
        page = MagicMock()
        page.query_selector.side_effect = [None, None, None, object()]  # All miss, then a hit next attempt.
        geo._active_page = MagicMock(return_value=page)
        monkeypatch.setattr(ui_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: ""))
        assert geo.ensure_location_field_ready(max_prompts=2) is True

    def test_close_terminates_spawned(self):
        """close() terminates a browser we spawned and clears the handle."""
        geo = MistUIGeocoder()
        proc = MagicMock()
        geo._spawned_proc = proc
        geo.close()
        proc.terminate.assert_called_once()
        assert geo._spawned_proc is None
