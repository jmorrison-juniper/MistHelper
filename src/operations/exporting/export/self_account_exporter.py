"""SelfAccountExporter -- the ``verifySelfEmail`` endpoint.

Added for spec 907 and issue #1415. The class wraps the Mist API
``verifySelfEmail``
(``GET /api/v1/self/update/verify/{token}``). An operator pastes the
single-use token from the Mist email-change email, and the endpoint applies
the email address change. The exporter then records one audit row through
the DataExporter pipeline.

Why:
    MistHelper holds no entry point for the self-account endpoints. An
    operator who completes an email change had to verify the token by hand.
    This menu closes that gap.

Shape of the response:
    A 200 body is empty, and the email address is updated. A 400 body holds
    ``{"detail": "invalid token"}`` or ``{"detail": "email already existed"}``.
    The exporter reports the status code and only recognized, fixed detail
    messages. It omits arbitrary response text and SDK exception details.

Security:
    The token is a single-use credential. It is never logged, never written
    to the audit row, and never echoed back to the operator.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import logging  # WHY: structured trace for the verification lifecycle.
from datetime import UTC, datetime  # WHY: a timezone-aware UTC audit timestamp.
from typing import Any  # WHY: the API payload is untyped.

import mistapi  # WHY: the SDK provides the verifySelfEmail call.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Use a module logger for non-exception export messages.

# The operationId that selects the primary-key strategy for the written row.
_OPERATION = "verifySelfEmail"


class SelfAccountExporter:
    """Email change token verifier for ``verifySelfEmail``.

    Why:
        Provides the only MistHelper entry point for the self-account
        verification endpoint. Static methods only, with no per-instance
        state, matching the peer exporters such as ``OrgSecIntelProfileExporter``.
    """

    @staticmethod
    def _prompt_token() -> str:
        """Read the token from the operator. Return an empty string on cancel.

        Why:
            The token is a credential, so the prompt never echoes it, and the
            safe_input helper keeps the EOF path inside the menu.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        token = str(  # WHY: the lazy module attribute is untyped, so pin the declared str return.
            mh.InputUtils.safe_input(
                "Paste the email change token from the Mist email: ",
                context="verify_self_email.token",
            )
        ).strip()  # WHY: strip whitespace around the pasted token.
        logger.debug("Token prompt answered (length=%d)", len(token))  # Length only, never the token.
        return token

    @staticmethod
    def _detail(data: Any, token: str) -> str:
        """Return a fixed public detail message or an empty string.

        Why:
            A response can contain private values. Only an exact recognized
            message is safe, unless it contains the submitted token.
        """
        if not isinstance(data, dict):
            return ""
        detail = data.get("detail")
        if not isinstance(detail, str):
            return ""
        for safe_detail in ("invalid token", "email already existed", "server unavailable"):
            if detail == safe_detail and (not token or token not in safe_detail):
                return safe_detail
        return ""

    @staticmethod
    def _verify(token: str) -> tuple[int, str]:
        """Call ``verifySelfEmail`` once and return (status_code, detail).

        Why:
            The call applies the email change, so the caller reports by status
            code and never retries.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Calling verifySelfEmail for the configured account")  # Pre-call log, no token.
        response = mistapi.api.v1.self.update.verifySelfEmail(mh.apisession, token)  # The single SDK call.
        detail = SelfAccountExporter._detail(response.data, token)
        logger.debug("verifySelfEmail returned status=%s", response.status_code)  # Post-call trace.
        return response.status_code, detail

    @staticmethod
    def _build_row(org_id: str, status_code: int, detail: str) -> dict[str, Any]:
        """Build the one audit row that the writers persist.

        Why:
            The response holds no stable identifier, so the row is a local
            audit record tagged with the org, the status, and a UTC timestamp.
            The token is never a column.
        """
        row = {
            "org_id": org_id,  # WHY: scope the event to the configured org.
            "status_code": status_code,  # WHY: 200 means the email was updated.
            "detail": detail,  # WHY: a 400 message such as "invalid token".
            "verified_at_utc": datetime.now(UTC).isoformat(),  # WHY: audit timestamp.
        }
        logger.debug("Built 1 verifySelfEmail audit row")  # Post-build count trace.
        return row

    @staticmethod
    def _persist(row: dict[str, Any], filename: str) -> None:
        """Persist the audit row through the multi-backend exporter.

        Why:
            The shared pipeline keeps CSV, SQLite, and ArangoDB writes in one
            place, and the operationId selects the primary-key strategy.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            [row], filename, api_function_name=_OPERATION
        )
        logger.debug("%s persisted 1 row to %s", _OPERATION, filename)  # Post-call count.

    @staticmethod
    def verify_email() -> None:
        """Verify an email change token for the configured account (menu 247).

        Why:
            Interactive menu entry point. The method owns the prompts, the
            single API call, and the write, and it keeps every failure inside
            the menu.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Email Change Token Verification:")  # Menu header echoed to the operator.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve which org to scope to.
        if not org_id:  # The resolver already logged the cancellation.
            return
        token = SelfAccountExporter._prompt_token()  # Read the token once.
        if not token:  # An empty answer cancels before any API call.
            logger.info("! No token provided. Returning to the menu.")  # User-facing cancel.
            return
        try:
            status_code, detail = SelfAccountExporter._verify(token)  # The single SDK call.
        except Exception:
            # SDK exception text, types, and tracebacks can contain private values.
            logger.error("verifySelfEmail failed for org %s. SDK error details omitted.", org_id)
            logger.info("! Email change token verification failed. Returning to the menu.")
            return
        if status_code == 200:
            logger.info("! Email address updated - the token was valid")  # ASCII-only success notice.
        else:
            logger.info(  # WHY: the 400 body names the reason.
                "! Email change token verification failed (status %s): %s",
                status_code,
                detail or "no detail",
            )
        SelfAccountExporter._persist(  # Record the event, success or failure.
            SelfAccountExporter._build_row(org_id, status_code, detail),
            "verify_self_email.csv",
        )
