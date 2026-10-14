"""Limit firmware policy requests to validated SDK settings and catalog operations."""

from __future__ import annotations

import logging
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

import mistapi
from mistapi.__api_response import APIResponse
from mistapi.__api_response import console as sdk_console
from mistapi.api.v1.const import device_models
from mistapi.api.v1.orgs import devices, inventory, orgs, sites, ssr
from mistapi.api.v1.orgs import setting as org_setting
from mistapi.api.v1.self import usage
from mistapi.api.v1.sites import setting as site_setting
from requests.exceptions import RequestException

from src.foundation.support.utils.rate_limiting import AdaptivePacer
from src.mist.access.api.api_usage_cache import api_usage_cache

logger = logging.getLogger(__name__)


class SettingsRequestGuard(logging.Filter):
    """Protect private settings from SDK diagnostics and prevent repeated settings writes."""

    lock = threading.RLock()

    def __init__(self, session: mistapi.APISession, write: bool = False) -> None:
        """Retain the SDK session without exposing its credentials."""
        super().__init__()
        self.session = session
        self.write = write
        self.previous: int | None = None
        self.console_level = 0

    def __enter__(self) -> SettingsRequestGuard:
        """Serialize guarded calls and redact the SDK's shared diagnostic logger."""
        self.lock.acquire()
        self._privacy(True)
        if self.write:
            self.previous = getattr(self.session, "_MAX_429_RETRIES", None)
            self.session._MAX_429_RETRIES = 0
        return self

    def __exit__(self, *_exception: Any) -> None:
        """Restore the pinned SDK retry setting and release the diagnostic guard."""
        if self.write:
            if self.previous is None:
                del self.session._MAX_429_RETRIES
            else:
                self.session._MAX_429_RETRIES = self.previous
        self._privacy(False)
        self.lock.release()

    def _privacy(self, enabled: bool) -> None:
        """Protect both SDK log handlers and its separate direct console output."""
        if enabled:
            self.console_level = sdk_console.level
            sdk_console.level = 0
            logging.getLogger("mistapi").addFilter(self)
        else:
            logging.getLogger("mistapi").removeFilter(self)
            sdk_console.level = self.console_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Replace SDK diagnostic content before any log handler receives settings."""
        record.msg = "SDK settings diagnostic redacted. See the checked settings request status."
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


class PolicyError(RuntimeError):
    """Report a failed policy operation without exposing a settings response."""


class PolicyAdmission:
    """Admit SDK requests through shared pacing and authoritative rolling-hour usage."""

    def __init__(self, session: mistapi.APISession, progress: Callable[[dict[str, Any]], None] | None) -> None:
        """Use the existing cache and controller rather than an independent rate limiter."""
        self.session = session  # Use the same authenticated SDK for usage and settings.
        self.progress = progress  # Keep request waits visible without exposing settings.
        self.pacer = AdaptivePacer(self, api_usage_cache)  # Route controller probes through the checked SDK boundary.
        self.observed = 0.0  # Require an authoritative probe before the first external request.
        self.used = 0  # Count requests since the last authoritative observation.
        self.limit = 0  # Never assume quota availability before a successful probe.
        self.quota_wait = 60.0  # Poll actual rolling usage when the API supplies no wait duration.

    def wait(self, seconds: float, identifier: str) -> None:
        """Report a sanitized wait before sleeping for quota admission."""
        if seconds > 0:  # Zero-delay fixture clocks need no sleep.
            if self.progress:
                self.progress({"phase": "waiting", "id": identifier, "wait_seconds": seconds})
            logger.info("Wait %.3f seconds for policy request admission", seconds)
            time.sleep(seconds)  # A rolling quota does not reset at a wall-clock hour boundary.
            logger.debug("Completed policy admission wait")

    def refresh(self, identifier: str) -> None:
        """Read real usage through the SDK and fail closed on an unreadable quota."""
        self.wait(self.pacer.next_delay(), identifier)  # Pace the usage probe as an external request.
        self.mist_get("/api/v1/self/usage")  # Use the same checked probe as the shared controller.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> APIResponse:
        """Admit the shared controller's real usage probe without recursive pacing."""
        if uri != "/api/v1/self/usage":
            raise PolicyError("The request controller attempted an unsupported usage probe.")
        response = PolicyResponse.request(
            lambda: usage.getSelfApiUsage(self.session), "Read API usage", "quota"
        )  # The pinned SDK owns transport and URI construction.
        document = PolicyResponse.mapping(response.data)
        used = self.usage_integer(document.get("requests"), 0)
        limit = self.usage_integer(document.get("request_limit"), 1)
        self.used, self.limit, self.observed = used + 1, limit, time.time()  # Include the usage probe itself.
        self.quota_wait = self.usage_seconds(document.get("seconds"))
        api_usage_cache.update(
            used=self.used,
            limit=limit,
            last_updated=self.observed,
            initialized=True,
            perceived_requests=0,
            policy_observed_at=self.observed,
            policy_actual_used=self.used,
        )  # Publish the actual quota observation to the shared request tools.
        return response  # The shared controller consumes the same verified actual usage response.

    @staticmethod
    def usage_integer(value: Any, minimum: int) -> int:
        """Reject a missing or malformed quota rather than assuming available requests."""
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise PolicyError("The API usage response has no valid request quota.")
        return value

    @staticmethod
    def usage_seconds(value: Any) -> float:
        """Honor a valid server wait without treating it as a guaranteed quota reset."""
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0:
            return float(value)
        return 60.0  # Without a supplied wait, poll the actual rolling usage again.

    def request(self, call: Callable[[], APIResponse], action: str, identifier: str) -> APIResponse:
        """Count every read, page, and write once, without repeating uncertain writes."""
        with SettingsRequestGuard.lock:  # Serialize reservation against other policy operations.
            self.used = max(self.used, int(api_usage_cache.get("policy_actual_used", 0)))
            if not self.limit or time.time() - self.observed >= 60:
                self.refresh(identifier)  # Refresh before estimates can hide another client's usage.
            self.admit(identifier)  # Controller probes can discover quota exhaustion during pacing.
            self.used += 1  # Reserve quota even when transport completion is uncertain.
            api_usage_cache.update(policy_actual_used=self.used)  # Retain the actual local request count.
            if self.progress:
                self.progress({"phase": action, "id": identifier, "wait_seconds": 0})
            return PolicyResponse.request(call, action, identifier)  # Never retry an uncertain settings write.

    def admit(self, identifier: str) -> None:
        """Recheck authoritative quota after pacing and before reserving a request."""
        while True:
            if self.used >= self.limit - 1:
                self.wait(self.quota_wait, identifier)  # A real rolling quota decides when requests can continue.
                self.refresh(identifier)
                continue
            self.wait(self.pacer.next_delay(), identifier)
            self.used = max(self.used, int(api_usage_cache.get("policy_actual_used", 0)))
            if self.used < self.limit - 1:
                return  # Never dispatch a settings call after a controller probe reports exhaustion.


class PolicyResponse:
    """Validate identifiers and SDK responses before a caller uses their content."""

    @staticmethod
    def identifier(value: str) -> str:
        """Reject malformed scope identifiers before any external request."""
        try:
            return str(UUID(value))  # Validate the external identifier.
        except (ValueError, TypeError, AttributeError) as error:
            raise PolicyError("A scope identifier is not a valid UUID.") from error

    @staticmethod
    def request(call: Callable[[], APIResponse], action: str, identifier: str) -> APIResponse:
        """Check request status and redact exceptions at the request boundary."""
        logger.info("Policy request %s for %s", action, identifier)  # Record the action without its body.
        try:
            response = call()  # Delegate authentication and transport to the SDK.
        except (RequestException, RuntimeError, OSError) as error:
            logger.error("Policy request %s for %s failed: %s", action, identifier, type(error).__name__)
            raise PolicyError(f"{action} failed for {identifier}: {type(error).__name__}.") from None
        status = getattr(response, "status_code", None)  # Reject missing status rather than assuming success.
        if not isinstance(status, int) or not 200 <= status < 300:
            logger.error("Policy request %s for %s returned HTTP %s", action, identifier, status)
            raise PolicyError(f"{action} failed for {identifier}: HTTP {status}.")
        logger.debug("Policy request %s for %s returned HTTP %s", action, identifier, status)
        return response  # Callers validate the expected data shape and pagination.

    @staticmethod
    def mapping(value: Any) -> dict[str, Any]:
        """Reject unreadable settings rather than replacing them with empty settings."""
        if not isinstance(value, dict):
            raise PolicyError("The settings response is not an object.")
        return value  # Preserve the SDK object without logging its sensitive fields.

    @staticmethod
    def rows(value: Any) -> list[dict[str, Any]]:
        """Reject malformed lists before model or scope selection."""
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise PolicyError("The list response contains an invalid record.")
        return value  # Preserve each checked record.

    @staticmethod
    def collect(
        session: mistapi.APISession,
        call: Callable[[], APIResponse],
        action: str,
        identifier: str,
        request: Callable[[Callable[[], APIResponse], str, str], APIResponse] | None = None,
    ) -> list[dict[str, Any]]:
        """Collect checked SDK pages and refuse a repeated or failed next page."""
        records: list[dict[str, Any]] = []  # Never substitute an incomplete target list.
        seen: set[str] = set()  # Detect a repeated pagination link.
        checked = request or PolicyResponse.request  # Let the API admit every SDK page through shared pacing.
        response = checked(call, action, identifier)  # Validate the first page.
        while True:
            records.extend(PolicyResponse.rows(response.data))  # Fail when any page is malformed.
            link = getattr(response, "next", None)  # A missing link means the last page.
            if not link:
                return records  # Only a complete list can reach the workflow.
            if link in seen:
                raise PolicyError("The settings target list has a repeated pagination link.")
            seen.add(link)  # Prevent an unbounded pagination loop.

            def next_page(page: APIResponse = response) -> APIResponse:
                """Bind the checked page before requesting its SDK next-page response."""
                return mistapi.get_next(session, page)

            response = checked(next_page, action, identifier)


@dataclass
class PolicyApi:
    """Expose only the reads and settings writes needed by menu 305."""

    session: mistapi.APISession
    progress: Callable[[dict[str, Any]], None] | None = None
    guard: PolicyAdmission = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Bind the optional progress callback to shared request admission."""
        self.guard = PolicyAdmission(self.session, self.progress)

    def organization(self, identifier: str) -> dict[str, Any]:
        """Resolve actual organization identity through an admitted SDK lookup."""
        identifier = PolicyResponse.identifier(identifier)
        with SettingsRequestGuard(self.session):
            result = PolicyResponse.mapping(
                self.guard.request(lambda: orgs.getOrg(self.session, identifier), "Read organization", identifier).data
            )
        if result.get("id", identifier) != identifier or not isinstance(result.get("name"), str):
            raise PolicyError("The organization identity response is invalid.")
        return {"id": identifier, "name": result["name"]}  # Never return private identity response siblings.

    def models(self, org_id: str) -> list[dict[str, Any]]:
        """Read authoritative model constants without inventing compatibility names."""
        org_id = PolicyResponse.identifier(org_id)
        with SettingsRequestGuard(self.session):
            return PolicyResponse.collect(
                self.session,
                lambda: device_models.listDeviceModels(self.session),
                "Read device models",
                org_id,
                self.guard.request,
            )

    def read(self, scope: Literal["org", "site"], identifier: str) -> dict[str, Any]:
        """Read local settings without substituting an effective organization policy."""
        identifier = PolicyResponse.identifier(identifier)  # Check the scope before using it.

        def call() -> APIResponse:
            """Select the SDK settings read for the requested scope."""
            if scope == "org":
                return org_setting.getOrgSettings(self.session, identifier)
            return site_setting.getSiteSetting(self.session, identifier)

        with SettingsRequestGuard(self.session):
            return PolicyResponse.mapping(self.guard.request(call, f"Read {scope} settings", identifier).data)

    def write(self, scope: Literal["org", "site"], identifier: str, body: dict[str, Any]) -> None:
        """Write settings only and let the workflow verify the saved state."""
        identifier = PolicyResponse.identifier(identifier)  # Check the scope before using it.

        def call() -> APIResponse:
            """Select a settings write, never a firmware execution endpoint."""
            if scope == "org":
                return org_setting.updateOrgSettings(self.session, identifier, body=body)
            return site_setting.updateSiteSettings(self.session, identifier, body=body)

        with SettingsRequestGuard(self.session, write=True):
            self.guard.request(call, f"Write {scope} settings", identifier)  # Check every write status.

    def sites(self, org_id: str) -> list[dict[str, Any]]:
        """Read every site before confirmation, including paginated site lists."""
        org_id = PolicyResponse.identifier(org_id)  # Refuse malformed organization input.
        logger.info("Read all policy sites for %s", org_id)  # Record the complete-list action.
        with SettingsRequestGuard(self.session):
            result = PolicyResponse.collect(  # Check every SDK page rather than accepting partial pagination.
                self.session,
                lambda: sites.listOrgSites(self.session, org_id),
                "List organization sites",
                org_id,
                self.guard.request,
            )
        logger.debug("Read %s policy sites for %s", len(result), org_id)  # Record the examined count.
        return result  # The workflow reads each site's local settings next.

    def versions(self, org_id: str, kind: str) -> list[dict[str, Any]]:
        """Read the appropriate firmware catalog for the selected hardware type."""
        org_id = PolicyResponse.identifier(org_id)  # Validate the scope before a catalog request.
        device_type = {"ap": "ap", "switch": "switch", "juniper_srx": "gateway", "ssr": "gateway"}
        if kind not in device_type:
            raise PolicyError("The device type has no supported auto-upgrade policy.")

        def call() -> APIResponse:
            """Use the dedicated SSR catalog instead of the gateway catalog."""
            if kind == "ssr":
                return ssr.listOrgAvailableSsrVersions(self.session, org_id)
            return devices.listOrgAvailableDeviceVersions(self.session, org_id, type=device_type[kind])

        with SettingsRequestGuard(self.session):
            records = PolicyResponse.collect(self.session, call, "Read firmware versions", org_id, self.guard.request)
        return sorted(records, key=lambda row: self.version_key(str(row.get("version", ""))), reverse=True)

    @staticmethod
    def version_key(version: str) -> tuple[Any, ...]:
        """Sort dotted numeric components before deterministic release suffixes."""
        import re  # Split numeric components without treating a version as a floating-point value.

        match = re.fullmatch(r"([^\d]*)(\d+(?:\.\d+)*)(.*)", version)
        if not match:
            return version.casefold(), (), True, ()
        prefix, number, suffix = match.groups()
        components = tuple(
            (1, int(component)) if component.isdigit() else (0, component.casefold())
            for component in re.findall(r"\d+|[^\d]+", suffix)
        )
        return prefix.casefold(), tuple(int(component) for component in number.split(".")), not bool(suffix), components

    def inventory(self, org_id: str) -> list[dict[str, Any]]:
        """Read gateway models because SSR catalog rows do not contain model names."""
        org_id = PolicyResponse.identifier(org_id)  # Check the scope before inventory access.
        with SettingsRequestGuard(self.session):
            return PolicyResponse.collect(
                self.session,
                lambda: inventory.getOrgInventory(self.session, org_id, type="gateway"),
                "Read gateway inventory",
                org_id,
                self.guard.request,
            )
