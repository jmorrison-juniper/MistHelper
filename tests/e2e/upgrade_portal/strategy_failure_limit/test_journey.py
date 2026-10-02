"""Prove the organization failure limit with the shipped page and script."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.e2e.upgrade_portal.strategy_failure_limit.browser import FailureLimitBrowser, FailureLimitChecks
from tests.e2e.upgrade_portal.strategy_failure_limit.portal import FailureLimitPortal
from tests.unit.upgrade_portal.strategy_failure_limit.markup import FailureFieldGuard

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")


@pytest.fixture
def javascript_enabled() -> bool:
    """Keep JavaScript active unless an initial-render case explicitly disables it."""
    return True


@pytest.fixture
def failure_browser(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    layout: tuple[int, int, str],
    javascript_enabled: bool,
) -> Iterator[FailureLimitBrowser]:
    """Own the page, actual server, trace, record graph, and counted transport boundaries."""
    portal = FailureLimitPortal(monkeypatch)
    settings = {
        "theme": layout[2],
        "context": {
            "viewport": {"width": layout[0], "height": layout[1]},
            "java_script_enabled": javascript_enabled,
        },
    }
    journey = FailureLimitBrowser(request.getfixturevalue("browser"), portal, tmp_path, settings)
    journey.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    try:
        journey.server.start(portal.run_id)
        yield journey
    finally:
        journey.close(request.module.__name__)


@pytest.mark.parametrize(
    "layout",
    [
        (1280, 900, "magenta"),
        (390, 844, "magenta"),
        (1280, 900, "default"),
        (390, 844, "default"),
    ],
)
class TestInitialStates:
    """Require saved and default states with and without the shipped JavaScript."""

    @pytest.mark.parametrize("javascript_enabled", [False, True])
    @pytest.mark.parametrize("strategy", ["canary", "big_bang", "rrm", "serial"])
    def test_saved_initial_strategy(self, failure_browser: FailureLimitBrowser, strategy: str) -> None:
        """Each saved strategy paints the specified field state before an operator action."""
        failure_browser.open(strategy, 23)
        measured = failure_browser.state()
        FailureLimitChecks.state(measured, strategy, 23)
        FailureLimitChecks.geometry(measured)
        FailureLimitChecks.adjacent(failure_browser.page, strategy)
        assert measured["theme"] == ("dark" if failure_browser.artifacts.name == "magenta" else "light")

    @pytest.mark.parametrize("javascript_enabled", [False, True])
    def test_initial_canary_default(self, failure_browser: FailureLimitBrowser) -> None:
        """An unsaved page shows the original default percentage of five."""
        failure_browser.open(None)
        measured = failure_browser.state()
        FailureLimitChecks.state(measured, "canary", 5)
        FailureLimitChecks.geometry(measured)
        assert failure_browser.page.get_by_label("Maximum failure percentage").count() == 1

    def test_big_bang_hides_and_disables_the_failure_percentage(self, failure_browser: FailureLimitBrowser) -> None:
        """The original red journey now hides and disables an edited percentage."""
        failure_browser.open(None)
        page = failure_browser.page
        page.get_by_test_id("org-upgrade-max-failures").fill("17")
        page.get_by_test_id("org-strategy-big_bang").check()
        measured = failure_browser.state()
        FailureLimitChecks.state(measured, "big_bang", 17)
        FailureLimitChecks.geometry(measured)
        assert measured["posted"] == []


@pytest.mark.parametrize(
    "layout",
    [
        (1280, 900, "magenta"),
        (390, 844, "magenta"),
        (1280, 900, "default"),
        (390, 844, "default"),
    ],
)
class TestStrategyJourneys:
    """Preserve edited values, native form safety, exact saves, and adjacent controls."""

    def test_repeated_switches_keep_the_edited_value_and_device_choices(
        self, failure_browser: FailureLimitBrowser
    ) -> None:
        """Each real radio selector preserves a valid edited percentage through two cycles."""
        failure_browser.open("canary", 23)
        page = failure_browser.page
        targets = FailureLimitChecks.targets(page)
        page.get_by_test_id("org-upgrade-max-failures").fill("17")
        start_positions = {}
        for strategy in ("big_bang", "rrm", "serial", "canary") * 2:
            page.get_by_test_id(f"org-strategy-{strategy}").check()
            measured = failure_browser.state()
            FailureLimitChecks.state(measured, strategy, 17)
            FailureLimitChecks.geometry(measured)
            FailureLimitChecks.adjacent(page, strategy)
            assert FailureLimitChecks.targets(page) == targets
            start_positions[strategy] = measured["startTop"]
        assert start_positions["big_bang"] < start_positions["serial"]

    @pytest.mark.parametrize("strategy", ["canary", "big_bang", "rrm", "serial"])
    def test_formdata_and_the_actual_review_json_match(
        self, failure_browser: FailureLimitBrowser, strategy: str
    ) -> None:
        """Review includes the exact percentage or omits it from both actual payloads."""
        failure_browser.open(strategy, 23)
        page = failure_browser.page
        targets = FailureLimitChecks.targets(page)
        measured = failure_browser.state()
        FailureLimitChecks.state(measured, strategy, 23)
        body = failure_browser.review()
        FailureLimitChecks.payload(measured, body, targets)
        assert failure_browser.portal.require_idle()["plan_count"] == 1
        page.get_by_role("link", name="Back", exact=True).click()
        expected = 5 if strategy == "big_bang" else 23
        FailureLimitChecks.state(failure_browser.state(), strategy, expected)
        assert FailureLimitChecks.targets(page) == targets

    def test_native_validation_and_keyboard_access(self, failure_browser: FailureLimitBrowser) -> None:
        """Required validation applies only to active strategies and Tab skips the hidden field."""
        failure_browser.open("canary", 23)
        page = failure_browser.page
        field = page.get_by_test_id("org-upgrade-max-failures")
        for value, flag in (("", "valueMissing"), ("-1", "rangeUnderflow"), ("101", "rangeOverflow")):
            field.fill(value)
            measured = failure_browser.state()
            assert (measured[flag], measured["formValid"], measured["willValidate"]) == (True, False, True)
        for value in ("0", "100"):
            field.fill(value)
            FailureLimitChecks.state(failure_browser.state(), "canary", int(value))
        field.fill("")
        page.get_by_test_id("org-strategy-big_bang").check()
        assert failure_browser.state()["formValid"] is True
        page.get_by_test_id("org-upgrade-force").focus()
        page.keyboard.press("Tab")
        sync_api.expect(page.get_by_test_id("org-upgrade-start-time")).to_be_focused()
        page.get_by_test_id("org-strategy-big_bang").focus()
        page.keyboard.press("ArrowRight")
        sync_api.expect(page.get_by_test_id("org-strategy-rrm")).to_be_checked()
        field.fill("17")
        field.press("Tab")
        sync_api.expect(page.get_by_test_id("org-upgrade-start-time")).to_be_focused()
        FailureLimitChecks.state(failure_browser.state(), "rrm", 17)

    @pytest.mark.parametrize("defect", ["missing_rule", "enabled_hidden_input"])
    def test_browser_negative_controls_fail_the_guard(self, failure_browser: FailureLimitBrowser, defect: str) -> None:
        """Real DOM mutations prove that neither failure decision can report success."""
        failure_browser.open("canary", 23)
        page = failure_browser.page
        field = page.get_by_test_id("org-upgrade-max-failures")
        if defect == "missing_rule":
            field.evaluate("node => node.parentElement.removeAttribute('data-org-requires-strategy')")
        page.get_by_test_id("org-strategy-big_bang").check()
        if defect == "enabled_hidden_input":
            field.evaluate("node => { node.disabled = false; }")
        measured = failure_browser.state()
        assert measured["posted"] == ["23"]
        guard = FailureFieldGuard(page.content())
        with pytest.raises(AssertionError, match="strategy rule|enabled state"):
            guard.require("big_bang", 23)
        assert guard.checked == 1

    def test_refused_review_keeps_the_hidden_field_disabled(self, failure_browser: FailureLimitBrowser) -> None:
        """A target refusal preserves Big bang state, the edited value, and the existing message focus."""
        failure_browser.open("canary", 23)
        page = failure_browser.page
        page.get_by_test_id("org-strategy-big_bang").check()
        controls = page.locator("[data-org-version-for]")
        for index in range(controls.count()):
            controls.nth(index).select_option("")
        with page.expect_response("**/api/org-upgrades/options") as received:
            page.get_by_test_id("org-upgrade-review").click()
        assert received.value.status == 400
        body = received.value.request.post_data_json
        assert isinstance(body, dict)
        assert "max_failure_percentage" not in body
        flash = page.get_by_test_id("flash-message")
        sync_api.expect(flash).to_contain_text('"Device target versions"')
        assert flash.evaluate("node => node.contains(document.activeElement)") is True
        assert page.url.endswith("/upgrade/org/options?theme=" + failure_browser.artifacts.name)
        FailureLimitChecks.state(failure_browser.state(), "big_bang", 23)
        assert failure_browser.portal.require_idle()["plan_count"] == 0
