"""Expose bounded preview, review, and JSON export without Mist access."""

import io
import logging
from typing import IO

from flask import Blueprint, Flask, Request, Response, jsonify, render_template, request, session
from flask.sansio.blueprints import BlueprintSetupState
from werkzeug.exceptions import BadRequest

from .conversion import IOSDnsConverter
from .models import ReviewState, SourceConfiguration

logger = logging.getLogger(__name__)


class ConverterRequest(Request):
    """Keep converter uploads in memory before the CSRF guard reads form data."""

    def _get_file_stream(
        self,
        total_content_length: int | None,
        content_type: str | None,
        filename: str | None = None,
        content_length: int | None = None,
    ) -> IO[bytes]:
        """Avoid Werkzeug disk spooling only for the converter route family."""
        if self.path.startswith("/cisco-config-converter/"):
            return io.BytesIO()
        return super()._get_file_stream(total_content_length, content_type, filename, content_length)

    @property
    def max_content_length(self) -> int | None:
        """Apply the file and multipart bound before any request-body reader."""
        if self.path.startswith("/cisco-config-converter/"):
            return 16 * 1024 * 1024 + 16 * 1024
        return super().max_content_length

    @max_content_length.setter
    def max_content_length(self, value: int | None) -> None:
        """Preserve Flask request-level overrides for other portal routes."""
        self._max_content_length = value


class ConverterRoutes:
    """Build a feature-owned blueprint without shared portal registration."""

    @classmethod
    def blueprint(cls) -> Blueprint:
        """Return routes for a host that enables CSRF and ConverterRequest."""
        blueprint = Blueprint(
            "cisco_converter",
            __name__,
            url_prefix="/cisco-config-converter",
            template_folder="presentation",
            static_folder="presentation",
            static_url_path="/assets",
        )
        blueprint.record_once(ConverterInput.verify_host)
        blueprint.after_request(ConverterInput.no_store)
        blueprint.add_url_rule("/", view_func=cls.page)
        blueprint.add_url_rule("/preview", view_func=cls.preview, methods=["POST"])
        blueprint.add_url_rule("/review", view_func=cls.review, methods=["POST"])
        blueprint.add_url_rule("/export", view_func=cls.export, methods=["POST"])
        return blueprint

    @staticmethod
    def page() -> str:
        """Render the shared portal shell with no configuration state."""
        return render_template("converter.html")

    @staticmethod
    def preview() -> Response | tuple[Response, int]:
        """Validate an in-memory upload and invalidate previous approval."""
        logger.info("Validating an offline converter upload.")
        session.pop("cisco_proposal", None)
        session.pop("cisco_reviewed", None)
        try:
            source = ConverterInput.source()
            proposal = IOSDnsConverter.convert(source)
            ReviewState.publish(proposal)
        except ValueError as error:
            logger.error("Converter input validation failed: %s", error)
            return jsonify(error=str(error)), 400
        logger.debug("Prepared the current converter preview.")
        return jsonify(proposal)

    @staticmethod
    def review() -> Response | tuple[Response, int]:
        """Bind operator approval to the current proposal."""
        return ConverterInput.action("review")

    @staticmethod
    def export() -> Response | tuple[Response, int]:
        """Return only the exact approved proposal as a JSON download."""
        return ConverterInput.action("export")


class ConverterInput:
    """Validate route input and enforce review state."""

    @staticmethod
    def verify_host(state: BlueprintSetupState) -> None:
        """Fail registration when upload or CSRF protections are absent."""
        if not isinstance(state.app, Flask) or not issubclass(state.app.request_class, ConverterRequest):
            raise ValueError("Set the portal request class to ConverterRequest before registration.")
        if "csrf" not in state.app.extensions or not state.app.config.get("WTF_CSRF_ENABLED", True):
            raise ValueError("Enable CSRFProtect before converter registration.")

    @staticmethod
    def no_store(response: Response) -> Response:
        """Prevent browser caching of transient source-derived responses."""
        response.headers["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def source() -> SourceConfiguration:
        """Read no more than one byte beyond the allowed file limit."""
        upload = request.files.get("file")
        if upload is None or len(request.files) != 1:
            raise ValueError("Select one configuration file.")
        return SourceConfiguration.read(
            upload.filename or "",
            upload.read(16 * 1024 * 1024 + 1),
            request.form.get("name", ""),
            request.form.get("type", ""),
        )

    @staticmethod
    def action(operation: str) -> Response | tuple[Response, int]:
        """Check the entire JSON proposal before approval or export."""
        logger.info("Validating converter %s.", operation)
        try:
            proposal = request.get_json()
            if not isinstance(proposal, dict):
                raise ValueError("Submit a JSON proposal object.")
            ReviewState.verify(proposal, reviewed=operation == "export")
            if operation == "review":
                ReviewState.approve(proposal)
            response = jsonify(proposal)
        except (ValueError, BadRequest) as error:
            logger.error("Converter %s input is invalid (%s).", operation, type(error).__name__)
            return jsonify(error="Submit a valid JSON proposal."), 400
        except LookupError as error:
            logger.error("Converter %s state check failed.", operation)
            return jsonify(error=str(error)), 409
        if operation == "export":
            response.headers["Content-Disposition"] = 'attachment; filename="cisco-proposal.json"'
        response.headers["Cache-Control"] = "no-store"
        logger.debug("Completed converter %s.", operation)
        return response
