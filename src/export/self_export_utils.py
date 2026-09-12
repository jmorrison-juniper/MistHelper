"""SelfExportUtils -- authenticated self/account export utilities.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 7).
Exports data scoped to the currently authenticated admin account rather
than an org or site. Handles self audit logs and similar account-level
read operations.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to avoid circular load.
import logging  # WHY: emit structured trace for export progress + failures.

import mistapi  # WHY: dotted-path API resolution + pagination helper.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.time.time_utils import TimeUtils  # WHY: 1014 P6 direct import (FR-005).


class SelfExportUtils:  # Self/account exporters.
    # pylint: disable=too-few-public-methods  # WHY: static-method utility class. Grouping by domain is the point.
    """Authenticated self/account export utilities.

    Exports data scoped to the currently authenticated admin account rather
    than an org or site. Handles self audit logs and similar account-level
    read operations.
    """

    @staticmethod
    def _persist_self_audit_rows(rows: list, filename: str, hours: int) -> None:
        """Flatten + persist self audit rows, or write an empty file when nothing was returned."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live writer + processing helpers.
        if not rows:  # No data returned -- write empty output rather than failing silently.
            logging.warning("No self audit log records returned for the last %d hours", hours)  # Warn empty.
            mh.DataExporter.write_with_format_selection([], filename)  # Empty file signals successful run.
            return  # Done.
        rows = DataProcessingUtils.flatten_nested_fields(rows)  # Flatten nested change-detail dicts for CSV.
        mh.DataExporter.write_with_format_selection(  # Persist to disk with format selection.
            rows, filename, api_function_name="listSelfAuditLogs"
        )
        logging.info("Exported %d self audit log records to %s", len(rows), filename)  # Log success.

    @staticmethod
    def audit_logs() -> None:  # Export audit logs.
        """Export audit log of changes made by the authenticated admin account to SelfAuditLogs.csv."""
        logging.info("Starting export of self (admin account) audit logs...")  # Log before operation.
        filename = "SelfAuditLogs.csv"  # Output filename for self audit log entries.
        try:
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live session.
            hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Same lookback as other audit log exports.
            TimeUtils.log_dynamic_lookback("self audit logs export", hours)  # Log lookback window selection.
            logging.info("Fetching self audit logs for last %d hours...", hours)  # Log before API call.
            response = mistapi.api.v1.self.logs.listSelfAuditLogs(  # Call Mist API for admin account audit log.
                mh.apisession,
                duration=f"{hours}h",  # Limit results to the dynamic lookback window.
                limit=1000,  # Request large page to minimise pagination round-trips.
            )
            logging.debug("Raw API response received for self audit logs")  # Log after API call.
            rows = mistapi.get_all(response=response, mist_session=mh.apisession)  # Paginate through all results.
            logging.debug("Received %d self audit log records after pagination", len(rows))  # Log record count.
            SelfExportUtils._persist_self_audit_rows(rows, filename, hours)  # Persist or write empty.
        except Exception as exception:  # Catch any API or processing error.
            logging.exception("Failed to export self audit logs: %s", exception)  # Log full traceback.
