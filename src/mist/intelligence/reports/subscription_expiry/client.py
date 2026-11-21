"""Mist SDK client seam for the subscription expiry report."""

from __future__ import annotations  # Keep annotations import-safe during tests.

import logging  # Record client actions for operator traceability.
import time  # Bound the one HTTP 429 retry.
from types import SimpleNamespace  # Build safe SDK-shaped responses for transport failures.
from typing import Any  # Type SDK responses without importing Mist response classes.

import mistapi  # Use the project-approved Mist SDK for API calls.

from src.foundation.runtime.config import runtime_settings  # Reuse the project page-limit setting.
from src.mist.intelligence.reports.subscription_expiry.model import (
    MISSING_VALUE,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    OrganizationScope,
)

logger = logging.getLogger(__name__)  # Give this module a stable logger name.
HTTP_BAD_REQUEST = 400  # Detect the no-linked-account JSI path.


class JsiAccountNotLinkedError(RuntimeError):
    """Raised when the JSI endpoint reports no linked Juniper account."""


class SubscriptionExpiryClientError(RuntimeError):
    """Raised when a Mist API response reports an unexpected failure."""


class SubscriptionExpiryClient:
    """Wrap the Mist SDK calls used by the subscription expiry report."""

    def __init__(self, apisession: Any) -> None:
        """Store the active Mist API session."""
        self.apisession = apisession  # Keep the session explicit for tests and operation wiring.

    def _request_with_retry(
        self,
        operation: str,
        target: str,
        request_call: Any,
    ) -> Any:
        """Retry one HTTP 429 response and return the SDK response."""
        for attempt in range(2):  # Permit no more than one retry.
            try:
                response = request_call()  # Send one SDK read request.
            except Exception as error:  # Transport and SDK failures need a safe response.
                logger.error(
                    "Mist request %s failed for %s with %s",
                    operation,
                    target,
                    type(error).__name__,
                )  # Keep the secret and exception text out of logs.
                return SimpleNamespace(status_code=0, data=None, next=None)  # Return a transport-failure shape.
            status_code = getattr(response, "status_code", None)  # Read the SDK status.
            if status_code == 429 and attempt == 0:  # Rate limit is the one retryable status.
                logger.warning("Mist limited %s for %s. Waiting 60 seconds.", operation, target)  # Explain wait.
                time.sleep(60)  # Honor the source retry window.
                continue  # Retry exactly once.
            return response  # Return success or a non-retryable status.
        return response  # Return the final response as a fail-safe.

    def fetch_profile(self) -> tuple[int | None, dict[str, Any]]:
        """Fetch the active profile and return status plus normalized data."""
        logger.info("Fetching active Mist profile")  # Log before profile read.
        response = self._request_with_retry(
            "getSelf",
            "active session",
            lambda: mistapi.api.v1.self.self.getSelf(self.apisession),
        )  # Call the SDK profile method.
        status_code = getattr(response, "status_code", None)  # Read safe status.
        payload = self._response_payload(response)  # Normalize the response body.
        logger.debug("Profile read status=%s", status_code)  # Log status only.
        return status_code, payload if isinstance(payload, dict) else {}  # Return normalized profile.

    def discover_organizations(
        self,
        active_org_id: str,
        active_org_name: str,
    ) -> tuple[list[OrganizationScope], list[OrganizationScope]]:
        """Discover direct and MSP organizations granted to the active profile."""
        logger.info("Discovering cross-org organization scope")  # Log before discovery.
        organizations = self._direct_organizations(active_org_id, active_org_name)  # Seed direct scope.
        status_code, profile = self.fetch_profile()  # Read profile grants.
        failures = self._profile_failure(active_org_id, active_org_name, status_code)  # Preserve profile failure.
        privileges = profile.get("privileges") if isinstance(profile, dict) else None  # Read grants.
        if not isinstance(privileges, list):  # Invalid profile grants need a visible failure.
            privileges = []  # Keep direct organization scope and stop MSP parsing.
            if status_code == 200:  # Only successful profile reads get this shape.
                logger.warning("Profile returned no organization grant list")  # Name missing grant data.
        for privilege in privileges:  # Walk each profile grant.
            if not isinstance(privilege, dict):  # Skip malformed grants.
                continue  # Keep only mapping grants.
            self._add_direct_privilege(organizations, privilege)  # Add direct grant.
            msp_id = privilege.get("msp_id")  # Read MSP grant.
            if isinstance(msp_id, str) and msp_id:  # Valid MSP grant.
                self._discover_msp(msp_id, organizations, failures)  # Add MSP organizations.
        logger.debug(
            "Discovered %d organizations and %d discovery failures",
            len(organizations),
            len(failures),
        )  # Log discovery counts.
        return self._order_organizations(organizations, active_org_id), failures  # Return stable scope.

    @staticmethod
    def _direct_organizations(active_org_id: str, active_org_name: str) -> dict[str, OrganizationScope]:
        """Seed direct organization scope from the active context."""
        if not active_org_id:  # No configured organization exists.
            return {}  # Keep an empty direct scope.
        return {
            active_org_id: OrganizationScope(
                org_id=active_org_id,
                org_name=active_org_name or active_org_id,
                source="direct",
                request_status="success",
            )
        }  # Seed one direct organization.

    @staticmethod
    def _profile_failure(
        active_org_id: str,
        active_org_name: str,
        status_code: int | None,
    ) -> list[OrganizationScope]:
        """Build visible profile failure scope."""
        if status_code == 200:  # A successful profile has no discovery failure.
            return []  # Return no failure.
        return [
            OrganizationScope(
                org_id=active_org_id or MISSING_VALUE,
                org_name=active_org_name or MISSING_VALUE,
                source="profile",
                request_status="failed",
                error=f"HTTP {status_code}",
            )
        ]  # Preserve profile failure.

    @staticmethod
    def _add_direct_privilege(
        organizations: dict[str, OrganizationScope],
        privilege: dict[str, Any],
    ) -> None:
        """Add one direct organization privilege."""
        direct_org_id = privilege.get("org_id")  # Read direct organization.
        if not isinstance(direct_org_id, str) or not direct_org_id:  # Skip malformed direct grants.
            return  # Keep only valid IDs.
        organizations.setdefault(
            direct_org_id,
            OrganizationScope(
                org_id=direct_org_id,
                org_name=privilege.get("org_name") or privilege.get("name") or direct_org_id,
                source="direct",
                request_status="success",
            ),
        )  # Add direct organization scope.

    def _discover_msp(
        self,
        msp_id: str,
        organizations: dict[str, OrganizationScope],
        failures: list[OrganizationScope],
    ) -> None:
        """Discover organizations under one MSP grant."""
        response = self._request_with_retry(
            "listMspOrgs",
            msp_id,
            lambda: mistapi.api.v1.msps.orgs.listMspOrgs(self.apisession, msp_id),
        )  # Call MSP organization discovery.
        status_code = getattr(response, "status_code", None)  # Read MSP status.
        if status_code != 200:  # MSP discovery failed at the first page.
            failures.append(
                OrganizationScope(
                    org_id=MISSING_VALUE,
                    org_name=f"MSP {msp_id}",
                    msp_id=msp_id,
                    source="msp",
                    request_status="failed",
                    error=f"HTTP {status_code}" if status_code is not None else "Invalid MSP organization list",
                )
            )  # Preserve visible failure.
            return  # Keep direct organizations.
        try:  # Validate every continuation page before organization data is added.
            org_rows = self._paginate_list_response(
                "listMspOrgs",
                msp_id,
                response,
            )  # Follow all MSP organization pages.
        except SubscriptionExpiryClientError as error:  # A later page or invalid shape is incomplete.
            failures.append(
                OrganizationScope(
                    org_id=MISSING_VALUE,
                    org_name=f"MSP {msp_id}",
                    msp_id=msp_id,
                    source="msp",
                    request_status="failed",
                    error=str(error),
                )
            )  # Preserve visible MSP pagination failure.
            return  # Keep direct organizations.
        for org in org_rows:  # Walk each MSP organization.
            if not isinstance(org, dict):  # Skip malformed org rows.
                continue  # Keep only mapping rows.
            org_id = org.get("id")  # Read organization ID.
            if not isinstance(org_id, str) or not org_id:  # Skip missing IDs.
                continue  # An organization call needs an ID.
            organizations.setdefault(
                org_id,
                OrganizationScope(
                    org_id=org_id,
                    org_name=org.get("name") or org_id,
                    msp_id=msp_id,
                    source="msp",
                    request_status="success",
                ),
            )  # Add MSP organization once.

    @staticmethod
    def _order_organizations(
        organizations: dict[str, OrganizationScope],
        active_org_id: str,
    ) -> list[OrganizationScope]:
        """Place the active organization first and then MSP organizations."""
        ordered_organizations = list(organizations.values())  # Preserve direct organizations before MSP additions.
        if active_org_id in organizations:  # Keep the active/direct organization first.
            active_organization = organizations.pop(active_org_id)  # Remove direct for stable placement.
            ordered_organizations = [
                active_organization,
                *organizations.values(),
            ]  # Place direct before MSP organizations.
        return ordered_organizations  # Return the stable organization order.

    def fetch_inventory(self, org_id: str) -> list[dict[str, Any]]:
        """Fetch all inventory pages for one organization."""
        logger.info("Fetching inventory for organization %s", org_id)  # Log before inventory read.
        page_size = runtime_settings.DEFAULT_API_PAGE_LIMIT  # Reuse the project page limit.
        response = self._request_with_retry(
            "getOrgInventory",
            org_id,
            lambda: mistapi.api.v1.orgs.inventory.getOrgInventory(
                self.apisession,
                org_id,
                limit=page_size,
                page=1,
                vc=True,
            ),
        )  # Call one first inventory page with Virtual Chassis expansion.
        status_code = getattr(response, "status_code", None)  # Read inventory status.
        if status_code != 200:  # Inventory page failed.
            raise SubscriptionExpiryClientError(f"Inventory returned HTTP {status_code}")  # Surface status.
        inventory_rows = self._paginate_list_response(
            "getOrgInventory",
            org_id,
            response,
        )  # Follow all inventory pages.
        expanded_rows = self._expand_virtual_chassis_members(org_id, inventory_rows)  # Read physical VC members.
        logger.debug(
            "Fetched %d inventory rows and expanded %d VC member rows",
            len(inventory_rows),
            len(expanded_rows),
        )  # Log inventory and expansion counts.
        return expanded_rows  # Return every inventory and physical VC member mapping.

    def fetch_msp_licenses(self, msp_id: str) -> dict[str, Any] | None:
        """Fetch optional MSP purchase evidence or return None for an HTTP failure."""
        logger.info("Fetching MSP license evidence for %s", msp_id)  # Log before MSP read.
        response = self._request_with_retry(
            "listMspLicenses",
            msp_id,
            lambda: mistapi.api.v1.msps.licenses.listMspLicenses(self.apisession, msp_id),
        )  # Call the SDK MSP license endpoint.
        status_code = getattr(response, "status_code", None)  # Read MSP license status.
        if status_code != 200:  # MSP license read failed.
            logger.warning("MSP license read returned HTTP %s", status_code)  # Surface status only.
            return None  # Degrade to organization license evidence.
        payload = self._response_payload(response)  # Normalize payload.
        return payload if isinstance(payload, dict) else None  # Return mapping or no evidence.

    def fetch_license_summary(self, org_id: str) -> LicenseSummarySource:
        """Fetch and normalize the organization license summary."""
        logger.info("Fetching license summary for organization %s", org_id)  # Log before the SDK call.
        response = self._request_with_retry(
            "getOrgLicensesSummary",
            org_id,
            lambda: mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(self.apisession, org_id),
        )  # Call the SDK license summary method.
        status_code = getattr(response, "status_code", None)  # Read license summary status.
        if status_code is not None and status_code != 200:  # Reject explicit HTTP and transport failures.
            raise SubscriptionExpiryClientError(f"License summary returned HTTP {status_code}")  # Surface status.
        payload = self._response_payload(response)  # Convert the SDK response wrapper to a plain container.
        logger.debug("Fetched license summary payload type %s", type(payload).__name__)  # Log safe result shape.
        return self._license_summary_from_payload(payload)  # Normalize the source payload.

    def fetch_license_usage_by_site(self, org_id: str) -> list[LicenseUsageSource]:
        """Fetch and normalize license usage by site."""
        logger.info("Fetching license usage by site for organization %s", org_id)  # Log before the SDK call.
        response = self._request_with_retry(
            "getOrgLicensesBySite",
            org_id,
            lambda: mistapi.api.v1.orgs.licenses.getOrgLicensesBySite(self.apisession, org_id),
        )  # Call the SDK license usage method.
        status_code = getattr(response, "status_code", None)  # Read license usage status.
        if status_code is not None and status_code != 200:  # Reject explicit HTTP and transport failures.
            raise SubscriptionExpiryClientError(f"License usage returned HTTP {status_code}")  # Surface status.
        payload = self._response_payload(response)  # Convert the SDK response wrapper to a plain container.
        rows = self._list_payload(payload)  # Normalize singleton or list payloads into a list.
        logger.debug("Fetched %d license usage rows", len(rows))  # Log normalized row count.
        return [self._license_usage_from_payload(row) for row in rows]  # Convert rows to source dataclasses.

    def search_jsi_assets_and_contracts(self, org_id: str) -> list[JsiContractSource]:
        """Fetch and normalize paginated JSI asset and contract rows."""
        logger.info("Searching JSI assets and contracts for organization %s", org_id)  # Log before the SDK call.
        response = self._request_with_retry(
            "searchOrgJsiAssetsAndContracts",
            org_id,
            lambda: mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts(
                self.apisession,
                org_id,
                limit=runtime_settings.DEFAULT_API_PAGE_LIMIT,
            ),
        )  # Call Mist SDK with the shared page size.
        self._raise_for_jsi_error(response)  # Convert expected 400 response into a clear operation signal.
        rows = mistapi.get_all(response=response, mist_session=self.apisession)  # Let mistapi handle pagination.
        logger.debug("Fetched %d JSI asset and contract rows", len(rows))  # Log normalized row count.
        return [self._jsi_contract_from_payload(row) for row in rows]  # Convert rows to source dataclasses.

    @staticmethod
    def _response_payload(response: Any) -> Any:
        """Return response.data when present, otherwise return the response itself."""
        return getattr(response, "data", response)  # Support SDK responses and plain test containers.

    def _paginate_list_response(
        self,
        operation: str,
        target: str,
        response: Any,
    ) -> list[dict[str, Any]]:
        """Follow validated SDK continuation pages and return mapping rows."""
        records: list[dict[str, Any]] = []  # Accumulate only mapping rows.
        current = response  # Start with the first validated SDK response.
        seen_links: set[str] = set()  # Detect repeated continuation links.
        while True:  # Walk every page until the SDK reports no continuation.
            records.extend(self._validated_page_records(operation, current))  # Keep validated mapping rows.
            next_link = self._continuation_link(operation, current, seen_links)  # Read and validate the next link.
            if next_link is None:  # The final page has no continuation.
                break  # Stop without inventing another page.
            seen_links.add(next_link)  # Remember this continuation before the SDK call.
            logger.info("Fetching the next %s page for %s", operation, target)  # Log before later-page read.
            current = self._fetch_continuation_page(operation, target, current)  # Follow the SDK continuation.
        logger.debug("Fetched %d mapping rows for %s", len(records), operation)  # Log page completion.
        return records  # Return every mapping row from every validated page.

    def _validated_page_records(
        self,
        operation: str,
        response: Any,
    ) -> list[dict[str, Any]]:
        """Validate one SDK page and return its mapping records."""
        status_code = getattr(response, "status_code", None)  # Read one page status.
        if status_code != 200:  # No later page may become partial success.
            raise SubscriptionExpiryClientError(f"{operation} returned HTTP {status_code}")  # Surface status.
        payload = self._response_payload(response)  # Normalize the SDK wrapper.
        if not isinstance(payload, list):  # The endpoint contract requires a list.
            raise SubscriptionExpiryClientError(f"{operation} returned an invalid result list")  # Surface shape.
        return [row for row in payload if isinstance(row, dict)]  # Keep mapping rows only.

    @staticmethod
    def _continuation_link(
        operation: str,
        response: Any,
        seen_links: set[str],
    ) -> str | None:
        """Return one valid SDK continuation link or None for the final page."""
        next_link = getattr(response, "next", None)  # Read the SDK continuation link.
        if not next_link:  # The final page has no continuation.
            return None  # Stop without inventing another page.
        if not isinstance(next_link, str) or not next_link:  # A continuation needs a usable URL.
            raise SubscriptionExpiryClientError(f"{operation} returned an invalid continuation")  # Surface link.
        if next_link in seen_links:  # Repeated links would never complete.
            raise SubscriptionExpiryClientError(f"{operation} returned a repeated continuation")  # Surface loop.
        return next_link  # Return one validated continuation link.

    def _fetch_continuation_page(
        self,
        operation: str,
        target: str,
        response: Any,
    ) -> Any:
        """Read one SDK continuation response and reject a missing page."""

        def page_call(page_response: Any = response) -> Any:
            """Bind the exact SDK page response for one continuation request."""
            return mistapi.get_next(
                mist_session=self.apisession,
                response=page_response,
            )  # Request only the response that owns this continuation.

        page = self._request_with_retry(
            operation,
            target,
            page_call,
        )  # Follow the SDK-provided continuation.
        if page is None:  # A missing later response is incomplete.
            raise SubscriptionExpiryClientError(f"{operation} returned no next page")  # Surface truncation.
        return page  # Return the validated continuation response.

    @staticmethod
    def _is_synthetic_virtual_identity(value: Any) -> bool:
        """Identify Mist synthetic Virtual Chassis MAC and serial values."""
        text = str(value).strip().lower() if value is not None else ""  # Normalize source text.
        return text.startswith("020003") or text.startswith("020004")  # Name the synthetic prefixes.

    @staticmethod
    def _is_switch_record(record: dict[str, Any]) -> bool:
        """Return True for one switch inventory record."""
        return str(record.get("type") or "").strip().lower() == "switch"  # A switch uses the VC status endpoint.

    @staticmethod
    def _is_logical_vc_candidate(
        record: dict[str, Any],
    ) -> bool:
        """Return True for a logical VC or FPC0 inventory record."""
        serial = str(record.get("serial") or "").strip()  # Read the logical or physical serial.
        mac = str(record.get("mac") or "").strip()  # Read the logical or physical MAC.
        vc_mac = str(record.get("vc_mac") or "").strip()  # Read the VC parent MAC.
        if SubscriptionExpiryClient._is_synthetic_virtual_identity(serial):  # A synthetic serial names a logical VC.
            return True  # The row needs physical member expansion.
        if SubscriptionExpiryClient._is_synthetic_virtual_identity(mac):  # A synthetic MAC names a logical VC.
            return True  # The row needs physical member expansion.
        return bool(vc_mac and vc_mac.lower() == mac.lower())  # FPC0 and virtual MAC use the VC status endpoint.

    @staticmethod
    def _partner_device_id(
        record: dict[str, Any],
        inventory: list[dict[str, Any]],
        vc_mac: str,
    ) -> str:
        """Find a partner inventory ID for a logical VC without an ID field."""
        for partner in inventory:  # Walk candidate partner rows.
            if not isinstance(partner, dict):  # Skip malformed partner rows.
                continue  # Keep only mapping rows.
            partner_id = str(partner.get("id") or "").strip()  # Read partner device ID.
            if not partner_id:  # A partner needs an ID.
                continue  # Try the next partner.
            partner_vc = str(partner.get("vc_mac") or "").lower()  # Read partner VC MAC.
            partner_mac = str(partner.get("mac") or "").lower()  # Read partner physical MAC.
            if partner_vc == vc_mac.lower() or partner_mac == vc_mac.lower():  # Match the VC identity.
                return partner_id  # Use the matching partner ID.
        return ""  # No partner carries a usable ID.

    @staticmethod
    def _vc_device_id(
        record: dict[str, Any],
        inventory: list[dict[str, Any]],
        vc_mac: str,
    ) -> str:
        """Resolve the device ID needed by getSiteDeviceVirtualChassis."""
        device_id = str(record.get("id") or record.get("device_id") or "").strip()  # Read direct ID fields.
        if device_id:  # The inventory row carries the needed ID.
            return device_id  # Use the direct ID.
        return SubscriptionExpiryClient._partner_device_id(record, inventory, vc_mac)  # Find a partner ID.

    @staticmethod
    def _logical_vc_context(
        record: dict[str, Any],
        inventory: list[dict[str, Any]],
    ) -> tuple[str, str, str] | None:
        """Return site, device, and VC MAC values for one logical VC row."""
        if not isinstance(record, dict):  # Skip malformed records.
            return None  # Keep no VC context.
        if not SubscriptionExpiryClient._is_switch_record(record):  # Only switches have this VC status endpoint.
            return None  # Keep AP and gateway inventory unchanged.
        site_id = str(record.get("site_id") or "").strip()  # Read the required site path field.
        if not site_id:  # A VC status call needs a site.
            return None  # Keep the row without expansion.
        mac = str(record.get("mac") or "").strip()  # Read the logical or physical MAC.
        vc_mac = str(record.get("vc_mac") or "").strip()  # Read the VC parent MAC.
        if not SubscriptionExpiryClient._is_logical_vc_candidate(
            record
        ):  # Real member rows use vc_mac but are not the logical parent.
            return None  # Keep physical member rows unchanged.
        device_id = SubscriptionExpiryClient._vc_device_id(
            record, inventory, vc_mac
        )  # Resolve the inventory device ID.
        if not device_id:  # A VC status call needs the device ID.
            return None  # Keep the logical row without expansion.
        vc_parent = vc_mac or mac  # Preserve the VC parent MAC.
        return site_id, device_id, vc_parent  # Return one VC call context.

    def _fetch_virtual_chassis_members(
        self,
        org_id: str,
        site_id: str,
        device_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch physical VC member records through the existing Mist status endpoint."""
        logger.info(
            "Fetching Virtual Chassis members for organization %s at site %s",
            org_id,
            site_id,
        )  # Log before the read-only VC status call.
        response = self._request_with_retry(
            "getSiteDeviceVirtualChassis",
            f"{org_id}/{site_id}/{device_id}",
            lambda: mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(
                self.apisession,
                site_id,
                device_id,
            ),
        )  # Call the proven menu 17 and 63 endpoint.
        status_code = getattr(response, "status_code", None)  # Read VC status.
        if status_code != 200:  # A failed member status call is not physical evidence.
            logger.warning(
                "Virtual Chassis status returned HTTP %s for site %s device %s",
                status_code,
                site_id,
                device_id,
            )  # Surface the status without fabricating members.
            return []  # Leave the logical inventory row for model filtering.
        payload = self._response_payload(response)  # Normalize the SDK wrapper.
        if not isinstance(payload, dict):  # The VC status contract uses an object.
            logger.warning(
                "Virtual Chassis status returned an invalid result object for site %s device %s",
                site_id,
                device_id,
            )  # Surface invalid shape.
            return []  # Leave the logical inventory row for model filtering.
        members = payload.get("members")  # Read the physical member list.
        if not isinstance(members, list):  # No member evidence exists.
            logger.debug(
                "Virtual Chassis status has no member list for site %s device %s",
                site_id,
                device_id,
            )  # Explain the no-member outcome.
            return []  # Leave the logical inventory row for model filtering.
        normalized = [member for member in members if isinstance(member, dict)]  # Keep only mapping member records.
        logger.debug(
            "Fetched %d physical Virtual Chassis members for site %s device %s",
            len(normalized),
            site_id,
            device_id,
        )  # Log physical member count.
        return normalized  # Return one physical member record per VC member.

    @staticmethod
    def _member_value(
        member: dict[str, Any],
        keys: tuple[str, ...],
        fallback: Any = MISSING_VALUE,
    ) -> Any:
        """Return the first present VC member value."""
        for key in keys:  # Check each source field in priority order.
            value = member.get(key)  # Read one member field.
            if value not in (None, ""):  # A visible value is usable.
                return value  # Return the first usable value.
        return fallback  # Preserve Missing or a parent fallback.

    @staticmethod
    def _physical_vc_member_record(
        logical_record: dict[str, Any],
        vc_payload_mac: str,
        member: dict[str, Any],
    ) -> dict[str, Any]:
        """Build one physical inventory record from a VC status member."""
        record = dict(logical_record)  # Copy parent organization and site context.
        record.pop("members", None)  # Remove the nested source list before output.
        serial = SubscriptionExpiryClient._member_value(member, ("serial", "chassis_serial"))  # Read serial.
        mac = SubscriptionExpiryClient._member_value(member, ("mac", "chassis_mac"))  # Read MAC.
        model = SubscriptionExpiryClient._member_value(
            member,
            ("model", "chassis_model"),
            record.get("model") or MISSING_VALUE,
        )  # Read model.
        record["serial"] = serial  # Preserve Missing instead of synthetic.
        record["mac"] = mac  # Preserve the physical MAC.
        record["model"] = model  # Preserve the physical model.
        record["name"] = SubscriptionExpiryClient._member_value(
            member,
            ("name",),
            record.get("name") or MISSING_VALUE,
        )  # Preserve member name.
        record["vc_mac"] = vc_payload_mac or MISSING_VALUE  # Preserve the logical VC MAC.
        record["chassis_serial"] = serial or MISSING_VALUE  # Preserve explicit chassis serial.
        record["chassis_mac"] = mac or MISSING_VALUE  # Preserve explicit chassis MAC.
        record["chassis_model"] = model or MISSING_VALUE  # Preserve explicit chassis model.
        record["vc_role"] = member.get("vc_role")  # Preserve member role when the source provides it.
        record["fpc_idx"] = member.get("fpc_idx")  # Preserve member FPC index.
        return record  # Return one physical member identity.

    @staticmethod
    def _physical_vc_records(
        logical_record: dict[str, Any],
        vc_payload_mac: str,
        members: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build physical inventory records from a VC status member list."""
        parent_mac = (
            vc_payload_mac or str(logical_record.get("vc_mac") or logical_record.get("mac") or "").strip()
        )  # Preserve the VC parent MAC.
        return [
            SubscriptionExpiryClient._physical_vc_member_record(
                logical_record,
                parent_mac,
                member,
            )
            for member in members
        ]  # Return one verified physical member record per member.

    def _expand_virtual_chassis_members(
        self,
        org_id: str,
        inventory: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Expand logical switch VC rows into physical member inventory rows."""
        expanded: list[dict[str, Any]] = []  # Accumulate inventory and physical member rows.
        seen_vc: set[tuple[str, str, str]] = set()  # Read one logical VC once.
        for record in inventory:  # Walk every paginated inventory record.
            context = self._logical_vc_context(record, inventory)  # Resolve VC call context.
            if context is None:  # Standalone or physical member row.
                expanded.append(record)  # Preserve it unchanged.
                continue  # Continue without a VC status call.
            site_id, device_id, vc_mac = context  # Unpack one logical VC context.
            key = (site_id, device_id, vc_mac)  # Build the duplicate key.
            if key in seen_vc:  # Another record represents the same logical VC.
                continue  # Avoid duplicate status calls and member rows.
            seen_vc.add(key)  # Remember this logical VC.
            members = self._fetch_virtual_chassis_members(org_id, site_id, device_id)  # Fetch physical members.
            if not members:  # The status call failed or found no members.
                expanded.append(record)  # Preserve the source row for visible fallback and model filtering.
                continue  # Continue without physical evidence.
            vc_payload_mac = str(record.get("vc_mac") or record.get("mac") or vc_mac).strip()  # Resolve parent MAC.
            expanded.extend(
                self._physical_vc_records(record, vc_payload_mac, members)
            )  # Add one record per physical member.
        logger.debug(
            "Expanded %d inventory rows to %d inventory and VC member rows",
            len(inventory),
            len(expanded),
        )  # Log expansion counts.
        return expanded  # Return inventory evidence for the model classifier.

    @staticmethod
    def _list_payload(payload: Any) -> list[dict[str, Any]]:
        """Normalize a payload into a list of dictionaries."""
        if isinstance(payload, list):  # The usage endpoint normally returns a list.
            return [row for row in payload if isinstance(row, dict)]  # Keep only mapping rows.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):  # Search payloads can nest rows.
            return [row for row in payload["results"] if isinstance(row, dict)]  # Keep only mapping rows.
        if isinstance(payload, dict):  # A singleton mapping can still be normalized.
            return [payload]  # Preserve the one mapping row.
        return []  # Unsupported payloads produce no source rows.

    @staticmethod
    def _license_summary_from_payload(payload: Any) -> LicenseSummarySource:
        """Build a license summary source from a plain payload."""
        source = payload if isinstance(payload, dict) else {}  # Guard against malformed SDK payloads.
        entitled = source.get("entitled") if isinstance(source.get("entitled"), dict) else {}  # Normalize map.
        licenses = source.get("licenses") if isinstance(source.get("licenses"), list) else []  # Normalize list.
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}  # Normalize map.
        return LicenseSummarySource(
            dict(entitled), [row for row in licenses if isinstance(row, dict)], dict(summary)
        )  # Build dataclass.

    @staticmethod
    def _license_usage_from_payload(row: dict[str, Any]) -> LicenseUsageSource:
        """Build a license usage source from one plain row."""
        usages = row.get("usages") if isinstance(row.get("usages"), dict) else {}  # Normalize usage map.
        loaded = row.get("fully_loaded") if isinstance(row.get("fully_loaded"), dict) else {}  # Normalize map.
        return LicenseUsageSource(row.get("site_id"), row.get("num_devices"), dict(usages), dict(loaded))  # Build row.

    @staticmethod
    def _jsi_contract_from_payload(row: dict[str, Any]) -> JsiContractSource:
        """Build a JSI contract source from one plain row."""
        return JsiContractSource(
            serial=row.get("serial"),  # Preserve device serial when available.
            model=row.get("model"),  # Preserve device model when available.
            status=row.get("status"),  # Preserve contract status when the API sends it.
            end_date=row.get("end_date"),  # Preserve contract end date when the API sends it.
            sku=row.get("sku"),  # Preserve SKU for future tie-breaks.
            type=row.get("type"),  # Preserve source type for future diagnostics.
            warranty_type=row.get("warranty_type"),  # Preserve Mist contract status.
            eol_time=row.get("eol_time"),  # Preserve end-of-life date source.
            eos_time=row.get("eos_time"),  # Preserve end-of-support date source.
            has_support=row.get("has_support"),  # Preserve live JSI support evidence.
            claimed=row.get("claimed"),  # Preserve live JSI claim evidence.
            device_name=row.get("device_name"),  # Preserve live JSI device name.
            org_id=row.get("org_id"),  # Preserve live JSI organization.
            master=row.get("master"),  # Preserve live JSI master evidence.
        )

    @staticmethod
    def _raise_for_jsi_error(response: Any) -> None:
        """Raise a clear exception for the expected no-linked-account response."""
        status_code = getattr(response, "status_code", None)  # Read SDK status without requiring SDK class types.
        if status_code == 0:  # Transport failures use the bounded sentinel.
            logger.error("The JSI contract search returned no transport status")  # Name the transport failure.
            raise SubscriptionExpiryClientError(
                "The JSI contract search returned no transport status."
            )  # Surface status.
        if status_code is None:  # Plain SDK test doubles omit status.
            if isinstance(response, dict):  # Plain test payloads have no status wrapper.
                return  # Accept the plain payload in test and direct-container use.
            if hasattr(response, "data"):  # SDK-like test doubles can omit status but hold data.
                return  # Accept a plain SDK wrapper that omits status.
            logger.error("The JSI contract search returned no HTTP status")  # Name the failure.
            raise SubscriptionExpiryClientError("The JSI contract search returned no HTTP status.")  # Surface status.
        if status_code < HTTP_BAD_REQUEST:  # Successful SDK responses need no conversion.
            return  # Leave successful and plain test responses alone.
        if status_code == HTTP_BAD_REQUEST:  # Mist returns 400 when no Juniper account is linked.
            logger.warning("The JSI account is not linked for the selected organization")  # Explain the condition.
            raise JsiAccountNotLinkedError("No linked Juniper account is available for JSI contracts.")  # Signal path.
        logger.error("The JSI contract search failed with HTTP %s", status_code)  # Surface unexpected HTTP errors.
        raise SubscriptionExpiryClientError(  # Stop before pagination can hide a failed API response.
            f"The JSI contract search failed with HTTP {status_code}."
        )
