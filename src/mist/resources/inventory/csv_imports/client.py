"""Mist API client for CSV import file uploads."""

from __future__ import annotations  # WHY: keep type annotations import-safe during CLI startup.

import logging  # WHY: log request boundaries without logging CSV contents.
from collections.abc import Callable  # WHY: type injected SDK call seams.
from pathlib import Path  # WHY: pass file paths without hard-coded separators.
from typing import Any  # WHY: SDK response objects are dynamic.

from mistapi.api.v1.orgs import assets as org_assets  # WHY: call the generated org asset file importer.
from mistapi.api.v1.orgs import psks as org_psks  # WHY: call the generated org PSK file importer.
from mistapi.api.v1.orgs import usermacs as org_user_macs  # WHY: call the generated org user MAC importer.
from mistapi.api.v1.sites import assets as site_assets  # WHY: call the generated site asset file importer.
from mistapi.api.v1.sites import psks as site_psks  # WHY: call the generated site PSK file importer.

from src.mist.resources.inventory.csv_imports.model import (
    CsvImportDefinition,
)  # WHY: bind requests to audited import metadata.

logger = logging.getLogger(__name__)  # WHY: module logger supports focused log capture tests.

ImportCall = Callable[[Any, str, str], Any]  # WHY: all chosen SDK file functions share this shape.


class CsvImportClient:
    """Send CSV import files to the selected Mist import endpoint."""

    _CALLS: dict[str, ImportCall] = {  # WHY: map operation IDs to the SDK file-upload functions.
        "importOrgPsks": org_psks.importOrgPsksFile,
        "importOrgUserMacs": org_user_macs.importOrgUserMacsFile,
        "importOrgAssets": org_assets.importOrgAssetsFile,
        "importSitePsks": site_psks.importSitePsksFile,
        "importSiteAssets": site_assets.importSiteAssetsFile,
    }

    def __init__(self, session: Any, calls: dict[str, ImportCall] | None = None) -> None:
        """Create the import client."""
        self._session = session  # WHY: the active Mist session owns auth and regional host state.
        self._calls = calls or self._CALLS  # WHY: tests inject local call doubles without network access.

    def send(self, definition: CsvImportDefinition, scope_id: str, file_path: Path) -> Any:
        """Upload one CSV file to Mist."""
        logger.info("Sending CSV import request operation=%s rows_source=file", definition.operation_id)  # WHY: start.
        call = self._calls[definition.operation_id]  # WHY: KeyError exposes a missing client mapping in tests.
        response = call(self._session, scope_id, str(file_path))  # WHY: SDK file functions require a string path.
        status_code = getattr(response, "status_code", "unknown")  # WHY: response doubles may not expose a status.
        logger.debug("CSV import request finished operation=%s status=%s", definition.operation_id, status_code)
        return response  # WHY: operation converts the response into a sanitized result row.


class CsvImportResponseSummary:
    """Build sanitized summaries from dynamic SDK response objects."""

    @staticmethod
    def summarize(response: Any) -> str:
        """Return a summary that contains no row data."""
        status_code = getattr(response, "status_code", None)  # WHY: status is safe and useful when present.
        if status_code is None:  # WHY: old SDK tests often use response doubles without status.
            return "request_sent"  # WHY: do not inspect response bodies that could include secrets.
        return f"request_sent_status_{status_code}"  # WHY: status-only output is safe for PSK imports.
