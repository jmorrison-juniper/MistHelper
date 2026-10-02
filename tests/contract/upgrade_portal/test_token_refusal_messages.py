"""Pin token refusal text, privacy, and unchanged sign-in responses offline."""

from __future__ import annotations

import html
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from unittest.mock import create_autospec

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

TOKEN_SENTINEL = "fake-3290-token-that-must-not-reach-a-response"
PASSWORD_SENTINEL = "fake-3290-password-that-must-not-reach-a-response"
EMAIL = "probe.3290@example.invalid"
TOKEN_MESSAGE = "The portal could not sign you in. Check the token, then try again."
EMPTY_MESSAGE = "The token field is empty. Type your token, then try again."
PAIR_MESSAGE = "The portal could not sign you in. Check the address and the password, then try again."
PASSWORD_MESSAGE = "The portal received no password. Type your password, then try again."
ENVIRONMENT_FIELDS = {"mode": "environment_token", "email": EMAIL, "password": ""}
BROWSER_FIELDS = {"mode": "browser_token", "token": TOKEN_SENTINEL}
ALERT_PATTERN = re.compile(r'data-testid="signin-error"[^>]*>([^<]*)</div>')


class TokenCloudStandIn:
    """Keep only safe boundary names and raise controlled offline faults."""

    def __init__(self) -> None:
        """Start each request sequence with no credential state."""
        self.stage = ""
        self.calls: list[str] = []

    def environment_session(self, host: str) -> TokenCloudStandIn:
        """Replace the environment-token cloud builder."""
        self.calls.append("environment")
        if self.stage == "environment-cloud":
            raise ValueError(f"The stand-in refused {TOKEN_SENTINEL}.")
        return self

    def browser_session(self, host: str, token: str) -> TokenCloudStandIn:
        """Discard the submitted value after the shaped cloud boundary."""
        self.calls.append("browser")
        if self.stage == "browser-cloud":
            raise ValueError(f"The stand-in refused {token}.")
        return self

    def token_identity(self, session: object) -> dict[str, str]:
        """Replace the token identity read without a cloud request."""
        self.calls.append("identity")
        if self.stage == "browser-identity":
            raise ValueError(f"The identity read refused {TOKEN_SENTINEL}.")
        return {"name": "" if self.stage == "browser-owner" else "fake-3290-token-owner"}

    def login_with_return(self, two_factor: str = "") -> dict[str, bool]:
        """Refuse the provider pair through its existing classifier."""
        self.calls.append("provider")
        return {"authenticated": False}


@dataclass(frozen=True)
class TokenContractContext:
    """Keep the test client and safe observation tools together."""

    client: FlaskClient
    cloud: TokenCloudStandIn
    captured: pytest.LogCaptureFixture
    monkeypatch: pytest.MonkeyPatch
    registry_size: int


@dataclass(frozen=True)
class RefusalCase:
    """Describe one existing failure without changing a production check."""

    name: str
    body: dict[str, str]
    allowed: bool
    calls: tuple[str, ...]
    message: str


@pytest.fixture(autouse=True)
def isolated_token_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace inherited Mist tokens before the application factory executes."""
    monkeypatch.setenv("MIST_APITOKEN", TOKEN_SENTINEL)
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)


@pytest.fixture
def token_context(
    portal_app: Flask, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[TokenContractContext]:
    """Install shaped stand-ins and remove only this test's registry entries."""
    cloud = TokenCloudStandIn()
    portal_app.config.update(
        WTF_CSRF_ENABLED=False,
        BROWSER_TOKEN_SIGNIN_ALLOWED=True,
        CLOUD_TOKEN_SESSION=cloud.environment_session,
        CLOUD_BROWSER_TOKEN_SESSION=cloud.browser_session,
        CLOUD_TOKEN_IDENTITY=cloud.token_identity,
        CLOUD_LOGIN=lambda actor_email, password, host: cloud,
    )
    caplog.set_level(logging.DEBUG, logger="src.upgrade_portal")
    initial_keys = set(identity.SESSION_REGISTRY._sessions)
    try:
        with portal_app.test_client() as client:
            yield TokenContractContext(client, cloud, caplog, monkeypatch, identity.SESSION_REGISTRY.owner_count())
    finally:
        for key in set(identity.SESSION_REGISTRY._sessions) - initial_keys:
            identity.SESSION_REGISTRY.drop(key)


@pytest.fixture(
    params=[
        RefusalCase("environment-missing", ENVIRONMENT_FIELDS, True, ("environment",), TOKEN_MESSAGE),
        RefusalCase("environment-empty", ENVIRONMENT_FIELDS, True, ("environment",), TOKEN_MESSAGE),
        RefusalCase("environment-spaces", ENVIRONMENT_FIELDS, True, ("environment",), TOKEN_MESSAGE),
        RefusalCase("environment-cloud", ENVIRONMENT_FIELDS, True, ("environment",), TOKEN_MESSAGE),
        RefusalCase("environment-registry", ENVIRONMENT_FIELDS, True, ("environment",), TOKEN_MESSAGE),
        RefusalCase("browser-disabled", BROWSER_FIELDS, False, (), TOKEN_MESSAGE),
        RefusalCase("browser-disabled-empty", {"mode": "browser_token", "token": ""}, False, (), TOKEN_MESSAGE),
        RefusalCase("browser-cloud", BROWSER_FIELDS, True, ("browser",), TOKEN_MESSAGE),
        RefusalCase("browser-identity", BROWSER_FIELDS, True, ("browser", "identity"), TOKEN_MESSAGE),
        RefusalCase("browser-owner", BROWSER_FIELDS, True, ("browser", "identity"), TOKEN_MESSAGE),
        RefusalCase("browser-registry", BROWSER_FIELDS, True, ("browser", "identity"), TOKEN_MESSAGE),
        RefusalCase("browser-missing", {"mode": "browser_token"}, True, (), EMPTY_MESSAGE),
        RefusalCase("browser-empty", {"mode": "browser_token", "token": ""}, True, (), EMPTY_MESSAGE),
        RefusalCase("browser-spaces", {"mode": "browser_token", "token": " \t "}, True, (), EMPTY_MESSAGE),
    ],
    ids=lambda case: case.name,
)
def refusal_case(request: pytest.FixtureRequest, token_context: TokenContractContext) -> RefusalCase:
    """Select only the existing cause that this route case must exercise."""
    case: RefusalCase = request.param
    token_context.cloud.stage = case.name
    token_context.client.application.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = case.allowed
    if case.name in ("environment-missing", "environment-empty", "environment-spaces"):
        token_context.monkeypatch.delenv("MIST_APITOKEN")
        if case.name != "environment-missing":
            token_context.monkeypatch.setenv("MIST_APITOKEN", "" if case.name == "environment-empty" else " \t ")
    if case.name in ("environment-registry", "browser-registry"):
        fault = ValueError(f"The session stand-in refused {TOKEN_SENTINEL}.")
        token_context.monkeypatch.setattr(identity, "sign_in", create_autospec(identity.sign_in, side_effect=fault))
    return case


@pytest.mark.parametrize("representation", ["application/json", "text/html"])
class TestTokenRefusalContracts:
    """Check real route selection and the existing JSON and HTML contracts."""

    def test_refusal_sentence(
        self, token_context: TokenContractContext, refusal_case: RefusalCase, representation: str
    ) -> None:
        """Every token refusal keeps its code and names the selected input."""
        arguments = {"json": refusal_case.body} if representation == "application/json" else {"data": refusal_case.body}
        response = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        assert response.status_code == 400
        assert tuple(token_context.cloud.calls) == refusal_case.calls
        assert identity.SESSION_REGISTRY.owner_count() == token_context.registry_size
        self._assert_private(token_context, response)
        self._assert_message(response, refusal_case.message, representation)

    @pytest.mark.parametrize(
        "scenario",
        [(PASSWORD_SENTINEL, PAIR_MESSAGE, ("provider",)), ("", PASSWORD_MESSAGE, ())],
        ids=["rejected-pair", "empty-password"],
    )
    def test_provider_sentences_stay_unchanged(
        self, token_context: TokenContractContext, representation: str, scenario: tuple[str, str, tuple[str, ...]]
    ) -> None:
        """Token-specific text must not replace the provider cures."""
        password, message, calls = scenario
        body = {"mode": "provider_login", "email": EMAIL, "password": password}
        arguments = {"json": body} if representation == "application/json" else {"data": body}
        response = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        assert response.status_code == 400
        assert tuple(token_context.cloud.calls) == calls
        self._assert_private(token_context, response)
        self._assert_message(response, message, representation)

    @pytest.mark.parametrize("mode", ["environment_token", "browser_token"])
    def test_accepted_tokens_keep_the_next_destination(
        self, token_context: TokenContractContext, representation: str, mode: str
    ) -> None:
        """Each token mode keeps its success response and safe session record."""
        body = ENVIRONMENT_FIELDS if mode == "environment_token" else BROWSER_FIELDS
        arguments = {"json": body} if representation == "application/json" else {"data": body}
        response = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        if representation == "application/json":
            assert response.status_code == 200
            assert response.get_json() == {"next": "/select/org"}
        else:
            assert response.status_code == 303
            assert response.headers["Location"] == "/select/org"
        assert identity.SESSION_REGISTRY.owner_count() == token_context.registry_size + 1
        assert tuple(token_context.cloud.calls) == (
            ("environment",) if mode == "environment_token" else ("browser", "identity")
        )
        self._assert_private(token_context, response)
        with token_context.client.session_transaction() as session:
            record = identity.SESSION_REGISTRY.get(session[identity.SESSION_OWNER_KEY])
        if record is None:
            raise AssertionError("The accepted token created no registered session.")
        assert record.credential_mode.value == mode
        assert TOKEN_SENTINEL not in repr(vars(record.cloud_session))

    @staticmethod
    def _assert_message(response: TestResponse, message: str, representation: str) -> None:
        """Pin the JSON envelope or the exact real sign-in alert text."""
        if representation == "application/json":
            assert response.get_json() == {"error": {"code": "bad_credentials", "message": message}}
        else:
            assert response.mimetype == "text/html"
            match = ALERT_PATTERN.search(response.get_data(as_text=True))
            if match is None:
                raise AssertionError("The refusal page contains no sign-in alert.")
            assert html.unescape(match.group(1)).strip() == message
            assert 'data-testid="signin-submit"' in response.get_data(as_text=True)

    @staticmethod
    def _assert_private(context: TokenContractContext, response: TestResponse) -> None:
        """Inspect credential surfaces, including raw captured log metadata."""
        with context.client.session_transaction() as session:
            metadata = dict(session)
        surfaces = (
            response.get_data(as_text=True),
            str(response.headers),
            repr(context.client._cookies),
            repr(metadata),
            repr([vars(record) for record in context.captured.records]),
            repr(list(identity.SESSION_REGISTRY._sessions.values())),
        )
        for sentinel in (TOKEN_SENTINEL, PASSWORD_SENTINEL):
            for surface in surfaces:
                assert sentinel not in surface, "A test credential reached a response, session, or log."


@pytest.mark.parametrize("representation", ["application/json", "text/html"])
class TestTokenRefusalAntiProbe:
    """Keep absence, disabled mode, and rejection indistinguishable in text."""

    def test_environment_absence_and_cloud_rejection_share_the_message(
        self, token_context: TokenContractContext, representation: str
    ) -> None:
        """The response must not expose which environment-token check failed."""
        token_context.monkeypatch.delenv("MIST_APITOKEN")
        arguments = (
            {"json": ENVIRONMENT_FIELDS} if representation == "application/json" else {"data": ENVIRONMENT_FIELDS}
        )
        absent = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        token_context.monkeypatch.setenv("MIST_APITOKEN", TOKEN_SENTINEL)
        token_context.cloud.stage = "environment-cloud"
        rejected = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        assert absent.status_code == rejected.status_code == 400
        TestTokenRefusalContracts._assert_message(absent, TOKEN_MESSAGE, representation)
        TestTokenRefusalContracts._assert_message(rejected, TOKEN_MESSAGE, representation)
        if representation == "application/json":
            assert absent.get_json() == rejected.get_json()
        assert token_context.cloud.calls == ["environment", "environment"]
        assert identity.SESSION_REGISTRY.owner_count() == token_context.registry_size

    def test_disabled_and_rejected_browser_tokens_share_the_message(
        self, token_context: TokenContractContext, representation: str
    ) -> None:
        """The selected mode may appear in text, but its failure cause must not."""
        token_context.client.application.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = False
        arguments = {"json": BROWSER_FIELDS} if representation == "application/json" else {"data": BROWSER_FIELDS}
        disabled = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        token_context.client.application.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = True
        token_context.cloud.stage = "browser-cloud"
        rejected = token_context.client.post("/auth/signin", headers={"Accept": representation}, **arguments)
        assert disabled.status_code == rejected.status_code == 400
        TestTokenRefusalContracts._assert_message(disabled, TOKEN_MESSAGE, representation)
        TestTokenRefusalContracts._assert_message(rejected, TOKEN_MESSAGE, representation)
        if representation == "application/json":
            assert disabled.get_json() == rejected.get_json()
        assert token_context.cloud.calls == ["browser"]
        assert identity.SESSION_REGISTRY.owner_count() == token_context.registry_size
