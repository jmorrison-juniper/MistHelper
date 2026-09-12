"""Configuration services for the MistHelper web portal.

Contains PortalConfigLoader for ENV-based configuration,
SecurityMiddleware for CSRF, CSP headers, and IP allowlisting,
and ThemeManager for CSS theme enumeration.

The IP allowlist judges the socket peer address from `request.remote_addr`.
The portal reads the `X-Forwarded-For` header only when the peer address
matches an entry in `PORTAL_TRUSTED_PROXIES`. That setting is empty by
default, so a client-supplied header never changes the decision.

The portal has no user authentication. The address allowlist is therefore the
only access control. `PORTAL_ALLOWED_IPS` is empty by default, so the portal
falls back to a closed set of networks. A workstation serves the loopback
address only. A container serves the private ranges only, because a container
that serves loopback only cannot answer a published port. An operator opens the
portal to every address with `PORTAL_ALLOW_PUBLIC_ACCESS`. See issue #1933.
"""

import ipaddress
import logging
import os
import re
import uuid

from flask import Flask, abort, request

from src.utils.environment_utils import EnvironmentUtils

# The networks that a workstation serves when the operator sets no allowlist.
# A browser on the same machine uses one of these two addresses.
LOOPBACK_FALLBACK_NETWORKS = ("127.0.0.0/8", "::1/128")

# The networks that a container serves when the operator sets no allowlist.
# The list holds the loopback ranges for the health probe, the three RFC 1918
# ranges for an office network, the link-local ranges, and the IPv6 private
# range. A container reaches a published port through a private address.
PRIVATE_FALLBACK_NETWORKS = (
    "127.0.0.0/8",
    "::1/128",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "169.254.0.0/16",
    "fe80::/10",
    "fc00::/7",
)

# The setting that an operator sets to serve every source address on purpose.
PUBLIC_ACCESS_SETTING = "PORTAL_ALLOW_PUBLIC_ACCESS"

# The values that count as a clear yes. Every other value keeps the portal shut.
AFFIRMATIVE_VALUES = frozenset({"1", "true", "yes", "on"})

# An example value for the startup message. A junior engineer copies this shape.
ALLOWLIST_EXAMPLE = "10.20.30.0/24,192.168.1.5"


class PortalConfigLoader:
    """Load portal configuration from environment variables.

    Reads branding, theme, port, and security settings from ENV.
    Configuration is immutable after load_config() returns.
    """

    ENV_DEFAULTS = {
        "PORTAL_TITLE": "MistHelper",
        "PORTAL_LOGO_URL": "/static/img/logo-default.svg",
        "PORTAL_ACCENT_COLOR": "#0077B6",
        "PORTAL_THEME": "dark",
        "WEB_PORT": "8055",
        "PORTAL_ALLOWED_IPS": "",
        "PORTAL_TRUSTED_PROXIES": "",
        PUBLIC_ACCESS_SETTING: "",
    }

    def load_config(self) -> dict:
        """Read all portal ENV variables and return validated config."""
        raw = self._read_env_values()
        validated = self._validate_values(raw)
        return validated

    def _read_env_values(self) -> dict:
        """Read raw values from environment with defaults."""
        values = {}
        for key, default in self.ENV_DEFAULTS.items():
            values[key] = os.environ.get(key, default)
        return values

    def _validate_values(self, raw: dict) -> dict:
        """Validate and transform raw ENV values into typed config."""
        config = {
            "title": raw["PORTAL_TITLE"],
            "logo_url": raw["PORTAL_LOGO_URL"],
            "accent_color": self._validate_color(raw["PORTAL_ACCENT_COLOR"]),
            "theme": raw["PORTAL_THEME"],
            "web_port": self._validate_port(raw["WEB_PORT"]),
        }
        config["allowed_ips"] = self.parse_networks(raw["PORTAL_ALLOWED_IPS"], "PORTAL_ALLOWED_IPS")
        # An empty trusted proxy list keeps the forwarded header untrusted by default.
        config["trusted_proxies"] = self.parse_networks(raw["PORTAL_TRUSTED_PROXIES"], "PORTAL_TRUSTED_PROXIES")
        config["secret_key"] = os.environ.get("PORTAL_SECRET_KEY") or str(uuid.uuid4())
        return config

    def _validate_color(self, color: str) -> str:
        """Validate hex color format, return default on failure."""
        if re.match(r"^#[0-9A-Fa-f]{6}$", color):
            return color
        logging.warning("Invalid PORTAL_ACCENT_COLOR '%s', using default", color)
        return "#0077B6"

    def _validate_port(self, port_str: str) -> int:
        """Validate port number is in valid range."""
        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                return port
        except ValueError:
            pass
        logging.warning("Invalid WEB_PORT '%s', using default 8055", port_str)
        return 8055

    @staticmethod
    def parse_networks(ip_string: str, setting_name: str) -> list:
        """Parse a comma-separated list of addresses or CIDR ranges."""
        if not ip_string.strip():
            return []  # An empty setting yields an empty list, which the caller reads as "not configured".
        logging.info("Parsing the %s setting", setting_name)
        networks = []
        for position, entry in enumerate(ip_string.split(","), start=1):
            entry = entry.strip()  # Trim the spaces that an operator leaves around a comma.
            if not entry:
                continue  # Skip an empty field, because a trailing comma is a common typing slip.
            try:
                # strict=False accepts a plain address, which becomes a single-host network.
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                # The message names the position, not the text. An environment value can hold a secret.
                logging.warning(
                    "Entry %d of the %s setting is not an address or a CIDR range",
                    position,
                    setting_name,
                )
        logging.debug("Parsed %d networks from the %s setting", len(networks), setting_name)
        return networks


class SecurityMiddleware:
    """Apply security controls to the Flask application.

    Registers CSRF protection, CSP response headers,
    XSS prevention, and IP allowlist enforcement.
    """

    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )

    def __init__(self) -> None:
        """Start with no trusted proxy, so a forged header carries no trust."""
        self._trusted_proxies: list = []

    def apply(self, app: Flask, allowed_ips: list, trusted_proxies: list | None = None) -> None:
        """Register all security hooks on the Flask app."""
        logging.info("Applying the portal security controls to the Flask application")
        # Resolve the trusted proxies first, because the allowlist hook reads them.
        self._trusted_proxies = self._resolve_trusted_proxies(trusted_proxies)
        # Resolve the allowlist next, because an empty setting needs a safe fallback.
        effective_ips = self._resolve_effective_allowlist(allowed_ips)
        self._register_csp_headers(app)
        self._register_ip_allowlist(app, effective_ips)
        self._configure_csrf(app)
        logging.debug(
            "Applied the portal security controls with %d allowed networks and %d trusted proxies",
            len(effective_ips),
            len(self._trusted_proxies),
        )

    def _resolve_effective_allowlist(self, allowed_ips: list) -> list:
        """Return the networks that the portal serves after the fallback runs."""
        if allowed_ips:
            # The operator named the networks, so the portal obeys the setting.
            logging.debug("Using the %d networks that the operator configured", len(allowed_ips))
            return allowed_ips
        if self._public_access_is_allowed():
            # The operator chose an open portal, so the log records the choice.
            logging.warning(
                "Warning: the portal serves every source address, because %s is set. "
                "The portal has no user authentication. Any caller who reaches the port "
                "gets every page. Set PORTAL_ALLOWED_IPS instead, for example %s.",
                PUBLIC_ACCESS_SETTING,
                ALLOWLIST_EXAMPLE,
            )
            return []  # An empty list turns the address check off on purpose.
        return self._build_fallback_allowlist()

    @staticmethod
    def _public_access_is_allowed() -> bool:
        """Return True when the operator opts out of the address check."""
        # An unset value reads as an empty string, which is not a clear yes.
        raw = os.environ.get(PUBLIC_ACCESS_SETTING, "").strip().lower()
        # Only a value from the affirmative set opens the portal, so a typing
        # slip such as "maybe" leaves the portal shut.
        return raw in AFFIRMATIVE_VALUES

    def _build_fallback_allowlist(self) -> list:
        """Return the closed network set that fits the current run mode."""
        in_container = EnvironmentUtils.is_running_in_container()
        # A container answers a published port from a private address, so a
        # loopback only rule would make every existing deployment unreachable.
        sources = PRIVATE_FALLBACK_NETWORKS if in_container else LOOPBACK_FALLBACK_NETWORKS
        scope = "the private network ranges" if in_container else "the loopback address"
        logging.warning(
            "Warning: the portal has no user authentication and no configured allowlist. "
            "The portal now serves %s only. Set PORTAL_ALLOWED_IPS to the networks that "
            "need access, for example %s. To serve every source address on purpose, set "
            "%s to true.",
            scope,
            ALLOWLIST_EXAMPLE,
            PUBLIC_ACCESS_SETTING,
        )
        # Every entry is a fixed constant, so the parser cannot raise an error.
        networks = [ipaddress.ip_network(entry) for entry in sources]
        logging.debug("Built a fallback allowlist of %d networks", len(networks))
        return networks

    def _resolve_trusted_proxies(self, trusted_proxies: list | None) -> list:
        """Return the proxy networks that may set the forwarded header."""
        if trusted_proxies is not None:
            return trusted_proxies  # An explicit argument wins, because the caller already read the config.
        # A caller that omits the argument still gets the operator setting, never blind trust.
        raw = os.environ.get("PORTAL_TRUSTED_PROXIES", "")
        return PortalConfigLoader.parse_networks(raw, "PORTAL_TRUSTED_PROXIES")

    def _register_csp_headers(self, app: Flask) -> None:
        """Add security headers to every response."""

        @app.after_request
        def add_security_headers(response):
            response.headers["Content-Security-Policy"] = self.CSP_POLICY
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return response

    def _register_ip_allowlist(self, app: Flask, allowed_ips: list) -> None:
        """Block requests from IPs not in the allowlist."""
        if not allowed_ips:
            # The caller reaches this line only after a deliberate opt-out.
            # `_resolve_effective_allowlist` already logged that choice.
            return

        logging.info("Registering the portal IP allowlist with %d networks", len(allowed_ips))

        @app.before_request
        def check_ip_allowlist():
            peer_ip = self._get_peer_ip()  # The socket peer is the one address a caller cannot forge.
            client_ip = self._resolve_client_ip(peer_ip)  # Only a trusted proxy can name a different client.
            if not self._ip_matches_any(client_ip, allowed_ips):
                # The message names both addresses, so the audit trail keeps the real source.
                logging.warning("Blocked request from client %s with peer %s", client_ip, peer_ip)
                abort(403)
            # Debug level keeps the allowed path quiet, because every request reaches this line.
            logging.debug("Allowed request from client %s with peer %s", client_ip, peer_ip)

        logging.debug("Registered the portal IP allowlist")

    def _configure_csrf(self, app: Flask) -> None:
        """Initialize CSRF protection via flask-wtf."""
        from flask_wtf.csrf import CSRFProtect

        csrf = CSRFProtect()
        csrf.init_app(app)
        app.config["csrf"] = csrf

    def _get_peer_ip(self) -> str:
        """Return the socket peer address of the current request."""
        # The fallback value is a placeholder address, not a bind address.
        return request.remote_addr or "0.0.0.0"  # nosec B104

    def _resolve_client_ip(self, peer_ip: str) -> str:
        """Return the address that the allowlist check must judge."""
        if not self._trusted_proxies:
            return peer_ip  # Without a trusted proxy the forwarded header carries no trust.
        if not self._ip_matches_any(peer_ip, self._trusted_proxies):
            return peer_ip  # An untrusted peer cannot rename itself with a header.
        forwarded = request.headers.get("X-Forwarded-For", "")  # Only a trusted proxy reaches this line.
        if not forwarded:
            return peer_ip  # The trusted proxy sent no header, so the peer is the client.
        # The rightmost entry is the address the trusted proxy observed. A caller controls the entries to its left.
        client_ip = forwarded.split(",")[-1].strip()
        logging.debug("Trusted proxy %s reported client %s", peer_ip, client_ip)
        return client_ip

    def _ip_matches_any(self, client_ip: str, networks: list) -> bool:
        """Check if an address falls inside any network in the list."""
        try:
            addr = ipaddress.ip_address(client_ip)  # Reject a malformed value before the range test.
            return any(addr in network for network in networks)
        except ValueError:
            logging.debug("Address '%s' is not a valid IP address", client_ip)
            return False  # An unreadable address never matches, so the caller blocks the request.


class ThemeManager:
    """Enumerate available CSS themes and resolve the default.

    Scans the static/css/themes/ directory for .css files and
    provides metadata for the theme switcher UI component.
    """

    DISPLAY_LABELS = {
        "dark": "Dark NOC",
        "light": "Light Office",
        "high-contrast": "High Contrast",
    }

    def __init__(self, themes_dir: str, default_theme: str = "dark"):
        """Initialize with path to themes directory and default name."""
        self._themes_dir = themes_dir
        self._default_theme = default_theme
        self._themes = []

    def load_themes(self) -> list:
        """Scan themes directory and build theme metadata list."""
        self._themes = self._scan_theme_files()
        self._apply_default_flag()
        return self._themes

    def get_themes(self) -> list:
        """Return cached list of theme metadata dictionaries."""
        if not self._themes:
            self.load_themes()
        return self._themes

    def get_default_name(self) -> str:
        """Return the name of the default theme."""
        return self._default_theme

    def _scan_theme_files(self) -> list:
        """Read .css files from themes directory into metadata."""
        themes = []
        if not os.path.isdir(self._themes_dir):
            logging.warning("Themes directory not found: %s", self._themes_dir)
            return themes
        for filename in sorted(os.listdir(self._themes_dir)):
            if not filename.endswith(".css"):
                continue
            name = filename.removesuffix(".css")
            label = self.DISPLAY_LABELS.get(name, name.replace("-", " ").title())
            themes.append(
                {
                    "name": name,
                    "display_label": label,
                    "is_default": False,
                }
            )
        return themes

    def _apply_default_flag(self) -> None:
        """Mark the ENV-configured default theme in the list."""
        found = False
        for theme in self._themes:
            if theme["name"] == self._default_theme:
                theme["is_default"] = True
                found = True
                break
        if not found and self._themes:
            logging.warning(
                "Default theme '%s' not found, falling back to '%s'",
                self._default_theme,
                self._themes[0]["name"],
            )
            self._themes[0]["is_default"] = True
            self._default_theme = self._themes[0]["name"]
