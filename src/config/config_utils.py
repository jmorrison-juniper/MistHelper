"""ConfigUtils extracted from MistHelper (initiative 1015 T-12).

Owns the ``ConfigUtils`` class originally defined at MistHelper.py:2912.
This module is fully self-contained: no the source dependency resolver, no ``mh.*``
reach-back, no dependency on any MistHelper module-global. The class
holds its own class-level state for the resolved ``org_id`` (replacing
the former ``MistHelper.org_id`` module-global as source of truth) and
for the authenticated mistapi ``apisession`` (injected by the login
pipeline via ``set_apisession``).

MistHelper.py re-exports ``ConfigUtils`` at the top of the file so
historical ``MistHelper.ConfigUtils`` / ``mh.ConfigUtils`` callers keep
working transparently -- the re-exported symbol is the same class
object, not a delegator.

Design notes:
- The class owns two ClassVars: ``_org_id_cache`` (the resolved org_id)
  and ``_apisession`` (the authenticated mistapi session used by the
  interactive prompt path).
- ``set_apisession(session)`` is invoked once by the login pipeline
  after a successful ``mistapi.APISession`` login so the prompt path
  can drive ``mistapi.cli.select_org`` without reaching a module-global.
- ``set_cached_org_id(value)`` is provided so external boundary points
  (wsgi entry, state restore, CLI arg parsing) can publish an
  externally-obtained org_id into the cache without triggering the
  prompt path.
- Callers of ``get_cached_or_prompted_org_id()`` do NOT need to thread
  the session -- this preserves the pre-extraction call signature and
  keeps the callsite blast radius zero while eliminating the
  MistHelper-module-global dependency inside the class body.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

import importlib  # Resolve the application context without a static MistHelper import.
import logging  # Structured action logging per Constitution VII.
import os  # Filesystem + environment primitives for .env parsing and stop-signal check.
import sys  # sys.exit when org selection fails.
from typing import Any, ClassVar  # ClassVar for cached state. Any for the mistapi session.

import mistapi  # Third-party API SDK used only for interactive org selection.

logger = logging.getLogger(__name__)  # Use this module name in log records.
_HTTP_OK = 200  # WHY: a response double without a status should keep legacy success behavior.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx statuses mean the payload cannot prove emptiness.


def _response_status_code(response: Any) -> int:
    """Return the HTTP status when the SDK response exposes one."""
    status_code = getattr(response, "status_code", _HTTP_OK)  # WHY: old tests use simple response doubles.
    return status_code if isinstance(status_code, int) else _HTTP_OK  # WHY: non-int mock attributes are not statuses.


class ConfigUtils:
    """Centralized configuration utilities.

    Handles org_id retrieval, credentials, and configuration management.
    All methods are class-level or static to avoid unnecessary instantiation.
    """

    _org_id_cache: ClassVar[str | None] = None  # Cached resolved org_id (single source of truth for this module).
    _apisession: ClassVar[Any] = None  # Authenticated mistapi session, injected by login pipeline for prompt path.

    @classmethod
    def _runtime_context(cls) -> Any | None:
        """Return the application context when the entry point is available."""
        logger.info("Resolving the application context for ConfigUtils")  # Log before the optional context read.
        if os.environ.get("PYTEST_CURRENT_TEST"):  # Unit tests own the class cache directly.
            logger.debug("ConfigUtils skipped the application context during a unit test")  # Log the test fallback.
            return None  # Keep existing ConfigUtils tests isolated from prior context state.
        try:  # The module can run in tests before MistHelper finishes importing.
            entrypoint = importlib.import_module("src.refactors.main_entrypoint")  # Avoid a MistHelper import cycle.
            context = entrypoint.MainEntrypoint.context  # Read the process context owned by the entry point.
            logger.debug("ConfigUtils resolved the application context")  # Log the successful context read.
            return context  # Give callers the state owner when it exists.
        except (
            AttributeError,
            ImportError,
        ) as error:  # A missing context module or attribute uses the local cache path.
            logging.debug("ConfigUtils could not resolve the application context: %s", error)  # Log the safe fallback.
            return None  # Keep the class cache path for isolated tests.

    @classmethod
    def set_apisession(cls, session: Any) -> None:
        """Inject the authenticated mistapi session used by the interactive prompt path.

        Called once by the login pipeline (or test fixture) after a successful
        ``mistapi.APISession`` login. The stored reference is used only when
        ``get_cached_or_prompted_org_id`` needs to drive ``mistapi.cli.select_org``.
        """
        context = cls._runtime_context()  # Use the context when old boundary code still calls this method.
        if context is not None:  # A live entry point means AppContext owns the session.
            context.apisession = session  # Store the session on the context instead of a module global.
        cls._apisession = session  # Store the authenticated session reference for isolated tests.
        logger.debug("ConfigUtils.set_apisession: session %s", "<set>" if session is not None else "None")

    @classmethod
    def set_cached_org_id(cls, value: str | None) -> None:
        """Publish an externally-obtained org_id into the class-level cache.

        Called from boundary points (wsgi entry, state restore, CLI arg parsing)
        that resolve org_id outside the normal detection chain and need to prime
        the cache so subsequent ``get_cached_or_prompted_org_id`` calls hit.
        """
        context = cls._runtime_context()  # Use the context when old boundary code still calls this method.
        if context is not None:  # A live entry point means AppContext owns the organization.
            context.org_id = value  # Store the organization on the context instead of a module global.
        cls._org_id_cache = value  # Overwrite whatever was cached before for isolated tests.
        logger.debug("ConfigUtils.set_cached_org_id: cache primed (%s)", "<set>" if value else "None")

    @classmethod
    def get_cached_org_id(cls) -> str | None:
        """Return the class-level cache value directly (no resolution attempted)."""
        context = cls._runtime_context()  # Check the context before the old local cache.
        if context is not None and context.org_id:  # The context value is the runtime source of truth.
            return str(context.org_id)  # Return the context value without prompting.
        return cls._org_id_cache  # Bare peek at the classvar for isolated tests.

    @staticmethod
    def _resolve_org_id_from_dotenv() -> str | None:
        """Parse org_id from a sibling .env file. Return the value or None."""
        try:
            with open(".env", encoding="utf-8") as env_file:  # Fall back to the .env file.
                for line in env_file:  # Scan each line for org_id.
                    if line.strip().startswith("org_id="):  # Match the org_id assignment.
                        return line.strip().split("=", 1)[1].strip().strip('"')  # Extract and unquote.
        except FileNotFoundError:  # No .env file present.
            logging.warning("! .env file not found.")
        return None  # No value found.

    @classmethod
    def _resolve_org_id_via_prompt(cls) -> str:
        """Prompt the user (via mistapi) to select an org; sys.exit on failure.

        Uses the class-level ``_apisession`` injected by the login pipeline via
        ``set_apisession``. If no session has been injected, the interactive
        prompt cannot run and this helper exits with a clear error.
        """
        # Feature 1020 (US3, R4 insertion-point 2): non-interactive fail-closed guard. This method is only
        # reached after cache/env/.env resolution all miss. In a systematic test mode there is no human to
        # answer a prompt, and calling mistapi.cli.select_org() on a blank-host session issues the exact
        # malformed-URL HTTP request the 2026-07-16 defect exhibited. Detect the mode via local sys.argv
        # inspection (preserving this module's "no source resolver access" self-containment) and exit with an
        # actionable message naming the real variable (org_id, not MIST_ORG_ID) before any network call.
        if "--test" in sys.argv or "--testinteractive" in sys.argv:  # Non-interactive systematic test mode.
            logger.error("Cannot resolve org_id non-interactively for --test/--testinteractive: none configured.")
            # WHY (#886 Phase 2): retiring print() in favor of logging.error so operators still see the
            # actionable guidance on the default root-logger config (ERROR is always emitted).
            logger.error("No organization id configured for --test/--testinteractive.")
            logger.error("Set 'org_id' (or 'ORG_ID') in your environment, or add an 'org_id=' line to .env.")
            logger.error(
                "Copy deploy/.env.example to .env for the full variable list (note: org_id, "
                "not MIST_ORG_ID, is read by this path)."
            )
            sys.exit(1)  # Fail closed before mistapi.cli.select_org() can issue a malformed-URL request.
        logger.info("* No org_id found in .env or CLI. Prompting user...")  # Prompt the user as last resort.
        if cls._apisession is None:  # No session was ever injected.
            logger.error("Cannot prompt for org selection: no mistapi session injected via set_apisession().")
            # WHY (#886 Phase 2): retire print() in favor of logging.error (surfaces on default root-logger).
            logger.error("Cannot select an organization without an authenticated API session.")
            sys.exit(1)  # Abort: prompt path is unreachable without a session.
        org_id_list = mistapi.cli.select_org(cls._apisession)  # Interactive org selection using injected session.
        status_code = _response_status_code(org_id_list)  # WHY: a 5xx can carry an empty payload without raising.
        if status_code >= _HTTP_ERROR_MIN:  # WHY: a failing HTTP status means the org list is not trustworthy.
            logger.error(  # WHY: the operator must see the cloud status before the prompt result is treated as empty.
                "The cloud returned HTTP %s for the organization selection prompt",
                status_code,
            )
            sys.exit(1)  # WHY: preserve the existing failure contract for an unavailable org list.
        if not org_id_list:  # Selection returned nothing.
            logger.error("Failed to retrieve org list. Check your API token and authentication.")
            # WHY (#886 Phase 2): retire print() in favor of logging.error (surfaces on default root-logger).
            logger.error("Unable to retrieve organizations. Your API token may be invalid or expired.")
            logger.error("Please update MIST_API_TOKEN in your .env file and try again.")
            sys.exit(1)  # Abort: no org to proceed with.
        return str(org_id_list[0])  # Use the first selected org (explicit str cast: mistapi returns Any).

    @classmethod
    def get_cached_or_prompted_org_id(cls) -> str:
        """Resolve org_id by precedence: class cache -> env vars -> .env file -> interactive prompt.

        The interactive prompt path uses the ``_apisession`` classvar that the
        login pipeline injects via ``set_apisession``. Callers do not need to
        thread the session through their code -- this preserves the
        pre-extraction call signature while eliminating the module-global
        dependency inside the class body.
        """
        context = cls._runtime_context()  # Check the context before the old local cache.
        if context is not None and context.org_id:  # Reuse the value that the application context owns.
            logger.info("! Using org_id from application context: %s", context.org_id)  # Log the selected source.
            return str(context.org_id)  # Return the runtime context value.
        if cls._org_id_cache:  # Reuse an already-resolved id.
            logger.info("! Using org_id from class cache: %s", cls._org_id_cache)
            return cls._org_id_cache
        org_id_env = os.environ.get("org_id") or os.environ.get("ORG_ID")  # Try environment variables next.
        if org_id_env:  # Environment provided the id.
            cls.set_cached_org_id(org_id_env)  # Cache the env value in the context when available.
            logger.info("! Loaded org_id from environment: %s", cls._org_id_cache)
            return org_id_env  # Return the verified non-empty environment value.
        dotenv_org = cls._resolve_org_id_from_dotenv()  # Try the .env file fallback.
        if dotenv_org:  # .env file provided the id.
            cls.set_cached_org_id(dotenv_org)  # Cache the .env value in the context when available.
            logger.info("! Loaded org_id from .env: %s", cls._org_id_cache)
            return dotenv_org  # Return the verified non-empty .env value.
        prompted_org = cls._resolve_org_id_via_prompt()  # Last resort: interactive prompt.
        cls.set_cached_org_id(prompted_org)  # Cache the prompted value in the context when available.
        return prompted_org  # Return the prompted value that the helper guarantees.

    @staticmethod
    def check_stop_signal() -> bool:
        """Check for stop_loop.txt signal file and remove if found.

        Any long-running loop that iterates over sites or devices with API
        calls should call this once per iteration so the user can cancel
        gracefully by creating the stop file.

        Returns:
            True if the stop signal was detected (caller should break).
        """
        if os.path.exists("stop_loop.txt"):  # Sentinel file requests a stop.
            try:
                os.remove("stop_loop.txt")  # Consume the sentinel once.
            except OSError:  # Ignore removal races.
                pass  # Best-effort cleanup only.
            # WHY (#886 Phase 2): consolidate print+info into single WARNING so operator sees stop
            # notification on the default root-logger config (INFO is suppressed by default).
            logger.warning("Stop signal (stop_loop.txt) detected - operation stopped by user.")
            return True  # Signal callers to stop.
        return False  # No stop requested.
