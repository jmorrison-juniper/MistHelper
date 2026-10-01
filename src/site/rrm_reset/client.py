"""Mist API client for site RRM optimize or reset plan capture."""

from __future__ import annotations  # WHY: keep annotations lightweight at runtime.

import logging  # WHY: log before and after every Mist API call.
from typing import Any, Protocol  # WHY: type SDK modules and sessions without importing concrete classes.

import mistapi  # WHY: call the installed Mist SDK for supported RRM operations.

from src.export.site_export_utils import _channel_planning_rows_from_raw, _response_status_code

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter this feature.

HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx responses make the payload unsafe.
RESET_RRM_PATH = "/api/v1/sites/{site_id}/devices/reset_radio_config"  # WHY: SDK lacks reset operation today.


class MistPostSession(Protocol):
    """Protocol for the fallback Mist POST session method."""

    def mist_post(self, uri: str, body: dict[str, Any] | list[Any] | None = None) -> Any:
        """Post to a Mist API path and return the SDK response."""


class RrmResetClient:
    """Read RRM plans and send RRM optimize or reset requests."""

    def __init__(self, apisession: Any) -> None:
        """Store the active Mist API session."""
        self.apisession = apisession  # WHY: every request uses the same authenticated session.

    def get_current_plan(self, site_id: str) -> list[dict[str, Any]]:
        """Read and normalize the current channel plan for one site."""
        logger.info("Reading current RRM plan for site %s", site_id)  # WHY: action log before API read.
        response = mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning(
            self.apisession, site_id
        )  # WHY: menu 86 read.
        status_code = _response_status_code(response)  # WHY: a failed response can carry an empty payload.
        if status_code >= HTTP_ERROR_MIN:  # WHY: do not export a false empty before or after plan.
            msg = f"Mist returned HTTP {status_code} for current RRM plan at site {site_id}."  # WHY: clear error.
            raise RuntimeError(msg)  # WHY: caller must stop before a destructive request.
        raw = getattr(response, "data", response) or {}  # WHY: tolerate SDK response or test double.
        rows = _channel_planning_rows_from_raw(raw, site_id)  # WHY: reuse the menu 86 RRM read normalizer.
        logger.debug("Read current RRM plan rows=%d for site %s", len(rows), site_id)  # WHY: result summary.
        return rows  # WHY: caller writes these rows before or after the request.

    def optimize(self, site_id: str, body: dict[str, Any]) -> Any:
        """Send a site RRM optimize request."""
        logger.info("Sending RRM optimize request for site %s", site_id)  # WHY: action log before mutation.
        response = mistapi.api.v1.sites.rrm.optimizeSiteRrm(self.apisession, site_id, body)  # WHY: SDK supports this.
        logger.debug("RRM optimize request finished for site %s", site_id)  # WHY: summarize mutation completion.
        return response  # WHY: caller can inspect or test the SDK response.

    def reset(self, site_id: str, body: dict[str, Any]) -> Any:
        """Send a site reset-to-RRM request through the documented path."""
        uri = RESET_RRM_PATH.format(site_id=site_id)  # WHY: OpenAPI path requires the site id in the URI.
        logger.info("Sending reset-to-RRM request for site %s", site_id)  # WHY: action log before mutation.
        session = self.apisession  # WHY: local name narrows the protocol for static checks.
        if not hasattr(session, "mist_post"):  # WHY: fail clearly when a test double lacks the fallback method.
            raise RuntimeError("Mist session does not support mist_post for RRM reset.")  # WHY: no silent skip.
        response = session.mist_post(uri, body=body)  # WHY: installed SDK lacks resetSiteAllApsToUseRrm.
        logger.debug("Reset-to-RRM request finished for site %s", site_id)  # WHY: summarize mutation completion.
        return response  # WHY: caller can inspect or test the SDK response.
