"""Build the five production WebSocket service collaborators."""

from __future__ import annotations  # Keep Flask and collaborator annotations lazy.

from dataclasses import dataclass  # Store the fixed collaborator set.
from typing import Any  # Collaborators cross package boundaries.

from flask import Flask  # Read portal configuration.


@dataclass(frozen=True, slots=True)
class WebSocketCollaborators:
    """Hold the five collaborators used by route services."""

    catalog: Any | None  # Build the public catalog.
    checker: Any | None  # Validate start requests.
    picker: Any | None  # Read Mist picker data.
    manager: Any  # Own live and ended sessions.
    settings: Any  # Supply limits and feature locks.


class WebSocketCollaboratorFactory:
    """Build production collaborators from one Flask app."""

    @classmethod
    def build(cls, app: Flask) -> WebSocketCollaborators | None:
        """Return production collaborators when credentials exist."""
        settings = cls.settings()  # Read environment limits and locks.
        apisession = app.config.get("APISESSION")  # Read the configured Mist API session.
        org_id = str(app.config.get("ORG_ID") or "")  # Read the configured organization.
        if apisession is None or not org_id:  # Both values are required for Mist operations.
            return None  # The service factory builds a not-ready bundle.
        catalog, picker = cls._catalog(settings), cls._picker(apisession, org_id)  # Build request data sources.
        checker = cls._checker(catalog, picker, org_id)  # Validate starts with the shared sources.
        manager = WebSocketManagerFactory.build(settings, apisession)  # Own the live session runners.
        return WebSocketCollaborators(catalog, checker, picker, manager, settings)  # Return all collaborators.

    @staticmethod
    def settings() -> Any:
        """Return settings from the current environment."""
        from src.mist.realtime.websocket_streams.live.sessions.settings import (
            StreamSettings,
        )  # Load environment settings.

        return StreamSettings.from_environment()  # Preserve all limits and flags.

    @staticmethod
    def _catalog(settings: Any) -> Any:
        """Build the locked public catalog."""
        from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Load channel definitions.
        from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import (
            StreamCatalog,
        )  # Join the catalog.
        from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
            UtilityCatalog,
        )  # Load utilities.

        return StreamCatalog(
            ChannelCatalog(),
            UtilityCatalog(),
            changes_enabled=settings.changes_enabled,
            shell_enabled=settings.shell_enabled,
        )  # Preserve current lock flags.

    @staticmethod
    def _picker(apisession: Any, org_id: str) -> Any:
        """Build the shared Mist picker."""
        from src.mist.realtime.websocket_streams.intake.pickers.service import (
            StreamPickerService,
        )  # Load picker behavior.

        return StreamPickerService(apisession, org_id)  # Preserve picker caches and locks.

    @staticmethod
    def _checker(catalog: Any, picker: Any, org_id: str) -> Any:
        """Build the start request checker."""
        from src.mist.realtime.websocket_streams.intake.start_request.checker import StartRequestChecker  # Load checks.

        return StartRequestChecker(catalog, picker, org_id)  # Preserve targets, parameters, and confirmations.


class WebSocketManagerFactory:
    """Build the live session manager and runner factory."""

    @staticmethod
    def build(settings: Any, apisession: Any) -> Any:
        """Return the configured live session manager."""
        from src.mist.realtime.websocket_streams.live.sessions.manager.factory import RunnerFactory  # Build runners.
        from src.mist.realtime.websocket_streams.live.sessions.manager.lifecycle import (
            StreamSessionManager,
        )  # Own sessions.

        return StreamSessionManager(settings, RunnerFactory(apisession))  # Preserve runners and cleanup.
