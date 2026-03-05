"""WSGI entry point for the MistHelper web portal.

Used by Gunicorn in the container:
    gunicorn wsgi:app -w 1 -k gthread --threads 4

The portal starts without apisession/menu_actions/org_id.
Those are injected when MistHelper authenticates and passes
them into the running app via the --web-portal CLI flag or
container startup.
"""

import logging
import os
import sys

# Ensure project root is on sys.path so MistHelper imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_portal.app import WebPortalApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = WebPortalApp.create_app(
    apisession=None,
    menu_actions={},
    org_id=None,
)
