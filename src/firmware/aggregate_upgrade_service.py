"""Coordinate one multi-site firmware operation across safe Mist routes.

Why:
    The Mist organization device route supports access point upgrades only.
    Switches and Junos gateways use site routes. Session smart routers use
    their existing organization route. This class keeps those child calls in
    one operation and preserves each result without a hidden retry.
"""

from __future__ import annotations  # Keep modern annotations available at runtime.

import logging  # Record each boundary before and after its action.
import uuid  # Create durable operation and child identifiers.
from collections.abc import Callable, Mapping, MutableMapping, Sequence  # Define collection boundaries.
from copy import deepcopy  # Detach cloud and plan data before storage.
from dataclasses import dataclass  # Group the build input below the parameter limit.
from datetime import UTC, datetime, timedelta  # Bound destructive claim leases in UTC.
from typing import Any, Protocol  # Accept the SDK and define the durable store seam.

from src.firmware import upgrade_service  # Reuse the proven site and SSR planner.
from src.firmware.org_upgrade_service import OrgUpgradeResult, OrgUpgradeService  # Reuse the AP boundary.

logger = logging.getLogger(__name__)  # Use the module logger without secret fields.

FINAL_CHILD_STATES = frozenset({"cancelled", "completed", "failed", "rejected"})  # Known end states.
ACCEPTED_CHILD_STATES = frozenset({"accepted", "partial", "running", "read_unknown"})  # Readable states.
ACTIVE_CHILD_STATES = frozenset({"accepted", "partial", "running", "read_unknown"})  # Polling states.
FAILED_CHILD_STATES = frozenset({"failed", "rejected", "submission_unknown", "not_submitted", "unknown"})  # Problems.
CLAIM_LEASE = timedelta(minutes=5)  # A later request can recover only after this bounded interval.
AP_ACTIVE_STATES = frozenset(  # Cloud words that prove one AP site job still runs.
    {"accepted", "running", "upgrading", "downloading", "scheduled", "pending", "in_progress"}
)
AP_FAILURE_STATES = frozenset({"failed", "rejected", "error"})  # Known terminal failure words.
AP_TERMINAL_STATES = frozenset({"completed", "cancelled"})  # Known terminal nonfailure words.
SETTLED_STATE_RULES = (  # Map one settled child-state group to one aggregate word, in priority order.
    (frozenset({"submission_claimed"}), "running"),  # A fresh claim is still in flight.
    (frozenset({"submission_unknown", "not_submitted", "unknown"}), "attention_required"),  # Uncertain work.
    (frozenset({"failed", "rejected"}), "failed"),  # Only terminal failures remain.
)
CAS_ATTEMPTS = 4  # A bounded retry handles independent status updates without a blind write.
LockRefresh = Callable[[Mapping[str, Any], Mapping[str, Any]], None]  # Revalidate locks before one child write.


class RunStore(Protocol):
    """Define the durable read and compare-and-set seam."""

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Read one durable run."""

    def compare_and_set_run(
        self,
        run_id: str,
        expected_version: int,
        replacement: dict[str, Any],
    ) -> bool:
        """Replace one run only when its record version matches."""


@dataclass(frozen=True, slots=True)
class SubmissionResources:
    """Hold the store and lock refresh action for child submission."""

    store: RunStore  # Coordinate every state transition through durable compare-and-set.
    refresh_lock: LockRefresh  # Revalidate required site locks before each cloud write.


@dataclass(frozen=True, slots=True)  # Keep the confirmed build input immutable.
class AggregateBuildInput:  # Group related build values below the parameter limit.
    """Hold the confirmed values that create one aggregate operation."""

    owner: str  # Identify the signed operator that owns the operation.
    org_id: str  # Limit every child to one selected organization.
    sites: Sequence[Mapping[str, object]]  # Keep the selected site order and names.
    targets: Sequence[upgrade_service.DeviceTarget]  # Keep each confirmed device explicit.
    options: upgrade_service.UpgradeOptions  # Apply the confirmed choices to every child.
    request_nonce: str  # Prevent a confirmed request from starting twice.


class AggregateUpgradeService:  # Coordinate all child routes through one durable record.
    """Build, submit, read, and cancel one durable aggregate operation."""

    def __init__(  # Accept the established organization and device boundaries.
        self, org_service: Any = OrgUpgradeService, device_service: Any = upgrade_service
    ) -> None:
        """Keep the two proven cloud boundaries."""
        self._org_service = org_service  # The organization service sends the AP child.
        self._device_service = device_service  # The site planner sends switch and gateway children.

    def build(self, request: AggregateBuildInput) -> dict[str, Any]:  # Build without a cloud call.
        """Build one aggregate record and every child before a cloud write."""
        logger.info("Build an aggregate upgrade for organization %s", request.org_id)  # Log before the build.
        children = self._children(request)  # Build every safe route from the confirmed targets.
        operation_id = f"org-run-{uuid.uuid4().hex}"  # Create one stable identity for the visible operation.
        record = self._build_record(request, operation_id, children)  # Create the durable parent record.
        logger.debug("The aggregate upgrade holds %s child job(s)", len(children))  # Log after the build.
        return record  # The caller writes the record before submission.

    @staticmethod  # This record builder needs no service state.
    def _build_record(
        request: AggregateBuildInput,
        operation_id: str,
        children: list[dict[str, Any]],
    ) -> dict[str, Any]:  # Return a JSON-safe parent record.
        """Create the durable parent record for confirmed children."""
        return {  # Persist this whole record before the first destructive call.
            "_key": operation_id,  # The document store reads this key directly.
            "run_id": operation_id,  # The shared store expects a run identifier.
            "operation_id": operation_id,  # The portal paths use the aggregate identity.
            "owner": request.owner,  # The signed operator owns status and cancellation.
            "org_id": request.org_id,  # Every child stays inside one organization.
            "site_ids": [str(site["site_id"]) for site in request.sites],  # Keep the approved site order.
            "request_nonce": request.request_nonce,  # A repeated confirmation cannot send the writes again.
            "record_version": 0,  # Every later state transition uses durable compare-and-set.
            "state": "planned",  # No cloud call has left yet.
            "submission_claim_id": None,  # No request owns the parent submission yet.
            "submission_claimed_at": None,  # No parent claim lease exists yet.
            "site_locks": {},  # The route stores each acquired lock before submission.
            "children": children,  # Each child keeps its route, targets, and outcome.
            "errors": [],  # One child error must not replace another result.
            "cancellation": {"requested": False, "results": []},  # Keep each cancellation result.
        }

    def submit(  # Submit the durable children once.
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        store: RunStore,
        refresh_lock: LockRefresh,
    ) -> MutableMapping[str, Any]:  # Return the changed durable record.
        """Submit each planned child at most once and persist every outcome."""
        OrgUpgradeService.check_write_session(cloud_session)  # Require the no-retry write session.
        self._claim_submission(record, store)  # Claim the parent before any child cloud write.
        resources = SubmissionResources(store, refresh_lock)  # Keep the child helper below five parameters.
        child_ids = [str(child.get("child_id", "")) for child in record.get("children", [])]  # Keep plan order.
        for child_id in child_ids:  # Continue after one child refusal.
            if not self._submit_child(cloud_session, record, child_id, resources):  # Stop after lock loss.
                break  # No later child can write without all required locks.
        self._finish_parent(record, store)  # Persist the aggregate state and release the parent claim.
        logger.debug("Aggregate upgrade %s now has state %s", record.get("operation_id", ""), record["state"])
        return record  # The route returns the durable identity.

    def _claim_submission(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Claim the parent or recover a stale parent before submission."""
        current = self._current(record, store)  # Use the durable record as the decision source.
        if current.get("state") == "submission_claimed":  # Resolve the existing parent claim first.
            if not self._claim_is_stale(current, "submission"):  # A live request can still finish its call.
                raise ValueError("This aggregate upgrade has an active submission claim.")  # Refuse concurrency.
            self._cas(record, store, self._recover_parent_for_submit)  # Persist stale uncertainty first.
        claim_id = uuid.uuid4().hex  # Give this request a durable claim identity.

        def update(candidate: MutableMapping[str, Any]) -> None:
            if candidate.get("state") == "submission_claimed" and not self._claim_is_stale(candidate, "submission"):
                raise ValueError("This aggregate upgrade has an active submission claim.")  # Refuse the race.
            self._recover_submission_claims(candidate, for_status=False)  # Preserve uncertain earlier calls.
            if not any(child.get("status") == "planned" for child in candidate.get("children", [])):
                raise ValueError("This aggregate upgrade has no untouched child.")  # Never repeat a claimed call.
            candidate["state"] = "submission_claimed"  # Mark the parent before a child cloud write.
            candidate["submission_claim_id"] = claim_id  # Bind the claim to this request.
            candidate["submission_claimed_at"] = self._now_text()  # Start the bounded lease.

        logger.info("Claim aggregate upgrade %s for submission", record.get("operation_id", ""))  # Log before CAS.
        self._cas(record, store, update)  # Install the parent claim atomically.
        logger.debug("Aggregate upgrade %s has a submission claim", record.get("operation_id", ""))  # Log after CAS.

    def _recover_parent_for_submit(self, record: MutableMapping[str, Any]) -> None:
        """Convert stale claims before a later submission resumes untouched work."""
        self._recover_submission_claims(record, for_status=False)  # Preserve all uncertain child calls.
        record["state"] = "submission_unknown"  # Persist the stale parent outcome.
        record["submission_claim_id"] = None  # Release the stale request identity.
        record["submission_claimed_at"] = None  # Remove the expired lease.

    def status(  # Refresh every readable child.
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        store: RunStore,
    ) -> MutableMapping[str, Any]:  # Return the changed durable record.
        """Read every known child and preserve an unreadable child as unknown."""
        self._recover_for_status(record, store)  # Resolve stale write claims before any status read.
        logger.info("Read aggregate upgrade %s", record.get("operation_id", ""))  # Log before the reads.
        child_ids = [str(child.get("child_id", "")) for child in record.get("children", [])]  # Keep durable order.
        for child_id in child_ids:  # Read each submitted child independently.
            self._read_child(cloud_session, record, child_id, store)  # Persist this child's exact result.
        self._set_aggregate_state(record, store)  # Derive only the aggregate display state.
        logger.debug("Aggregate upgrade %s reports state %s", record.get("operation_id", ""), record["state"])
        return record  # The route builds the public status view.

    def cancel(  # Cancel every eligible child once.
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        store: RunStore,
    ) -> MutableMapping[str, Any]:  # Return the changed durable record.
        """Request cancellation for each eligible child one time."""
        OrgUpgradeService.check_write_session(cloud_session)  # Require the no-retry write session.
        self._start_cancellation(record, store)  # Persist the aggregate cancellation marker.
        child_ids = [str(child.get("child_id", "")) for child in record.get("children", [])]  # Keep durable order.
        for child_id in child_ids:  # Keep every child cancellation result.
            self._cancel_child(cloud_session, record, child_id, store)  # Claim and send at most one cancel call.
        self._finish_cancellation(record, store)  # Persist the aggregate state and result list.
        logger.debug("Aggregate cancellation %s recorded every child result", record.get("operation_id", ""))
        return record  # The route returns the aggregate cancellation view.

    def _start_cancellation(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Mark cancellation requested without rejecting a later recovery."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            cancellation = candidate.get("cancellation")  # Read the durable aggregate marker.
            if not isinstance(cancellation, MutableMapping):  # Repair a malformed optional marker.
                cancellation = {"requested": False, "results": []}  # Restore the supported JSON shape.
                candidate["cancellation"] = cancellation  # Keep the repaired marker in the record.
            cancellation["requested"] = True  # A later request keeps this true and continues untouched children.

        logger.info("Mark aggregate upgrade %s for cancellation", record.get("operation_id", ""))  # Log before CAS.
        self._cas(record, store, update)  # Store the marker atomically.
        logger.debug("Aggregate upgrade %s records cancellation", record.get("operation_id", ""))  # Log after CAS.

    def _children(self, request: AggregateBuildInput) -> list[dict[str, Any]]:
        """Build the AP organization child and the proven non-AP plans."""
        site_names = self._site_names(request.sites)  # Preserve the approved site order.
        access_points = self._access_points(request.targets)  # Select the only organization device family.
        children = self._ap_children(request, access_points, site_names)  # Build zero or one AP child.
        children.extend(self._non_ap_children(request, site_names))  # Reuse site and SSR planning.
        if not children:  # A confirmed operation must name at least one supported target.
            raise ValueError("The aggregate upgrade needs at least one target.")  # Reject an empty plan.
        return children  # Every target belongs to exactly one child.

    @staticmethod
    def _site_names(sites: Sequence[Mapping[str, object]]) -> dict[str, str]:
        """Return approved site names in their selected order."""
        logger.debug("Build the selected site index")  # Log before the data transformation.
        names = {str(site["site_id"]): str(site.get("name", site["site_id"])) for site in sites}  # Index sites.
        logger.debug("The selected site index holds %s site(s)", len(names))  # Log after the transformation.
        return names  # The dictionary keeps insertion order.

    @staticmethod
    def _access_points(
        targets: Sequence[upgrade_service.DeviceTarget],
    ) -> tuple[upgrade_service.DeviceTarget, ...]:
        """Return the targets that use the organization AP route."""
        return tuple(  # Preserve the confirmed target order.
            target for target in targets if target.device_type == upgrade_service.DEVICE_TYPE_AP  # Select APs only.
        )

    def _ap_children(
        self,
        request: AggregateBuildInput,
        targets: Sequence[upgrade_service.DeviceTarget],
        site_names: Mapping[str, str],
    ) -> list[dict[str, Any]]:
        """Build zero or one organization AP child."""
        if not targets:  # Do not create an empty cloud request.
            return []  # The non-AP plans can still form an operation.
        return [self._ap_child(request.org_id, targets, request.options, site_names)]  # Use one AP child.

    def _non_ap_children(
        self,
        request: AggregateBuildInput,
        site_names: Mapping[str, str],
    ) -> list[dict[str, Any]]:
        """Build site and SSR children through the proven planner."""
        children: list[dict[str, Any]] = []  # Preserve the deterministic site and plan order.
        for site_id, site_name in site_names.items():  # Plan each selected site independently.
            members = self._non_ap_site_targets(request.targets, site_id)  # Keep APs out of site plans.
            logger.debug("Plan non-AP children for site %s", site_id)  # Log before the planner.
            plans = upgrade_service.plan_upgrade(members, request.options, request.org_id, site_id) if members else ()
            logger.debug("The site plan holds %s child job(s)", len(plans))  # Log after the planner.
            children.extend(self._plan_child(plan, request.org_id, site_name) for plan in plans)  # Copy plans.
        return children  # Keep site routes and the existing SSR organization route.

    @staticmethod
    def _non_ap_site_targets(
        targets: Sequence[upgrade_service.DeviceTarget],
        site_id: str,
    ) -> tuple[upgrade_service.DeviceTarget, ...]:
        """Return non-AP targets for one selected site."""
        return tuple(  # Preserve the confirmed target order.
            target  # Keep the complete immutable target.
            for target in targets  # Inspect only the confirmed selection.
            if target.site_id == site_id and target.device_type != upgrade_service.DEVICE_TYPE_AP  # Match the site.
        )

    @classmethod
    def _ap_child(
        cls,
        org_id: str,
        targets: Sequence[upgrade_service.DeviceTarget],
        options: upgrade_service.UpgradeOptions,
        site_names: Mapping[str, str],
    ) -> dict[str, Any]:
        """Build the one AP organization child."""
        logger.debug("Build the organization AP child")  # Log before the body transformation.
        body = cls._ap_body(targets, options)  # Build the validated organization request body.
        site_ids = list(dict.fromkeys(target.site_id for target in targets))  # Keep explicit approved sites.
        child = cls._base_child("upgradeOrgDevices", "org", org_id, None, "ap")  # Create the common state.
        child.update(  # Add the AP-specific route and target values.
            site_name=", ".join(site_names.get(site_id, site_id) for site_id in site_ids),
            target_ids=[target.mac for target in targets],
            body=body,
        )
        logger.debug("The organization AP child holds %s target(s)", len(targets))  # Log after the build.
        return child  # The organization route receives every selected AP.

    @classmethod
    def _ap_body(
        cls,
        targets: Sequence[upgrade_service.DeviceTarget],
        options: upgrade_service.UpgradeOptions,
    ) -> dict[str, object]:
        """Build the organization AP request body."""
        versions = {target.version_target for target in targets}  # Check the one-version contract.
        if len(versions) != 1:  # Never send one version for targets that requested another.
            raise ValueError("All access points in an organization child need one target version.")
        site_ids = list(dict.fromkeys(target.site_id for target in targets))  # Keep approved site order.
        body = cls._ap_base_body(site_ids, next(iter(versions)), options)  # Build required fields.
        cls._add_ap_schedule(body, options)  # Add only supported optional fields.
        return body  # The caller stores the exact request before submission.

    @staticmethod
    def _ap_base_body(
        site_ids: list[str],
        version: str,
        options: upgrade_service.UpgradeOptions,
    ) -> dict[str, object]:
        """Build the required AP request fields."""
        version_record: dict[str, object] = {"firmware_type": "ap", "version": version}  # Name one AP version.
        if options.force:  # The organization schema puts force inside the version record.
            version_record["force"] = True  # Include the explicit force choice.
        return {  # Keep the organization route limited to APs and approved sites.
            "all_sites": False,  # Never expand beyond the selected sites.
            "device_type": "ap",  # Use the only verified device family.
            "site_ids": site_ids,  # Name each selected site explicitly.
            "versions": [version_record],  # Send one compatible AP version.
            "strategy": options.strategy,  # Preserve the confirmed rollout strategy.
        }

    @staticmethod
    def _add_ap_schedule(body: dict[str, object], options: upgrade_service.UpgradeOptions) -> None:
        """Add the optional AP schedule and canary fields."""
        if options.start_time is not None:  # Omit an unset schedule.
            body["start_time"] = options.start_time  # Preserve the confirmed epoch value.
        AggregateUpgradeService._add_ap_canary(body, options)  # Add strategy-specific fields separately.

    @staticmethod
    def _add_ap_canary(body: dict[str, object], options: upgrade_service.UpgradeOptions) -> None:
        """Add optional AP canary controls."""
        if options.strategy == upgrade_service.STRATEGY_CANARY:  # Add phases only for canary.
            body["canary_phases"] = list(options.canary.canary_phases or (1, 10, 50, 100))  # Keep defaults.
        failure = options.canary.max_failure_percentage  # Read the optional failure threshold once.
        if options.strategy != upgrade_service.STRATEGY_DEFAULT and failure is not None:  # Match the schema.
            body["max_failure_percentage"] = failure  # Preserve the confirmed threshold.

    @classmethod
    def _plan_child(
        cls,
        plan: upgrade_service.UpgradePlan,
        org_id: str,
        site_name: str,
    ) -> dict[str, Any]:
        """Copy one proven site or SSR plan into a durable child row."""
        family = "ssr" if plan.endpoint == upgrade_service.ENDPOINT_ORG_SSRS else plan.targets[0].device_type
        child = cls._base_child(plan.endpoint, plan.scope, org_id, plan.targets[0].site_id, family)  # Base state.
        child.update(  # Add the exact plan values that support later reads and cancellation.
            site_name=site_name,
            target_ids=[target.mac for target in plan.targets],
            body=deepcopy(dict(plan.body)),
            targets=[cls._target_record(target) for target in plan.targets],
        )
        return child  # The stored child can rebuild the proven plan.

    @staticmethod
    def _base_child(route: str, scope: str, org_id: str, site_id: str | None, family: str) -> dict[str, Any]:
        """Create the common durable child state."""
        return {  # Keep each child outcome independent.
            "child_id": f"child-{uuid.uuid4().hex}",  # Give the child a stable local identity.
            "route": route,  # Name the sanctioned cloud function.
            "scope": scope,  # Record whether the route uses a site or organization.
            "org_id": org_id,  # Preserve the parent organization boundary.
            "site_id": site_id,  # Preserve the site boundary when one exists.
            "device_family": family,  # Select the correct status and cancel behavior.
            "upgrade_id": None,  # No cloud identity exists before submission.
            "status": "planned",  # The replay marker starts before any write.
            "raw_status": 0,  # No HTTP response exists before submission.
            "error": None,  # No outcome exists before submission.
            "status_data": {},  # No status read exists before submission.
            "cancellation": None,  # No cancellation attempt exists before submission.
        }

    @staticmethod
    def _target_record(target: upgrade_service.DeviceTarget) -> dict[str, str]:
        """Copy one immutable target into a JSON-safe record."""
        return {  # Retain every value needed to rebuild the original plan.
            "mac": target.mac,  # Keep the explicit device identity.
            "name": target.name,  # Keep the display name.
            "device_type": target.device_type,  # Keep the planner family.
            "model": target.model,  # Keep the family classification input.
            "version_before": target.version_before,  # Keep the prior version for display.
            "version_target": target.version_target,  # Keep the confirmed target version.
            "site_id": target.site_id,  # Keep the selected site identity.
        }

    @staticmethod
    def _plan_from_child(child: Mapping[str, Any]) -> upgrade_service.UpgradePlan:
        """Rebuild a proven plan from its durable child row."""
        route = upgrade_service.PlanRoute(  # Restore the sanctioned route and its identifier.
            scope=str(child["scope"]),  # Restore the saved route scope.
            endpoint=str(child["route"]),  # Restore the saved endpoint.
            scope_id=str(child["org_id"] if child["scope"] == "org" else child["site_id"]),  # Restore its scope ID.
        )
        targets = tuple(upgrade_service.DeviceTarget(**dict(target)) for target in child.get("targets", ()))
        return upgrade_service.UpgradePlan(route=route, targets=targets, body=dict(child["body"]), warnings=())

    def _submit_child(
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        child_id: str,
        resources: SubmissionResources,
    ) -> bool:
        """Submit one child and persist an accepted, rejected, or unknown result."""
        current = self._current(record, resources.store)  # Read the latest child and lock records.
        child = self._find_child(current, child_id)  # Select the durable child by identity.
        if child is None or child.get("status") != "planned":  # A prior claim blocks another write.
            return True  # Continue with untouched children.
        try:  # A missing or lost lock must stop this child and all later writes.
            resources.refresh_lock(current, child)  # Revalidate every site lock that this child requires.
        except Exception as fault:  # Preserve a truthful stop reason without a cloud call.
            self._mark_lock_failure(record, resources.store, child_id, fault)  # Mark this and untouched children.
            return False  # Stop all later destructive writes.
        claim_id = uuid.uuid4().hex  # Give the child cloud call one durable identity.
        self._claim_child(record, resources.store, child_id, claim_id)  # Claim this child atomically.
        claimed = self._find_child(record, child_id)  # Read the child state installed by the claim.
        if claimed is None:  # A damaged record cannot reach a cloud boundary.
            raise RuntimeError("The claimed aggregate child is absent.")  # Fail closed.
        outcome = deepcopy(dict(claimed))  # Keep the cloud outcome separate until its CAS succeeds.
        logger.info("Submit aggregate child %s through %s", child_id, outcome.get("route", ""))  # Log before write.
        try:  # A transport failure after a write has an unknown outcome.
            self._send_child(cloud_session, outcome)  # Send exactly one destructive cloud call.
        except Exception as fault:  # Do not retry an uncertain destructive write.
            self._mark_submission_unknown(record, outcome, fault)  # Preserve the exception type only.
        self._finish_child(record, resources.store, (child_id, claim_id), outcome)  # Store this claim result.
        logger.debug("Aggregate child %s reports %s", child_id, outcome.get("status", "unknown"))  # Log after CAS.
        return True  # The next child can now revalidate its locks.

    def _claim_child(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        child_id: str,
        claim_id: str,
    ) -> None:
        """Claim one planned child before its cloud write."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the child from this CAS candidate.
            if child.get("status") != "planned":  # A concurrent claim must not repeat the write.
                raise ValueError("This aggregate child already has a submission claim.")  # Report the conflict.
            child["status"] = "submission_claimed"  # Make a process loss visible as an uncertain write.
            child["submission_claim_id"] = claim_id  # Bind completion to this exact cloud call.
            child["submission_claimed_at"] = self._now_text()  # Start the child lease.

        self._cas(record, store, update)  # Install the child barrier atomically.

    def _finish_child(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        claim: tuple[str, str],
        outcome: Mapping[str, Any],
    ) -> None:
        """Store one child outcome only when this request still owns the claim."""
        child_id, claim_id = claim  # Keep the helper within the parameter limit.

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the durable child.
            if child.get("submission_claim_id") != claim_id:  # Never overwrite a later recovery.
                raise RuntimeError("The aggregate child submission claim changed.")  # Leave the claim uncertain.
            child.clear()  # Replace all child fields with the detached cloud outcome.
            child.update(deepcopy(dict(outcome)))  # Keep the complete result and raw status data.
            child["submission_claim_id"] = claim_id  # Retain the identity for audit and replay analysis.
            if child.get("error"):  # Keep the child error in the aggregate history.
                candidate["errors"].append({"child_id": child_id, "error": child["error"]})  # Preserve it.

        self._cas(record, store, update)  # Persist the exact result atomically.

    def _mark_lock_failure(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        child_id: str,
        fault: Exception,
    ) -> None:
        """Mark the blocked child and all untouched children as not submitted."""
        message = f"The site lock is unavailable: {type(fault).__name__}."  # Name the truthful failure class.

        def update(candidate: MutableMapping[str, Any]) -> None:
            for child in candidate.get("children", []):  # Stop every child that has no cloud claim.
                if not isinstance(child, MutableMapping):  # Ignore a damaged child row.
                    continue  # Preserve the other rows.
                if child.get("child_id") == child_id or child.get("status") == "planned":  # Mark blocked work.
                    child["status"] = "not_submitted"  # State that no cloud write ran.
                    child["error"] = message  # Give each untouched child the actual reason.
            candidate["state"] = "attention_required"  # Tell the operator that the plan stopped.
            candidate["submission_claim_id"] = None  # Release the parent claim after the safe stop.
            candidate["submission_claimed_at"] = None  # Remove the completed lease timestamp.

        self._cas(record, store, update)  # Persist the stop before returning.

    def _send_child(self, cloud_session: Any, child: MutableMapping[str, Any]) -> None:
        """Send one child through its established cloud boundary."""
        if child.get("route") == "upgradeOrgDevices":  # Only the AP child uses this route.
            result = self._org_service.submit(cloud_session, str(child["org_id"]), child["body"])  # Send APs.
            self._apply_org_submission(child, result)  # Normalize the organization response.
            return  # Do not enter the site planner path.
        plan = self._plan_from_child(child)  # Restore the confirmed site or SSR plan.
        submission = self._device_service.invoke_upgrade(cloud_session, plan)  # Send the proven plan once.
        self._apply_device_submission(child, submission)  # Normalize the device response.

    @staticmethod
    def _mark_submission_unknown(
        record: MutableMapping[str, Any],
        child: MutableMapping[str, Any],
        fault: Exception,
    ) -> None:
        """Store an uncertain submission without a hidden retry."""
        child["status"] = "submission_unknown"  # Never retry the claimed destructive write.
        child["error"] = f"The submission outcome is unknown: {type(fault).__name__}."  # Expose the uncertainty.
        record["errors"].append({"child_id": child["child_id"], "error": child["error"]})  # Keep the child error.

    @staticmethod
    def _apply_org_submission(child: MutableMapping[str, Any], result: OrgUpgradeResult) -> None:
        """Copy an organization AP submission result."""
        child["upgrade_id"] = result.upgrade_id  # Keep an identifier when the response has one.
        child["raw_status"] = result.raw_status  # Preserve the true HTTP status.
        child["error"] = result.error  # Keep a malformed success distinct from acceptance.
        child["status_data"] = deepcopy(dict(result.data))  # Retain every site result.
        child["status"] = "accepted" if result.error is None and result.upgrade_id else "rejected"  # Set outcome.

    @staticmethod
    def _apply_device_submission(child: MutableMapping[str, Any], submission: Any) -> None:
        """Copy one site or SSR submission result."""
        child["upgrade_id"] = submission.upgrade_id  # Keep a cloud identifier when one exists.
        child["raw_status"] = submission.raw_status  # Preserve the exact HTTP status.
        accepted = bool(submission.accepted) and submission.raw_status in upgrade_service.ACCEPTED_STATUS
        child["status"] = "accepted" if accepted else "rejected"  # Do not turn a refusal into success.
        child["error"] = None if accepted else f"The cloud answered status {submission.raw_status}."  # Explain refusal.

    def _read_child(
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        child_id: str,
        store: RunStore,
    ) -> None:
        """Read one accepted child without changing another child."""
        current = self._current(record, store)  # Read the latest child state.
        child = self._find_child(current, child_id)  # Select one durable child.
        if child is None:  # A damaged row cannot stop the other reads.
            return  # Continue with the next child.
        if not self._can_read(child):  # A rejected or unknown submission has no safe status read.
            return  # Leave its exact submission outcome unchanged.
        logger.info("Read aggregate child %s through %s", child.get("child_id", ""), child.get("route", ""))
        outcome = deepcopy(dict(child))  # Apply the read away from the durable record.
        try:  # A read failure changes only this child's current reading.
            self._read_known_child(cloud_session, outcome)  # Use the route that created the child.
        except Exception as fault:  # Keep the operation readable when one endpoint fails.
            self._mark_status_unknown(outcome, fault)  # Preserve an explicit retryable read result.
        self._store_read(record, store, child_id, outcome)  # Persist the read if the child did not change.
        logger.debug("Aggregate child %s now reports %s", child_id, outcome.get("status", "unknown"))  # Log after CAS.

    @staticmethod
    def _can_read(child: Mapping[str, Any]) -> bool:
        """Return true when a child has a safe status read."""
        return child.get("status") in ACCEPTED_CHILD_STATES and bool(child.get("upgrade_id"))  # Require both gates.

    def _read_known_child(self, cloud_session: Any, child: MutableMapping[str, Any]) -> None:
        """Read a child through its organization or device route."""
        if child.get("route") == "upgradeOrgDevices":  # Read the AP organization job.
            self._read_org_child(cloud_session, child)  # Preserve the organization response.
            return  # Do not use the site status route.
        self._read_device_child(cloud_session, child)  # Use the existing family logic.

    def _read_org_child(self, cloud_session: Any, child: MutableMapping[str, Any]) -> None:
        """Read and apply one organization AP status."""
        result = self._org_service.status(cloud_session, str(child["org_id"]), str(child["upgrade_id"]))  # Read once.
        child["raw_status"] = result.raw_status  # Preserve the exact HTTP status.
        child["status_data"] = deepcopy(dict(result.data))  # Preserve every site and target result.
        child["error"] = result.error  # Preserve an invalid response as an error.
        child["status"] = self._org_status(result)  # Normalize only the display state.

    @staticmethod
    def _org_status(result: OrgUpgradeResult) -> str:
        """Return the organization child display state."""
        if result.error is not None:  # An invalid response cannot report a known state.
            return "unknown"  # Keep the invalid response visible.
        root = str(result.data.get("status", "")).lower()  # Prefer an explicit root state.
        if root:  # A root state is authoritative when the cloud supplies it.
            return root  # Preserve the cloud state word.
        raw_entries = result.data.get("site_upgrades", result.data.get("upgrades", []))  # Read either collection.
        entries = raw_entries if isinstance(raw_entries, list) else []  # Ignore a malformed collection.
        states = [AggregateUpgradeService._site_entry_status(entry) for entry in entries if isinstance(entry, Mapping)]
        return AggregateUpgradeService._combined_site_status(states)  # Derive a visible state from all sites.

    @staticmethod
    def _site_entry_status(entry: Mapping[str, Any]) -> str:
        """Return the nested or direct state of one AP site entry."""
        nested = entry.get("upgrade")  # Read the documented nested object.
        source = nested if isinstance(nested, Mapping) else entry  # Support both response shapes.
        return str(source.get("status", entry.get("status", "unknown"))).lower()  # Preserve unknown cloud words.

    @staticmethod
    def _combined_site_status(states: Sequence[str]) -> str:
        """Combine AP site states without hiding active or unknown entries."""
        values = [state or "unknown" for state in states]  # Keep each site state visible.
        if not values:  # An answer without site entries reports no known state.
            return "unknown"  # Never turn an empty answer into a success.
        seen = set(values)  # Compare the distinct words one time.
        if seen & AP_ACTIVE_STATES:  # An active site keeps the child nonterminal.
            return "partial" if seen & AP_FAILURE_STATES else "running"  # Show mixed failure.
        if seen <= AP_TERMINAL_STATES:  # Every site reached a terminal nonfailure state.
            return "cancelled" if seen == {"cancelled"} else "completed"  # Summarize the final words.
        if seen & AP_FAILURE_STATES:  # No active site remains, so a failure is now terminal.
            return "failed"  # Report the terminal failure for this child.
        return values[0]  # Preserve an unrecognized cloud word instead of hiding it.

    def _read_device_child(self, cloud_session: Any, child: MutableMapping[str, Any]) -> None:
        """Read and apply one site or SSR status."""
        plan = self._plan_from_child(child)  # Restore the confirmed route and targets.
        family = self._status_family(child)  # Select the existing SSR or Junos reader.
        status = self._device_service.read_upgrade_status(  # Read the child without a write.
            cloud_session, plan.scope, plan.route.scope_id, str(child["upgrade_id"]), family
        )
        child["status_data"] = deepcopy(dict(status))  # Preserve the complete normalized status.
        child["raw_status"] = int(status.get("raw_status", 0))  # Preserve the status code.
        child["status"] = str(status.get("status") or "unknown").lower()  # Preserve the cloud state.
        child["error"] = None if status.get("status_known", True) else "The cloud status is unknown."  # Mark doubt.

    @staticmethod
    def _status_family(child: Mapping[str, Any]) -> upgrade_service.GatewayFamily:
        """Return the family that selects the existing status route."""
        if child.get("device_family") == "ssr":  # SSR uses the organization status route.
            return upgrade_service.GatewayFamily.SSR  # Select the SSR reader.
        return upgrade_service.GatewayFamily.JUNOS  # Other planned children use the site reader.

    @staticmethod
    def _mark_status_unknown(child: MutableMapping[str, Any], fault: Exception) -> None:
        """Store an unreadable child status without hiding other children."""
        child["status"] = "read_unknown"  # Keep the child eligible for a later status retry.
        child["error"] = f"The status outcome is unknown: {type(fault).__name__}."  # Name the failure class.

    def _store_read(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        child_id: str,
        outcome: Mapping[str, Any],
    ) -> None:
        """Store one status read without overwriting a concurrent child action."""
        expected_claim = outcome.get("submission_claim_id")  # Keep the submission identity stable.

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the current durable child.
            if child.get("submission_claim_id") != expected_claim:  # Do not overwrite a changed submission.
                raise RuntimeError("The aggregate child changed during the status read.")  # Fail safely.
            child.clear()  # Replace the prior status fields.
            child.update(deepcopy(dict(outcome)))  # Preserve the full raw status response.

        self._cas(record, store, update)  # Persist the read result atomically.

    def _cancel_child(
        self,
        cloud_session: Any,
        record: MutableMapping[str, Any],
        child_id: str,
        store: RunStore,
    ) -> None:
        """Cancel one child and retain its exact cancellation result."""
        current = self._current(record, store)  # Read the latest cancellation state.
        child = self._find_child(current, child_id)  # Select one durable child.
        if child is None:  # Ignore a damaged row.
            return  # Do not call the cloud again.
        cancellation = child.get("cancellation")  # Read the durable child marker.
        if isinstance(cancellation, Mapping) and cancellation.get("status") == "cancel_claimed":
            if self._claim_is_stale(cancellation, "cancel"):  # Recover a stale uncertain cancel.
                self._mark_cancel_unknown(record, store, child_id)  # Never repeat that cloud call.
            return  # Continue with untouched children.
        if cancellation is not None:  # A final result prevents a second cancel write.
            return  # Do not call the cloud again.
        claim_id = uuid.uuid4().hex  # Give this cancel call one durable identity.
        self._claim_cancel(record, store, child_id, claim_id)  # Claim before the destructive call.
        claimed = self._required_child(record, child_id)  # Read the claimed child.
        logger.info("Cancel aggregate child %s through %s", child_id, claimed.get("route", ""))  # Log before write.
        try:  # A transport failure after a cancel stays unknown.
            result = self._cancellation_result(cloud_session, claimed)  # Send zero or one cloud call.
        except Exception as fault:  # Never retry an uncertain cancel.
            result = self._unknown_cancellation(fault)  # Preserve the uncertain result.
        self._finish_cancel(record, store, (child_id, claim_id), result)  # Store only for this exact claim.
        logger.debug("Aggregate child %s has a cancellation result", child_id)  # Log after action.

    def _claim_cancel(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        child_id: str,
        claim_id: str,
    ) -> None:
        """Claim one child cancellation before its cloud call."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the child in this CAS candidate.
            if child.get("cancellation") is not None:  # Another request already claimed or finished it.
                raise ValueError("This aggregate child already has a cancellation claim.")  # Refuse a duplicate.
            child["cancellation"] = {  # Persist the uncertain action before the cloud call.
                "status": "cancel_claimed",  # Mark an in-flight destructive cancellation.
                "claim_id": claim_id,  # Bind the result to this request.
                "claimed_at": self._now_text(),  # Start the cancellation lease.
                "message": "The cancellation request is in progress.",  # Give the UI a truthful state.
            }

        self._cas(record, store, update)  # Install the cancel barrier atomically.

    def _finish_cancel(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        claim: tuple[str, str],
        result: Mapping[str, Any],
    ) -> None:
        """Store one cancellation result only for its matching claim."""
        child_id, claim_id = claim  # Keep the helper within the parameter limit.

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the durable child.
            cancellation = child.get("cancellation")  # Read the current claim.
            if not isinstance(cancellation, Mapping) or cancellation.get("claim_id") != claim_id:
                raise RuntimeError("The aggregate child cancellation claim changed.")  # Preserve uncertainty.
            child["cancellation"] = {"claim_id": claim_id, **deepcopy(dict(result))}  # Keep claim and result.

        self._cas(record, store, update)  # Persist the cancellation outcome atomically.

    def _mark_cancel_unknown(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        child_id: str,
    ) -> None:
        """Convert one stale cancellation claim to a final unknown result."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            child = self._required_child(candidate, child_id)  # Select the durable child.
            cancellation = child.get("cancellation")  # Preserve the original claim identity.
            if not isinstance(cancellation, Mapping) or cancellation.get("status") != "cancel_claimed":
                return  # Another request already resolved this cancellation.
            child["cancellation"] = {  # Never repeat the stale destructive call.
                **dict(cancellation),  # Keep the claim time and identity.
                "status": "cancel_unknown",  # State that the prior outcome is not known.
                "message": "The cancellation outcome is unknown after the claim lease expired.",
            }

        self._cas(record, store, update)  # Persist the stale recovery atomically.

    def _cancellation_result(self, cloud_session: Any, child: Mapping[str, Any]) -> dict[str, Any]:
        """Return the cancellation result for one known child."""
        if not child.get("upgrade_id"):  # No known cloud identity can receive a cancel.
            return {"status": "unavailable", "message": "The child has no known upgrade identifier."}
        if child.get("route") == "upgradeOrgDevices":  # The AP child uses its organization cancel.
            return self._cancel_org_child(cloud_session, child)  # Send one organization cancel.
        return self._cancel_device_child(cloud_session, child)  # Use the proven site or SSR helper.

    def _cancel_org_child(self, cloud_session: Any, child: Mapping[str, Any]) -> dict[str, Any]:
        """Cancel one organization AP child."""
        result = self._org_service.cancel(cloud_session, str(child["org_id"]), str(child["upgrade_id"]))  # Send once.
        return {  # Preserve the complete normalized cancel result.
            "status": "requested" if result.error is None else "failed",  # Do not claim a failed request.
            "raw_status": result.raw_status,  # Preserve the exact HTTP status.
            "message": result.error,  # Preserve the validation or cloud error.
        }

    def _cancel_device_child(self, cloud_session: Any, child: Mapping[str, Any]) -> dict[str, Any]:
        """Cancel one site or SSR child through the proven helper."""
        outcome = self._device_service.cancel_upgrade(  # Send one best-effort cancellation.
            cloud_session, self._plan_from_child(child), str(child["upgrade_id"]), child.get("status_data")
        )
        return {  # Preserve every target category from the helper.
            "status": "requested",  # The helper reports the detailed limitations below.
            "cancelled": list(outcome.cancelled),  # List targets that stopped before writing.
            "already_writing": list(outcome.already_writing),  # List targets that can still complete.
            "no_cancel_available": list(outcome.no_cancel_available),  # List unsupported targets.
            "message": outcome.message,  # Keep the exact safe summary.
        }

    @staticmethod
    def _unknown_cancellation(fault: Exception) -> dict[str, str]:
        """Return an uncertain cancellation result."""
        return {  # Do not claim success after a transport exception.
            "status": "unknown",  # Make the uncertain outcome explicit.
            "message": f"The cancellation outcome is unknown: {type(fault).__name__}.",  # Name no secret detail.
        }

    @classmethod
    def _aggregate_state(cls, record: Mapping[str, Any]) -> str:
        """Return one display state without hiding a child result."""
        states = {
            str(child.get("status", "unknown")).lower() for child in record.get("children", [])
        }  # Collect states.
        if states & ACTIVE_CHILD_STATES:  # Never report a terminal aggregate while one child remains active.
            return "partial" if states & FAILED_CHILD_STATES else "running"  # Show mixed active and problem states.
        return cls._settled_state(states)  # Every remaining child holds a settled state.

    @staticmethod
    def _settled_state(states: set[str]) -> str:
        """Return the aggregate word for children that hold no active state."""
        for words, result in SETTLED_STATE_RULES:  # Apply the first matching rule in priority order.
            if states & words:  # This group decides the aggregate word.
                return result  # Report the matching aggregate state.
        if states and states <= AP_TERMINAL_STATES:  # Every child reached a nonfailure terminal state.
            return "cancelled" if states == {"cancelled"} else "completed"  # Preserve an all-cancelled result.
        if not states or states == {"planned"}:  # No child started a cloud call.
            return "planned"  # Preserve the initial state.
        return "attention_required"  # Keep unrecognized child states visible and non-successful.

    def _finish_parent(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Store the aggregate state and clear the completed parent claim."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            if candidate.get("state") != "attention_required":  # Preserve an explicit lock-loss stop.
                candidate["state"] = self._aggregate_state(candidate)  # Summarize the latest child states.
            candidate["submission_claim_id"] = None  # The request no longer owns the parent.
            candidate["submission_claimed_at"] = None  # The completed claim has no active lease.

        self._cas(record, store, update)  # Persist the summary atomically.

    def _finish_cancellation(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Store cancellation results and the current aggregate state."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            results = []  # Rebuild the list to avoid duplicate entries on a later request.
            for child in candidate.get("children", []):  # Preserve one result for each resolved child.
                cancellation = child.get("cancellation") if isinstance(child, Mapping) else None  # Read result.
                if isinstance(cancellation, Mapping):  # Skip untouched children only.
                    results.append({"child_id": child.get("child_id", ""), **dict(cancellation)})  # Add identity.
            candidate["cancellation"]["results"] = results  # Store the complete deduplicated result list.
            candidate["state"] = self._aggregate_state(candidate)  # Keep active children nonterminal.

        self._cas(record, store, update)  # Persist the cancellation summary atomically.

    def _recover_for_status(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Convert stale submission claims and stop untouched children."""
        current = self._current(record, store)  # Read the durable parent claim.
        stale_parent = current.get("state") == "submission_claimed" and self._claim_is_stale(current, "submission")
        stale_child = any(
            child.get("status") == "submission_claimed" and self._claim_is_stale(child, "submission")
            for child in current.get("children", [])
            if isinstance(child, Mapping)
        )  # Detect a stale child even if the parent summary changed.
        if not stale_parent and not stale_child:  # No recovery write is necessary.
            return  # Continue to ordinary status reads.

        def update(candidate: MutableMapping[str, Any]) -> None:
            self._recover_submission_claims(candidate, for_status=True)  # Mark claims and untouched work.

        self._cas(record, store, update)  # Persist recovery before a status read.

    def _recover_submission_claims(self, record: MutableMapping[str, Any], for_status: bool) -> None:
        """Convert stale child claims and optionally stop untouched children."""
        for child in record.get("children", []):  # Inspect every planned child.
            if not isinstance(child, MutableMapping):  # Ignore a damaged row.
                continue  # Preserve valid siblings.
            stale = child.get("status") == "submission_claimed" and self._claim_is_stale(child, "submission")
            if stale:  # The prior cloud call can have succeeded.
                child["status"] = "submission_unknown"  # Never repeat the claimed cloud write.
                child["error"] = "The submission outcome is unknown after the claim lease expired."
            elif for_status and child.get("status") == "planned":  # Status does not resume untouched work.
                child["status"] = "not_submitted"  # State that no cloud write ran.
                child["error"] = "The parent submission claim expired before this child started."
        if for_status:  # A status request ends the stale parent workflow.
            record["state"] = "attention_required"  # Show that manual review is necessary.
            record["submission_claim_id"] = None  # Release the stale parent claim.
            record["submission_claimed_at"] = None  # Remove the expired lease.

    def _set_aggregate_state(self, record: MutableMapping[str, Any], store: RunStore) -> None:
        """Persist the aggregate state from the latest children."""

        def update(candidate: MutableMapping[str, Any]) -> None:
            candidate["state"] = self._aggregate_state(candidate)  # Derive the display state only.

        self._cas(record, store, update)  # Store the summary atomically.

    @staticmethod
    def _now_text() -> str:
        """Return the current UTC claim time."""
        return datetime.now(UTC).isoformat()  # Use one parseable timezone-aware format.

    @staticmethod
    def _claim_is_stale(record: Mapping[str, Any], prefix: str) -> bool:
        """Return true when a claim timestamp is absent, invalid, or expired."""
        field = "claimed_at" if prefix == "cancel" else f"{prefix}_claimed_at"  # Select the stored timestamp.
        value = record.get(field)  # Read the claim time without trusting its type.
        try:  # Invalid persisted text must fail closed as stale uncertainty.
            claimed = datetime.fromisoformat(str(value))  # Parse the UTC timestamp.
        except (TypeError, ValueError):  # A missing or damaged time cannot hold a live lease.
            return True  # Recover it without repeating the destructive call.
        return datetime.now(UTC) - claimed.astimezone(UTC) >= CLAIM_LEASE  # Compare against the bounded lease.

    @staticmethod
    def _find_child(record: Mapping[str, Any], child_id: str) -> MutableMapping[str, Any] | None:
        """Return one mutable child by its durable identity."""
        for child in record.get("children", []):  # Search the small planned child list.
            if isinstance(child, MutableMapping) and child.get("child_id") == child_id:  # Match one valid row.
                return child  # Return the durable child.
        return None  # The record is damaged or the child disappeared.

    @classmethod
    def _required_child(cls, record: Mapping[str, Any], child_id: str) -> MutableMapping[str, Any]:
        """Return one child or fail closed."""
        child = cls._find_child(record, child_id)  # Search by stable identity.
        if child is None:  # A missing child invalidates the planned action.
            raise RuntimeError("The aggregate child record is absent.")  # Stop before a cloud write.
        return child  # Return the validated mutable row.

    @staticmethod
    def _current(record: MutableMapping[str, Any], store: RunStore) -> dict[str, Any]:
        """Read and copy the current durable record."""
        run_id = str(record.get("run_id", ""))  # Read the stable store key.
        current = store.read_run(run_id)  # The durable store decides the current version.
        if not isinstance(current, Mapping):  # A missing store record cannot coordinate writes.
            raise RuntimeError("The durable aggregate record is unavailable.")  # Fail closed.
        record.clear()  # Replace the caller snapshot with the durable state.
        record.update(deepcopy(dict(current)))  # Detach the durable record before local work.
        return deepcopy(dict(record))  # Give the caller an independent working copy.

    def _cas(
        self,
        record: MutableMapping[str, Any],
        store: RunStore,
        update: Callable[[MutableMapping[str, Any]], None],
    ) -> None:
        """Apply one bounded compare-and-set update to the durable record."""
        for _ in range(CAS_ATTEMPTS):  # Bound contention retries.
            current = self._current(record, store)  # Read the current durable version.
            expected = current.get("record_version")  # Read the application version.
            if type(expected) is not int:  # A malformed version cannot coordinate writes.
                raise RuntimeError("The aggregate record version is invalid.")  # Fail closed.
            candidate: MutableMapping[str, Any] = deepcopy(current)  # Keep failed attempts detached.
            update(candidate)  # Apply the requested state transition.
            candidate["record_version"] = expected + 1  # Advance exactly one version.
            if store.compare_and_set_run(str(candidate["run_id"]), expected, dict(candidate)):  # Try atomic CAS.
                record.clear()  # Replace the caller snapshot only after success.
                record.update(deepcopy(dict(candidate)))  # Keep later actions on the accepted version.
                return  # The durable transition succeeded.
        raise RuntimeError("The aggregate record changed during the operation.")  # Stop after bounded contention.
