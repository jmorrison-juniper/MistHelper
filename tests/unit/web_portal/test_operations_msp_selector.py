"""Tests for the account-aware MSP selector route."""

from __future__ import annotations

from types import SimpleNamespace

from flask import Flask

from web_portal.routes.operations import operations_bp


class FakeMistSession:
    """Return one controlled self response through the SDK session contract."""

    def __init__(self, response: SimpleNamespace) -> None:
        self.response = response

    def mist_get(self, *, uri: str, query: dict[str, str]) -> SimpleNamespace:
        """Return the response that the SDK self endpoint requests."""
        assert uri == "/api/v1/self"
        assert query == {}
        return self.response


def _client(response: SimpleNamespace) -> object:
    """Build a client with one authenticated fake Mist session."""
    app = Flask(__name__)
    app.config["APISESSION"] = FakeMistSession(response)
    app.register_blueprint(operations_bp)
    return app.test_client()


def test_msp_route_returns_permitted_msp_rows() -> None:
    """The portal exposes permitted MSP rows to the browser selector."""
    response_data = SimpleNamespace(
        status_code=200,
        data={"privileges": [{"msp_id": "msp-1", "msp_name": "MSP One"}]},
    )
    response = _client(response_data).get("/api/operations/msps")

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
    response = _client(response_data).get("/api/operations/msps")

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
    response = _client(response_data).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "This account has no MSP scope.",
    }


def test_msp_route_names_http_failure_status() -> None:
    """The portal distinguishes a failed MSP lookup from an empty MSP result."""
    response_data = SimpleNamespace(status_code=404, data={"error": "not found"})
    response = _client(response_data).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "The Mist API returned status 404 while reading MSP access.",
    }


def test_msp_route_names_server_failure_status() -> None:
    """The portal preserves a server error status in the picker reason."""
    response_data = SimpleNamespace(status_code=500, data={"error": "server error"})
    response = _client(response_data).get("/api/operations/msps")

    assert response.status_code == 200
    assert response.get_json() == {
        "msps": [],
        "total_count": 0,
        "reason": "The Mist API returned status 500 while reading MSP access.",
    }
