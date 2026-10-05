"""Build ready or not-ready WebSocket service bundles."""

from __future__ import annotations  # Keep Flask and collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any  # Cross-package collaborators use behavior types.

from flask import Flask  # Read portal configuration.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.mist.realtime.websocket_streams.web.services.assembly.bundle import (
    PickerServices,
    SessionServices,
    WebSocketServiceBundle,
)  # Return the grouped leaf services.
from src.mist.realtime.websocket_streams.web.services.assembly.collaborators import (
    WebSocketCollaboratorFactory,
    WebSocketCollaborators,
)  # Build production collaborators.
from src.mist.realtime.websocket_streams.web.services.assembly.fallback import (
    EmptySessionManager,
    FallbackSettings,
)  # Safe fallback.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import (
    SessionArtifactService,
)  # Delete and download.
from src.mist.realtime.websocket_streams.web.services.operations.catalog import (
    WebSocketCatalogService,
)  # Catalog payload.
from src.mist.realtime.websocket_streams.web.services.operations.sessions import (
    WebSocketMessageService,
    WebSocketSessionService,
)  # Session lifecycle and message reads.
from src.mist.realtime.websocket_streams.web.services.operations.terminal import (
    WebSocketTerminalService,
)  # Terminal actions.
from src.mist.realtime.websocket_streams.web.services.pickers.related import (
    RelatedPickerService,
)  # Related picker actions.
from src.mist.realtime.websocket_streams.web.services.pickers.service import (
    ClientSuggestionService,
    SitePickerService,
)  # Site and client suggestion actions.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep assembly fields safe and bounded.


class WebSocketServiceFactory:
    """Build the route-facing service bundle."""

    @classmethod
    def build(cls, app: Flask) -> WebSocketServiceBundle:
        """Build a ready bundle or a safe not-ready bundle."""
        try:  # A partial installation must keep the catalog route available.
            collaborators = WebSocketCollaboratorFactory.build(app)  # Build production collaborators.
        except ImportError as error:  # A missing feature module creates a safe fallback.
            logger.emit(logging.WARNING, "web.service.import.error", {"detail": error.name or "unknown"})  # Bound name.
            return cls.not_ready("The WebSocket engine is still loading.")  # Preserve the public reason.
        if collaborators is None:  # Missing credentials keep the page in not-ready mode.
            settings = WebSocketCollaboratorFactory.settings()  # Preserve environment limit reporting.
            return cls.not_ready("The portal has no Mist session or organization.", settings)  # Safe bundle.
        return cls._ready(collaborators)  # Build and start the production manager.

    @classmethod
    def not_ready(cls, reason: str, settings: Any | None = None) -> WebSocketServiceBundle:
        """Build a safe service bundle for a not-ready portal."""
        collaborators = WebSocketCollaborators(
            None, None, None, EmptySessionManager(), settings or FallbackSettings()
        )  # Supply safe fallback collaborators.
        return cls._bundle(collaborators, reason)  # Build guarded leaf services.

    @classmethod
    def from_collaborators(
        cls, collaborators: WebSocketCollaborators, reason: str | None = None
    ) -> WebSocketServiceBundle:
        """Build a bundle from explicit collaborators."""
        return cls._bundle(collaborators, reason)  # Support deterministic tests without app construction.

    @staticmethod
    def _ready(collaborators: WebSocketCollaborators) -> WebSocketServiceBundle:
        """Build and start a ready bundle."""
        bundle = WebSocketServiceFactory._bundle(collaborators, None)  # Build the ready leaf services.
        collaborators.manager.start_reaper()  # Start the idle-session reaper once.
        return bundle  # Return the ready route services.

    @staticmethod
    def _bundle(collaborators: WebSocketCollaborators, reason: str | None) -> WebSocketServiceBundle:
        """Build all route-facing leaf services."""
        catalog = WebSocketCatalogService(collaborators.catalog, collaborators.settings, reason)  # Build catalog.
        lifecycle = WebSocketSessionService(collaborators.checker, collaborators.manager, reason)  # Build lifecycle.
        messages = WebSocketMessageService(collaborators.manager)  # Build message reads.
        artifacts = SessionArtifactService(collaborators.manager, reason)  # Build deletion and downloads.
        terminal = WebSocketTerminalService(collaborators.manager, reason)  # Build terminal actions.
        site_pickers = SitePickerService(collaborators.picker, reason)  # Build site picker actions.
        related_pickers = RelatedPickerService(collaborators.picker, reason)  # Build related picker actions.
        client_suggestions = ClientSuggestionService(collaborators.picker, reason)  # Build scoped client suggestions.
        return WebSocketServiceBundle(
            catalog,
            SessionServices(lifecycle, messages),
            artifacts,
            terminal,
            PickerServices(site_pickers, related_pickers, client_suggestions),
        )  # Keep the service set fixed and explicit.
