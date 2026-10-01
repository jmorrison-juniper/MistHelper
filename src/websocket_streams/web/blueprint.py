"""Flask routes for the WebSockets portal tab.

Why:
    Issue #3551. The browser uses these short routes to list the catalog,
    start streams, read messages, and send safe shell input through the server.
    Issue #3671. The terminal routes read the terminal bytes, send the keys and
    the pasted text without a change, and send the terminal size.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

import logging  # Use the portal logger for each route action.
import math  # Refuse a wait value that is not a finite number.
import re  # Validate identifiers until the shared rules module is present.
from collections.abc import Callable  # Type route helpers and streamed lines.
from typing import Any, cast  # Flask service objects use dependency injection.

from flask import Blueprint, Response, current_app, jsonify, render_template, request  # Build the blueprint routes.

from src.websocket_streams.intake.fields import StreamRequestError  # Convert request refusals to JSON.

logger = logging.getLogger(__name__)  # Keep route records under this module name.

websockets_bp = Blueprint(  # The web portal registers this blueprint in the application factory.
    "websockets",  # Route endpoint prefix.
    __name__,  # Let Flask find templates and static files near this module.
    template_folder="templates",  # Store the page inside the gated source package.
    static_folder="static",  # Store the script and stylesheet inside the package.
    static_url_path="/websockets/assets",  # Serve static files below the WebSockets path.
)


class TerminalRequestValues:
    """Convert the values of one terminal request to checked Python values.

    The routes refuse a bad value shape at once. The terminal gateway checks
    each range, so one class owns each limit of the terminal contract.
    """

    MAX_WAIT_SECONDS = 25.0  # The contract holds one read for 25 seconds at most.

    @staticmethod
    def read_query() -> tuple[int, float]:
        """Return the checked ``after`` and ``wait`` values of a terminal read.

        Returns:
            The byte position after which the read starts, and the wait in seconds.

        Raises:
            StreamRequestError: A value is not a number, or the wait is outside 0 to 25 seconds.
        """
        after_text = request.args.get("after", "0")  # A missing position starts at the oldest kept byte.
        wait_text = request.args.get("wait", "0")  # A missing wait answers at once.
        if not after_text.isdecimal():  # Only a whole number names a byte position.
            raise StreamRequestError(
                "bad_request", "The after value must be a whole number.", {"field": "after"}
            )  # Refuse before the gateway runs.
        wait = TerminalRequestValues._wait_seconds(wait_text)  # Check the wait text and its range.
        return int(after_text), wait  # The gateway checks the position against the history.

    @staticmethod
    def input_text(body: object) -> str:
        """Return the text of a terminal input body.

        Args:
            body: The JSON body of the request.

        Returns:
            The keys or the pasted text, without a change.

        Raises:
            StreamRequestError: The body holds no text in the ``data`` field.
        """
        data = body.get("data") if isinstance(body, dict) else None  # Only a JSON object can hold the text.
        if not isinstance(data, str) or data == "":  # The old line and key shapes have no data field.
            raise StreamRequestError(
                "bad_request", "The input must hold text in the data field.", {"field": "data"}
            )  # Refuse the old body shapes.
        return data  # The gateway checks the size and sends the text without a change.

    @staticmethod
    def size(body: object) -> tuple[int, int]:
        """Return the columns and the rows of a terminal resize body.

        Args:
            body: The JSON body of the request.

        Returns:
            The column count and the row count.

        Raises:
            StreamRequestError: A size value is not a whole number.
        """
        values = body if isinstance(body, dict) else {}  # Only a JSON object can hold the size.
        for field in ("cols", "rows"):  # Check each size value in the same way.
            value = values.get(field)  # Read one size value.
            if isinstance(value, bool) or not isinstance(value, int):  # JSON true is not a size.
                raise StreamRequestError(
                    "bad_request", "The terminal size must be whole numbers.", {"field": field}
                )  # Refuse before the gateway runs.
        return int(values["cols"]), int(values["rows"])  # The gateway checks the size range.

    @staticmethod
    def _wait_seconds(text: str) -> float:
        """Return the checked wait in seconds.

        Args:
            text: The ``wait`` query text.

        Returns:
            The wait in seconds, from 0 to 25.

        Raises:
            StreamRequestError: The text is not a finite number from 0 to 25.
        """
        try:  # The query holds text, so convert it first.
            wait = float(text)  # Accept a whole number or a decimal number.
        except ValueError:  # The text is not a number.
            wait = -1.0  # Use a value outside the range, so one check refuses both cases.
        if not math.isfinite(wait) or not 0.0 <= wait <= TerminalRequestValues.MAX_WAIT_SECONDS:  # Range check.
            raise StreamRequestError(
                "bad_request", "The wait value must be a number from 0 to 25.", {"field": "wait"}
            )  # Refuse before a thread waits.
        return wait  # The gateway waits for this time at most.


class WebSocketRouteViews:
    """Route handlers for the WebSockets blueprint."""

    @staticmethod
    def page() -> str:
        """Render the WebSockets page.

        Returns:
            The rendered page.
        """
        logger.info("Rendering the WebSockets page")  # Log before the template render.
        html: str = render_template("websockets_page.html")  # Render the page shell.
        logger.debug("Rendered the WebSockets page with %d characters", len(html))  # Log the size only.
        return html  # Flask accepts the rendered HTML text.

    @staticmethod
    def catalog() -> Response | tuple[Response, int]:
        """Return the WebSockets catalog payload.

        Returns:
            A JSON response.
        """
        return WebSocketRouteViews._json_call(lambda services: services.catalog_payload())  # One service call.

    @staticmethod
    def sessions() -> Response | tuple[Response, int]:
        """List or start sessions.

        Returns:
            A JSON response with the session list or the new session.
        """
        if request.method == "POST":  # A POST starts one checked session.
            return WebSocketRouteViews._json_call(
                lambda services: services.start_session(request.get_json(silent=True)), 201
            )  # Start.
        return WebSocketRouteViews._json_call(lambda services: services.list_sessions())  # List sessions.

    @staticmethod
    def messages(session_id: str) -> Response | tuple[Response, int]:
        """Return messages after one sequence number.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response with new messages.
        """
        parsed = WebSocketRouteViews._message_query()  # Validate query numbers before service use.
        if isinstance(parsed, StreamRequestError):  # Bad query values refuse the request.
            return jsonify(parsed.to_payload()), parsed.status  # Return the standard error shape.
        after, limit = parsed  # The query now holds integers.
        try:  # The service can refuse an unknown session.
            logger.debug("Reading WebSocket messages for session %s", session_id)  # Debug level: the page polls often.
            page = WebSocketRouteViews._services().read_messages(session_id, after, limit)  # Read one answer.
            body = page.to_json_text()  # The stored message text joins the answer with no decode step.
            logger.debug("Read WebSocket messages with %d characters", len(body))  # Log the size only.
            return Response(body, mimetype="application/json")  # Send the JSON text as it is.
        except StreamRequestError as error:  # Convert a service refusal.
            logger.debug("WebSocket message read refused with code %s", error.code)  # Log only the code.
            return jsonify(error.to_payload()), error.status  # Return the standard error shape.

    @staticmethod
    def stop(session_id: str) -> Response | tuple[Response, int]:
        """Stop one session.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response with the session state.
        """
        return WebSocketRouteViews._json_call(lambda services: services.stop_session(session_id), 202)  # Stop.

    @staticmethod
    def send_input(session_id: str) -> Response | tuple[Response, int]:
        """Send keys or pasted text to the terminal of one shell session.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response with the accepted byte count and the queue state.
        """
        body = request.get_json(silent=True)  # A missing or bad JSON body becomes None, and the check refuses it.
        return WebSocketRouteViews._json_call(
            lambda services: services.terminal().send(session_id, TerminalRequestValues.input_text(body)), 202
        )  # Send the text without a change.

    @staticmethod
    def terminal(session_id: str) -> Response | tuple[Response, int]:
        """Read the terminal bytes of one session after one byte position.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response with the next terminal bytes.
        """
        return WebSocketRouteViews._json_call(
            lambda services: services.terminal().read(session_id, *TerminalRequestValues.read_query())
        )  # Read and wait for new bytes.

    @staticmethod
    def resize(session_id: str) -> Response | tuple[Response, int]:
        """Send the terminal size of one shell session.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response with the stored size.
        """
        body = request.get_json(silent=True)  # A missing or bad JSON body becomes None, and the check refuses it.
        return WebSocketRouteViews._json_call(
            lambda services: services.terminal().resize(session_id, *TerminalRequestValues.size(body)), 202
        )  # Store and send the size.

    @staticmethod
    def delete(session_id: str) -> Response | tuple[Response, int]:
        """Delete one ended session.

        Args:
            session_id: The session identifier.

        Returns:
            A JSON response that confirms deletion.
        """
        return WebSocketRouteViews._json_call(lambda services: services.delete_session(session_id))  # Delete.

    @staticmethod
    def download(session_id: str) -> Response | tuple[Response, int]:
        """Download one session buffer as JSON Lines.

        Args:
            session_id: The session identifier.

        Returns:
            A streamed download response.
        """
        try:  # Stream setup can still refuse an unknown session.
            logger.info("Preparing a WebSocket session download for %s", session_id)  # Log before the service call.
            filename, lines = WebSocketRouteViews._services().download_session(session_id)  # Get the stream parts.
            logger.debug("Prepared WebSocket session download %s", filename)  # Log the file name only.
            return Response(
                lines,
                mimetype="application/x-ndjson",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )  # Stream.
        except StreamRequestError as error:  # Convert a service refusal.
            logger.debug("WebSocket download refused with code %s", error.code)  # Log only the code.
            return jsonify(error.to_payload()), error.status  # Return the standard error shape.

    @staticmethod
    def devices(site_id: str) -> Response | tuple[Response, int]:
        """Return device picker rows.

        Args:
            site_id: The site identifier.

        Returns:
            A JSON response with picker rows.
        """
        if not WebSocketRouteViews._valid_uuid(site_id):  # A route identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("site_id")  # Refuse before service use.
        return WebSocketRouteViews._json_call(lambda services: services.devices(site_id))  # Read picker rows.

    @staticmethod
    def maps(site_id: str) -> Response | tuple[Response, int]:
        """Return map picker rows.

        Args:
            site_id: The site identifier.

        Returns:
            A JSON response with picker rows.
        """
        if not WebSocketRouteViews._valid_uuid(site_id):  # A route identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("site_id")  # Refuse before service use.
        return WebSocketRouteViews._json_call(lambda services: services.maps(site_id))  # Read picker rows.

    @staticmethod
    def assets(site_id: str) -> Response | tuple[Response, int]:
        """Return asset picker rows.

        Args:
            site_id: The site identifier.

        Returns:
            A JSON response with picker rows.
        """
        if not WebSocketRouteViews._valid_uuid(site_id):  # A route identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("site_id")  # Refuse before service use.
        return WebSocketRouteViews._json_call(lambda services: services.assets(site_id))  # Read picker rows.

    @staticmethod
    def sdkclients(site_id: str, map_id: str) -> Response | tuple[Response, int]:
        """Return SDK client picker rows.

        Args:
            site_id: The site identifier.
            map_id: The map identifier.

        Returns:
            A JSON response with picker rows.
        """
        if not WebSocketRouteViews._valid_uuid(site_id):  # A route identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("site_id")  # Refuse before service use.
        if not WebSocketRouteViews._valid_uuid(map_id):  # A route identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("map_id")  # Refuse before service use.
        return WebSocketRouteViews._json_call(lambda services: services.sdkclients(site_id, map_id))  # Read rows.

    @staticmethod
    def mxedges() -> Response | tuple[Response, int]:
        """Return Mist Edge picker rows.

        Returns:
            A JSON response with picker rows.
        """
        site_id = request.args.get("site_id")  # The query can narrow the picker to one site.
        if site_id and not WebSocketRouteViews._valid_uuid(site_id):  # A query identifier must be a UUID.
            return WebSocketRouteViews._bad_identifier("site_id")  # Refuse before service use.
        return WebSocketRouteViews._json_call(lambda services: services.mxedges(site_id))  # Read picker rows.

    @staticmethod
    def _services() -> Any:
        """Return the service object for the current app.

        Returns:
            The WebSockets service object.
        """
        from src.websocket_streams.web.services import WebSocketsServices  # Import lazily to avoid cycles.

        logger.debug("Loading the WebSockets service object")  # Debug level: every API request runs this lookup.
        app = cast(Any, current_app)._get_current_object()  # Resolve the Flask local proxy for typing.
        services = WebSocketsServices.for_app(app)  # Build or reuse the service object.
        logger.debug("Loaded the WebSockets service object")  # Confirm the dependency lookup.
        return services  # Return the injected or built service object.

    @staticmethod
    def _json_call(
        action: Callable[[Any], dict[str, object] | None], success: int = 200
    ) -> Response | tuple[Response, int]:
        """Call one service method and return JSON.

        Args:
            action: The service method call.
            success: The success HTTP status.

        Returns:
            A JSON response and optional status.
        """
        try:  # Each service method can refuse the request with a contract error.
            logger.debug("Handling a WebSocket API request")  # Debug level: the service method logs each real action.
            payload = action(WebSocketRouteViews._services()) or {"ok": True}  # Call exactly one service action.
            logger.debug("Handled a WebSocket API request with keys %s", sorted(payload.keys()))  # Log keys only.
            return (jsonify(payload), success) if success != 200 else jsonify(payload)  # Send JSON.
        except StreamRequestError as error:  # Convert a service refusal.
            logger.debug("WebSocket API request refused with code %s", error.code)  # Log only the code.
            return jsonify(error.to_payload()), error.status  # Return the standard error shape.

    @staticmethod
    def _message_query() -> tuple[int, int] | StreamRequestError:
        """Return checked message query numbers, or a refusal."""
        after_text = request.args.get("after", "0")  # Missing after starts at the beginning.
        limit_text = request.args.get("limit", "200")  # Missing limit uses the contract default.
        if not after_text.isdecimal():  # Only whole numbers are accepted.
            return StreamRequestError(
                "bad_request", "The after value must be a whole number.", {"field": "after"}
            )  # Error.
        if not limit_text.isdecimal():  # Only whole numbers are accepted.
            return StreamRequestError(
                "bad_request", "The limit value must be a whole number.", {"field": "limit"}
            )  # Error.
        return int(after_text), int(limit_text)  # The manager clamps the limit range.

    @staticmethod
    def _valid_uuid(value: object) -> bool:
        """Return true when the shared rules accept the identifier."""
        try:  # Agent A owns the shared identifier rules.
            from src.websocket_streams.intake.identifiers import IdentifierRules  # Import only when a picker runs.

            return bool(IdentifierRules.is_uuid(value))  # Use the shared rule when it exists.
        except ImportError:  # Agent A may still be writing the shared module.
            text = str(value)  # The fallback protects current route tests.
            pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"  # UUID.
            return re.fullmatch(pattern, text) is not None  # Match the contract UUID shape.

    @staticmethod
    def _bad_identifier(field: str) -> tuple[Response, int]:
        """Return the standard bad identifier answer."""
        error = StreamRequestError("bad_request", "The identifier is not valid.", {"field": field})  # Build refusal.
        return jsonify(error.to_payload()), error.status  # Return the standard error shape.


websockets_bp.add_url_rule("/websockets", view_func=WebSocketRouteViews.page)  # Page route.
websockets_bp.add_url_rule("/api/websockets/catalog", view_func=WebSocketRouteViews.catalog)  # Catalog route.
websockets_bp.add_url_rule(
    "/api/websockets/sessions", view_func=WebSocketRouteViews.sessions, methods=["GET", "POST"]
)  # List and start.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/messages", view_func=WebSocketRouteViews.messages
)  # Read.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/stop", view_func=WebSocketRouteViews.stop, methods=["POST"]
)  # Stop.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/input", view_func=WebSocketRouteViews.send_input, methods=["POST"]
)  # Input.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/terminal", view_func=WebSocketRouteViews.terminal
)  # Terminal read.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/resize", view_func=WebSocketRouteViews.resize, methods=["POST"]
)  # Terminal size.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>", view_func=WebSocketRouteViews.delete, methods=["DELETE"]
)  # Delete.
websockets_bp.add_url_rule(
    "/api/websockets/sessions/<session_id>/download", view_func=WebSocketRouteViews.download
)  # Download.
websockets_bp.add_url_rule("/api/websockets/sites/<site_id>/devices", view_func=WebSocketRouteViews.devices)  # Devices.
websockets_bp.add_url_rule("/api/websockets/sites/<site_id>/maps", view_func=WebSocketRouteViews.maps)  # Maps.
websockets_bp.add_url_rule("/api/websockets/sites/<site_id>/assets", view_func=WebSocketRouteViews.assets)  # Assets.
websockets_bp.add_url_rule(
    "/api/websockets/sites/<site_id>/maps/<map_id>/sdkclients", view_func=WebSocketRouteViews.sdkclients
)  # Clients.
websockets_bp.add_url_rule("/api/websockets/mxedges", view_func=WebSocketRouteViews.mxedges)  # Mist Edges.
