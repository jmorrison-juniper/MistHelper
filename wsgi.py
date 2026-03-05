"""WSGI entry point for the MistHelper web portal.

Used by Gunicorn in the container:
    gunicorn wsgi:app -w 1 -k gthread --threads 4

Bootstraps API authentication from .env and loads the static
menu registry so the portal is fully functional at startup.
"""

import logging
import os
import sys

# Ensure project root is on sys.path so MistHelper imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _bootstrap_api_session():
    """Create a Mist API session from environment/.env file.

    Returns (apisession, org_id) tuple. Both may be None
    if authentication is not configured.
    """
    apisession = None
    org_id = None
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


def _resolve_org_id(apisession) -> str:
    """Resolve org_id from the authenticated API session."""
    try:
        import mistapi
        resp = mistapi.api.v1.self.self.getSelf(apisession)
        data = resp.data if hasattr(resp, "data") else {}
        privileges = data.get("privileges", [])
        for priv in privileges:
            if priv.get("org_id"):
                return priv["org_id"]
    except Exception as exc:
        logging.warning("WSGI: Could not resolve org_id: %s", exc)
    return ""


apisession, org_id = _bootstrap_api_session()
menu_actions = build_static_menu_actions()

app = WebPortalApp.create_app(
    apisession=apisession,
    menu_actions=menu_actions,
    org_id=org_id,
)
