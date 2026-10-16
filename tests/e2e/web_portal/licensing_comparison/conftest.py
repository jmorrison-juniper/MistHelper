"""Build an isolated Flask client for licensing comparison route tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask

from src.interfaces.portals.licensing_comparison import licensing_comparison_bp


@pytest.fixture
def licensing_app(tmp_path: Path) -> Iterator[Flask]:
    """Create a test-only app with no Mist credentials or database."""
    app = Flask(__name__)  # Use a local Flask instance, not the production portal.
    app.config.update(
        TESTING=True,
        SECRET_KEY="licensing-comparison-test-key",
        APISESSION=object(),
        ORG_ID="org-1",
        ORG_NAME="Primary",
        DATA_DIR=str(tmp_path),
    )  # Keep every route test inside a temporary directory.
    app.jinja_env.globals["csrf_token"] = lambda: "test-csrf-token"  # Supply the shared form token boundary.
    app.register_blueprint(licensing_comparison_bp)  # Register only the isolated feature routes.
    yield app  # Keep the test app available for one test.


@pytest.fixture
def licensing_client(licensing_app: Flask):
    """Return a client that does not start a server or open a port."""
    return licensing_app.test_client()  # Exercise Flask routes in process.
