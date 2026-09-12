"""The security controls that every request and every response passes through.

Why:
    The portal drives a firmware upgrade, so a forged request could start work
    on a live site. This module holds the five controls that stop that. They
    are the proxy trust boundary, the content security policy, the standard
    response headers, the cross-site request forgery token, and the network
    allow list.

    The controls live in one module, so a reader finds every control in one
    place and an audit needs one file.
"""

import logging  # The portal logs with the standard library only.
from ipaddress import ip_address  # Parses a client address for the allow list.

from flask import Flask, Response, abort, request  # The application, the response, and the request context.
from flask_wtf.csrf import CSRFError, CSRFProtect  # The token check and the fault it raises.
from werkzeug.middleware.proxy_fix import ProxyFix  # Reads the forwarded headers that the operator trusts.

from .config import Network, PortalSettings  # The allow list type and the settings record.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# Every asset loads from the portal itself, so the policy names 'self' only and
# names no external origin. The vendored Bootstrap files satisfy that rule.
#
# The image rule also names the `data:` scheme. Bootstrap draws the caret of a
# selection list, the dot of a radio control, the tick of a checkbox, and the
# knob of a switch as an inline SVG image, and each one arrives as a `data:` URI
# inside `bootstrap.min.css`. Without the scheme the browser blocks all 23 of
# them, and every one of those controls renders as an empty box. The scheme is
# safe here because a `data:` image runs no code. It stays out of `script-src`,
# where it would be an attack path.
CSP_POLICY = (
    "default-src 'self'; "  # The fallback rule for every directive that follows.
    "script-src 'self'; "  # No inline script and no external script.
    "style-src 'self'; "  # No inline style, so every rule lives in a stylesheet.
    "img-src 'self' data:; "  # The vendored stylesheet draws its controls inline. No other origin may supply one.
    "connect-src 'self'; "  # The status poll reaches the portal only.
    "font-src 'self'; "  # The vendored font files load from the portal.
    "form-action 'self'; "  # A form cannot post a credential to another origin.
    "frame-ancestors 'none'; "  # No other page may frame the portal.
    "base-uri 'self'; "  # A tag cannot move the base of every relative link.
    "object-src 'none'"  # The portal embeds no plugin object.
)

RESPONSE_HEADERS = {
    "Content-Security-Policy": CSP_POLICY,  # The policy above, on every response.
    "X-Content-Type-Options": "nosniff",  # The browser must trust the declared type.
    "X-Frame-Options": "DENY",  # The older guard against framing, for an older browser.
    "Referrer-Policy": "strict-origin-when-cross-origin",  # A site identifier must not leak in a referrer.
    "Cache-Control": "no-store",  # A shared workstation must not keep a page with site data.
}

FORWARDED_HEADER = "X-Forwarded-For"  # `ProxyFix` reads this header. No code here parses it by hand.
BLOCKED_STATUS = 403  # The answer for an address outside the allow list.
CSRF_STATUS = 400  # The contract binds this status to a missing token.
CSRF_MISSING_CODE = "csrf_missing"  # The fixed code that a contract test asserts on.
CSRF_MISSING_MESSAGE = (
    "The request carries no valid security token. Reload the page and try again."  # A test reads the code only.
)


class PortalSecurity:
    """Register the transport controls on one Flask application.

    Why:
        The factory builds the application and this class arms it. The split
        keeps the factory short and gives the security rules one owner.
    """

    def apply(self, app: Flask, settings: PortalSettings) -> None:
        """Register every security control on the application.

        Args:
            app: The application to protect.
            settings: The settings that carry the network allow list.
        """
        self._register_proxy_trust(app, settings.proxy.trusted_hops)  # The address must be true before any guard.
        self._register_headers(app)  # Every response carries the standard headers.
        self._register_allow_list(app, settings.web.allowed_networks)  # The network guard runs first.
        self._register_csrf(app)  # The token check covers every state-changing request.

    def _register_proxy_trust(self, app: Flask, trusted_hops: int) -> None:
        """Read the forwarded headers that the operator says a proxy wrote.

        Why:
            A forwarded header is client-supplied text that any caller can send.
            `ProxyFix` counts the entries from the right. It therefore reads the
            entry that the outermost trusted proxy wrote, and no prepended entry
            can move that position. It then writes the result into the request
            environment, where `request.remote_addr` and `request.is_secure`
            read it. Nothing else in the portal touches a forwarded header.

            One count drives both headers, so the network allow list and the
            cookie `Secure` flag can never disagree about the deployment.

            A count of zero installs nothing at all. The socket address then
            stays the client address and the portal ignores every forwarded
            header, which is the correct reading for a direct listener.

        Args:
            app: The application to protect.
            trusted_hops: The count of proxies the operator runs in front of
                the portal.
        """
        if trusted_hops <= 0:  # The operator named no proxy, so no header is trustworthy.
            logger.info("The portal trusts no forwarded header. The socket address is the client address.")
            return  # Install no middleware, so a direct listener pays no cost for each request.
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]  # WHY: The documented way to wrap a WSGI app.
            app.wsgi_app,
            x_for=trusted_hops,  # Sets `REMOTE_ADDR`, which the allow list then tests.
            x_proto=trusted_hops,  # Sets the scheme, which decides the `Secure` cookie flag.
        )
        logger.info("The portal trusts the forwarded headers of %s proxies.", trusted_hops)  # State the count.

    def _register_headers(self, app: Flask) -> None:
        """Add the standard headers to every response.

        Args:
            app: The application to protect.
        """

        @app.after_request  # The hook runs after a view and after an error handler.
        def add_headers(response: Response) -> Response:
            """Copy each standard header onto one outgoing response.

            Args:
                response: The response on its way to the browser.

            Returns:
                The same response with the headers in place.
            """
            for name, value in RESPONSE_HEADERS.items():  # One pass over the fixed header table.
                response.headers[name] = value  # A later value replaces an earlier one.
            return response  # Flask sends the response the hook returns.

    def _register_allow_list(self, app: Flask, networks: tuple[Network, ...]) -> None:
        """Refuse every request that arrives from outside the allow list.

        Why:
            An empty list keeps the portal open, which matches the behavior of
            the port 8055 portal. The guard costs nothing when the list is
            empty, because this method then registers no hook at all.

            An empty list here always means that the operator asked for no
            guard. `config.read_allowed_networks` raises `SettingsError` when
            the operator asks for a guard and no entry names a network. A
            list of typed entries can therefore never reach this method as an
            empty tuple. That invariant makes an empty list safe to read as
            "open".

        Args:
            app: The application to protect.
            networks: The networks that may reach the portal.
        """
        if not networks:  # An empty list means the operator set no guard.
            logger.info("The address allow list is empty. The portal accepts every client address.")  # Said once.
            return  # Register no hook, so an open portal pays no cost for each request.

        @app.before_request  # The hook runs before the token check and before any view.
        def check_address() -> None:
            """Stop one request that arrives from an address outside the list."""
            address = read_client_address()  # The socket address, or what a trusted proxy reported.
            if address_is_allowed(address, networks):  # A match ends the check.
                return  # Let the request continue to the view.
            logger.warning("The portal refused a request from the address %s.", address)  # Audit trail.
            abort(BLOCKED_STATUS)  # Raise the 403 fault that the JSON handler answers.

    def _register_csrf(self, app: Flask) -> None:
        """Register the token check and the answer for a missing token.

        Why:
            `flask-wtf` checks the token on every request that changes state and
            leaves a `GET` request alone, which matches the contract exactly.

        Args:
            app: The application to protect.
        """
        CSRFProtect().init_app(app)  # The extension adds its own before_request hook.
        app.register_error_handler(CSRFError, csrf_error_response)  # A class handler beats the plain 400 handler.


def csrf_error_response(error: Exception) -> tuple[Response, int]:
    """Answer a state-changing request that carries no valid token.

    Why:
        The contract binds one answer to this fault: the status 400 with the
        code `csrf_missing`. The import of the envelope builder sits inside this
        function, because `factory` imports this module while it loads. A module
        level import here would close that circle.

    Args:
        error: The token fault that `flask-wtf` raised.

    Returns:
        The error envelope and the status code 400.
    """
    from .factory import json_error  # The late import breaks the circle with the factory.

    logger.warning(
        "The portal refused a request with no valid token: %s.",  # The class name only, never the token.
        type(error).__name__,
    )
    return json_error(CSRF_STATUS, CSRF_MISSING_CODE, CSRF_MISSING_MESSAGE)  # The one shape the contract allows.


def read_client_address() -> str:
    """Read the address of the client that sent the current request.

    Why:
        This function never reads a forwarded header. A caller can send any
        header it likes. A header that the portal parsed by hand would let a
        caller name its own address and pass the allow list.

        `request.remote_addr` is correct in both deployments. With no trusted
        proxy it holds the socket address of the caller. Behind a trusted proxy
        `ProxyFix` has already replaced it with the entry that the outermost
        trusted proxy wrote. See `PortalSecurity._register_proxy_trust`.

    Returns:
        The client address, or an empty string when no address is available.
    """
    return request.remote_addr or ""  # The one address the portal is willing to trust.


def address_is_allowed(address: str, networks: tuple[Network, ...]) -> bool:
    """Report whether one client address falls inside the allow list.

    Why:
        An unreadable address returns False, so the portal refuses a request it
        cannot place. A guard that fails open would give no protection at all.

    Args:
        address: The client address as text.
        networks: The networks that may reach the portal.

    Returns:
        True when the address falls inside one network.
    """
    try:  # A proxy may report any text at all, and a socket may report none.
        parsed = ip_address(address)  # Turn the text into a comparable address.
    except ValueError:  # The text was not an address.
        return False  # Deny by default, because the portal cannot place the client.
    return any(parsed in network for network in networks)  # One match is enough.
