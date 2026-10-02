"""Prove issue #3295 through the shipped sign-in controller and stylesheet.

Collect this module under ``tests/e2e/`` with strict browser mode. The shared
fixture owns the server, storage, cloud stand-ins, and evidence lifecycle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.e2e.upgrade_portal.issue_3295_signin_support import (
    SigninBrowserContext,
    SigninGuards,
    SigninJourney,
    SigninMeasurements,
    SigninTheme,
)
from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck

if TYPE_CHECKING:
    from playwright.sync_api import Page, Request, Response

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")


@pytest.fixture
def layout_browser(
    signed_out_page: Page,
    browser_token_value: str,
    browser_token_evidence_path: Path,
    browser_token_server_log_path: Path,
    tmp_path: Path,
) -> SigninBrowserContext:
    """Use the existing process owner without importing conftest globals."""
    return SigninBrowserContext(
        signed_out_page, browser_token_value, browser_token_evidence_path, browser_token_server_log_path, tmp_path
    )


class TestSigninLayoutMeasurements:
    """Measure actual geometry and Warning weight at each required width."""

    @pytest.mark.parametrize("viewport", [(1280, 720), (360, 800)])
    @pytest.mark.parametrize(("catalog", "theme"), SigninTheme.variants())
    def test_token_label_is_above_its_field(
        self, layout_browser: SigninBrowserContext, viewport: tuple[int, int], catalog: str, theme: str
    ) -> None:
        """Require a contained token group below all mode buttons."""
        context = layout_browser
        context.page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
        SigninJourney.open(context, "default" if catalog == "main" else theme)
        asset = SigninTheme.apply(context, theme, catalog)
        context.page.get_by_test_id("signin-mode-browser-token").check()
        measured = SigninMeasurements.geometry(context.page)
        SigninJourney.save(context, f"geometry-{catalog}-{theme}-{viewport[0]}", {"asset": asset, "geometry": measured})
        SigninGuards.geometry(measured)
        group = context.page.get_by_test_id("signin-browser-token-group")
        assert group.get_attribute("role") == "group"
        assert group.get_attribute("aria-labelledby") == "signin-browser-token-label"
        sync_api.expect(context.page.get_by_test_id("signin-browser-token")).to_have_accessible_name("Mist API token")
        context.page.get_by_test_id("signin-browser-token-label").click()
        sync_api.expect(context.page.get_by_test_id("signin-browser-token")).to_be_focused()

    @pytest.mark.parametrize("viewport", [(1280, 720), (360, 800)])
    @pytest.mark.parametrize("theme", SigninTheme.native)
    def test_warning_weight_matches_the_actual_error_page(
        self, layout_browser: SigninBrowserContext, viewport: tuple[int, int], theme: str
    ) -> None:
        """Compare service, client refusal, and real missing-route prefixes."""
        context = layout_browser
        context.page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
        SigninJourney.open(context, theme)
        measured = self.signin_warning_styles(context)
        SigninJourney.save(context, f"warnings-{theme}-{viewport[0]}", measured)
        response = context.page.goto(f"/__issue3295_missing_page__?theme={theme}", wait_until="networkidle")
        assert response is not None and response.status == 404
        owner = context.evidence.parent.name
        assert RunOwnerHeaderCheck(owner).require(response.headers) == owner
        error = context.page.get_by_test_id("error-message")
        measured["error"] = SigninMeasurements.prefix(error)
        comparison = {"styles": measured, "status": response.status}
        SigninJourney.save(context, f"actual-warning-comparison-{theme}-{viewport[0]}", comparison)
        for style in measured.values():
            SigninGuards.prefix(style)
        assert len({style["foreground"] for style in measured.values()}) == 1
        assert len({style["background"] for style in measured.values()}) == 1
        assert error.aria_snapshot().count("Warning:") == 1

    @staticmethod
    def signin_warning_styles(context: SigninBrowserContext) -> dict[str, dict[str, str]]:
        """Read the actual service warning and existing empty-token client cure."""
        dependency = context.page.get_by_test_id("dependency-warning")
        assert dependency.count() == 1 and dependency.is_visible() is True
        context.page.get_by_test_id("signin-mode-browser-token").check()
        context.page.get_by_test_id("signin-submit").click()
        refusal = context.page.get_by_test_id("signin-error")
        sync_api.expect(refusal).to_have_text("Type a Mist API token before you sign in.")
        assert dependency.aria_snapshot().count("Warning:") == 1
        assert refusal.aria_snapshot().count("Warning:") == 1
        return {"service": SigninMeasurements.prefix(dependency), "refusal": SigninMeasurements.prefix(refusal)}

    @pytest.mark.parametrize("theme", SigninTheme.native)
    def test_dependency_overflow_remains_outside_the_token_group(
        self, layout_browser: SigninBrowserContext, theme: str
    ) -> None:
        """Preserve the measured 400-pixel service table at a 360-pixel viewport."""
        context = layout_browser
        context.page.set_viewport_size({"width": 360, "height": 800})
        SigninJourney.open(context, theme)
        context.page.get_by_test_id("signin-mode-browser-token").check()
        measured = SigninMeasurements.geometry(context.page)
        SigninGuards.geometry(measured)
        assert measured["pageWidth"] == 360 and measured["pageScroll"] == 400
        assert len(measured["overflow"]) > 0
        assert all(row["dependency"] is True for row in measured["overflow"])
        assert max(row["right"] for row in measured["overflow"]) == 399.71875
        SigninJourney.save(context, f"existing-dependency-overflow-{theme}", measured)

    def test_empty_alerts_and_adjacent_signal_words_remain_unchanged(
        self, layout_browser: SigninBrowserContext
    ) -> None:
        """Keep empty alerts hidden and escape message text without a bare prefix."""
        context = layout_browser
        SigninJourney.open(context)
        alert = context.page.get_by_test_id("signin-error")
        assert alert.is_hidden() is True and SigninMeasurements.prefix(alert)["content"] == "none"
        assert '"Warning:"' not in alert.aria_snapshot()
        for level, signal in (
            ("info", "Note: "),
            ("success", "Done: "),
            ("warning", "Caution: "),
            ("danger", "Warning: "),
        ):
            sentence = "<strong>Issue 3295 plain text</strong>"
            context.page.evaluate("([text, level]) => window.upgradePortal.showFlash(text, level)", [sentence, level])
            region = context.page.get_by_test_id("flash-message")
            assert region.locator("strong").count() == 0
            assert f"{signal}{sentence}" in region.aria_snapshot()
            item = region.locator(".flash-item").last
            measured = SigninMeasurements.prefix(item)
            assert measured["content"] == json.dumps(signal) and measured["weight"] == "700"


class TestSigninModeMeasurements:
    """Measure native focus, successful controls, and request counts."""

    def test_inactive_token_is_hidden_and_excluded(self, layout_browser: SigninBrowserContext) -> None:
        """Do not expose or submit the unused token in provider mode."""
        context = layout_browser
        SigninJourney.open(context)
        measured = SigninMeasurements.mode(context.page)
        SigninJourney.save(context, "initial-provider-mode", measured)
        SigninGuards.mode(measured, False)
        assert measured["emailRequired"] is True and measured["passwordRequired"] is True
        context.page.get_by_test_id("signin-mode-browser-token").check()
        SigninGuards.mode(SigninMeasurements.mode(context.page), True)
        context.page.get_by_test_id("signin-browser-token").fill("fake-token-retained-only-in-browser-memory")
        context.page.get_by_test_id("signin-mode-provider").check()
        SigninGuards.mode(SigninMeasurements.mode(context.page), False)
        token = context.page.get_by_test_id("signin-browser-token")
        token.evaluate("node => node.focus()")
        assert token.evaluate("node => document.activeElement === node") is False
        context.page.get_by_test_id("signin-mode-browser-token").check()
        sync_api.expect(token).to_have_value("fake-token-retained-only-in-browser-memory")
        token.fill("")

    @pytest.mark.parametrize("viewport", [(1280, 720), (360, 800)])
    def test_keyboard_reaches_the_token_after_mode_switches(
        self, layout_browser: SigninBrowserContext, viewport: tuple[int, int]
    ) -> None:
        """Use only native Tab and arrow keys to enter and leave the token mode."""
        context = layout_browser
        context.page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
        SigninJourney.open(context)
        evidence: list[dict[str, str]] = []
        for _step in range(20):
            context.page.keyboard.press("Tab")
            focused = SigninMeasurements.focus(context.page)
            evidence.append({"key": "Tab", "focus": focused})
            if focused == "signin-mode-provider":
                break
        evidence.extend(SigninJourney.keyboard(context))
        SigninJourney.save(context, f"keyboard-{viewport[0]}", evidence)
        assert len(evidence) >= 11
        assert evidence[-1] == {"key": "Tab", "focus": "signin-browser-token"}
        SigninGuards.mode(SigninMeasurements.mode(context.page), True)

    def test_provider_validation_restores_without_a_request(self, layout_browser: SigninBrowserContext) -> None:
        """Restore native provider requirements without removing entered values."""
        context = layout_browser
        SigninJourney.open(context)
        posts: list[str] = []
        context.page.on("request", lambda request: posts.append(request.url) if request.method == "POST" else None)
        context.page.get_by_test_id("signin-email").fill("probe.operator@example.invalid")
        context.page.get_by_test_id("signin-password").fill("fake-password-for-layout-check-only")
        context.page.get_by_test_id("signin-mode-browser-token").check()
        measured = SigninMeasurements.mode(context.page)
        assert measured["emailRequired"] is False and measured["passwordRequired"] is False
        context.page.get_by_test_id("signin-mode-provider").check()
        sync_api.expect(context.page.get_by_test_id("signin-email")).to_have_value("probe.operator@example.invalid")
        sync_api.expect(context.page.get_by_test_id("signin-password")).to_have_value(
            "fake-password-for-layout-check-only"
        )
        context.page.get_by_test_id("signin-password").fill("")
        context.page.get_by_test_id("signin-submit").click()
        assert context.page.get_by_test_id("signin-password").evaluate("node => node.validity.valueMissing") is True
        context.page.get_by_test_id("signin-email").fill("not-an-email")
        context.page.get_by_test_id("signin-password").fill("fake-password-for-layout-check-only")
        context.page.get_by_test_id("signin-submit").click()
        assert context.page.get_by_test_id("signin-email").evaluate("node => node.validity.typeMismatch") is True
        assert posts == []


class TestSigninSubmissionMeasurements:
    """Count repeated-mode requests and preserve the existing refusal boundary."""

    class SigninSubmitChecks:
        """Observe the request boundary and verify existing mode and refusal rules."""

        @staticmethod
        def observe_submit(context: SigninBrowserContext) -> tuple[list[Request], list[str]]:
            """Observe actual POST requests and the field state at their boundary."""
            requests: list[Request] = []
            cleared: list[str] = []

            def record(request: Request) -> None:
                if request.method == "POST":
                    requests.append(request)
                    cleared.append(context.page.get_by_test_id("signin-browser-token").input_value())

            context.page.on("request", record)
            return requests, cleared

        @staticmethod
        def switch_ten_times(context: SigninBrowserContext) -> dict[str, int]:
            """Require unchanged listeners, provider values, and the selected cloud."""
            baseline = SigninMeasurements.listeners(context.page)
            for _cycle in range(10):
                context.page.get_by_test_id("signin-mode-provider").check()
                SigninGuards.mode(SigninMeasurements.mode(context.page), False)
                context.page.get_by_test_id("signin-mode-browser-token").check()
            assert SigninMeasurements.listeners(context.page) == baseline
            sync_api.expect(context.page.get_by_test_id("signin-browser-token")).to_have_value(
                f"{context.token}-issue3295-refused"
            )
            sync_api.expect(context.page.get_by_test_id("signin-email")).to_have_value("probe.operator@example.invalid")
            sync_api.expect(context.page.get_by_test_id("signin-password")).to_have_value(
                "fake-password-for-layout-check-only"
            )
            assert (
                context.page.get_by_test_id("signin-submit").evaluate("button => button.form.elements.host.value")
                == "api.eu.mist.com"
            )
            return baseline

        @staticmethod
        def assert_one_refusal(
            context: SigninBrowserContext, response: Response, requests: list[Request], cleared: list[str]
        ) -> None:
            """Check the exact transport shape and current refusal message."""
            assert len(requests) == 1 and cleared == [""]
            assert requests[0].headers["content-type"] == "application/json"
            assert set(requests[0].post_data_json) == {"mode", "host", "token"}
            assert requests[0].post_data_json["mode"] == "browser_token"
            assert requests[0].post_data_json["host"] == "api.eu.mist.com"
            assert "x-csrftoken" in requests[0].headers
            assert response.status == 400
            message = "The portal could not sign you in. Check the token, then try again."
            assert response.json() == {"error": {"code": "bad_credentials", "message": message}}
            alert = context.page.get_by_test_id("signin-error")
            sync_api.expect(alert).to_have_text(message)
            sync_api.expect(context.page.get_by_test_id("signin-browser-token")).to_have_value("")
            SigninGuards.prefix(SigninMeasurements.prefix(alert))

        @staticmethod
        def assert_transport_body(response: Response, status: int) -> None:
            """Prove the actual empty body or malformed JSON that reaches the controller."""
            if status == 503:
                assert response.body() == b""
            else:
                with pytest.raises(json.JSONDecodeError):
                    response.json()

    def test_repeated_switches_keep_one_json_submit_and_clear_before_refusal(
        self, layout_browser: SigninBrowserContext
    ) -> None:
        """Ten cycles preserve values and listeners, then send one safe request."""
        context = layout_browser
        SigninJourney.open(context)
        context.page.get_by_test_id("signin-mode-browser-token").check()
        submitted = f"{context.token}-issue3295-refused"
        context.page.get_by_test_id("signin-browser-token").fill(submitted)
        context.page.get_by_test_id("signin-email").fill("probe.operator@example.invalid")
        context.page.get_by_test_id("signin-password").fill("fake-password-for-layout-check-only")
        context.page.get_by_test_id("signin-submit").evaluate(
            "button => { button.form.elements.host.value = 'api.eu.mist.com'; }"
        )
        before = SigninJourney.events(context)
        requests, cleared = self.SigninSubmitChecks.observe_submit(context)
        listeners = self.SigninSubmitChecks.switch_ten_times(context)
        assert requests == []
        with context.page.expect_response(lambda response: response.request.method == "POST") as event:
            context.page.get_by_test_id("signin-submit").click()
        self.SigninSubmitChecks.assert_one_refusal(context, event.value, requests, cleared)
        assert len(SigninJourney.events(context)[len(before) :]) == 1
        SigninJourney.private(context, submitted, event.value)
        measured = {"cycles": 10, "listeners": listeners, "requests": 1, "cleared": cleared}
        SigninJourney.save(context, "submit-boundary", measured)

    @pytest.mark.parametrize("value", ["", " \t "])
    def test_empty_browser_token_sends_zero_requests(self, layout_browser: SigninBrowserContext, value: str) -> None:
        """Keep the exact client cure and the server boundary unchanged."""
        context = layout_browser
        SigninJourney.open(context)
        before = SigninJourney.events(context)
        requests: list[str] = []
        context.page.on("request", lambda request: requests.append(request.url) if request.method == "POST" else None)
        context.page.get_by_test_id("signin-mode-browser-token").check()
        context.page.get_by_test_id("signin-browser-token").fill(value)
        context.page.get_by_test_id("signin-submit").click()
        sync_api.expect(context.page.get_by_test_id("signin-error")).to_have_text(
            "Type a Mist API token before you sign in."
        )
        assert requests == [] and SigninJourney.events(context) == before
        context.page.get_by_test_id("signin-browser-token").fill("")
        SigninJourney.save(context, f"empty-client-{len(value)}", {"requests": 0, "boundary_events": 0})

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param((503, "", "The request failed."), id="empty_body"),
            pytest.param((200, "<strong>not JSON</strong>", "The response was not JSON."), id="malformed_json"),
        ],
    )
    def test_empty_body_and_malformed_json_keep_the_token_cleared(
        self, layout_browser: SigninBrowserContext, scenario: tuple[int, str, str]
    ) -> None:
        """Exercise bad transport answers without reaching a cloud or changing policy."""
        context = layout_browser
        SigninJourney.open(context)
        before = SigninJourney.events(context)
        status, body, message = scenario
        checks = TestSigninSubmissionMeasurements.SigninSubmitChecks
        context.page.route(
            "**/auth/signin", lambda route: route.fulfill(status=status, body=body, content_type="application/json")
        )
        context.page.get_by_test_id("signin-mode-browser-token").check()
        submitted = f"{context.token}-transport-control"
        context.page.get_by_test_id("signin-browser-token").fill(submitted)
        requests, cleared = checks.observe_submit(context)
        with context.page.expect_response(lambda response: response.request.method == "POST") as event:
            context.page.get_by_test_id("signin-submit").click()
        sync_api.expect(context.page.get_by_test_id("signin-error")).to_have_text(message)
        assert len(requests) == 1 and cleared == [""]
        assert event.value.status == status and SigninJourney.events(context) == before
        checks.assert_transport_body(event.value, status)
        SigninJourney.private(context, submitted, event.value)
        SigninJourney.save(context, f"transport-{status}", {"requests": 1, "boundary_events": 0, "cleared": cleared})
