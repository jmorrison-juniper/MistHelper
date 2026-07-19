"""WSGI entry point for the MistHelper web portal.

Used by Gunicorn in the container:
    gunicorn wsgi:app -w 1 -k gthread --threads 4

Imports MistHelper as a module (safe: __name__ guard exists),
bootstraps API authentication, injects session globals, and
exposes the real menu_actions with working callables.
"""

import logging
import os
import sys
from typing import Any

# Ensure project root is on sys.path so MistHelper imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_portal.app import WebPortalApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _bootstrap_api_session() -> tuple[Any, str]:
    """Create a Mist API session from environment/.env file.

    Returns (apisession, org_id) tuple. Both may be None
    if authentication is not configured.
    """
    apisession = None
    org_id = ""
    try:
        import mistapi

        env_file = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.isfile(env_file):
            apisession = mistapi.APISession(env_file=env_file)
            apisession.login()
            logging.info("WSGI: API session authenticated from .env")
        else:
            apisession = mistapi.APISession()
            apisession.login()
            logging.info("WSGI: API session authenticated from environment")
        org_id = os.environ.get("MIST_ORG_ID", "")
        if not org_id and apisession:
            org_id = _resolve_org_id(apisession)
    except Exception as exc:
        logging.warning("WSGI: API auth failed (%s) - maps/execution disabled", exc)
        apisession = None
    return apisession, org_id


def _resolve_org_id(apisession: Any) -> str:
    """Resolve org_id from the authenticated API session."""
    try:
        import mistapi

        resp = mistapi.api.v1.self.self.getSelf(apisession)
        data = resp.data if hasattr(resp, "data") else {}
        privileges = data.get("privileges", [])
        for priv in privileges:
            if priv.get("org_id"):
                return str(priv["org_id"])
    except Exception as exc:
        logging.warning("WSGI: Could not resolve org_id: %s", exc)
    return ""


def _load_menu_actions(wsgi_session: Any, wsgi_org_id: str) -> Any:
    """Import MistHelper and extract real menu_actions with live callables.

    Sets MistHelper module globals so lambdas and class methods
    resolve apisession/org_id at call time.  Falls back to the
    static description-only registry on import failure.
    """
    try:
        import MistHelper

        if wsgi_session is not None:
            MistHelper.apisession = wsgi_session
            # Apply timeout adapter so API calls don't hang indefinitely
            MistHelper._configure_session_timeout(wsgi_session)
        if wsgi_org_id:
            MistHelper.org_id = wsgi_org_id
            os.environ["ORG_ID"] = wsgi_org_id
        logging.info("WSGI: MistHelper imported - %d menu actions loaded", len(MistHelper.menu_actions))
        return MistHelper.menu_actions
    except Exception as exc:
        logging.warning("WSGI: MistHelper import failed (%s) - using static registry", exc)
        from web_portal.menu_registry import build_static_menu_actions

        return build_static_menu_actions()


apisession, org_id = _bootstrap_api_session()
menu_actions = _load_menu_actions(apisession, org_id)

app = WebPortalApp.create_app(
    apisession=apisession,
    menu_actions=menu_actions,
    org_id=org_id,
)
