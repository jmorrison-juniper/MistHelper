"""Tests for the web portal IP allowlist and the trusted proxy setting.

Issue #1857 reports that a client-supplied `X-Forwarded-For` header defeats the
`PORTAL_ALLOWED_IPS` allowlist. These tests hold the contract for the fix. The
allowlist reads the peer address from `request.remote_addr`. The portal reads
the forwarded header only when the peer address matches `PORTAL_TRUSTED_PROXIES`.
"""

import logging

import pytest
from flask import Flask

from web_portal.services.config import PortalConfigLoader, SecurityMiddleware

BLOCKED_PEER = "203.0.113.9"
ALLOWED_CLIENT = "10.0.0.1"
PROXY_PEER = "127.0.0.1"
ALLOWLIST_TEXT = "10.0.0.0/24"


def _build_app(allowed_ips: list, trusted_proxies: list | None) -> Flask:
    """Build a small Flask app that carries the security middleware."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["WTF_CSRF_ENABLED"] = False

    @app.route("/")
    def index():
        return "portal home"

    middleware = SecurityMiddleware()
    middleware.apply(app, allowed_ips, trusted_proxies)
    return app


def _parse(text: str) -> list:
    """Turn a comma-separated setting value into a network list."""
    return PortalConfigLoader.parse_networks(text, "PORTAL_ALLOWED_IPS")


@pytest.fixture
def allowlist() -> list:
    """Return the parsed allowlist that every test shares."""
    return _parse(ALLOWLIST_TEXT)


def test_forged_forwarded_header_from_blocked_peer_returns_403(allowlist):
    """A forged header must not change the allowlist decision."""
    app = _build_app(allowlist, [])
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": BLOCKED_PEER},
    )
    assert response.status_code == 403


def test_allowed_peer_without_header_returns_200(allowlist):
    """An allowed peer address reaches the portal with no header present."""
    app = _build_app(allowlist, [])
    client = app.test_client()
    response = client.get("/", environ_base={"REMOTE_ADDR": ALLOWED_CLIENT})
    assert response.status_code == 200


def test_blocked_peer_without_header_returns_403(allowlist):
    """The decision uses the peer address when no trusted proxy is set."""
    app = _build_app(allowlist, [])
    client = app.test_client()
    response = client.get("/", environ_base={"REMOTE_ADDR": BLOCKED_PEER})
    assert response.status_code == 403


def test_trusted_proxy_peer_uses_forwarded_address(allowlist):
    """A trusted proxy peer makes the portal read the forwarded address."""
    app = _build_app(allowlist, _parse(PROXY_PEER))
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": PROXY_PEER},
    )
    assert response.status_code == 200


def test_trusted_proxy_peer_blocks_forwarded_address_outside_allowlist(allowlist):
    """The forwarded address still faces the allowlist check."""
    app = _build_app(allowlist, _parse(PROXY_PEER))
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": BLOCKED_PEER},
        environ_base={"REMOTE_ADDR": PROXY_PEER},
    )
    assert response.status_code == 403


def test_trusted_proxy_reads_the_rightmost_forwarded_entry(allowlist):
    """The rightmost entry is the address that the trusted proxy observed."""
    app = _build_app(allowlist, _parse(PROXY_PEER))
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": f"{ALLOWED_CLIENT}, {BLOCKED_PEER}"},
        environ_base={"REMOTE_ADDR": PROXY_PEER},
    )
    assert response.status_code == 403


def test_trusted_proxy_accepts_a_cidr_range(allowlist):
    """A CIDR range names a trusted proxy just as a plain address does."""
    app = _build_app(allowlist, _parse("127.0.0.0/8"))
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": PROXY_PEER},
    )
    assert response.status_code == 200


def test_untrusted_peer_ignores_the_header_even_when_proxies_exist(allowlist):
    """Only a trusted proxy peer unlocks the forwarded header."""
    app = _build_app(allowlist, _parse(PROXY_PEER))
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": BLOCKED_PEER},
    )
    assert response.status_code == 403


def test_blocked_request_log_records_the_peer_address(allowlist, caplog):
    """The audit trail always names the real peer address."""
    app = _build_app(allowlist, _parse(PROXY_PEER))
    client = app.test_client()
    with caplog.at_level(logging.WARNING):
        client.get(
            "/",
            headers={"X-Forwarded-For": BLOCKED_PEER},
            environ_base={"REMOTE_ADDR": PROXY_PEER},
        )
    assert PROXY_PEER in caplog.text
    assert BLOCKED_PEER in caplog.text


def test_apply_reads_the_trusted_proxy_setting_from_the_environment(allowlist, monkeypatch):
    """A caller that omits the argument still gets the configured proxies."""
    monkeypatch.setenv("PORTAL_TRUSTED_PROXIES", PROXY_PEER)
    app = _build_app(allowlist, None)
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": PROXY_PEER},
    )
    assert response.status_code == 200


def test_apply_defaults_to_no_trusted_proxy_when_the_environment_is_empty(allowlist, monkeypatch):
    """An empty environment leaves the forwarded header without any trust."""
    monkeypatch.delenv("PORTAL_TRUSTED_PROXIES", raising=False)
    app = _build_app(allowlist, None)
    client = app.test_client()
    response = client.get(
        "/",
        headers={"X-Forwarded-For": ALLOWED_CLIENT},
        environ_base={"REMOTE_ADDR": BLOCKED_PEER},
    )
    assert response.status_code == 403


def test_loader_defaults_the_trusted_proxy_setting_to_empty(monkeypatch):
    """The new setting ships with an empty default value."""
    monkeypatch.delenv("PORTAL_TRUSTED_PROXIES", raising=False)
    config = PortalConfigLoader().load_config()
    assert config["trusted_proxies"] == []


def test_loader_parses_a_plain_address_and_a_cidr_range(monkeypatch):
    """The loader accepts both forms in one comma-separated value."""
    monkeypatch.setenv("PORTAL_TRUSTED_PROXIES", "127.0.0.1, 10.9.0.0/16")
    config = PortalConfigLoader().load_config()
    assert [str(network) for network in config["trusted_proxies"]] == [
        "127.0.0.1/32",
        "10.9.0.0/16",
    ]


def test_loader_drops_an_invalid_trusted_proxy_entry(monkeypatch):
    """An invalid entry never becomes a trusted proxy."""
    monkeypatch.setenv("PORTAL_TRUSTED_PROXIES", "not-an-address")
    config = PortalConfigLoader().load_config()
    assert config["trusted_proxies"] == []


def test_loader_reports_the_position_of_an_invalid_entry(monkeypatch, caplog):
    """The warning names the position, so no setting text reaches the log.

    CodeQL rule `py/clear-text-logging-sensitive-data` reported the old message,
    because an environment value can hold a secret. The message must therefore
    hold the position of the bad entry and the name of the setting only.
    """
    monkeypatch.setenv("PORTAL_TRUSTED_PROXIES", "127.0.0.1,super-secret-value")
    with caplog.at_level(logging.WARNING):
        config = PortalConfigLoader().load_config()
    assert [str(network) for network in config["trusted_proxies"]] == ["127.0.0.1/32"]
    assert "super-secret-value" not in caplog.text
    assert "Entry 2 of the PORTAL_TRUSTED_PROXIES setting" in caplog.text
