"""Unit tests for the web portal webhook signature check.

Regression cover for issue #1907. The route read ``WEBHOOK_SECRET`` from
the Flask config, but no code ever wrote that key. The secret was always
the empty string, and the empty string is false, so the guard
``if secret and not _verify_signature(...)`` short circuited. The check
never ran. Any client that could reach the portal could post an unsigned
body and reach the dispatch path.

These tests hold the fail-closed contract:

* A request with no signature receives code 403 when the secret is set.
* A request with a wrong signature receives code 403.
* A request receives code 503 when the secret is absent or empty.
* A rejected request never reaches the dispatch path.
* The app factory reads the secret from the environment.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest
from flask import Flask

from web_portal.app import WebPortalApp
from web_portal.routes import webhooks as webhooks_module
from web_portal.routes.webhooks import webhook_bp

# WHY: a fixed secret keeps every signature in these tests reproducible.
_SECRET = "0123456789abcdef0123456789abcdef"

# WHY: the audit topic reaches the router, so it proves the dispatch path.
_AUDIT_BODY = json.dumps({"topic": "audits", "events": [{"id": "event-1"}]}).encode()

_JSON_HEADERS = {"Content-Type": "application/json"}


class _RecordingRouter:
    """Record every audit event that the route dispatches."""

    def __init__(self) -> None:
        """Start with an empty record of dispatched events."""
        self.audit_events: list[dict] = []

    def handle_webhook_audit(self, event: dict) -> None:
        """Store one dispatched audit event for a later assertion."""
        self.audit_events.append(event)


def _sign(body: bytes, secret: str) -> str:
    """Return the HMAC-SHA256 hex digest that the route expects."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _build_test_app(secret: Any = None, router: Any = None) -> Flask:
    """Build a minimal Flask app that serves the webhook blueprint."""
    app = Flask(__name__)  # WHY: a bare app avoids the portal factory and its side effects.
    if secret is not None:  # WHY: None models a config key that no code ever wrote.
        app.config["WEBHOOK_SECRET"] = secret
    app.config["DB_ROUTER"] = router  # WHY: the route reads this key to find the dispatch target.
    app.register_blueprint(webhook_bp)  # WHY: register the route under test only.
    return app


@pytest.fixture
def recording_router() -> _RecordingRouter:
    """Return a router that records the events the route dispatches."""
    return _RecordingRouter()


class TestUnsignedRequests:
    """Verify the route rejects a request that carries no signature."""

    def test_a_post_with_no_signature_header_is_rejected(self, recording_router: _RecordingRouter) -> None:
        """A missing X-Mist-Signature header must produce code 403."""
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=_JSON_HEADERS)

        assert response.status_code == 403, "An unsigned webhook must never receive a success reply"
        assert response.get_json()["error"] == "invalid signature"

    def test_a_post_with_no_signature_never_reaches_the_dispatch_path(self, recording_router: _RecordingRouter) -> None:
        """An unsigned payload must not reach the database router."""
        client = _build_test_app(_SECRET, recording_router).test_client()

        client.post("/api/webhook", data=_AUDIT_BODY, headers=_JSON_HEADERS)

        assert recording_router.audit_events == [], "A forged payload must not reach the audit handler"

    def test_an_empty_signature_header_is_rejected(self, recording_router: _RecordingRouter) -> None:
        """An empty signature value must produce code 403."""
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": ""})
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 403
        assert recording_router.audit_events == []


class TestSignatureVerification:
    """Verify the route accepts a valid signature and rejects a wrong one."""

    def test_a_valid_signature_is_accepted(self, recording_router: _RecordingRouter) -> None:
        """A correct digest must produce code 200 and reach the router."""
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, _SECRET)})
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"
        assert recording_router.audit_events == [{"id": "event-1"}]

    def test_a_wrong_signature_is_rejected_with_403(self, recording_router: _RecordingRouter) -> None:
        """A digest from another secret must produce code 403."""
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, "the-wrong-secret")})
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 403
        assert recording_router.audit_events == []

    def test_a_signature_for_a_different_body_is_rejected(self, recording_router: _RecordingRouter) -> None:
        """A replayed digest must not authenticate a changed body."""
        tampered = json.dumps({"topic": "audits", "events": [{"id": "forged"}]}).encode()
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, _SECRET)})
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=tampered, headers=headers)

        assert response.status_code == 403
        assert recording_router.audit_events == []

    def test_the_route_compares_the_digest_in_constant_time(
        self, recording_router: _RecordingRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The route must compare with hmac.compare_digest.

        A comparison with ``==`` stops at the first wrong byte, so an
        attacker can recover the digest one byte at a time.
        """
        calls: list[tuple[Any, Any]] = []
        real_compare = hmac.compare_digest  # WHY: keep the real behavior, and only count the calls.

        def _recording_compare(left: Any, right: Any) -> bool:
            """Record one comparison and return the real result."""
            calls.append((left, right))
            return bool(real_compare(left, right))

        monkeypatch.setattr(webhooks_module.hmac, "compare_digest", _recording_compare)
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, _SECRET)})
        client = _build_test_app(_SECRET, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 200
        assert calls, "The route must call hmac.compare_digest to compare the signature"


class TestMissingSecret:
    """Verify the route fails closed when no secret is configured."""

    @pytest.mark.parametrize(
        "secret",
        [None, "", "   "],
        ids=["absent-key", "empty-string", "whitespace-only"],
    )
    def test_an_unconfigured_secret_returns_503(self, secret: Any, recording_router: _RecordingRouter) -> None:
        """An unusable secret must produce code 503, not a success reply."""
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, _SECRET)})
        client = _build_test_app(secret, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 503, "An unconfigured receiver must refuse the request"
        assert recording_router.audit_events == [], "An unverified payload must not reach the audit handler"

    def test_an_unconfigured_secret_rejects_an_unsigned_post(self, recording_router: _RecordingRouter) -> None:
        """The defect case must fail closed rather than accept the body."""
        client = _build_test_app(None, recording_router).test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=_JSON_HEADERS)

        assert response.status_code != 200, "An unsigned post must never receive a success reply"
        assert response.status_code == 503
        assert recording_router.audit_events == []


class TestVerifySignatureHelper:
    """Verify the helper that computes and compares the digest."""

    def test_an_empty_secret_never_verifies(self) -> None:
        """An empty secret must fail, because it authenticates nobody."""
        assert _verify(_AUDIT_BODY, _sign(_AUDIT_BODY, ""), "") is False

    def test_an_empty_signature_never_verifies(self) -> None:
        """An empty signature must fail, because it matches no digest."""
        assert _verify(_AUDIT_BODY, "", _SECRET) is False

    def test_a_correct_signature_verifies(self) -> None:
        """A digest built from the same secret and body must pass."""
        assert _verify(_AUDIT_BODY, _sign(_AUDIT_BODY, _SECRET), _SECRET) is True


def _verify(body: bytes, signature: str, secret: str) -> bool:
    """Call the module helper under test by its private name."""
    return webhooks_module._verify_signature(body, signature, secret)


class TestAppFactoryWebhookConfig:
    """Verify the app factory loads the webhook settings from the environment."""

    def test_the_factory_reads_the_secret_from_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The factory must copy WEBHOOK_SECRET into the app config."""
        monkeypatch.setenv("WEBHOOK_SECRET", _SECRET)
        app = Flask(__name__)

        WebPortalApp._load_webhook_config(app)

        assert app.config["WEBHOOK_SECRET"] == _SECRET

    def test_the_factory_stores_an_empty_secret_when_the_variable_is_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An absent variable must leave an empty secret, not a missing key."""
        monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
        app = Flask(__name__)

        WebPortalApp._load_webhook_config(app)

        assert app.config["WEBHOOK_SECRET"] == ""
        assert app.config["WEBHOOK_ENABLED"] is True

    def test_the_factory_disables_the_receiver_on_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WEBHOOK_ENABLED=false must turn the receiver off."""
        monkeypatch.setenv("WEBHOOK_ENABLED", "false")
        app = Flask(__name__)

        WebPortalApp._load_webhook_config(app)

        assert app.config["WEBHOOK_ENABLED"] is False

    def test_a_disabled_receiver_serves_no_webhook_route(self) -> None:
        """A disabled receiver must not register the route at all."""
        app = Flask(__name__)
        app.config["WEBHOOK_ENABLED"] = False

        WebPortalApp._register_webhook_blueprint(app)

        assert "/api/webhook" not in {rule.rule for rule in app.url_map.iter_rules()}

    def test_an_enabled_receiver_serves_the_webhook_route(self) -> None:
        """An enabled receiver must register the route."""
        app = Flask(__name__)
        app.config["WEBHOOK_ENABLED"] = True

        WebPortalApp._register_webhook_blueprint(app)

        assert "/api/webhook" in {rule.rule for rule in app.url_map.iter_rules()}


class TestCsrfExemption:
    """Verify the webhook route stays reachable behind CSRF protection.

    The portal protects every form post with flask-wtf. Mist Cloud holds
    no CSRF token, so an unexempt route would answer 400 for every real
    webhook and the HMAC check would never run.
    """

    @staticmethod
    def _build_protected_app() -> Flask:
        """Build an app that carries CSRF protection and the webhook route."""
        from flask_wtf.csrf import CSRFProtect

        app = Flask(__name__)
        app.secret_key = "test-secret-key"  # WHY: flask-wtf signs the CSRF token with this key.
        app.config["WEBHOOK_ENABLED"] = True
        app.config["WEBHOOK_SECRET"] = _SECRET
        csrf = CSRFProtect()
        csrf.init_app(app)
        app.config["csrf"] = csrf  # WHY: SecurityMiddleware stores the instance under this key.
        WebPortalApp._register_webhook_blueprint(app)
        return app

    def test_a_signed_post_passes_the_csrf_guard(self) -> None:
        """A signed webhook must reach the route, not a CSRF rejection."""
        headers = dict(_JSON_HEADERS, **{"X-Mist-Signature": _sign(_AUDIT_BODY, _SECRET)})
        client = self._build_protected_app().test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=headers)

        assert response.status_code == 200, "CSRF protection must not block a signed machine request"

    def test_an_unsigned_post_still_receives_403(self) -> None:
        """The CSRF exemption must not weaken the signature check."""
        client = self._build_protected_app().test_client()

        response = client.post("/api/webhook", data=_AUDIT_BODY, headers=_JSON_HEADERS)

        assert response.status_code == 403
