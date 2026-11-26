"""Scope checks SMK-08 to SMK-10: the site scope, the filters and limits, and the inventory and webhooks.

Why: the checks prove that the token reads one site.
The checks also prove that the device filters return only the filter types.
The checks also prove that the page-size probe is observed.
The checks also prove that the inventory and webhook endpoints answer.
Each request is a GET, and each probe records an observation without lowering the status.
"""

from __future__ import annotations  # Postpone annotation evaluation.

from collections.abc import Sequence  # Type the attempt lists and the part lists.
from dataclasses import replace  # Copy the result with the names of the fields that the check confirmed.
from typing import Any, ClassVar  # Type the JSON values and the class constants.

import structlog  # Structured logging of each request and each probe.

from scripts.netcool_runbook_smoke.checks import (  # Import the run context and the result types of the checks.
    CheckContext,
    CheckResult,
    CheckStatus,
)
from scripts.netcool_runbook_smoke.client import CallRecord  # Import the attempt record that the checks read.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class FilterProbes:  # Hold probe answers, which never lower the check status.
    """Read the answers of the filter and page-size probes of SMK-09, one response at a time.

    Why: a probe observes how the service treats a request. It never lowers the status of SMK-09, so a probe cannot
    turn a passing filter into a failure. The answers are kept as observations for the operator.
    """

    def limit_outcome(  # Separate four page-size outcomes that the contract names.
        self,
        status: int | None,
        echoed: int | None,
        received: int,
        has_next: bool,
        requested: int,
    ) -> str:
        """Return the outcome word of the page-size probe.

        Why: the contract separates an accepted limit, a reduced limit, a rejected limit, and an unobserved answer.

        Args:
            status: HTTP status of the probe, or None when no response exists.
            echoed: Limit that the service echoed, or None when it echoed none.
            received: Number of records in the probe page.
            has_next: True when the probe page carries a next link.
            requested: Limit that the probe asked for.

        Returns:
            The outcome word: accepted, reduced, rejected, or not_observed.
        """
        if status in (400, 422):  # The service refused the page size.
            return "rejected"  # Report rejected when the service refuses the page size.
        if status != 200:  # Any other status is recorded with its code, not judged.
            return "not_observed"  # Report not_observed when the status is not HTTP 200.
        if echoed == requested:  # The service used the requested page size.
            return "accepted"  # Report accepted when the service uses the page size asked.
        if (echoed is not None and echoed < requested) or (has_next and received < requested):  # A smaller page.
            return "reduced"  # Report reduced when the service gives a smaller page size.
        return "not_observed"  # The page size could not be read from this response.

    def device_types(  # Show which event types each device type filter returned.
        self, attempt: CallRecord
    ) -> list[str]:
        """Return the distinct device event types of one page, in sorted order.

        Why: the observation of the device type filters lists the event types that each filter returned.

        Args:
            attempt: Final attempt of the device event request.

        Returns:
            The sorted distinct type values. Empty when the page has no records.
        """
        body = attempt.data if isinstance(attempt.data, dict) else {}  # The body must be an object.
        rows = body.get("results")  # Records of the page, as the response holds them.
        results: list[Any] = rows if isinstance(rows, list) else []  # An unreadable page has no records.
        types = {  # Keep only string types, so malformed records add no type.
            str(item["type"]) for item in results if isinstance(item, dict) and isinstance(item.get("type"), str)
        }
        return sorted(types)  # Distinct types in a stable order.

    def window(  # Read the echoed window, which the q2 probes compare.
        self, attempt: CallRecord
    ) -> dict[str, int | None]:
        """Return the start and end of a Mist Edge response as integers, or null.

        Why: the two probes of observation q2 compare the echoed window with the requested one.

        Args:
            attempt: Final attempt of the Mist Edge request.

        Returns:
            The start and end values, each an integer or None.
        """
        body = attempt.data if isinstance(attempt.data, dict) else {}  # The body must be an object.
        values: dict[str, int | None] = {}  # The two echoed values.
        for name in ("start", "end"):  # Read each echoed value in turn.
            value = body.get(name)  # The echoed epoch value.
            if isinstance(value, bool) or not isinstance(value, (int, float)):  # A boolean or text is not a time.
                values[name] = None  # The answer stays null.
            else:  # A number is an epoch value, kept as integer seconds.
                values[name] = int(value)  # Integer seconds.
        return values  # Return both values, None when a value is not a number.

    def filter_verdict(  # Let only the type filter request decide the check status.
        self, keys: Sequence[str], attempt: CallRecord
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of request 1, which alone decides the status of SMK-09.

        Why: the type filter is the proof. Its records must hold only the filter types, and an empty page proves little.

        Args:
            keys: The filter types of request 1.
            attempt: Final attempt of request 1.

        Returns:
            The status and the text of the type filter.
        """
        body = attempt.data if isinstance(attempt.data, dict) else {}  # The body must be an object.
        results = body.get("results")  # Records of the filtered page.
        if attempt.status_code != 200 or not isinstance(results, list):  # The proof needs HTTP 200 and records.
            return (  # Report FAIL when the filter lacks HTTP 200 or a list.
                CheckStatus.FAIL,
                "the type filter request did not return HTTP 200 with a results list.",
            )
        if not results:  # Zero records do not prove that the filter works.
            return (  # Report WARN on zero records, which do not prove the filter.
                CheckStatus.WARN,
                "zero records, so the type filter is not proven.",
            )
        types = {str(item.get("type")) for item in results if isinstance(item, dict)}  # Types of the records.
        outside = sorted(value for value in types if value not in keys)  # Types that the filter must not return.
        if outside:  # The filter returned a type outside its list.
            return (  # Report FAIL when a record has a type outside the filter.
                CheckStatus.FAIL,
                f"the type filter returned a type outside the filter: {outside[0]}.",
            )
        return (  # Report PASS when every record type is a filter type.
            CheckStatus.PASS,
            "type filter returned only the filter types, limit 1000 gave HTTP 200.",
        )

    def record(  # Store answers of the six requests as run observations.
        self, observations: dict[str, Any], attempts: Sequence[CallRecord]
    ) -> None:
        """Store the answers of the probes in the observations of the run.

        Why: q3, the device type observations, and the two Mist Edge windows come from the six requests of SMK-09.

        Args:
            observations: Observations of the run, updated in place.
            attempts: Final attempts of the six requests, in request order.
        """
        probe = attempts[1]  # Request 2 is the page-size probe.
        body = probe.data if isinstance(probe.data, dict) else {}  # The probe body must be an object.
        echoed = body.get("limit") if isinstance(body.get("limit"), int) else None  # The limit that the service used.
        rows = body.get("results")  # The records of the probe page.
        received = len(rows) if isinstance(rows, list) else 0  # The number of records on the probe page.
        outcome = self.limit_outcome(  # Classify the 5000 page-size probe response for q3.
            probe.status_code, echoed, received, body.get("next") is not None, 5000
        )
        observations["q3_limit_5000"] = {  # The three values of q3.
            "outcome": outcome,
            "status_code": probe.status_code,
            "page_limit": echoed,
        }
        observations["device_event_types_by_device_type"] = {  # Requests 3 and 4 are the device type filters.
            "switch": self.device_types(attempts[2]),
            "gateway": self.device_types(attempts[3]),
        }
        observations["q2_mist_edge_window"] = {  # Requests 5 and 6 are the two Mist Edge windows.
            "echoes_start_end": (observations.get("q2_mist_edge_window") or {}).get("echoes_start_end"),
            "with_duration_1h": self.window(attempts[4]),
            "without_time_parameter": self.window(attempts[5]),
        }


class ScopeChecks:  # Hold the site scope and device filter checks as one unit.
    """Run SMK-08 and SMK-09: the scope of one site, and the filters and limits of the device event searches.

    Why: the site scope proves that the token reads the site.
    The filter checks prove that each device type filter returns only its own types.
    Both use read-only GET requests.
    """

    SITE_SEARCHES: ClassVar[tuple[tuple[str, str], ...]] = (  # Family label and site search path, in order.
        ("alarms", "/api/v1/sites/{site_id}/alarms/search"),
        ("device events", "/api/v1/sites/{site_id}/devices/events/search"),
        ("Mist Edge events", "/api/v1/sites/{site_id}/mxedges/events/search"),
        ("system events", "/api/v1/sites/{site_id}/events/system/search"),
    )
    DEVICE_PATH: ClassVar[str] = "/api/v1/orgs/{org_id}/devices/events/search"  # Organization device event search.
    MXEDGE_PATH: ClassVar[str] = "/api/v1/orgs/{org_id}/mxedges/events/search"  # Organization Mist Edge event search.

    def __init__(self, context: CheckContext) -> None:  # Share one run context for requests and observations.
        """Keep the run context that the checks share.

        Args:
            context: Run state of the smoke test.
        """
        self._context: CheckContext = context  # Run state that receives the requests and observations.

    def smk_08(self) -> CheckResult:  # Prove the token reads site events, not organization views.
        """Read one page of each site search for the run site, or for the first site of the organization.

        Why: a site search proves that the token reads the site's events, not only the organization view.

        Returns:
            The roll-up result of SMK-08, or SKIP when the organization has no site.
        """
        org = {"org_id": self._context.settings.org_id}  # Path value of the organization.
        calls: list[CallRecord] = []  # Every attempt of this check.
        site_id: str | None = self._context.settings.site_id  # The site that the operator named, or None.
        if site_id is None:  # Without --site-id, the first site of the organization is read.
            listing = self._context.get("/api/v1/orgs/{org_id}/sites", org, {})  # One site list request.
            calls.extend(listing)  # Keep the attempt for the request counts.
            site_id, status, text = SiteListing().first_site(listing[-1])  # The first site, or the stop cause.
            if site_id is None:  # No site can be searched, so the check ends with the listed cause.
                return CheckResult.from_calls(  # End SMK-08 when no site identifier exists to search.
                    "SMK-08", status, text, calls
                )
        parts: list[tuple[CheckStatus, str]] = []  # One status and text for each site search.
        for label, path in self.SITE_SEARCHES:  # Four site searches in the contract order.
            part_status, part_text, attempts = self._site_part(label, path, site_id)  # One page of the site search.
            calls.extend(attempts)  # Keep every attempt for the request counts.
            parts.append((part_status, part_text))  # Keep the part for the roll-up.
        status = CheckStatus.most_severe([part for part, _ in parts])  # Roll-up of the four searches.
        if status is CheckStatus.PASS:  # Every search returned HTTP 200 with records.
            text = "4 site searches returned HTTP 200 for site-1."  # The contract summary.
        else:  # A warning or failure names its family, so its text is used.
            text = next(part_text for part, part_text in parts if part is status)  # First text with the status.
        return CheckResult.from_calls(  # Report the overall status of the four site searches.
            "SMK-08", status, text, calls
        )

    def smk_09(self) -> CheckResult:  # Prove the type filter and store the other probe answers.
        """Send the six filter and page-size requests, judge request 1, and record the probes.

        Why: request 1 proves that the type filter returns only its types. The other requests observe the page-size
        behavior and the device type filters, and they never lower the status.

        Returns:
            The result of SMK-09. SKIP when the device event catalog holds no key.

        Raises:
            StopRun: A request ends the run (exit code 2, 3, or 4).
        """
        keys = self._device_keys()  # The first two device event keys of the catalog, from SMK-05.
        if not keys:  # Without a key, the type filter cannot be built.
            return CheckResult.skipped(  # Skip SMK-09 when the catalog gives no key for the filter.
                "SMK-09", "device event catalog holds no key"
            )
        org = {"org_id": self._context.settings.org_id}  # Path value of the organization.
        window = dict(self._context.window_query)  # Collection window of the device event requests.
        requests = [  # Six single-page requests, in the contract order.
            (self.DEVICE_PATH, {**window, "type": ",".join(keys)}),
            (self.DEVICE_PATH, {**window, "limit": "5000"}),
            (self.DEVICE_PATH, {**window, "device_type": "switch"}),
            (self.DEVICE_PATH, {**window, "device_type": "gateway"}),
            (self.MXEDGE_PATH, {"duration": "1h"}),
            (self.MXEDGE_PATH, {}),
        ]
        groups = [self._context.get(path, org, query) for path, query in requests]  # Each request reads one page.
        attempts = [group[-1] for group in groups]  # The final attempt of each request, in order.
        probes = FilterProbes()  # Reads the answers of the probes.
        status, text = probes.filter_verdict(keys, attempts[0])  # Request 1 alone decides the status.
        probes.record(self._context.observations, attempts)  # Store the answers of requests 2 to 6.
        calls = [call for group in groups for call in group]  # Every attempt, for the request counts.
        return CheckResult.from_calls(  # Report the status from request 1, which alone decides it.
            "SMK-09", status, text, calls
        )

    def _site_part(  # Judge one site search, so each family has its own status.
        self, label: str, path: str, site_id: str
    ) -> tuple[CheckStatus, str, tuple[CallRecord, ...]]:
        """Read one page of one site search, and judge it.

        Why: each site search is a part of SMK-08, and a zero-record page is a warning, as in SMK-06.

        Args:
            label: Name of the family in the output.
            path: Site search path with the site placeholder.
            site_id: Identifier of the site, which the client encodes as one path segment.

        Returns:
            The status, the text, and every attempt of the request.
        """
        attempts = self._context.get(path, {"site_id": site_id}, dict(self._context.window_query))  # One page.
        final = attempts[-1]  # The final attempt decides the part.
        body = final.data if isinstance(final.data, dict) else {}  # The body must be an object.
        results = body.get("results")  # Records of the page.
        if final.error_class is not None or final.status_code != 200 or not isinstance(results, list):  # Not readable.
            return (  # Report FAIL when the search is not HTTP 200 with a list.
                CheckStatus.FAIL,
                f"{label} site search did not return a results list.",
                attempts,
            )
        if not results:  # Zero records do not prove that no event exists.
            return (  # Report WARN on zero records, which do not prove absence.
                CheckStatus.WARN,
                f"zero records for {label} in the site-1 collection window.",
                attempts,
            )
        return (  # Report PASS when the search returns HTTP 200 with records.
            CheckStatus.PASS,
            f"{label} returned HTTP 200 for site-1.",
            attempts,
        )

    def _device_keys(self) -> list[str]:  # Use live catalog keys, so the filter stays current.
        """Return the first two keys of the device event catalog, in catalog order.

        Why: the device type filter of request 1 uses two keys of the live catalog, so the filter stays current.

        Returns:
            Up to two catalog keys. Empty when the catalog holds none.
        """
        items = self._context.catalogs.get("device_events", {}).get("items", [])  # Catalog items from SMK-05.
        keys = [  # Keep string keys only, so malformed catalog items add none.
            item["key"] for item in items if isinstance(item, dict) and isinstance(item.get("key"), str)
        ]  # All keys.
        return keys[:2]  # The filter takes the first two keys.


class SiteListing:  # Pick the first listed site, since SMK-08 needs one site.
    """Read the first site of the organization list, for a run that gave no --site-id.

    Why: SMK-08 needs one site, and the shape of the list decides whether the check can run at all. The list must be
    an array whose first site carries an identifier.
    """

    def first_site(  # Give each site list outcome its own status and cause text.
        self, final: CallRecord
    ) -> tuple[str | None, CheckStatus, str]:
        """Return the identifier of the first site, or the status and the cause that end SMK-08.

        Why: each cause has its own status, so the check reports an unreadable list as a failure and an empty list as
        a skip.

        Args:
            final: Final attempt of the site list request.

        Returns:
            The site identifier when one exists. Otherwise None, the status, and the cause text.
        """
        sites = final.data  # The site list is a top-level array.
        if final.error_class is not None or not isinstance(sites, list):  # The list must be an array.
            return (  # Report FAIL when the site list has an error or no array.
                None,
                CheckStatus.FAIL,
                "the site list is not a JSON array.",
            )
        if not sites:  # An organization with no site has no site scope to check.
            return (  # Skip SMK-08 when the organization has no site to check.
                None,
                CheckStatus.SKIP,
                "no site in organization",
            )
        first = sites[0] if isinstance(sites[0], dict) else {}  # The first site of the list.
        site_id = str(first.get("id", ""))  # The identifier of the first site.
        if not site_id:  # A site without an identifier cannot be searched.
            return (  # Report FAIL when the first site has no identifier.
                None,
                CheckStatus.FAIL,
                "the first site has no identifier.",
            )
        return (  # Return the identifier, since the site searches need one.
            site_id,
            CheckStatus.PASS,
            "the first site of the organization",
        )


class InventoryReader:  # Hold each response shape rule in one place for SMK-10.
    """Read the top-level arrays and the inventory buckets of the SMK-10 requests.

    Why: each endpoint has one response shape.
    The reader holds those shapes in one place.
    The check therefore reads each response the same way.
    The check never keeps a webhook URL, a name, or a secret.
    """

    def items(  # Read top-level arrays, so an object or error is not a list.
        self, final: CallRecord
    ) -> list[Any] | None:
        """Return the items of a top-level array response, or None when the response is not an array.

        Why: the list endpoints return a top-level array, and an object or an error is not a readable list.

        Args:
            final: Final attempt of a list request.

        Returns:
            A copy of the items, or None.
        """
        if final.status_code != 200 or not isinstance(final.data, list):  # The contract needs HTTP 200 and an array.
            return None  # Return None unless the response is HTTP 200 with an array.
        return list(final.data)  # A copy, so the caller cannot change the response.

    def count_sum(self, final: CallRecord) -> int | None:  # Sum the buckets, since a device count is their total.
        """Return the sum of the count values of an inventory count, or None when the body is not readable.

        Why: the device count of a type is the sum of its buckets, and a body without a results list is a failure.

        Args:
            final: Final attempt of an inventory count request.

        Returns:
            The sum of the count values, or None.
        """
        body = final.data if isinstance(final.data, dict) else {}  # The body must be an object.
        results = body.get("results")  # The buckets of the count.
        if final.status_code != 200 or not isinstance(results, list):  # A count needs HTTP 200 and buckets.
            return None  # Return None when the count is not HTTP 200 with buckets.
        total = 0  # The running sum of the buckets.
        for item in results:  # Each bucket of the count.
            if isinstance(item, dict) and isinstance(item.get("count"), int):  # Only integer counts are summed.
                total += item["count"]  # Add the bucket to the device count.
        return total  # Return the total, where non-integer buckets add nothing.

    def list_part(  # Turn one list into a status and text, with its empty rule.
        self,
        items: list[Any] | None,
        label: str,
        empty: CheckStatus,
        empty_text: str,
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of one list request.

        Why: a list that cannot be read fails, an empty list has the status of the contract, and a readable list
        reports its count.

        Args:
            items: Items of the list, or None when the response is not a top-level array.
            label: Name of the items in the output.
            empty: Status of an empty list.
            empty_text: Text of an empty list.

        Returns:
            The status and the text of the request.
        """
        if items is None:  # The response is not an array, so the request failed.
            return (  # Report FAIL when the response is not a JSON array.
                CheckStatus.FAIL,
                f"{label} response is not a JSON array.",
            )
        if not items:  # An empty array has the status that the contract names.
            return empty, empty_text  # Report the contract status when the list has no item.
        return CheckStatus.PASS, f"{label} {len(items)}."  # Report PASS with the item count of a readable list.

    def webhook_part(  # Give topics and enabled counts, never the URL or secret.
        self, webhooks: list[Any] | None
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of the webhook list, with its topics and enabled counts.

        Why: the operator needs the topics and the enabled state. The URL, the name, and the secret are never read.

        Args:
            webhooks: Items of the webhook list, or None when the response is not an array.

        Returns:
            The status and the text of the webhook request.
        """
        if webhooks is None:  # The response is not an array, so the request failed.
            return (  # Report FAIL when the webhook response is not a JSON array.
                CheckStatus.FAIL,
                "webhook response is not a JSON array.",
            )
        if not webhooks:  # An organization may have no webhook.
            return CheckStatus.INFO, "no webhooks."  # Report INFO when the organization has no webhook.
        items = [item for item in webhooks if isinstance(item, dict)]  # Only objects hold the fields.
        topics = sorted(  # Collect each string topic once, in a stable order.
            {str(topic) for item in items for topic in item.get("topics", []) if isinstance(topic, str)}
        )
        enabled = sum(  # Count enabled webhooks, where a missing flag means enabled.
            1 for item in items if item.get("enabled", True) is True
        )  # Missing means enabled, as the file says.
        text = (  # Build the webhook summary with counts, topics, and states.
            f"webhooks {len(items)}, topics {', '.join(topics)}, enabled {enabled}, "
            f"disabled {len(items) - enabled}."
        )
        return CheckStatus.PASS, text  # Report PASS when the webhook response is a non-empty array.

    def last_trouble(  # Answer q6, which asks if AP statistics carry last_trouble.
        self, stats: list[Any] | None
    ) -> bool | None:
        """Return the answer to question q6 from the AP statistics items.

        Why: q6 asks whether the AP statistics carry the last_trouble field. The answer is null when no item exists.

        Args:
            stats: Items of the AP statistics list, or None when the response is not an array.

        Returns:
            True when an item carries the field, False when items exist and none does, or None.
        """
        items = [item for item in stats or [] if isinstance(item, dict)]  # Only objects can carry the field.
        if not items:  # Without an item, the field was not observed.
            return None  # Return None when the list has no object item to read.
        return any("last_trouble" in item for item in items)  # True when at least one item carries it.


class InventoryChecks:  # Prove the SMK-10 endpoints answer with the contract shape.
    """Run SMK-10: the inventory counts, the Mist Edge list, the AP statistics, and the webhook list.

    Why: each endpoint must answer with its contract shape.
    The counts prove the device inventory.
    The lists prove the Mist Edge and webhook setup.
    The statistics show whether the AP records carry the last_trouble field.
    """

    DEVICE_TYPES: ClassVar[tuple[str, ...]] = ("ap", "switch", "gateway")  # Device types of the inventory counts.

    def __init__(self, context: CheckContext) -> None:  # Share one run context for requests and observations.
        """Keep the run context that the check shares.

        Args:
            context: Run state of the smoke test.
        """
        self._context: CheckContext = context  # Run state that receives the requests and observations.

    def smk_10(self) -> CheckResult:  # Prove each request answers with its contract shape.
        """Send the six inventory, list, and statistics requests, and judge each one.

        Why: each request must return HTTP 200 with its contract shape, so one fault cannot pass as a zero count.

        Returns:
            The roll-up result of SMK-10.

        Raises:
            StopRun: A request ends the run (exit code 2, 3, or 4).
        """
        org = {"org_id": self._context.settings.org_id}  # Path value of the organization.
        window = dict(self._context.window_query)  # Collection window of the AP statistics request.
        requests = [  # Six requests, in the contract order.
            ("/api/v1/orgs/{org_id}/inventory/count", {"type": "ap", "distinct": "model"}),
            ("/api/v1/orgs/{org_id}/inventory/count", {"type": "switch", "distinct": "model"}),
            ("/api/v1/orgs/{org_id}/inventory/count", {"type": "gateway", "distinct": "model"}),
            ("/api/v1/orgs/{org_id}/mxedges", {}),
            ("/api/v1/orgs/{org_id}/stats/devices", {**window, "type": "ap"}),
            ("/api/v1/orgs/{org_id}/webhooks", {}),
        ]
        groups = [self._context.get(path, org, query) for path, query in requests]  # One page for each request.
        finals = [group[-1] for group in groups]  # The final attempt of each request.
        parts = self._judge(finals)  # Status and text of each request.
        ok_count = sum(1 for final in finals if final.status_code == 200 and final.error_class is None)  # HTTP 200.
        status = CheckStatus.most_severe([part for part, _ in parts])  # Roll-up of the six requests.
        text = f"{ok_count} calls returned HTTP 200. " + "; ".join(part_text for _, part_text in parts)  # Summary.
        calls = [call for group in groups for call in group]  # Every attempt, for the request counts.
        result = CheckResult.from_calls("SMK-10", status, text, calls)  # The result with the request facts.
        return replace(result, field_names=self._field_names(finals))  # Confirmed field names, never values.

    def _judge(  # Apply the rule of each request, so no fault passes as zero.
        self, finals: Sequence[CallRecord]
    ) -> list[tuple[CheckStatus, str]]:
        """Return the status and the text of each of the six requests, and store the q6 answer.

        Why: each request has its own rule. A count sums its buckets, a list needs items, and an empty list is a
        warning or an information note as the contract says.

        Args:
            finals: Final attempt of each request, in request order.

        Returns:
            One status and text for each request, in request order.
        """
        reader = InventoryReader()  # Reads each response with its contract shape.
        parts: list[tuple[CheckStatus, str]] = []  # One part for each request.
        for device_type, final in zip(self.DEVICE_TYPES, finals[:3], strict=True):  # The three inventory counts.
            total = reader.count_sum(final)  # Sum of the count buckets, or None when the body is not readable.
            if total is None:  # The count is not a results list, so its request failed.
                parts.append(  # Report FAIL when the count has no readable results list.
                    (CheckStatus.FAIL, f"{device_type} inventory count is not a results list.")
                )
            else:  # The sum of the buckets is the device count of the type.
                parts.append(  # Report PASS with the device total of this device type.
                    (CheckStatus.PASS, f"{device_type} devices {total}.")
                )
        mxedges = reader.items(finals[3])  # Top-level array of Mist Edge items.
        parts.append(  # Judge Mist Edge items, with INFO when the list is empty.
            reader.list_part(mxedges, "Mist Edge items", CheckStatus.INFO, "no Mist Edge items.")
        )
        stats = reader.items(finals[4])  # Top-level array of AP statistics items.
        self._context.observations["q6_last_trouble_present"] = reader.last_trouble(stats)  # The q6 answer.
        parts.append(  # Judge AP statistics, with WARN when the list is empty.
            reader.list_part(stats, "AP statistics items", CheckStatus.WARN, "no AP statistics items.")
        )
        parts.append(reader.webhook_part(reader.items(finals[5])))  # Count, topics, and enabled state.
        return parts  # Return one part for each request, in the contract order.

    def _rows(self, final: CallRecord) -> list[Any]:  # Read array items only, so an error adds no field name.
        """Return the items of a top-level array, or an empty list when the response is not an array.

        Why: the field names come only from readable arrays, so an error response adds no name to the record.

        Args:
            final: Final attempt of a list request.

        Returns:
            The items of the array, or an empty list.
        """
        return InventoryReader().items(final) or []  # An unreadable response has no items.

    def _field_names(  # List field names only, so the operator sees each shape.
        self, finals: Sequence[CallRecord]
    ) -> tuple[str, ...]:
        """Return the sorted names of the response fields that the check confirmed, never their values.

        Why: the check item lists the fields of the Mist Edge items.
        It also lists the webhook topics and enabled flags, and the last_trouble field.
        The operator therefore sees the shape of each response.

        Args:
            finals: Final attempt of each request, in request order.

        Returns:
            The sorted field names.
        """
        names: set[str] = {  # Collect Mist Edge item keys as field names, never values.
            str(key) for item in self._rows(finals[3]) if isinstance(item, dict) for key in item
        }
        if any(isinstance(item, dict) and "topics" in item for item in self._rows(finals[5])):  # Webhook fields.
            names.update(("enabled", "topics"))  # The two webhook fields that the check reads.
        if any(isinstance(item, dict) and "last_trouble" in item for item in self._rows(finals[4])):  # AP field.
            names.add("last_trouble")  # The name only, never the value.
        return tuple(sorted(names))  # Names in a stable order.
