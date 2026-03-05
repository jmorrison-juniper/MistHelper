"""Configuration services for the MistHelper web portal.

Contains PortalConfigLoader for ENV-based configuration,
SecurityMiddleware for CSRF, CSP headers, and IP allowlisting,
and ThemeManager for CSS theme enumeration.
"""

import ipaddress
import logging
import os
import re
import uuid

from flask import Flask, abort, request


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
        "PORTAL_SECRET_KEY": "",
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
        config["allowed_ips"] = self._parse_allowed_ips(raw["PORTAL_ALLOWED_IPS"])
        config["secret_key"] = raw["PORTAL_SECRET_KEY"] or str(uuid.uuid4())
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

    def _parse_allowed_ips(self, ip_string: str) -> list:
        """Parse comma-separated CIDR networks into list."""
        if not ip_string.strip():
            return []
        networks = []
        for entry in ip_string.split(","):
            entry = entry.strip()
            if not entry:
                continue
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                logging.warning("Invalid CIDR in PORTAL_ALLOWED_IPS: '%s'", entry)
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

    def apply(self, app: Flask, allowed_ips: list) -> None:
        """Register all security hooks on the Flask app."""
        self._register_csp_headers(app)
        self._register_ip_allowlist(app, allowed_ips)
        self._configure_csrf(app)

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
            return

        @app.before_request
        def check_ip_allowlist():
            client_ip = self._get_client_ip()
            if not self._ip_is_allowed(client_ip, allowed_ips):
                logging.warning("Blocked request from %s", client_ip)
                abort(403)

    def _configure_csrf(self, app: Flask) -> None:
        """Initialize CSRF protection via flask-wtf."""
        from flask_wtf.csrf import CSRFProtect
        csrf = CSRFProtect()
        csrf.init_app(app)
        app.config["csrf"] = csrf

    def _get_client_ip(self) -> str:
        """Extract client IP from request, respecting X-Forwarded-For."""
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr or "0.0.0.0"

    def _ip_is_allowed(self, client_ip: str, allowed_ips: list) -> bool:
        """Check if client IP matches any allowed CIDR network."""
        try:
            addr = ipaddress.ip_address(client_ip)
            return any(addr in network for network in allowed_ips)
        except ValueError:
            return False


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
            themes.append({
                "name": name,
                "display_label": label,
                "is_default": False,
            })
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
