"""Pin issue #3295 markup and native startup presentation without cloud calls."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from flask import Flask, render_template
from flask.testing import FlaskClient


class SigninMarkup(HTMLParser):
    """Read semantic relationships from the actual rendered sign-in response."""

    def __init__(self, html: str) -> None:
        """Keep each named node and its actual enclosing elements."""
        super().__init__(convert_charrefs=True)
        self.nodes: dict[str, dict[str, Any]] = {}
        self.stack: list[dict[str, Any]] = []
        self.order: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track named nodes without a dependency on a browser or CSS."""
        node = {"tag": tag, "attrs": dict(attrs), "ancestors": list(self.stack)}
        name = node["attrs"].get("data-testid") or node["attrs"].get("id")
        if name:
            assert name not in self.nodes, f"The form repeats the identifier {name}."
            self.nodes[name] = node
            self.order.append(name)
        if tag not in {"input", "meta", "link", "br", "img", "hr"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        """Close the matching element while retaining earlier node relationships."""
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break


class TestSigninSemanticContract:
    """Keep the token group conditional, accessible, and outside the flex choices."""

    def test_token_group_follows_the_complete_mode_fieldset(
        self, portal_client: FlaskClient, portal_app: Flask
    ) -> None:
        """Render the real route with one coherent, initially inactive group."""
        portal_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = True
        response = portal_client.get("/auth/signin")
        assert response.status_code == 200 and response.mimetype == "text/html"
        markup = SigninMarkup(response.get_data(as_text=True))
        group = markup.nodes["signin-browser-token-group"]
        assert group["tag"] == "div"
        assert group["attrs"]["role"] == "group" and "hidden" in group["attrs"]
        assert group["attrs"]["aria-labelledby"] == "signin-browser-token-label"
        assert all(node["tag"] != "fieldset" for node in group["ancestors"])
        children = ["signin-browser-token-label", "signin-browser-token", "signin-browser-token-note"]
        for name in children:
            assert markup.nodes[name]["ancestors"][-1] is group
        assert [markup.order.index(name) for name in children] == sorted(markup.order.index(name) for name in children)
        assert markup.order.index("signin-mode-browser-token") < markup.order.index(children[0])
        assert markup.order.index(children[-1]) < markup.order.index("signin-submit")

    def test_token_field_keeps_native_associations_and_no_value_attribute(
        self, portal_client: FlaskClient, portal_app: Flask
    ) -> None:
        """Keep the masked field name, note, and label association unchanged."""
        portal_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = True
        markup = SigninMarkup(portal_client.get("/auth/signin").get_data(as_text=True))
        field = markup.nodes["signin-browser-token"]["attrs"]
        label = markup.nodes["signin-browser-token-label"]["attrs"]
        assert label["for"] == "signin-browser-token"
        assert field["type"] == "password" and field["name"] == "token"
        assert field["aria-describedby"] == "signin-browser-token-note"
        assert field["autocomplete"] == "off" and field["spellcheck"] == "false"
        assert "disabled" in field and "value" not in field and "tabindex" not in field
        assert "required" in markup.nodes["signin-email"]["attrs"]
        assert "required" in markup.nodes["signin-password"]["attrs"]

    @pytest.mark.parametrize("environment_present", [True, False])
    def test_disabled_startup_gate_renders_no_browser_token_control(
        self, portal_client: FlaskClient, portal_app: Flask, monkeypatch: pytest.MonkeyPatch, environment_present: bool
    ) -> None:
        """Preserve native provider and environment choices without exposing a token."""
        for name in ("MIST_APITOKEN", "MIST_API_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        if environment_present:
            monkeypatch.setenv("MIST_APITOKEN", "fake-environment-token-for-issue3295-only")
        portal_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = False
        response = portal_client.get("/auth/signin")
        html = response.get_data(as_text=True)
        markup = SigninMarkup(html)
        assert response.status_code == 200
        assert all(
            name not in markup.nodes
            for name in (
                "signin-browser-token-group",
                "signin-browser-token",
                "signin-mode-browser-token",
            )
        )
        assert ("signin-mode-token" in markup.nodes) is environment_present
        assert ("required" in markup.nodes["signin-password"]["attrs"]) is not environment_present
        assert markup.nodes["signin-mode-provider"]["attrs"]["value"] == "provider_login"
        assert "fake-environment-token-for-issue3295-only" not in html

    def test_refusal_markup_stays_escaped_and_uses_the_existing_alert_classes(self, portal_app: Flask) -> None:
        """Keep the empty alert hidden and prevent executable refusal markup."""
        with portal_app.test_request_context("/auth/signin"):
            empty = render_template("auth/signin.html")
            refused = render_template("auth/signin.html", error_message="<strong>synthetic refusal</strong>")
        assert "hidden" in SigninMarkup(empty).nodes["signin-error"]["attrs"]
        assert "hidden" not in SigninMarkup(refused).nodes["signin-error"]["attrs"]
        assert "&lt;strong&gt;synthetic refusal&lt;/strong&gt;" in refused
        assert "<strong>synthetic refusal</strong>" not in refused
        assert SigninMarkup(refused).nodes["signin-error"]["attrs"]["class"] == "alert alert-danger flash-danger"


class TestSigninStylesheetContract:
    """Keep the shared Warning rule narrow and every signal word unchanged."""

    def test_danger_alert_reuses_the_common_prefix_weight(self) -> None:
        """Use the same declaration for the sign-in alert and error-page flash."""
        root = Path(__file__).resolve().parents[3]
        css = (root / "src/upgrade_portal/app/assets/static/css/portal.css").read_text(encoding="utf-8")
        rule = re.search(r"\.flash-item::before\s*,\s*\.flash-danger\.alert::before\s*\{([^}]+)\}", css)
        assert rule is not None and "font-weight: 700;" in rule.group(1)
        assert "white-space: nowrap;" in rule.group(1)
        danger = re.search(r"\.flash-danger::before\s*\{([^}]+)\}", css)
        assert danger is not None and 'content: "Warning: ";' in danger.group(1)
        assert "[hidden]::before," in css and "content: none !important;" in css

    def test_local_group_rules_do_not_redefine_shared_mode_layout(self) -> None:
        """Limit the geometry change to the new group and its own label."""
        root = Path(__file__).resolve().parents[3]
        css = (root / "src/upgrade_portal/app/assets/static/css/portal.css").read_text(encoding="utf-8")
        label = re.search(r"\.signin-token-group\s*>\s*\.form-label\s*\{([^}]+)\}", css)
        assert label is not None and "display: block;" in label.group(1)
        mode = re.search(r"\.bubble-group\s*\{([^}]+)\}", css)
        assert mode is not None and "display: flex;" in mode.group(1) and "flex-wrap: wrap;" in mode.group(1)
