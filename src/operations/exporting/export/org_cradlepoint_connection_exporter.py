"""OrgCradlepointConnectionExporter -- the ``testOrgCradlepointConnection`` endpoint.

Added for spec 905 and issue #1413. The class wraps the Mist API
``testOrgCradlepointConnection``
(``GET /api/v1/orgs/{org_id}/setting/cradlepoint/setup``). An operator reads
the Cradlepoint integration status through the standard MistHelper menu. The
DataExporter pipeline then writes the result to CSV, SQLite, or ArangoDB.

Why:
    The endpoint reports whether the Cradlepoint integration is active and,
    when it is inactive, the reason. A junior engineer had to open the Mist
    portal to read that status. This menu closes that gap.

Shape of the response:
    The endpoint returns one object, not a list. The body holds the two fields
    ``error`` and ``last_status``. The exporter reads ``response.data``
    directly, because the endpoint is not paginated and ``mistapi.get_all``
    would return nothing useful.

Transport status gate (issue #3819):
    The exporter reads the payload only after the HTTP transport status proves
    a completed ``2xx`` success. An absent, malformed, or non-success status
    raises with a named outcome, because a guessed status can write a row that
    says the integration is active when the HTTP result is unknown.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: the raw status body is a duck-typed dict from mistapi.

import mistapi  # WHY: direct SDK access for the Cradlepoint status endpoint.

from src.foundation.models.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.
from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.

# The operationId that selects the primary-key strategy for the written row.
_OPERATION = "testOrgCradlepointConnection"
_HTTP_SUCCESS_MIN = 200  # Only a completed 2xx result proves that the cloud answered the status question.
_HTTP_SUCCESS_MAX = 299  # A 3xx redirect is an unfinished exchange, so it ends the success band here.
_ABSENT_STATUS = object()  # A unique sentinel keeps an absent attribute distinct from every real value.
_OUTCOME_ABSENT = "absent"  # Name the case where the SDK response carries no transport status at all.
_OUTCOME_MALFORMED = "malformed"  # Name the case where the transport status is not a usable integer.
_OUTCOME_OUT_OF_RANGE = "out-of-range"  # Name the case where the integer status is not a completed success.


class OrgCradlepointConnectionExporter:
    """Cradlepoint connection status exporter for ``testOrgCradlepointConnection``.

    Why:
        Provides the only MistHelper entry point for the Cradlepoint status
        endpoint. Static methods only, with no per-instance state, matching the
        peer exporters such as ``OrgSecIntelProfileExporter``.
    """

    @staticmethod
    def _require_success_status(response: Any, org_id: str) -> int:
        """Return the HTTP status only when it proves a completed success.

        Why:
            Issue #3819. The previous gate changed an absent ``status_code`` to
            ``200`` and accepted ``None``, a string, a float, ``True``,
            ``False``, ``1xx``, and ``3xx``. A payload of ``last_status:
            active`` then reached CSV and SQLite although the HTTP result was
            unknown, and an engineer could read that row as a confirmed state.
            This helper binds each untrustworthy case to a named outcome,
            reports it, and refuses. It never invents a status value.

        Args:
            response: The SDK response whose transport status must be proved.
            org_id: The organization under export, logged for operator context.

        Returns:
            The HTTP status, which is always an integer in the 2xx band.

        Raises:
            RuntimeError: The transport status is absent, malformed, or not a
                completed success. The message names the condition and never
                carries the response body or the unusable value.
        """
        raw_status = getattr(response, "status_code", _ABSENT_STATUS)  # A sentinel marks an absent attribute.
        if raw_status is _ABSENT_STATUS:  # An absent status proves nothing, so it must not become a success.
            logger.error(  # Report the condition, because a silent default would write a false row.
                "The Cradlepoint status response for org %s carried no HTTP transport status, outcome=%s",
                org_id,
                _OUTCOME_ABSENT,
            )
            raise RuntimeError(f"Cradlepoint status request returned an {_OUTCOME_ABSENT} HTTP transport status")
        if isinstance(raw_status, bool) or not isinstance(raw_status, int):  # bool subclasses int, so test it first.
            logger.error(  # Log the type name only, because the value itself is untrusted response content.
                "The Cradlepoint status for org %s carried an unusable transport status of type %s, outcome=%s",
                org_id,
                type(raw_status).__name__,
                _OUTCOME_MALFORMED,
            )
            raise RuntimeError(
                f"Cradlepoint status request returned a {_OUTCOME_MALFORMED} HTTP transport status "
                f"of type {type(raw_status).__name__}"
            )
        if not _HTTP_SUCCESS_MIN <= raw_status <= _HTTP_SUCCESS_MAX:  # A 1xx, 3xx, 4xx, or 5xx result is not a success.
            logger.error(  # Report only the operation and status, never the response body.
                "The cloud returned HTTP %s for the Cradlepoint status at org %s, outcome=%s",
                raw_status,
                org_id,
                _OUTCOME_OUT_OF_RANGE,
            )
            raise RuntimeError(f"Cradlepoint status request returned HTTP {raw_status}")
        logger.debug("The Cradlepoint status for org %s carried a trusted HTTP %s", org_id, raw_status)  # Proved.
        return raw_status

    @staticmethod
    def _fetch(org_id: str) -> dict[str, Any]:
        """Call ``testOrgCradlepointConnection`` and return the status body.

        Why:
            The endpoint returns one object and is not paginated, so the caller
            reads ``response.data`` instead of running ``mistapi.get_all``.

        Args:
            org_id: The organization that owns the Cradlepoint integration.

        Returns:
            The status body as a dict, or an empty dict when the body is absent.

        Raises:
            RuntimeError: The HTTP transport status does not prove a success, so
                no payload may be read. See ``_require_success_status``.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Calling testOrgCradlepointConnection for org_id=%s", org_id)  # Pre-call log.
        response = mistapi.api.v1.orgs.setting.testOrgCradlepointConnection(
            mh.apisession, org_id
        )  # The SDK call for the Cradlepoint status.
        OrgCradlepointConnectionExporter._require_success_status(
            response, org_id
        )  # Prove the transport result before any payload read, so no false row can be built.
        payload = getattr(response, "data", None)  # The SDK exposes the body on .data.
        logger.debug(
            "testOrgCradlepointConnection returned payload_type=%s", type(payload).__name__
        )  # Post-call trace.
        if not isinstance(payload, dict):  # A list body or a None body means no status was returned.
            logger.debug("testOrgCradlepointConnection returned no dict body for org %s", org_id)  # Explain it.
            return {}
        return payload

    @staticmethod
    def _build_row(org_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the one flattened row that the writers persist.

        Why:
            The response holds only flat fields, but the shared flatten helper
            keeps the column behavior identical to the peer exporters, so the
            CSV header stays stable between two runs of the same org.

        Args:
            org_id: The organization that owns the status, added as a column.
            payload: The status body from the API.

        Returns:
            A list that holds one flattened row, or an empty list for no body.
        """
        if not payload:  # An absent body has nothing to write.
            logger.debug("No Cradlepoint status body to flatten")  # Explain the empty result.
            return []
        row = {"org_id": org_id, **payload}  # Tag the row with the org, then copy the status fields.
        flattened = DataProcessingUtils.flatten_nested_fields([row])  # Flatten every nested field.
        logger.debug("Built %d Cradlepoint status row(s)", len(flattened))  # Post-build count trace.
        return flattened

    @staticmethod
    def _persist(rows: list[dict[str, Any]], filename: str) -> None:
        """Escape and persist the status row, or report that there is none.

        Args:
            rows: The flattened rows to write. May be empty.
            filename: The output filename, used as the CSV name or the table name.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        if not rows:  # No rows, so inform the operator and return.
            logger.info("! No Cradlepoint connection status found")  # ASCII-only user notice.
            return
        sanitized_data = DataProcessingUtils.escape_multiline(rows)  # Make multiline values CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=_OPERATION
        )
        logger.debug("%s persisted %d rows to %s", _OPERATION, len(rows), filename)  # Post-call count.
        logger.info("! %d Cradlepoint status record(s) exported to %s", len(rows), filename)  # Notice.

    @staticmethod
    def status() -> None:
        """Export the Cradlepoint connection status for an org (menu 245).

        Why:
            Interactive menu entry point. The method owns the org prompt, the
            API call, and the write, and it keeps every failure inside the menu.
        """
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Organization Cradlepoint Connection Status:")  # Menu header echoed to the operator.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve which org to read.
        if not org_id:  # The resolver already logged the cancellation.
            return
        try:
            payload = OrgCradlepointConnectionExporter._fetch(org_id)  # Read the status body once.
            rows = OrgCradlepointConnectionExporter._build_row(org_id, payload)  # Flatten the body into one row.
            OrgCradlepointConnectionExporter._persist(rows, f"OrgCradlepointConnection_{org_id}.csv")  # Write it.
        except Exception as e:  # WHY: surface any SDK or network error, keep the menu alive.
            logging.error("Error fetching the Cradlepoint status for org %s: %s", org_id, e)  # Failure context.
            logging.info("! Error fetching Cradlepoint connection status: %s", e)  # ASCII-only user notice.
