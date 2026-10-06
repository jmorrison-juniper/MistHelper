"""Test that normal startup performs no external action."""

from __future__ import annotations

from typing import Any

import arango.client
import pytest
from flask import Flask


def test_default_factory_startup_opens_no_external_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    """The factory stores construction rules and opens no client."""
    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def refuse(*args: Any, **kwargs: Any) -> None:
        """Record and reject an unexpected startup client."""
        attempts.append((args, kwargs))
        raise AssertionError("Startup opened an ArangoDB client.")

    monkeypatch.setattr(arango.client, "ArangoClient", refuse)
    from src.interfaces.portals.upgrade_portal.app.factory import create_app

    application = create_app()
    assert isinstance(application, Flask)
    assert attempts == []
