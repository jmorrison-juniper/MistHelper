"""Store and stop one WebSocket service bundle for each Flask app."""

from __future__ import annotations  # Keep Flask annotations lazy.

import logging  # Structured events use repository handlers.
import threading  # Protect the first service build across request threads.
from typing import Any  # Tests can inject a behavior-compatible service bundle.

from flask import Flask  # Store the bundle on one application.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.mist.realtime.websocket_streams.web.services.assembly.factory import (
    WebSocketServiceFactory,
)  # Build production services.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep lifecycle fields safe and bounded.


class WebSocketServiceRegistry:
    """Build, store, and stop one service bundle for each app."""

    CONFIG_KEY = "WEBSOCKET_SERVICES"  # Keep the established injection key.
    _BUILD_LOCK = threading.Lock()  # Serialize the first production build.

    @classmethod
    def for_app(cls, app: Flask) -> Any:
        """Return the injected or production service bundle."""
        existing = app.config.get(cls.CONFIG_KEY)  # Reuse an injected or completed bundle.
        if existing is not None:  # Tests and prior requests already own this value.
            return existing  # Preserve dependency injection.
        with cls._BUILD_LOCK:  # Prevent duplicate managers and reapers.
            return cls._for_app_locked(app)  # Build or reuse while locked.

    @classmethod
    def stop_for_app(cls, app: Flask) -> None:
        """Stop the app-scoped WebSocket sessions."""
        services = app.config.get(cls.CONFIG_KEY)  # An unused app has no bundle.
        if services is None:  # Avoid building services during shutdown.
            logger.emit(logging.DEBUG, "web.service.stop.skip", {"status": "missing"})  # Record the safe no-op.
            return  # No session manager exists.
        logger.emit(logging.INFO, "web.service.stop.start")  # Record shutdown start.
        services.sessions.lifecycle.shutdown()  # Stop live sessions and the idle reaper.
        logger.emit(logging.DEBUG, "web.service.stop.finish", {"status": "stopped"})  # Confirm shutdown.

    @classmethod
    def _for_app_locked(cls, app: Flask) -> Any:
        """Build or reuse the bundle while the lock is held."""
        existing = app.config.get(cls.CONFIG_KEY)  # Another request may have completed the build.
        if existing is not None:  # Reuse the completed or injected bundle.
            return existing  # Avoid a second manager.
        logger.emit(logging.INFO, "web.service.build.start")  # Record service construction.
        services = WebSocketServiceFactory.build(app)  # Build the complete production bundle.
        app.config[cls.CONFIG_KEY] = services  # Store the bundle before route use.
        logger.emit(logging.DEBUG, "web.service.build.finish", {"status": "ready"})  # Confirm storage.
        return services  # Return the app-owned bundle.
