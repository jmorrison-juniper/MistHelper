"""Helpers of the smoke checks: the SDK session opener and the request trail of each check.

Why: the run state in checks/__init__.py holds the run-stop rules.
The mechanics of opening the SDK session are kept here.
The mechanics of sending a request or a paged query are also kept here.
Each class therefore stays within the structure limits.
This module never imports the checks package at import time, so no import cycle forms.
"""

from __future__ import annotations  # Postpone annotation evaluation.

import os  # Remove and restore the environment variables that the SDK reads at construction.
from collections.abc import Callable  # Type the session factory.
from typing import Any, ClassVar  # Type the SDK session and the class constants.

import structlog  # Structured logging of each request and each opened session.

from scripts.netcool_runbook_smoke.client import (  # Client types of the requests.
    CallRecord,
    PageSet,
    ReadOnlyMistClient,
)  # Client types of the requests.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class SessionOpener:  # Build the SDK session with its environment variables hidden.
    """Build the SDK session with the SDK environment variables hidden, so the SDK reads only the token argument.

    Why: the SDK reads several environment variables in its constructor, and a variable on the host would change
    the settings of the run. The variables are removed for the constructor call and restored after it, even when
    the constructor fails.
    """

    CONSOLE_LEVEL: ClassVar[int] = 51  # Above CRITICAL (50), so the SDK console prints nothing.
    LOGGING_LEVEL: ClassVar[int] = 30  # WARNING, the level of the mistapi logger during the run.
    ENVIRONMENT_NAMES: ClassVar[tuple[str, ...]] = (  # Variables that the SDK reads while its constructor runs.
        "MIST_APITOKEN",
        "MIST_API_TOKEN",
        "MIST_HOST",
        "MIST_USER",
        "MIST_PASSWORD",
        "MIST_VAULT_URL",
        "MIST_VAULT_PATH",
        "MIST_VAULT_MOUNT_POINT",
        "MIST_VAULT_TOKEN",
        "MIST_KEYRING_SERVICE",
    )

    @classmethod
    def open(cls, session_factory: Callable[..., Any], host: str, token: str) -> Any:  # Validate the token at once.
        """Build the SDK session, which validates the token, and restore the hidden variables.

        Why: the SDK sends one GET when its session receives the token, so the constructor is the validation.
        The session never reads the token from the environment, because the token is passed as an argument.

        Args:
            session_factory: Builds the SDK session, normally the SDK class.
            host: Regional host from the validated settings.
            token: Token value, passed to the constructor only.

        Returns:
            The SDK session.

        Raises:
            ValueError: The SDK rejected the token with HTTP 401.
            ConnectionError: No response reached the client during the validation.
        """
        logger.info("Opening the API session for %s", host)  # Log before the token validation request.
        removed = {  # Keep each hidden variable, so the restore sets its original value.
            name: os.environ.pop(name) for name in cls.ENVIRONMENT_NAMES if name in os.environ
        }  # Hidden variables.
        try:  # The variables must return even when the constructor fails.
            return session_factory(  # Build the SDK session, which validates the token at once.
                host=host,  # Regional host from the validated settings.
                apitoken=token,  # Token passed as an argument, never read from the environment.
                console_log_level=cls.CONSOLE_LEVEL,  # Suppresses the SDK console output.
                logging_log_level=cls.LOGGING_LEVEL,  # Sets the mistapi logger to WARNING.
                show_cli_notif=False,  # No decorative text on the console.
            )
        finally:  # Runs on success and on failure, so the process keeps its variables.
            os.environ.update(removed)  # Restore each variable that the constructor could not see.


class RequestTrail:  # Send each check request through the client, with its log events.
    """Send the requests of the checks through the client, with a log event before and after each request.

    Why: each request is an action with a log before it and a log after it. The client guard and the log events are
    kept in one place, so every request of every check logs the same way.
    """

    @staticmethod
    def require_client(client: ReadOnlyMistClient | None) -> ReadOnlyMistClient:  # Refuse a request without a session.
        """Return the client of the run, or raise when the API session is not open.

        Why: a request needs the session that open_client builds, and a missing session must stop the request
        before any call is sent.

        Args:
            client: Client of the run, or None when the session is not open.

        Returns:
            The client of the run.

        Raises:
            RuntimeError: The API session is not open.
        """
        if client is None:  # No session exists, so no request may be sent.
            raise RuntimeError("the API session is not open")  # Refuse the request before any call is sent.
        return client  # The session is open, so the request may proceed.

    @staticmethod
    def send(  # Send one GET request and log its attempts.
        client: ReadOnlyMistClient, path_template: str, identifiers: dict[str, str], query: dict[str, str]
    ) -> tuple[CallRecord, ...]:
        """Send one GET request through the client, and return every attempt in request order.

        Why: each check reads its data from the attempts, so the attempts are returned unchanged and the run-stop
        rules are applied by the caller.

        Args:
            client: Client of the run.
            path_template: Path that starts with /api/v1/ and holds placeholders.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters of the request.

        Returns:
            Every attempt of the request, in request order.
        """
        logger.info("Check request for %s", path_template)  # Log before the request.
        attempts = client.get(path_template, identifiers, query)  # Send the request through the budget.
        logger.debug("Check request for %s returned %s attempts", path_template, len(attempts))  # Log the result.
        return attempts  # Return every attempt, so each retry is counted.

    @staticmethod
    def read_pages(  # Read the pages of one paged query and log its outcome.
        client: ReadOnlyMistClient,
        path_template: str,
        identifiers: dict[str, str],
        query: dict[str, str],
        max_pages: int,
    ) -> PageSet:
        """Read the pages of one query through the client, and return the paged result.

        Why: a search reads up to the page ceiling. The run-stop rules for the paging are applied by the caller,
        after the pages are read.

        Args:
            client: Client of the run.
            path_template: Path that starts with /api/v1/ and holds placeholders.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters of the first page.
            max_pages: Most pages that the query reads.

        Returns:
            The paged result of the query.
        """
        logger.info("Paged request for %s, up to %s pages", path_template, max_pages)  # Log before the first page.
        page = client.get_pages(path_template, identifiers, query, max_pages)  # Read the pages of the query.
        logger.debug("Paged request for %s read %s pages", path_template, page.pages_read)  # Log the result.
        return page  # Return the paged result to the caller for the run-stop rules.
