"""WSGI entry point for the upgrade capture portal.

Why:
    Gunicorn loads one module-level name for each web application. The file
    `wsgi.py` already serves the data browsing portal on port 8055. This file
    keeps the capture portal on port 8056 in its own process, so a fault in one
    portal cannot stop the other. The container starts both processes from
    `container/scripts/start.sh`.

Used by Gunicorn in the container:
    gunicorn wsgi_capture:app -w 1 -k gthread --threads 4
"""

import logging
import os
import sys

# Put the repository root on sys.path, so the import of `src.upgrade_portal`
# resolves. Gunicorn starts from /app in the container and from the repository
# root on a workstation. Neither directory is on sys.path by default.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.upgrade_portal.app.factory import create_app

# Both portals share one record format, so one log file stays readable.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Gunicorn reads this name from the target string `wsgi_capture:app`.
# The factory reads CAPTURE_PORT and every other setting from the environment,
# so this module passes no argument and holds no credential value.
app = create_app()
