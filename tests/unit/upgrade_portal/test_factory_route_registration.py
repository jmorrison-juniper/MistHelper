"""Unit tests for upgrade portal route registration.

Why:
    The factory promises every name in `BLUEPRINT_NAMES`. A promised route
    module that cannot import must stop startup, so the portal cannot look
    healthy while an endpoint is absent.
"""

from __future__ import annotations  # Keep annotation evaluation stable during collection.

import pytest  # The test runner checks the raised startup fault.
from flask import Flask  # A small app is enough to exercise blueprint registration.

from src.upgrade_portal.app import factory  # The module under test.


def test_promised_route_import_failure_stops_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """A name listed in `BLUEPRINT_NAMES` must fail loudly when it cannot import."""
    application = Flask(__name__)  # The target app receives no routes after the import fault.
    missing_name = "absent_route"  # A fixed name makes the assertion independent of the real route set.
    monkeypatch.setattr(factory, "BLUEPRINT_NAMES", (missing_name,))  # Limit the test to one promised route.
    with pytest.raises(ModuleNotFoundError):  # The import fault must reach the caller.
        factory.register_blueprints(application)  # Registering a promised route must not hide a broken import.
