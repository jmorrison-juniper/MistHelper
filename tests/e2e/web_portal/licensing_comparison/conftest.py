"""Build an isolated Flask client for licensing comparison route tests."""

from collections.abc import Iterator
from pathlib import Path
from threading import Thread
from types import SimpleNamespace

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_wtf.csrf import CSRFProtect
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.serving import make_server

import src.interfaces.portals.licensing_comparison.api as licensing_api
from src.interfaces.portals.licensing_comparison import licensing_comparison_bp


@pytest.fixture
def licensing_app(tmp_path: Path) -> Iterator[Flask]:
    """Create a test-only app with no Mist credentials or database."""
    portal_root = Path(__file__).resolve().parents[4] / "web_portal"
    app = Flask(__name__, static_folder=str(portal_root / "static"), static_url_path="/static")
    app.jinja_loader = ChoiceLoader([FileSystemLoader(portal_root / "templates")])
    app.config.update(
        TESTING=True,
        SECRET_KEY="licensing-comparison-test-key",
        APISESSION=object(),
        ORG_ID="org-1",
        ORG_NAME="Primary",
        DATA_DIR=str(tmp_path),
        PORTAL={
            "title": "MistHelper",
            "theme": "magenta",
            "accent_color": "#E20074",
            "logo_url": "/static/img/logo-default.svg",
        },
        LICENSING_COMPARISON_NAV_ENABLED=True,
    )  # Keep every route test inside a temporary directory.
    app.jinja_env.globals["csrf_token"] = lambda: "test-csrf-token"  # Supply the shared form token boundary.
    app.register_blueprint(licensing_comparison_bp)  # Register only the isolated feature routes.
    for endpoint, path in (
        ("dashboard.dashboard", "/"),
        ("data.data_browser", "/data"),
        ("operations.operations_page", "/operations"),
        ("maps.maps_page", "/maps"),
        ("websockets.page", "/websockets"),
    ):
        app.add_url_rule(path, endpoint, lambda: "Synthetic shell destination")
    yield app  # Keep the test app available for one test.


@pytest.fixture
def licensing_client(licensing_app: Flask) -> FlaskClient:
    """Return a client that does not start a server or open a port."""
    return licensing_app.test_client()  # Exercise Flask routes in process.


@pytest.fixture
def licensing_portal_url(monkeypatch: pytest.MonkeyPatch, licensing_app: Flask) -> Iterator[str]:
    """Serve the actual shared shell and feature with synthetic SDK responses."""
    CSRFProtect(licensing_app)

    @licensing_app.get("/test-away")
    def away() -> str:
        """Provide a local destination for browser history tests."""
        return "away"

    responses = {
        "getSelf": {"privileges": []},
        "listLicenseTypes": [{"name": "SUB-AI", "key": "sub_ai", "includes": ["SUB-MAN"]}],
        "getOrgLicensesSummary": {"summary": {"SUB-AI": 1, "SUB-MAN": 2}, "entitled": {"SUB-AI": 3}},
        "getOrgLicensesBySite": [],
        "getOrgInventory": [],
    }
    for module, operation in (
        (licensing_api.self_api, "getSelf"),
        (licensing_api.license_types_api, "listLicenseTypes"),
        (licensing_api.licenses_api, "getOrgLicensesSummary"),
        (licensing_api.licenses_api, "getOrgLicensesBySite"),
        (licensing_api.inventory_api, "getOrgInventory"),
    ):
        monkeypatch.setattr(
            module,
            operation,
            lambda *_arguments, _operation=operation, **_keywords: SimpleNamespace(
                status_code=200, data=responses[_operation], next=None
            ),
        )
    monkeypatch.setattr(licensing_api.RateLimitingUtils, "get_rate_limited_delay", lambda *_arguments: (None, 0.0))
    server = make_server("127.0.0.1", 0, licensing_app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
