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
        monkeypatch.setattr(MistUIGeocoder, "spawn_debuggable_browser", staticmethod(lambda *a, **k: proc))
        monkeypatch.setattr(ui_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: ""))
        geo = MistUIGeocoder(UIGeocoderConfig(connect_mode="auto"))
        assert geo.connect() is True
        assert geo._spawned_proc is proc
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
