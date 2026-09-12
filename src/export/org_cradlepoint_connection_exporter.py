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
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: the raw status body is a duck-typed dict from mistapi.

import mistapi  # WHY: direct SDK access for the Cradlepoint status endpoint.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.

# The operationId that selects the primary-key strategy for the written row.
_OPERATION = "testOrgCradlepointConnection"


class OrgCradlepointConnectionExporter:
    """Cradlepoint connection status exporter for ``testOrgCradlepointConnection``.

    Why:
        Provides the only MistHelper entry point for the Cradlepoint status
        endpoint. Static methods only, with no per-instance state, matching the
        peer exporters such as ``OrgSecIntelProfileExporter``.
    """

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
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the apisession global.
        logging.info("Calling testOrgCradlepointConnection for org_id=%s", org_id)  # Pre-call log.
        response = mistapi.api.v1.orgs.setting.testOrgCradlepointConnection(
            mh.apisession, org_id
        )  # The SDK call for the Cradlepoint status.
        payload = getattr(response, "data", None)  # The SDK exposes the body on .data.
        logging.debug(
            "testOrgCradlepointConnection returned payload_type=%s", type(payload).__name__
        )  # Post-call trace.
        if not isinstance(payload, dict):  # A list body or a None body means no status was returned.
            logging.debug("testOrgCradlepointConnection returned no dict body for org %s", org_id)  # Explain it.
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
            logging.debug("No Cradlepoint status body to flatten")  # Explain the empty result.
            return []
        row = {"org_id": org_id, **payload}  # Tag the row with the org, then copy the status fields.
        flattened = DataProcessingUtils.flatten_nested_fields([row])  # Flatten every nested field.
        logging.debug("Built %d Cradlepoint status row(s)", len(flattened))  # Post-build count trace.
        return flattened

    @staticmethod
    def _persist(rows: list[dict[str, Any]], filename: str) -> None:
        """Escape and persist the status row, or report that there is none.

        Args:
            rows: The flattened rows to write. May be empty.
            filename: The output filename, used as the CSV name or the table name.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rows:  # No rows, so inform the operator and return.
            logging.info("! No Cradlepoint connection status found")  # ASCII-only user notice.
            return
        sanitized_data = DataProcessingUtils.escape_multiline(rows)  # Make multiline values CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=_OPERATION
        )
        logging.debug("%s persisted %d rows to %s", _OPERATION, len(rows), filename)  # Post-call count.
        logging.info("! %d Cradlepoint status record(s) exported to %s", len(rows), filename)  # Notice.

    @staticmethod
    def status() -> None:
        """Export the Cradlepoint connection status for an org (menu 245).

        Why:
            Interactive menu entry point. The method owns the org prompt, the
            API call, and the write, and it keeps every failure inside the menu.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the org resolver.
        logging.info("Organization Cradlepoint Connection Status:")  # Menu header echoed to the operator.
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
