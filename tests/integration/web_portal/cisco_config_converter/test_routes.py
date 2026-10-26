"""Exercise preview, review, and export with real CSRF protection."""

import io
import json
import re
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from flask import Flask, request
from flask.testing import FlaskClient
from flask_wtf.csrf import CSRFProtect
from jinja2 import DictLoader

from src.interfaces.portals.cisco_config_converter.routes import ConverterRequest, ConverterRoutes


@pytest.fixture
def client() -> Iterator[FlaskClient]:
    """Mount only the feature blueprint without any Mist runtime."""
    app = Flask(__name__)
    app.request_class = ConverterRequest
    app.config.update(TESTING=True, SECRET_KEY="isolated-test-session")
    app.jinja_loader = DictLoader(
        {
            "base.html": (
                '<meta name="csrf-token" content="{{ csrf_token() }}">'
                "{% block content %}{% endblock %}{% block extra_scripts %}{% endblock %}"
            )
        }
    )
    CSRFProtect(app)
    app.register_blueprint(ConverterRoutes.blueprint())
    with app.test_client() as test_client:
        yield test_client


class TestConverterRoutes:
    """Verify the offline HTTP boundary and digest state machine."""

    @staticmethod
    def token(client: FlaskClient) -> str:
        """Read the same CSRF token that the browser uses."""
        response = client.get("/cisco-config-converter/")
        assert response.status_code == 200
        match = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
        assert match is not None
        return match.group(1)

    @staticmethod
    def preview(client: FlaskClient, token: str, content: bytes = b"ip name-server 192.0.2.1") -> dict:
        """Submit an original fixture through the multipart boundary."""
        response = client.post(
            "/cisco-config-converter/preview",
            data={"csrf_token": token, "file": (io.BytesIO(content), "sample.cfg"), "name": "Branch", "type": "spoke"},
        )
        assert response.status_code == 200, response.text
        return response.json

    def test_complete_offline_journey(self, client: FlaskClient, caplog: pytest.LogCaptureFixture) -> None:
        """Export the exact review without network calls or file writes."""
        token = self.token(client)
        with (
            patch("socket.socket.connect", side_effect=AssertionError("Network access")),
            patch("builtins.open", side_effect=AssertionError("File access")),
        ):
            proposal = self.preview(client, token)
            headers = {"X-CSRFToken": token}
            reviewed = client.post("/cisco-config-converter/review", json=proposal, headers=headers)
            exported = client.post("/cisco-config-converter/export", json=proposal, headers=headers)
        assert reviewed.status_code == 200
        assert exported.status_code == 200
        assert exported.json == proposal
        assert "attachment" in exported.headers["Content-Disposition"]
        assert "192.0.2.1" not in caplog.text
        with client.session_transaction() as state:
            assert "192.0.2.1" not in json.dumps(dict(state))
            assert "gateway_template" not in state

    def test_review_required_and_edited_rejected(self, client: FlaskClient) -> None:
        """Reject unreviewed, edited, and stale proposals."""
        token = self.token(client)
        headers = {"X-CSRFToken": token}
        proposal = self.preview(client, token)
        assert client.post("/cisco-config-converter/export", json=proposal, headers=headers).status_code == 409
        assert client.post("/cisco-config-converter/review", json=proposal, headers=headers).status_code == 200
        changed = json.loads(json.dumps(proposal))
        changed["gateway_template"]["name"] = "Edited"
        assert client.post("/cisco-config-converter/export", json=changed, headers=headers).status_code == 409
        self.preview(client, token, b"ip name-server 192.0.2.2")
        assert client.post("/cisco-config-converter/export", json=proposal, headers=headers).status_code == 409

    @pytest.mark.parametrize("route", ["preview", "review", "export"])
    def test_csrf_required(self, client: FlaskClient, route: str) -> None:
        """All state-changing routes reject requests without a token."""
        assert client.post("/cisco-config-converter/" + route, json={}).status_code == 400

    def test_invalid_requests(self, client: FlaskClient) -> None:
        """Reject invalid input, malformed JSON, and an oversized request."""
        token = self.token(client)
        headers = {"X-CSRFToken": token}
        assert client.post("/cisco-config-converter/preview", data={"csrf_token": token}).status_code == 400
        assert client.post("/cisco-config-converter/review", json=[], headers=headers).status_code == 400
        assert (
            client.post(
                "/cisco-config-converter/export", data="{", content_type="application/json", headers=headers
            ).status_code
            == 400
        )
        response = client.post(
            "/cisco-config-converter/preview",
            data={
                "csrf_token": token,
                "file": (io.BytesIO(b"!" * (16 * 1024 * 1024 + 1)), "sample.cfg"),
                "name": "Branch",
                "type": "spoke",
            },
        )
        assert response.status_code == 400


class TestUploadProtection:
    """Prove request bounds and in-memory handling before CSRF form parsing."""

    def test_exact_boundary_without_disk_spooling(self, client: FlaskClient) -> None:
        """Keep an accepted 16 MiB upload out of temporary files."""
        from werkzeug.test import EnvironBuilder

        token = TestConverterRoutes.token(client)
        data = {
            "csrf_token": token,
            "file": (io.BytesIO(b"!\n" * (8 * 1024 * 1024)), "sample.cfg"),
            "name": "Branch",
            "type": "spoke",
        }
        builder = EnvironBuilder(path="/cisco-config-converter/preview", method="POST", data=data)
        environ = builder.get_environ()
        with patch("werkzeug.formparser.SpooledTemporaryFile", side_effect=AssertionError("Disk spooling")):
            response = client.open(environ)
        builder.close()
        assert response.status_code == 200
        assert "dns_servers" not in response.json["gateway_template"]

    def test_request_overhead_boundary(self, client: FlaskClient) -> None:
        """Reject a body above the file limit and form allowance."""
        token = TestConverterRoutes.token(client)
        response = client.post(
            "/cisco-config-converter/preview",
            data=b"x" * (16 * 1024 * 1024 + 16 * 1024 + 1),
            content_type="multipart/form-data; boundary=original",
            headers={"X-CSRFToken": token},
        )
        assert response.status_code == 413

    @pytest.mark.parametrize("filename", ["../sample.cfg", "C:\\sample.cfg", "sample.exe"])
    def test_path_rejection(self, client: FlaskClient, filename: str) -> None:
        """Reject unsafe file names through the public upload route."""
        token = TestConverterRoutes.token(client)
        response = client.post(
            "/cisco-config-converter/preview",
            data={
                "csrf_token": token,
                "file": (io.BytesIO(b"hostname sample"), filename),
                "name": "Branch",
                "type": "spoke",
            },
        )
        assert response.status_code == 400
        assert "error" in response.json

    def test_failed_preview_revokes_review(self, client: FlaskClient) -> None:
        """A failed upload cannot retain approval for a previous proposal."""
        token = TestConverterRoutes.token(client)
        proposal = TestConverterRoutes.preview(client, token)
        headers = {"X-CSRFToken": token}
        assert client.post("/cisco-config-converter/review", json=proposal, headers=headers).status_code == 200
        assert client.post("/cisco-config-converter/preview", data={"csrf_token": token}).status_code == 400
        assert client.post("/cisco-config-converter/export", json=proposal, headers=headers).status_code == 409

    def test_registration_fails_without_protection(self) -> None:
        """Reject a host that could spool uploads or disable CSRF."""
        app = Flask(__name__)
        with pytest.raises(ValueError, match="ConverterRequest"):
            app.register_blueprint(ConverterRoutes.blueprint())
        app = Flask(__name__)
        app.request_class = ConverterRequest
        with pytest.raises(ValueError, match="CSRFProtect"):
            app.register_blueprint(ConverterRoutes.blueprint())


class TestHostCompatibility:
    """Keep non-converter request behavior unchanged."""

    def test_other_uploads_keep_flask_behavior(self) -> None:
        """Preserve the host limit, request override, and default file stream."""
        app = Flask(__name__)
        app.request_class = ConverterRequest
        app.config["MAX_CONTENT_LENGTH"] = 2048
        with app.test_request_context(
            "/existing-upload", method="POST", data={"file": (io.BytesIO(b"original"), "sample.txt")}
        ):
            assert request.max_content_length == 2048
            request.max_content_length = 1024
            assert request.max_content_length == 1024
            assert request.files["file"].read() == b"original"
