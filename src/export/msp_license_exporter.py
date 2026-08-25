"""MSPLicenseExporter -- MSP license export for the ``listMspLicenses`` endpoint.

Added for spec 752 / issue #1260. The class wraps the Mist API
``listMspLicenses`` (``GET /api/v1/msps/{msp_id}/licenses``) so an operator can
read the licenses an MSP holds through the standard MistHelper menu and the
DataExporter pipeline (CSV, SQLite, or ArangoDB).

Why:
    The endpoint was absent from the menu. An operator who manages an MSP had to
    write custom code to read the MSP license entitlement and the usage counters.

Shape of the response:
    The endpoint returns one aggregate object, not a list of records. The object
    holds four counter maps (``entitled``, ``fully_loaded``, ``summary``, and
    ``usages``), one ``licenses`` array of subscription records, and one
    ``amendments`` array of subscription changes.

Why two files:
    The exporter writes a summary file and a detail file. This follows the
    pattern that ``LicenseExportUtils`` established for the org async-claim
    export. One wide row would hold one column for each subscription field, so
    the column count would change every time the MSP buys or retires a
    subscription. Two files keep both schemas stable, and both files upsert
    cleanly on a repeat run.

    - The summary file holds one row for each MSP, keyed by ``msp_id``.
    - The detail file holds one row for each subscription and for each
      amendment, keyed by the record ``id``. A ``record_type`` column separates
      the two kinds, because both kinds carry the same field names.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw license rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for listMspLicenses.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.
from src.utils.input_utils import InputUtils  # WHY: the shared, EOF-safe MSP identifier prompt.

# The two response keys that hold record arrays rather than counters. The
# summary row drops them, and the detail rows read them.
_RECORD_KEYS: tuple[tuple[str, str], ...] = (
    ("licenses", "license"),  # Subscription records the MSP owns.
    ("amendments", "amendment"),  # Recorded changes to those subscriptions.
)


class MSPLicenseExporter:
    """MSP license exporter for the ``listMspLicenses`` operationId.

    Why:
        Provides the only MistHelper entry point for the MSP license endpoint.
        Static methods only, with no per-instance state, matching the peer
        exporters such as ``SiteApplicationListExporter``.
    """

    @staticmethod
    def _fetch(msp_id: str) -> dict[str, Any]:
        """Call ``listMspLicenses`` for one MSP and return the aggregate payload.

        Why:
            The endpoint is not paginated, so the caller reads ``response.data``
            instead of running ``mistapi.get_all``.

        Args:
            msp_id: The MSP identifier the operator supplied.

        Returns:
            The response body as a dict, or an empty dict when the body is absent.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession.
        logging.info("Calling listMspLicenses for msp_id=%s", msp_id)  # Pre-call log.
        response = mistapi.api.v1.msps.licenses.listMspLicenses(mh.apisession, msp_id)  # SDK call.
        payload = getattr(response, "data", None)  # The SDK exposes the body on .data.
        logging.debug("listMspLicenses returned payload_type=%s", type(payload).__name__)  # Post-call trace.
        if not isinstance(payload, dict):  # A list body or a None body means the MSP has no license record.
            logging.debug("listMspLicenses returned no dict body for msp_id=%s", msp_id)  # Explain the empty result.
            return {}
        return payload

    @staticmethod
    def _build_summary_row(msp_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the one counter row for an MSP, dropping the record arrays.

        Why:
            The counter maps answer the question an operator asks first: how many
            licenses of each type does this MSP hold, and how many are in use.

        Args:
            msp_id: The MSP identifier, which becomes the primary key.
            payload: The aggregate body ``listMspLicenses`` returned.

        Returns:
            One flattened row that always carries ``msp_id``.
        """
        record_keys = {key for key, _ in _RECORD_KEYS}  # The array keys the detail file owns.
        counters = {key: value for key, value in payload.items() if key not in record_keys}  # Keep the maps only.
        logging.debug("Built the MSP summary from %d counter keys", len(counters))  # Post-build trace.
        flattened = DataProcessingUtils.flatten_nested_fields([counters])  # Expand each counter map into columns.
        row: dict[str, Any] = {"msp_id": msp_id}  # Lead with the primary key so the CSV reads left to right.
        row.update(flattened[0] if flattened else {})  # Merge the counters behind the identifier.
        return row

    @staticmethod
    def _build_detail_rows(msp_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Build one row for each subscription and for each amendment.

        Why:
            Both arrays carry the same field names and a stable ``id``, so one
            file with a ``record_type`` column holds both without a name clash.

        Args:
            msp_id: The MSP identifier, added to every row for attribution.
            payload: The aggregate body ``listMspLicenses`` returned.

        Returns:
            The detail rows, in subscription order and then amendment order.
        """
        rows: list[dict[str, Any]] = []  # Accumulate the rows of both arrays.
        for key, record_type in _RECORD_KEYS:  # Walk the subscription array, then the amendment array.
            records = payload.get(key) or []  # A missing key and a null value both mean no record.
            if not isinstance(records, list):  # A malformed body must not stop the export.
                logging.warning("listMspLicenses returned a non-list %s field; skipping it", key)  # Name the gap.
                continue
            for record in records:  # Each record becomes one row.
                if not isinstance(record, dict):  # Skip a malformed entry rather than write a broken row.
                    logging.warning("Skipping a non-dict entry in the %s field", key)  # Name the skipped entry.
                    continue
                rows.append({"msp_id": msp_id, "record_type": record_type, **record})  # Tag, then copy the record.
        logging.debug("Built %d MSP license detail rows", len(rows))  # Post-build count trace.
        return DataProcessingUtils.flatten_nested_fields(rows)  # Flatten any nested field before the write.

    @staticmethod
    def _persist(rows: list[dict[str, Any]], filename: str, api_function_name: str, noun: str) -> None:
        """Escape and persist one set of rows, or report that there are none.

        Why:
            An MSP with no license record is legitimate, so the exporter reports
            the empty result plainly instead of failing.

        Args:
            rows: The flattened rows to write. May be empty.
            filename: The output filename, used as the CSV name or the table name.
            api_function_name: The key that selects the primary-key strategy.
            noun: The word shown to the operator, for example ``license summary``.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rows:  # No rows, so inform the operator and return.
            logging.info("! No MSP %s data found", noun)  # ASCII-only user notice.
            return
        sanitized_data = DataProcessingUtils.escape_multiline(rows)  # Make multiline values CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=api_function_name
        )
        logging.debug("%s persisted %d rows to %s", api_function_name, len(rows), filename)  # Post-call count.
        logging.info("! %d MSP %s records exported to %s", len(rows), noun, filename)  # User notice with count.

    @staticmethod
    def licenses() -> None:
        """Export the license summary and the license details for an MSP (menu 238).

        Why:
            Interactive menu entry point. The method owns the prompt, the API
            call, and the two writes, and it keeps every failure inside the menu.
        """
        logging.info("MSP Licenses:")  # Menu header echoed to the operator.
        msp_id = InputUtils.prompt_msp_id()  # Ask which MSP to read.
        if msp_id is None:  # The prompt helper already logged the cancellation.
            return
        try:
            payload = MSPLicenseExporter._fetch(msp_id)  # Read the aggregate body once.
            summary_rows = [MSPLicenseExporter._build_summary_row(msp_id, payload)] if payload else []  # One row.
            detail_rows = MSPLicenseExporter._build_detail_rows(msp_id, payload)  # One row for each record.
            stem = f"MSPLicenses_{msp_id.replace(' ', '_')}"  # Per-MSP filename stem shared by both files.
            MSPLicenseExporter._persist(summary_rows, f"{stem}_summary.csv", "listMspLicenses", "license summary")
            MSPLicenseExporter._persist(detail_rows, f"{stem}_details.csv", "listMspLicensesDetails", "license detail")
        except Exception as e:  # noqa: BLE001 -- surface any SDK or network error, keep the menu alive.
            logging.error("Error fetching the licenses for MSP %s: %s", msp_id, e)  # Failure context.
            logging.info("! Error fetching MSP license data: %s", e)  # ASCII-only user notice.
