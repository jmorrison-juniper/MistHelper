"""Mist API client for on-demand synthetic test triggers."""

from __future__ import annotations  # WHY: keep annotations lazy for the menu loader.

import logging  # WHY: log before and after every Mist API action.
from typing import Any  # WHY: mistapi sessions and responses are SDK objects.

import mistapi.api.v1.sites.devices as site_devices  # WHY: device and switch RADIUS synthetic endpoints live here.
import mistapi.api.v1.sites.synthetic_test as site_synthetic_test  # WHY: site synthetic endpoints live here.

from src.mist.intelligence.troubleshooting.synthetic_test_trigger.models import (
    SyntheticTestRequest,
)  # WHY: client dispatch input.

logger = logging.getLogger(__name__)  # WHY: callers can filter logs to this feature package.


class SyntheticTestClient:
    """Call the Mist synthetic test APIs for one menu run."""

    def __init__(self, mist_session: Any) -> None:
        """Store the SDK session used by all endpoint calls."""
        self._session = mist_session  # WHY: the shared MistHelper session carries identity and regional host.

    def trigger(self, request: SyntheticTestRequest) -> object:
        """Start one synthetic test request in Mist."""
        logger.info(  # WHY: record the action before the Mist API call without secret values.
            "Triggering synthetic test scope=%s site=%s device=%s body=%s",
            request.scope,
            request.site_id,
            request.device_id or "",
            request.public_body(),
        )
        response = self._trigger_by_scope(request)  # WHY: each scope maps to a different SDK function.
        logger.debug("Synthetic test trigger returned response_type=%s", type(response).__name__)  # WHY: result log.
        return response  # WHY: caller may need the SDK response for troubleshooting.

    def poll_once(self, request: SyntheticTestRequest) -> object:
        """Read one synthetic test result poll from Mist."""
        logger.info(  # WHY: record the poll before the Mist API call.
            "Polling synthetic test result scope=%s site=%s device=%s",
            request.scope,
            request.site_id,
            request.device_id or "",
        )
        response = self._poll_by_scope(request)  # WHY: site and device scopes use different result endpoints.
        logger.debug("Synthetic test poll returned response_type=%s", type(response).__name__)  # WHY: result log.
        return response  # WHY: caller normalizes SDK data after each poll.

    def _trigger_by_scope(self, request: SyntheticTestRequest) -> object:
        """Dispatch one trigger call to the correct SDK function."""
        if request.scope == "site":  # WHY: site scope has no device identifier.
            return site_synthetic_test.triggerSiteSyntheticTest(self._session, request.site_id, request.body)
        if request.scope == "radius":  # WHY: RADIUS uses the switch-specific check endpoint.
            return site_devices.startSiteSwitchRadiusSyntheticTest(
                self._session, request.site_id, str(request.device_id), request.body
            )
        return site_devices.triggerSiteDeviceSyntheticTest(
            self._session, request.site_id, str(request.device_id), request.body
        )

    def _poll_by_scope(self, request: SyntheticTestRequest) -> object:
        """Dispatch one result read to the correct SDK function."""
        if request.scope == "site":  # WHY: site tests are discovered through the search endpoint.
            query = request.poll_query  # WHY: explicit SDK arguments keep the compatibility guard measurable.
            return site_synthetic_test.searchSiteSyntheticTest(
                self._session,
                request.site_id,
                mac=query.get("mac"),
                port_id=query.get("port_id"),
                vlan_id=query.get("vlan_id"),
                by=query.get("by"),
                reason=query.get("reason"),
                type=query.get("type"),
                protocol=query.get("protocol"),
                tenant=query.get("tenant"),
                limit=1,
                start=query.get("start"),
                end=query.get("end"),
                duration=query.get("duration"),
                search_after=query.get("search_after"),
            )
        return site_devices.getSiteDeviceSyntheticTest(self._session, request.site_id, str(request.device_id))
