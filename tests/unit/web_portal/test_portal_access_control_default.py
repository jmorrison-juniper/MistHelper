"""Prove that the portal refuses a remote client when no allowlist is set.

The portal has no user authentication. `PORTAL_ALLOWED_IPS` defaults to an
empty value, and the old code read an empty allowlist as "accept every source
address". The portal therefore served every route to any caller who reached the
port. See issue #1933.

These tests hold the contract for the fix.

- Without an allowlist, a workstation serves the loopback address only.
- Without an allowlist, a container serves the private ranges only, because a
  container that serves loopback only is unreachable through a published port.
- An operator opts out on purpose with `PORTAL_ALLOW_PUBLIC_ACCESS`.
- An explicit `PORTAL_ALLOWED_IPS` value still wins over every fallback.
"""

from __future__ import annotations

import logging

import pytest
from flask import Flask

from src.utils.environment_utils import EnvironmentUtils
from web_portal.services.config import PortalConfigLoader, SecurityMiddleware

# A routable public address. No fallback may ever allow this address.
PUBLIC_CLIENT = "203.0.113.10"

# A private address that a container reaches through the bridge gateway.
CONTAINER_GATEWAY = "172.17.0.1"

# A private address on a normal office network.
LAN_CLIENT = "192.168.1.50"

# The loopback address that a workstation browser uses.
LOOPBACK_CLIENT = "127.0.0.1"

# The name of the deliberate opt-out setting.
OPT_OUT_NAME = "PORTAL_ALLOW_PUBLIC_ACCESS"


def _build_app(allowed_ips: list, trusted_proxies: list | None = None) -> Flask:
    """Build a small Flask app that carries the security middleware."""
    logging.info("Building a test portal with %d configured networks", len(allowed_ips))
    app = Flask(__name__)
    # The CSRF extension needs a secret key even when the check is off.
    app.config["SECRET_KEY"] = "test-secret-key"
    # Turn the CSRF check off, because these tests judge the address check only.
    app.config["WTF_CSRF_ENABLED"] = False

    @app.route("/")
    def index():
        return "portal home"

    middleware = SecurityMiddleware()
    middleware.apply(app, allowed_ips, trusted_proxies)
    logging.debug("Built a test portal that serves one route")
    return app


def _get(app: Flask, client_ip: str):
    """Send one request from a chosen source address."""
    # `environ_base` sets the socket peer address that the middleware reads.
    return app.test_client().get("/", environ_base={"REMOTE_ADDR": client_ip})


@pytest.fixture
def workstation(monkeypatch):
    """Report that the process runs outside a container."""
    logging.info("Forcing the container probe to report a workstation")
    monkeypatch.setattr(EnvironmentUtils, "is_running_in_container", staticmethod(lambda: False))
    # Clear the opt-out so that a leaked value from the shell cannot pass a test.
    monkeypatch.delenv(OPT_OUT_NAME, raising=False)


@pytest.fixture
def container(monkeypatch):
    """Report that the process runs inside a container."""
    logging.info("Forcing the container probe to report a container")
    monkeypatch.setattr(EnvironmentUtils, "is_running_in_container", staticmethod(lambda: True))
    # Clear the opt-out so that the container fallback is the rule under test.
    monkeypatch.delenv(OPT_OUT_NAME, raising=False)


class TestWorkstationDefaultRefusesRemoteClients:
    """Without an allowlist a workstation must serve the loopback address only."""

    def test_a_public_client_is_refused(self, workstation) -> None:
        """A public address never reaches a portal that has no allowlist."""
        logging.info("Sending a request from a public address with no allowlist")
        # An empty list is the shipped default, so this is the upgrade path.
        response = _get(_build_app([]), PUBLIC_CLIENT)
        assert response.status_code == 403, (
            "A portal with no allowlist served a public address. "
            "The portal has no authentication, so every route was open."
        )
        logging.debug("The public address received %d", response.status_code)

    def test_a_lan_client_is_refused(self, workstation) -> None:
        """A neighbour on the office network cannot reach a workstation portal."""
        logging.info("Sending a request from a LAN address with no allowlist")
        # A workstation run needs the loopback address only, so the LAN is out.
        response = _get(_build_app([]), LAN_CLIENT)
        assert response.status_code == 403, "A workstation portal served a LAN address."
        logging.debug("The LAN address received %d", response.status_code)

    def test_the_loopback_client_still_works(self, workstation) -> None:
        """The operator who runs the portal still reaches it."""
        logging.info("Sending a request from the loopback address with no allowlist")
        # This case must keep working, because the fallback must not lock the
        # operator out of a portal that runs on the same machine.
        response = _get(_build_app([]), LOOPBACK_CLIENT)
        assert response.status_code == 200, "The fallback locked the operator out of a local portal."
        logging.debug("The loopback address received %d", response.status_code)


class TestContainerDefaultRefusesPublicClients:
    """Without an allowlist a container must serve the private ranges only."""

    def test_a_public_client_is_refused(self, container) -> None:
        """A public address never reaches a container portal that has no allowlist."""
        logging.info("Sending a request from a public address inside a container")
        # A container binds every interface, so the address check is the only
        # control that remains. Read pull request #1877.
        response = _get(_build_app([]), PUBLIC_CLIENT)
        assert response.status_code == 403, "A container portal served a public address."
        logging.debug("The public address received %d", response.status_code)

    def test_the_bridge_gateway_still_works(self, container) -> None:
        """A published port still reaches the portal from the host."""
        logging.info("Sending a request from the container bridge gateway")
        # A request through a published port arrives from the bridge gateway.
        # A loopback only rule would make the container unreachable.
        response = _get(_build_app([]), CONTAINER_GATEWAY)
        assert response.status_code == 200, (
            "The container fallback blocked the bridge gateway. "
            "A published port would stop working after an upgrade."
        )
        logging.debug("The bridge gateway received %d", response.status_code)

    def test_a_lan_client_still_works(self, container) -> None:
        """An operator on the office network still reaches a container portal."""
        logging.info("Sending a request from a LAN address inside a container")
        # A NOC engineer browses from a desk, so the LAN must keep working.
        response = _get(_build_app([]), LAN_CLIENT)
        assert response.status_code == 200, "The container fallback blocked the office network."
        logging.debug("The LAN address received %d", response.status_code)

    def test_the_loopback_client_still_works(self, container) -> None:
        """A health probe inside the container still reaches the portal."""
        logging.info("Sending a request from the loopback address inside a container")
        # The container health check calls the portal on the loopback address.
        response = _get(_build_app([]), LOOPBACK_CLIENT)
        assert response.status_code == 200, "The container fallback blocked the health probe."
        logging.debug("The loopback address received %d", response.status_code)


class TestTheOperatorCanOptOut:
    """An operator who wants an open portal must say so on purpose."""

    @pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
    def test_the_opt_out_serves_a_public_client(self, workstation, monkeypatch, value) -> None:
        """A deliberate opt-out restores the old open behavior."""
        logging.info("Setting the opt-out to %s and sending a public request", value)
        # The operator sets the value on purpose, so the portal obeys.
        monkeypatch.setenv(OPT_OUT_NAME, value)
        response = _get(_build_app([]), PUBLIC_CLIENT)
        assert response.status_code == 200, f"The opt-out value {value!r} did not open the portal."
        logging.debug("The opt-out value %s produced %d", value, response.status_code)

    @pytest.mark.parametrize("value", ["false", "no", "0", "off", "", "maybe"])
    def test_a_value_that_is_not_true_keeps_the_portal_closed(self, workstation, monkeypatch, value) -> None:
        """Only a clear yes opens the portal."""
        logging.info("Setting the opt-out to %s and sending a public request", value)
        # A typing slip must never open the portal, so the parser fails closed.
        monkeypatch.setenv(OPT_OUT_NAME, value)
        response = _get(_build_app([]), PUBLIC_CLIENT)
        assert response.status_code == 403, f"The value {value!r} opened the portal by accident."
        logging.debug("The value %s produced %d", value, response.status_code)

    def test_the_opt_out_records_a_warning(self, workstation, monkeypatch, caplog) -> None:
        """The open choice appears in the log, so an audit finds it."""
        logging.info("Checking that the opt-out writes a warning to the log")
        monkeypatch.setenv(OPT_OUT_NAME, "true")
        # Capture at warning level, because the message must be loud.
        with caplog.at_level(logging.WARNING):
            _build_app([])
        # The message must name the setting so that a reader can undo the choice.
        assert OPT_OUT_NAME in caplog.text, "The opt-out warning does not name the setting."
        logging.debug("The opt-out wrote %d characters to the log", len(caplog.text))


class TestAnExplicitAllowlistStillWins:
    """A configured allowlist must override every fallback."""

    def test_the_configured_network_is_served(self, workstation) -> None:
        """An address inside the configured range reaches the portal."""
        logging.info("Applying an explicit allowlist and sending a matching request")
        # The operator named this range, so the portal serves it.
        allowed = PortalConfigLoader.parse_networks("203.0.113.0/24", "PORTAL_ALLOWED_IPS")
        response = _get(_build_app(allowed), PUBLIC_CLIENT)
        assert response.status_code == 200, "An explicit allowlist did not serve its own range."
        logging.debug("The configured address received %d", response.status_code)

    def test_an_address_outside_the_configured_network_is_refused(self, workstation) -> None:
        """The fallback ranges do not widen a configured allowlist."""
        logging.info("Applying an explicit allowlist and sending a loopback request")
        # The loopback address sits in the fallback, so this test proves that
        # the fallback does not leak into an explicit configuration.
        allowed = PortalConfigLoader.parse_networks("203.0.113.0/24", "PORTAL_ALLOWED_IPS")
        response = _get(_build_app(allowed), LOOPBACK_CLIENT)
        assert response.status_code == 403, "The fallback widened an explicit allowlist."
        logging.debug("The loopback address received %d", response.status_code)


class TestTheFallbackTellsTheOperatorWhatToDo:
    """The startup message must name the setting and give an example."""

    def test_the_workstation_fallback_writes_one_warning(self, workstation, caplog) -> None:
        """The message names the setting that turns the fallback off."""
        logging.info("Checking the workstation fallback startup message")
        with caplog.at_level(logging.WARNING):
            _build_app([])
        # A reader must learn the exact setting name from the message.
        assert "PORTAL_ALLOWED_IPS" in caplog.text, "The warning does not name PORTAL_ALLOWED_IPS."
        # A reader must also learn the opt-out, so the message covers both paths.
        assert OPT_OUT_NAME in caplog.text, "The warning does not name the opt-out setting."
        logging.debug("The workstation fallback wrote a warning")

    def test_the_message_holds_an_example_value(self, workstation, caplog) -> None:
        """The message shows a CIDR range that an operator can copy."""
        logging.info("Checking that the startup message holds an example")
        with caplog.at_level(logging.WARNING):
            _build_app([])
        # A junior engineer needs a value to copy, not only a setting name.
        assert "/" in caplog.text, "The warning holds no CIDR example."
        logging.debug("The startup message holds an example")

    def test_the_message_is_ascii(self, workstation, caplog) -> None:
        """The log holds no character above the ASCII range."""
        logging.info("Checking that the startup message is ASCII")
        with caplog.at_level(logging.WARNING):
            _build_app([])
        # The project forbids a Unicode character in a log line.
        assert caplog.text.isascii(), "The startup message holds a character above ASCII."
        logging.debug("The startup message is ASCII")
