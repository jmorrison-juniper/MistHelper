"""Exercise verification masking and exact submission without a network service."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, Route, expect


class PortalDispatch:
    """Prevent browser network access while exercising the shipped Flask routes."""

    def __init__(self, client: Any) -> None:
        """Keep the test client and record each rejected external request."""
        self.client = client
        self.blocked_urls: list[str] = []

    def __call__(self, route: Route) -> None:
        """Reject external hosts and dispatch only portal requests to the Flask client."""
        target = urlsplit(route.request.url)
        if target.netloc != "portal.test":
            self.blocked_urls.append(route.request.url)
            route.abort("blockedbyclient")
            return
        response = self.client.open(
            target.path + ("?" + target.query if target.query else ""),
            method=route.request.method,
            data=route.request.post_data,
            headers=route.request.all_headers(),
        )
        route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.get_data())


@pytest.fixture
def verification_page(page: Page, client: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[Page]:
    """Use Flask dispatch and let pytest-playwright retain failed-flow traces."""
    metadata = client.get("/api/operations/parameters/247")
    assert metadata.status_code == 200
    executor = client.application.config["OPERATION_EXECUTOR"]
    monkeypatch.setattr(executor, "start_operation", Mock(return_value={"error": "Synthetic run intercepted."}))
    dispatch = PortalDispatch(client)
    page.route("**/*", dispatch)
    page.goto("http://portal.test/operations", wait_until="networkidle")
    yield page
    assert dispatch.blocked_urls == [], "The verification journey attempted a nonlocal request."


class TestVerificationSubmission:
    """Prove native masking, required validation, and the unchanged positional payload."""

    @pytest.mark.parametrize("value", ["000123", "  synthetic+/%&=\"'<> token  "])
    def test_masked_control_submits_exact_value(self, verification_page: Page, client: Any, value: str) -> None:
        """Use the actual script and run route while a mock prevents handler execution."""
        page = verification_page
        page.locator('.op-item[data-menu="247"]').evaluate("element => element.click()")
        control = page.get_by_test_id("param-email_change_token")
        expect(control).to_have_attribute("type", "password")
        expect(control).to_have_attribute("required", "")
        expect(control).to_have_attribute("name", "email_change_token")
        expect(control).to_have_attribute("placeholder", "Token from the Mist email")
        expect(page.get_by_label("Email Change Token")).to_have_count(1)
        expect(page.locator("#runBtn")).to_be_disabled()
        control.fill(value)
        expect(page.locator("#runBtn")).to_be_enabled()
        control.fill("")
        expect(page.locator("#runBtn")).to_be_disabled()
        control.fill(value)
        with page.expect_response("**/api/operations/run") as submitted:
            page.locator("#runBtn").click()
        assert submitted.value.status == 400
        client.application.config["OPERATION_EXECUTOR"].start_operation.assert_called_once_with(
            "247", {"input_answers": [value]}
        )

    @pytest.mark.parametrize("display_override", [None, "text", "email", "unsupported"])
    def test_other_text_controls_remain_text(self, verification_page: Page, display_override: str | None) -> None:
        """An absent or unsupported override cannot change an ordinary text control."""
        result = verification_page.evaluate(
            """override => {
                const param = {name: 'probe', label: 'Probe', param_type: 'text',
                    required: true, default: '0007', placeholder: 'Example'};
                if (override !== null) param.input_type = override;
                const control = createParameterControl(param);
                return {type: control.type, value: control.value, required: control.required,
                    name: control.name, placeholder: control.placeholder};
            }""",
            display_override,
        )
        assert result == {
            "type": "text",
            "value": "0007",
            "required": True,
            "name": "probe",
            "placeholder": "Example",
        }
