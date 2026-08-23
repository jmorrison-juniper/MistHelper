"""Flask application factory for the MistHelper web portal.

WebPortalApp creates and configures the Flask app instance,
registers blueprints, injects shared dependencies, and applies
security middleware.
"""

import atexit
import logging
import os
from typing import Any, Optional

from flask import Flask

from web_portal.services.config import PortalConfigLoader, SecurityMiddleware, ThemeManager
from web_portal.services.input_hook import InputInterceptor


class WebPortalApp:
    """Factory for creating the Flask web portal application.

    Usage:
        app = WebPortalApp.create_app(apisession, menu_actions, org_id)
        app.run(port=8055)
    """

    @staticmethod
    def create_app(
        apisession: Optional[Any],
        menu_actions: dict,
        org_id: Optional[str],
    ) -> Flask:
        """Create and configure the Flask application instance."""
        app = Flask(
            __name__,
            template_folder=WebPortalApp._get_template_dir(),
            static_folder=WebPortalApp._get_static_dir(),
        )
        config = WebPortalApp._load_portal_config(app)
        WebPortalApp._load_webhook_config(app)
        WebPortalApp._inject_dependencies(app, apisession, menu_actions, org_id)
        WebPortalApp._setup_theme_manager(app, config)
        WebPortalApp._apply_security(app, config)
        WebPortalApp._register_blueprints(app)
        WebPortalApp._register_context_processor(app)
        InputInterceptor.install()
        return app

    @staticmethod
    def _get_template_dir() -> str:
        """Return absolute path to the templates directory."""
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "templates")

    @staticmethod
    def _get_static_dir() -> str:
        """Return absolute path to the static assets directory."""
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "static")

    @staticmethod
    def _load_portal_config(app: Flask) -> dict:
        """Load ENV configuration and apply to Flask app."""
        loader = PortalConfigLoader()
        config = loader.load_config()
        app.config["PORTAL"] = config
        app.secret_key = config["secret_key"]
        return config

    @staticmethod
    def _load_webhook_config(app: Flask) -> None:
        """Load the webhook receiver settings from the environment.

        Issue #1907: the route read WEBHOOK_SECRET, but no code wrote
        the key. The secret was always empty, so the signature check
        never ran. This method is the single writer of that key.
        """
        from web_portal.routes.webhooks import WEBHOOK_ENABLED_CONFIG_KEY, WEBHOOK_SECRET_CONFIG_KEY

        raw_enabled = os.environ.get(WEBHOOK_ENABLED_CONFIG_KEY, "true")  # WHY: match the src/db default.
        enabled = raw_enabled.strip().lower() == "true"  # WHY: only the exact word "true" turns the route on.
        app.config[WEBHOOK_ENABLED_CONFIG_KEY] = enabled
        app.config[WEBHOOK_SECRET_CONFIG_KEY] = os.environ.get(WEBHOOK_SECRET_CONFIG_KEY, "").strip()
        logging.info("Webhook receiver enabled=%s", enabled)  # WHY: log the setting, never the secret.
        if app.config[WEBHOOK_SECRET_CONFIG_KEY]:  # WHY: a branch reports the state without logging the value.
            logging.debug("Webhook receiver found a configured secret")
        elif enabled:
            logging.error(
                "Webhook receiver is enabled, but WEBHOOK_SECRET is empty. "
                "The portal rejects every webhook with code 503 until you set the secret."
            )  # WHY: an operator must see the cause before the first 503 reply arrives.
        else:
            logging.debug("Webhook receiver is off and holds no secret")

    @staticmethod
    def _inject_dependencies(
        app: Flask,
        apisession: Optional[Any],
        menu_actions: dict,
        org_id: Optional[str],
    ) -> None:
        """Store shared MistHelper objects on app.config."""
        from web_portal.services.event_bus import PortalEventBus

        app.config["APISESSION"] = apisession
        app.config["MENU_ACTIONS"] = menu_actions
        app.config["ORG_ID"] = org_id
        data_dir = os.environ.get("DATA_DIR", "data")
        app.config["DATA_DIR"] = os.path.abspath(data_dir)

        event_bus = PortalEventBus()
        event_bus.start()
        app.config["EVENT_BUS"] = event_bus
        # WHY: nothing else calls stop(), so the heartbeat thread outlived the
        # process without this hook. A leaked thread keeps sleeping and, under
        # a patched time.sleep, leaks its interval into a test's recording.
        atexit.register(event_bus.stop)
        logging.info("Event bus started for SSE streaming")

    @staticmethod
    def _setup_theme_manager(app: Flask, config: dict) -> None:
        """Initialize ThemeManager and store on app.config."""
        themes_dir = os.path.join(WebPortalApp._get_static_dir(), "css", "themes")
        manager = ThemeManager(themes_dir, config.get("theme", "dark"))
        manager.load_themes()
        app.config["THEME_MANAGER"] = manager

    @staticmethod
    def _apply_security(app: Flask, config: dict) -> None:
        """Apply security middleware to the Flask app."""
        middleware = SecurityMiddleware()
        middleware.apply(app, config.get("allowed_ips", []))
        logging.info("Security middleware applied")

    @staticmethod
    def _register_blueprints(app: Flask) -> None:
        """Register all route blueprints with the app."""
        from web_portal.routes.dashboard import dashboard_bp
        from web_portal.routes.data import data_bp
        from web_portal.routes.maps import maps_bp
        from web_portal.routes.operations import operations_bp
        from web_portal.routes.settings import settings_bp

        app.register_blueprint(dashboard_bp)
        app.register_blueprint(data_bp)
        app.register_blueprint(operations_bp)
        app.register_blueprint(maps_bp)
        app.register_blueprint(settings_bp)
        WebPortalApp._register_webhook_blueprint(app)

    @staticmethod
    def _register_webhook_blueprint(app: Flask) -> None:
        """Register the Mist webhook receiver when the operator enables it.

        Issue #1907: no code registered this blueprint, so POST
        /api/webhook returned 404 and the receiver never worked. That
        broken state hid a latent hole, because the signature check
        behind the route also never ran.

        A disabled receiver serves no route, so an unwanted endpoint
        never reaches the dispatch path.
        """
        from web_portal.routes.webhooks import WEBHOOK_ENABLED_CONFIG_KEY, webhook_bp

        if not app.config.get(WEBHOOK_ENABLED_CONFIG_KEY, False):
            logging.info("Webhook receiver is disabled, so the portal does not serve /api/webhook")
            return

        app.register_blueprint(webhook_bp)
        csrf = app.config.get("csrf")  # WHY: SecurityMiddleware stores the CSRFProtect instance here.
        if csrf is not None:
            # Warning: Do not remove this exemption. It is not a weakness.
            # SecurityMiddleware protects every browser form with a CSRF
            # token. Mist Cloud is a machine caller and holds no token, so
            # an unexempt route answers 400 for every real webhook and the
            # signature check never runs. The HMAC signature authenticates
            # the sender here, and it is the stronger control, because it
            # covers the raw body as well as the sender.
            csrf.exempt(webhook_bp)
        logging.debug("Webhook receiver registered at POST /api/webhook")

    @staticmethod
    def _register_context_processor(app: Flask) -> None:
        """Inject branding variables into all templates."""

        @app.context_processor
        def inject_branding() -> dict:
            portal = app.config.get("PORTAL", {})
            theme_mgr = app.config.get("THEME_MANAGER")
            return {
                "portal_title": portal.get("title", "MistHelper"),
                "portal_logo": portal.get("logo_url", "/static/img/logo-default.svg"),
                "portal_accent": portal.get("accent_color", "#0d6efd"),
                "portal_theme": portal.get("theme", "dark"),
                "available_themes": theme_mgr.get_themes() if theme_mgr else [],
            }
