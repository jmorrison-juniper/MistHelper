"""LicenseExportUtils -- custom async-claim license status exporter.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 24).
Handles the org license async-claim status endpoint's custom flattening
(summary row + optional per-device detail rows).  All methods are static
-- no state is kept on the class.  Callers continue to reach it through
the ``MistHelper.LicenseExportUtils`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from datetime import UTC, datetime  # WHY: timezone-aware poll timestamps.
from typing import Any  # WHY: raw payload rows are duck-typed dicts from mistapi.
from uuid import UUID  # WHY: validate org_id shape before any API call.

import mistapi  # WHY: direct SDK access for async-claim endpoint.


class LicenseExportUtils:
    """Custom exporters for license payloads that need manual flattening."""

    @staticmethod
    def _is_valid_uuid(candidate: str) -> bool:
        """Validate that candidate looks like a UUID string."""
        try:  # Guard parse failure to keep caller flow simple.
            UUID(candidate)  # Parse the candidate as a UUID object.
            return True  # Signal valid UUID format.
        except (ValueError, AttributeError, TypeError):  # Handle malformed or missing values.
            return False  # Signal invalid UUID format.

    @staticmethod
    def _flatten_org_license_async_claim_status_summary(org_id_value: str, payload: dict) -> dict:
        """Flatten one async-claim payload into a summary row."""
        logging.info("Flattening async-claim summary for org %s", org_id_value)  # Log before summary flatten.
        completed_items = payload.get("completed") or []  # Normalize completed list for safe counting.
        incompleted_items = payload.get("incompleted") or []  # Normalize incompleted list for safe counting.
        polled_at_utc = datetime.now(UTC).isoformat()  # Capture UTC poll timestamp (timezone-aware).
        summary_row = {  # Build normalized row for DataExporter.
            "org_id": org_id_value,  # Inject org id for composite key use.
            "scheduled_at": payload.get("scheduled_at"),  # Keep stable job id from Mist.
            "status": payload.get("status"),  # Keep lifecycle state for status dashboards.
            "total": payload.get("total"),  # Keep total devices for progress math.
            "processed": payload.get("processed"),  # Keep processed counter for progress math.
            "succeed": payload.get("succeed"),  # Keep success counter for outcome reporting.
            "failed": payload.get("failed"),  # Keep failure counter for troubleshooting.
            "completed_count": len(completed_items),  # Store completed list size.
            "incompleted_count": len(incompleted_items),  # Store incompleted list size.
            "timestamp": payload.get("timestamp"),  # Keep Mist response timestamp.
            "polled_at_utc": polled_at_utc,  # Keep local poll timestamp.
        }
        logging.debug("Flattened summary scheduled_at=%s", summary_row.get("scheduled_at"))  # Log summary result.
        return summary_row  # Return normalized summary row.

    @staticmethod
    def _flatten_org_license_async_claim_status_details(org_id_value: str, payload: dict) -> list[dict]:
        """Flatten details[] payload into one row per device."""
        logging.info("Flattening async-claim details for org %s", org_id_value)  # Log before detail flatten.
        detail_items = payload.get("details") or []  # Normalize details list for safe iteration.
        scheduled_at_value = payload.get("scheduled_at")  # Capture parent job key for joins.
        polled_at_utc = datetime.now(UTC).isoformat()  # Capture UTC poll timestamp (timezone-aware).
        detail_rows = [  # Build one row per detail object.
            {
                "org_id": org_id_value,  # Inject org id for composite key use.
                "scheduled_at": scheduled_at_value,  # Preserve summary linkage key.
                "mac": detail_item.get("mac"),  # Keep device MAC from detail payload.
                "device_status": detail_item.get("status"),  # Map detail status field.
                "device_timestamp": detail_item.get("timestamp"),  # Map detail timestamp field.
                "polled_at_utc": polled_at_utc,  # Keep local poll timestamp.
            }
            for detail_item in detail_items  # Iterate all detail entries.
            if isinstance(detail_item, dict)  # Ignore malformed entries safely.
        ]
        logging.debug("Flattened %d detail rows for org %s", len(detail_rows), org_id_value)  # Log detail count.
        return detail_rows  # Return normalized detail rows.

    @staticmethod
    def _prompt_async_claim_include_detail() -> bool:
        """Prompt user for per-device detail preference; returns parsed boolean."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils helper.
        logging.info("Prompting for include_detail in async-claim export")  # Log before detail prompt.
        detail_answer = mh.InputUtils.safe_input(  # Collect detail preference from user.
            "Include per-device detail? (y/N): ",  # Prompt text with safe default.
            context="org_license_claim_status:detail",  # Tag prompt context for EOF handling.
            default_value="N",  # Default to summary-only mode.
        )
        include_detail = detail_answer.strip().lower() in {"y", "yes"}  # Parse yes/no to boolean.
        logging.debug("Resolved include_detail=%s", include_detail)  # Log parsed detail value.
        return include_detail  # Return parsed preference.

    @staticmethod
    def _call_async_claim_api(org_id: str, include_detail: bool) -> tuple[int, dict]:
        """Invoke the async-claim SDK endpoint and return (status_code, payload)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession global.
        detail_query_value = True if include_detail else None  # Omit query param when detail is false.
        logging.info("Calling async-claim API for org %s", org_id)  # Log before SDK call.
        response = mistapi.api.v1.orgs.claim.GetOrgLicenseAsyncClaimStatus(  # Call SDK endpoint.
            mh.apisession,  # Reuse global authenticated API session.
            org_id,  # Pass validated org id to API call.
            detail=detail_query_value,  # Pass optional detail query flag.
        )
        status_code = getattr(response, "status_code", 200)  # Read status code when SDK provides it.
        payload = getattr(response, "data", None) or {}  # Normalize body to dict when missing.
        logging.debug("Async-claim API status=%s", status_code)  # Log status code after API call.
        return status_code, payload  # Return raw response tuple for status routing.

    @staticmethod
    def _handle_async_claim_status(status_code: int, org_id: str, payload: dict) -> dict | None:
        """Route status code to bail-out (None) or normalized payload for downstream writes."""
        if status_code == 401:  # Handle auth failures explicitly.
            logging.error("Mist 401 for async-claim org %s; check token", org_id)  # Provide auth guidance.
            return None  # Signal bail-out to caller.
        if status_code == 403:  # Handle permission failures explicitly.
            logging.error("Mist 403 for async-claim org %s; check org access", org_id)  # Provide access guidance.
            return None  # Signal bail-out because caller lacks required permission.
        if status_code == 400:  # Handle invalid request inputs gracefully.
            logging.warning("Mist 400 for async-claim org %s; check org_id", org_id)  # Provide input guidance.
            return None  # Signal bail-out so user can retry with corrected input.
        if status_code == 404:  # Handle no-active-job response as empty export.
            logging.warning("No async claim job for org %s; exporting empty rows", org_id)  # Explain empty output.
            return {}  # Force empty payload for deterministic writes.
        return payload  # Pass through non-error payload for normal export flow.

    @staticmethod
    def _write_async_claim_summary(org_id: str, payload: dict) -> None:
        """Flatten and persist the single-row async-claim summary for the org."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        logging.info("Preparing summary rows for org %s", org_id)  # Log before summary transform.
        summary_rows: list[Any] = (  # Build summary rows list from payload.
            [LicenseExportUtils._flatten_org_license_async_claim_status_summary(org_id, payload)]  # Wrap flattened row.
            if isinstance(payload, dict) and payload  # Only flatten when payload has data.
            else []  # Keep empty list for no-data cases.
        )
        logging.debug("Prepared %d summary rows", len(summary_rows))  # Log summary count.
        summary_filename = f"org_{org_id[:8]}_claim_status_summary"  # Build summary filename stem.
        logging.info("Writing async-claim summary for org %s", org_id)  # Log before summary write.
        mh.DataExporter.write_with_format_selection(  # Write summary rows to selected backend.
            summary_rows,  # Pass summary rows or empty list.
            summary_filename,  # Use deterministic summary filename stem.
            api_function_name="getOrgLicenseAsyncClaimStatus",  # Route via summary PK strategy.
        )
        logging.debug("Completed summary write for org %s", org_id)  # Log summary write completion.

    @staticmethod
    def _write_async_claim_details(org_id: str, payload: dict) -> None:
        """Flatten and persist per-device async-claim detail rows for the org."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        logging.info("Preparing detail rows for org %s", org_id)  # Log before detail transform.
        detail_rows: list[Any] = (  # Build detail rows list from payload.
            LicenseExportUtils._flatten_org_license_async_claim_status_details(org_id, payload)  # Flatten details.
            if isinstance(payload, dict) and payload  # Only flatten when payload has data.
            else []  # Keep empty list for no-data cases.
        )
        logging.debug("Prepared %d detail rows", len(detail_rows))  # Log detail count.
        detail_filename = f"org_{org_id[:8]}_claim_status_details"  # Build detail filename stem.
        logging.info("Writing async-claim details for org %s", org_id)  # Log before detail write.
        mh.DataExporter.write_with_format_selection(  # Write detail rows to selected backend.
            detail_rows,  # Pass detail rows or empty list.
            detail_filename,  # Use deterministic detail filename stem.
            api_function_name="getOrgLicenseAsyncClaimStatusDetails",  # Route via detail PK strategy.
        )
        logging.debug("Completed detail write for org %s", org_id)  # Log detail write completion.

    @staticmethod
    def _resolve_async_claim_include_detail(include_detail: bool | None) -> bool:
        """Return caller-supplied detail flag, or prompt when the caller passed None."""
        if include_detail is None:  # No explicit preference -- go interactive.
            return LicenseExportUtils._prompt_async_claim_include_detail()  # Delegate prompt to helper.
        return bool(include_detail)  # Normalize truthy/falsy values to real bool.

    @staticmethod
    def export_org_license_async_claim_status(org_id: str | None = None, include_detail: bool | None = None) -> None:
        """Fetch and export async claim status summary plus optional details."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        logging.info("Resolving org_id for async-claim export")  # Log before org resolution.
        resolved_org_id = (
            org_id or mh.ConfigUtils.get_cached_or_prompted_org_id()
        )  # Explicit arg else standard resolver.
        logging.debug("Resolved async-claim org_id=%s", resolved_org_id)  # Log resolved org id.
        if not LicenseExportUtils._is_valid_uuid(resolved_org_id):  # Validate input before any API call.
            logging.warning("Invalid org_id %s for async-claim export", resolved_org_id)  # Warn on invalid input.
            return  # Stop early when input is invalid.
        detail = LicenseExportUtils._resolve_async_claim_include_detail(include_detail)  # Normalize detail flag.
        status_code, raw_payload = LicenseExportUtils._call_async_claim_api(  # SDK call for async-claim status.
            resolved_org_id, detail
        )
        payload = LicenseExportUtils._handle_async_claim_status(  # Route status code to bail-out or payload.
            status_code, resolved_org_id, raw_payload
        )
        if payload is None:  # Helper signalled bail-out via None sentinel.
            return  # Stop so user sees the specific error path in logs.
        LicenseExportUtils._write_async_claim_summary(resolved_org_id, payload)  # Always write summary rows.
        if detail:  # Write details only when user requested them.
            LicenseExportUtils._write_async_claim_details(resolved_org_id, payload)  # Delegate detail write to helper.
