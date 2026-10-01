"""Check token refusal decisions without a cloud or a template dependency."""

from __future__ import annotations

from unittest.mock import create_autospec

import pytest
from flask import Flask, Response

from src.upgrade_portal.app.routes import auth
from src.upgrade_portal.runtime import identity

TOKEN_SENTINEL = "fake-3290-token-that-must-not-reach-a-response"
PAIR_MESSAGE = "The portal could not sign you in. Check the address and the password, then try again."
TOKEN_MESSAGE = "The portal could not sign you in. Check the token, then try again."
EMPTY_MESSAGE = "The token field is empty. Type your token, then try again."


@pytest.fixture
def message_app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    """Keep message decisions active and replace only page rendering."""
    app = Flask(__name__)
    app.config[auth.DEPENDENCY_ROWS_KEY] = []
    for name in ("MIST_APITOKEN", "MIST_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(auth, "render_page", lambda name, **context: f"<p>{context['error_message']}</p>")
    return app


@pytest.mark.parametrize("representation", ["application/json", "text/html"])
class TestTokenRefusalMessages:
    """Pin the selected message and preserve the provider default."""

    def test_default_message_still_names_the_address_and_password(
        self, message_app: Flask, representation: str
    ) -> None:
        """Explicit token messages must not change provider refusals."""
        with message_app.test_request_context("/auth/signin", headers={"Accept": representation}):
            response, status = auth.credential_refusal()
        assert status == 400
        self._assert_refusal(response, status, PAIR_MESSAGE, representation)

    @pytest.mark.parametrize("message", [TOKEN_MESSAGE, EMPTY_MESSAGE])
    def test_supplied_message_keeps_the_existing_envelope(
        self, message_app: Flask, representation: str, message: str
    ) -> None:
        """The existing helper preserves each fixed token sentence."""
        with message_app.test_request_context("/auth/signin", headers={"Accept": representation}):
            response, status = auth.credential_refusal(message)
        assert status == 400
        self._assert_refusal(response, status, message, representation)

    def test_environment_failure_selects_the_token_message(self, message_app: Flask, representation: str) -> None:
        """A fault containing a fake token must produce fixed public text."""
        owner = identity.build_owner("probe.3290@example.invalid", "probe-browser-3290-Ab12_cd34")
        builder = create_autospec(auth.default_token_session, side_effect=ValueError(TOKEN_SENTINEL))
        with message_app.test_request_context("/auth/signin", headers={"Accept": representation}):
            response, status = auth.finish_token_session(owner, builder, "api.mist.com", owner.browser_id)
        self._assert_refusal(response, status, TOKEN_MESSAGE, representation)
        assert builder.call_count == 1
        assert TOKEN_SENTINEL not in response.get_data(as_text=True)

    @pytest.mark.parametrize(
        "scenario",
        [
            (False, {"token": TOKEN_SENTINEL}, TOKEN_MESSAGE),
            (False, {}, TOKEN_MESSAGE),
            (True, {}, EMPTY_MESSAGE),
            (True, {"token": ""}, EMPTY_MESSAGE),
            (True, {"token": " \t "}, EMPTY_MESSAGE),
            (True, {"token": TOKEN_SENTINEL}, TOKEN_MESSAGE),
        ],
        ids=["disabled", "disabled-empty", "missing", "empty", "spaces", "rejected"],
    )
    def test_browser_failure_selects_the_message_before_any_identity_read(
        self, message_app: Flask, representation: str, scenario: tuple[bool, dict[str, str], str]
    ) -> None:
        """Startup denial keeps precedence over the empty-field cure."""
        enabled, fields, message = scenario
        builder = create_autospec(auth.default_browser_token_session, side_effect=ValueError(TOKEN_SENTINEL))
        reader = create_autospec(auth.default_token_identity)
        message_app.config.update(
            BROWSER_TOKEN_SIGNIN_ALLOWED=enabled,
            CLOUD_BROWSER_TOKEN_SESSION=builder,
            CLOUD_TOKEN_IDENTITY=reader,
        )
        with message_app.test_request_context(
            "/auth/signin", method="POST", data=fields, headers={"Accept": representation}
        ):
            response, status = auth.start_browser_token_session()
        self._assert_refusal(response, status, message, representation)
        assert builder.call_count == int(enabled and bool(fields.get("token", "").strip()))
        assert reader.call_count == 0

    @staticmethod
    def _assert_refusal(response: Response, status: int, message: str, representation: str) -> None:
        """Compare the complete message in each existing response form."""
        assert status == 400
        if representation == "application/json":
            assert response.get_json() == {"error": {"code": "bad_credentials", "message": message}}
        else:
            assert response.mimetype == "text/html"
            assert response.get_data(as_text=True) == f"<p>{message}</p>"
