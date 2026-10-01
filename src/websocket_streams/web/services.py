"""Service assembly for the WebSockets portal routes.

Why:
    Issue #3551. The Flask routes need one seam that builds the catalog, the
    request checker, the picker service, and the session manager for one app.
"""

from __future__ import annotations  # Keep annotations lazy for Flask and agent-owned modules.

import logging  # Use portal logging for setup and shutdown actions.
import threading  # Protect the first service build across request threads.
from collections.abc import Iterator  # Type the JSON Lines download stream.
from dataclasses import dataclass  # Group constructor parts below the parameter limit.
from typing import Any, cast  # Cross-agent services are imported lazily and typed by behavior.

from flask import Flask  # The factory stores services on a Flask app.

from src.websocket_streams.intake.fields import StreamRequestError  # Raise contract errors when not ready.
from src.websocket_streams.intake.pickers import StreamPickerService  # Fill form identifiers from Mist.
from src.websocket_streams.live.sessions.buffer import MessagePage  # Message reads return JSON text parts.

logger = logging.getLogger(__name__)  # Keep service records under this module name.


@dataclass(frozen=True, slots=True)
class WebSocketsServiceParts:
    """Built parts of the WebSockets service.

    Attributes:
        catalog: The stream catalog, or None when imports are not ready.
        checker: The start request checker, or None when the portal is not ready.
        pickers: The picker service, or None when the portal is not ready.
        manager: The session manager object.
        settings: The WebSocket settings object.
        not_ready_reason: The plain reason when the service cannot start streams.
    """

    catalog: Any | None  # Agent A owns the concrete catalog type.
    checker: Any | None  # Agent A owns the concrete checker type.
    pickers: StreamPickerService | None  # The picker service needs a live Mist session.
    manager: Any  # Agent B owns the concrete manager type.
    settings: Any  # Agent B owns the concrete settings type.
    not_ready_reason: str | None  # None means the service can start streams.


class EmptySessionManager:
    """Small manager used while the portal is not ready."""

    def list_payload(self) -> dict[str, object]:
        """Return an empty session list.

        Returns:
            The empty session payload.
        """
        return {"sessions": [], "limits": {"max_sessions": 0, "live_count": 0}}  # No live manager exists.

    def shutdown(self) -> None:
        """Stop nothing.

        Returns:
            None.
        """
        logger.debug("No WebSocket session manager exists to shut down")  # Confirm the no-op path.


class WebSocketsServices:
    """Facade that the Flask blueprint calls."""

    CONFIG_KEY = "WEBSOCKET_SERVICES"  # Tests inject a fake or real service with this key.
    _BUILD_LOCK = threading.Lock()  # One thread builds the production service at a time.

    def __init__(self, parts: WebSocketsServiceParts) -> None:
        """Store the built service parts.

        Args:
            parts: The catalog, checker, picker, manager, settings, and ready state.
        """
        self._parts = parts  # One object keeps the constructor below the parameter limit.

    @classmethod
    def for_app(cls, app: Flask) -> Any:
        """Return the WebSockets service for one Flask app.

        Args:
            app: The Flask application.

        Returns:
            The service object.
        """
        existing = app.config.get(cls.CONFIG_KEY)  # Tests or an earlier request can install the service.
        if isinstance(existing, cls):  # A real service is ready to use.
            return existing  # Reuse the built object.
        if existing is not None:  # Tests can inject a fake service object.
            return existing  # The blueprint calls it by behavior.
        with cls._BUILD_LOCK:  # Only one request can build the service.
            return cls._for_app_locked(app)  # Build or reuse under the lock.

    @classmethod
    def stop_for_app(cls, app: Flask) -> None:
        """Stop WebSocket sessions for one Flask app.

        Args:
            app: The Flask application.
        """
        services = app.config.get(cls.CONFIG_KEY)  # The app may never have built WebSockets.
        if services is None:  # No service means no sessions.
            logger.debug("No WebSocket services object exists for shutdown")  # Confirm the no-op.
            return  # Nothing to stop.
        logger.info("Stopping WebSocket services for the portal")  # Log before session shutdown.
        services.shutdown()  # Stop the manager or fake service.
        logger.debug("Stopped WebSocket services for the portal")  # Confirm shutdown.

    @classmethod
    def _for_app_locked(cls, app: Flask) -> Any:
        """Build or reuse the service while the class lock is held."""
        existing = app.config.get(cls.CONFIG_KEY)  # Another thread may have built it while this thread waited.
        if existing is not None:  # Reuse any injected or built object.
            return existing  # Return the ready object.
        logger.info("Building WebSocket services for the portal")  # Log before construction.
        service = cls(cls._build_parts(app))  # Build each cross-agent part.
        app.config[cls.CONFIG_KEY] = service  # Store the service for later requests.
        if service._parts.not_ready_reason is None:  # Only a ready manager has a reaper.
            service._parts.manager.start_reaper()  # Start the idle session reaper one time.
        logger.debug("Built WebSocket services for the portal")  # Confirm construction.
        return service  # Return the stored service.

    @classmethod
    def _build_parts(cls, app: Flask) -> WebSocketsServiceParts:
        """Build the service parts from app settings."""
        try:  # Agents A and B may still be writing these modules.
            from src.websocket_streams.catalog.channels import ChannelCatalog  # Agent A catalog.
            from src.websocket_streams.catalog.registry import StreamCatalog  # Agent A registry.
            from src.websocket_streams.catalog.utilities import UtilityCatalog  # Agent A utilities.
            from src.websocket_streams.intake.start_request import StartRequestChecker  # Agent A checker.
            from src.websocket_streams.live.sessions.manager import RunnerFactory, StreamSessionManager  # Agent B.
            from src.websocket_streams.live.sessions.settings import StreamSettings  # Agent B settings.
        except ImportError as error:  # The catalog route must still answer not ready.
            logger.warning("WebSocket services are not ready because %s", error.name)  # Name the missing module.
            return cls._not_ready_parts("The WebSocket engine is still loading.")  # Safe empty service.
        settings = StreamSettings.from_environment()  # Read limits and safety flags.
        apisession = app.config.get("APISESSION")  # The portal injects the Mist session here.
        org_id = str(app.config.get("ORG_ID") or "")  # The portal injects the organization here.
        if apisession is None or not org_id:  # A page can load before credentials exist.
            return cls._not_ready_parts("The portal has no Mist session or organization.", settings)  # Not ready.
        pickers = StreamPickerService(apisession, org_id)  # Picker service also describes devices.
        catalog = StreamCatalog(
            ChannelCatalog(),
            UtilityCatalog(),
            changes_enabled=settings.changes_enabled,
            shell_enabled=settings.shell_enabled,
        )  # Catalog.
        checker = StartRequestChecker(catalog, pickers, org_id)  # Request checker uses the picker as directory.
        manager = StreamSessionManager(settings, RunnerFactory(apisession))  # Manager owns live sessions.
        return WebSocketsServiceParts(catalog, checker, pickers, manager, settings, None)  # Ready parts.

    @classmethod
    def _not_ready_parts(cls, reason: str, settings: Any | None = None) -> WebSocketsServiceParts:
        """Build a safe service for a not-ready portal."""
        if settings is None:  # Import failure can also remove the settings class.
            settings = cls._fallback_settings()  # Give the catalog route stable limits.
        return WebSocketsServiceParts(None, None, None, EmptySessionManager(), settings, reason)  # Safe parts.

    @classmethod
    def _fallback_settings(cls) -> Any:
        """Return the minimum settings behavior for an import failure."""

        class FallbackSettings:
            """Settings payload used before Agent B modules import."""

            def limits_payload(self) -> dict[str, int]:
                """Return zero limits while the engine is not ready."""
                return {"max_sessions": 0, "idle_seconds": 0, "capture_seconds": 60}  # Stable shape.

        return FallbackSettings()  # Return a small object with the needed method.

    def catalog_payload(self) -> dict[str, object]:
        """Return the catalog payload for the page.

        Returns:
            The catalog payload with readiness and limits.
        """
        logger.info("Building the WebSocket catalog payload")  # Log before the catalog read.
        payload = self._catalog_base()  # Get catalog data or a safe empty shape.
        payload["ready"] = self._parts.not_ready_reason is None  # Tell the page if starts are allowed.
        payload["reason"] = self._parts.not_ready_reason  # Plain not-ready reason, or None.
        payload["limits"] = self._parts.settings.limits_payload()  # Add current server limits.
        logger.debug("Built the WebSocket catalog payload")  # Confirm the payload build.
        return payload  # Return JSON-safe data.

    def start_session(self, body: object) -> dict[str, object]:
        """Check and start one session.

        Args:
            body: The JSON request body.

        Returns:
            The new session payload.
        """
        self._require_ready()  # A start needs every service part.
        checker = self._checker()  # Mypy needs the non-None checker after the readiness check.
        logger.info("Checking a WebSocket start request")  # Log before validation.
        request = checker.check(body)  # Build a checked request.
        logger.debug("Checked a WebSocket start request for key %s", request.key)  # Log only the key.
        logger.info("Starting a WebSocket session")  # Log before manager start.
        payload = cast(dict[str, object], self._parts.manager.start(request))  # Start the runner.
        logger.debug("Started a WebSocket session with id %s", payload.get("session_id"))  # Log the session id.
        return payload  # Return the session payload.

    def list_sessions(self) -> dict[str, object]:
        """Return the session list payload.

        Returns:
            The manager session list.
        """
        logger.debug("Listing WebSocket sessions")  # Debug level: the page refreshes the list every few seconds.
        payload = cast(dict[str, object], self._parts.manager.list_payload())  # Read live and ended sessions.
        logger.debug("Listed WebSocket sessions")  # Confirm the manager read.
        return payload  # Return the manager payload.

    def read_messages(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Read messages from one session.

        Args:
            session_id: The session identifier.
            after: The last sequence number already read.
            limit: The maximum messages to return.

        Returns:
            The manager read answer, with the records of the returned messages.
        """
        logger.debug("Reading WebSocket messages for session %s", session_id)  # The page polls each second.
        page = cast(MessagePage, self._parts.manager.read(session_id, after, limit))  # Read the buffer.
        logger.debug(
            "Read %s WebSocket messages for session %s", len(page.messages), session_id
        )  # Confirm the read with the count only.
        return page  # Return the manager read answer.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Stop one session.

        Args:
            session_id: The session identifier.

        Returns:
            The stopped session payload.
        """
        logger.info("Stopping WebSocket session %s", session_id)  # Log before the stop.
        payload = cast(dict[str, object], self._parts.manager.stop(session_id))  # Ask the manager to stop it.
        logger.debug("Stopped WebSocket session %s", session_id)  # Confirm the stop request.
        return payload  # Return the manager payload.

    def send_input(self, session_id: str, body: object) -> dict[str, object]:
        """Send shell input to one session.

        Args:
            session_id: The session identifier.
            body: The JSON request body.

        Returns:
            A small confirmation payload.
        """
        payload = body if isinstance(body, dict) else {}  # Only JSON objects can hold input.
        line = payload.get("line") if isinstance(payload.get("line"), str) else None  # Optional line.
        key = payload.get("key") if isinstance(payload.get("key"), str) else None  # Optional key.
        logger.info("Sending WebSocket shell input for session %s", session_id)  # Log before input send.
        self._parts.manager.send_input(session_id, line, key)  # Manager validates and sends the input.
        logger.debug("Sent WebSocket shell input for session %s", session_id)  # Never log the input text.
        return {"ok": True}  # The route returns 202 with this payload.

    def delete_session(self, session_id: str) -> dict[str, object]:
        """Delete one ended session.

        Args:
            session_id: The session identifier.

        Returns:
            A small confirmation payload.
        """
        logger.info("Deleting WebSocket session %s", session_id)  # Log before deletion.
        self._parts.manager.delete(session_id)  # The manager refuses live sessions.
        logger.debug("Deleted WebSocket session %s", session_id)  # Confirm deletion.
        return {"ok": True}  # The route returns this payload.

    def download_session(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return the download stream of one session.

        Args:
            session_id: The session identifier.

        Returns:
            The file name and the JSON Lines iterator.
        """
        logger.info("Creating WebSocket download for session %s", session_id)  # Log before download build.
        filename, lines = self._parts.manager.download(session_id)  # Ask manager for JSON Lines.
        logger.debug("Created WebSocket download for session %s", session_id)  # Confirm without reading lines.
        return filename, lines  # Return stream parts.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return device picker rows."""
        return self._pickers().devices(site_id)  # Delegate to the picker service.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return map picker rows."""
        return self._pickers().maps(site_id)  # Delegate to the picker service.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return asset picker rows."""
        return self._pickers().assets(site_id)  # Delegate to the picker service.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return SDK client picker rows."""
        return self._pickers().sdkclients(site_id, map_id)  # Delegate to the picker service.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return Mist Edge picker rows."""
        return self._pickers().mxedges(site_id)  # Delegate to the picker service.

    def shutdown(self) -> None:
        """Stop all WebSocket sessions and helper threads."""
        logger.info("Shutting down the WebSocket session manager")  # Log before manager shutdown.
        self._parts.manager.shutdown()  # Stop sessions and the reaper.
        logger.debug("Shut down the WebSocket session manager")  # Confirm manager shutdown.

    def _catalog_base(self) -> dict[str, object]:
        """Return catalog data or an empty catalog shape."""
        if self._parts.catalog is None:  # Missing imports or missing credentials can leave no catalog.
            return {"flags": {}, "channels": [], "utilities": []}  # Keep the page payload shape stable.
        payload = self._parts.catalog.page_payload()  # Catalog owns path redaction.
        if not isinstance(payload, dict):  # A defensive check prevents a bad catalog from leaking.
            return {"flags": {}, "channels": [], "utilities": []}  # Keep a safe shape.
        return payload  # Return the catalog payload.

    def _require_ready(self) -> None:
        """Raise when a route needs a ready Mist service."""
        if self._parts.not_ready_reason is not None:  # The page can load, but starts and pickers cannot run.
            raise StreamRequestError("not_ready", self._parts.not_ready_reason)  # Contract not-ready error.
        if self._parts.checker is None or self._parts.pickers is None:  # Defensive check for partial builds.
            raise StreamRequestError("not_ready", "The WebSocket engine is not ready.")  # Contract error.

    def _checker(self) -> Any:
        """Return the ready start request checker."""
        self._require_ready()  # The checker must exist before use.
        return self._parts.checker  # Return the Agent A checker.

    def _pickers(self) -> StreamPickerService:
        """Return the ready picker service."""
        self._require_ready()  # The picker must exist before use.
        return cast(StreamPickerService, self._parts.pickers)  # Return the non-None picker service.
