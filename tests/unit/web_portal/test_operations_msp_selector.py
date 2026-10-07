"""Tests for the account-aware MSP selector route."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from web_portal.routes.operations import operations_bp


def _client(session: object) -> object:
    """Build a client with one authenticated session."""
    app = Flask(__name__)
    app.config["APISESSION"] = session
    app.register_blueprint(operations_bp)
    return app.test_client()


def test_msp_route_returns_permitted_msp_rows() -> None:
    """The portal exposes permitted MSP rows to the browser selector."""
    response_data = SimpleNamespace(
        status_code=200,
        data={"privileges": [{"msp_id": "msp-1", "msp_name": "MSP One"}]},
    )
    with patch("mistapi.api.v1.self.self.getSelf", return_value=response_data):
        response = _client(object()).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [{"id": "msp-1", "name": "MSP One"}],
        "total_count": 1,
    }


def test_msp_route_returns_multiple_permitted_msp_rows() -> None:
    """The portal returns every permitted MSP grant for a multi-MSP account."""
    response_data = SimpleNamespace(
        status_code=200,
        data={
            "privileges": [
                {"msp_id": "msp-2", "msp_name": "MSP Two"},
                {"msp_id": "msp-1", "msp_name": "MSP One"},
            ]
        },
    )
    with patch("mistapi.api.v1.self.self.getSelf", return_value=response_data):
        response = _client(object()).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [
            {"id": "msp-1", "name": "MSP One"},
            {"id": "msp-2", "name": "MSP Two"},
        ],
        "total_count": 2,
    }


def test_msp_route_explains_missing_msp_scope() -> None:
    """The portal explains that an organization-only account has no MSP scope."""
    response_data = SimpleNamespace(status_code=200, data={"privileges": []})
    with patch("mistapi.api.v1.self.self.getSelf", return_value=response_data):
        response = _client(object()).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "This account has no MSP scope.",
    }


def test_msp_route_names_http_failure_status() -> None:
    """The portal distinguishes a failed MSP lookup from an empty MSP result."""
    response_data = SimpleNamespace(status_code=404, data={"error": "not found"})
    with patch("mistapi.api.v1.self.self.getSelf", return_value=response_data):
        response = _client(object()).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "The Mist API returned status 404 while reading MSP access.",
    }


def test_msp_route_names_server_failure_status() -> None:
    """The portal preserves a server error status in the picker reason."""
    response_data = SimpleNamespace(status_code=500, data={"error": "server error"})
    with patch("mistapi.api.v1.self.self.getSelf", return_value=response_data):
        response = _client(object()).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "The Mist API returned status 500 while reading MSP access.",
    }
