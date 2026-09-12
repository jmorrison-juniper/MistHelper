"""Hold process-owned portal records for one E2E server.

Why:
    An E2E server must not read a production database or a portal record file.
    This store keeps each record in one process and enforces one test owner.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Read the serialized lock token for atomic compare operations.
import logging  # Record each in-process read and write.
from copy import deepcopy  # Stop a caller from changing a stored record.
from dataclasses import dataclass  # Describe one capture load result.
from threading import RLock  # Keep each Redis-style compare and mutation atomic.
from typing import Any  # Portal records contain different JSON-compatible fields.

logger = logging.getLogger(__name__)  # Keep record activity tied to this module.


@dataclass(frozen=True, slots=True)
class CaptureLoad:  # Describe one capture result without a production store type.
    """Describe one process-owned capture read."""

    capture: dict[str, Any] | None  # Hold the capture when the identifier exists.
    comparable: bool  # Report whether the capture can join a comparison.
    reason: str  # Give the route a stable refusal reason.


class PortalRecordStore:  # Own portal records for one isolated server process.
    """Own run, capture, lock, and authorization records for one test run."""

    def __init__(self, test_run_id: str) -> None:  # Bind the empty record graph to one test owner.
        """Create an empty record graph for one E2E server."""
        self.test_run_id = test_run_id  # Bind every stored record to one server.
        self._runs: dict[str, dict[str, Any]] = {}  # Hold run records by identifier.
        self._captures: dict[str, dict[str, Any]] = {}  # Hold capture records by identifier.
        self._locks: dict[str, dict[str, Any]] = {}  # Hold owned lock records by Redis-style key.
        self._lock_guard = RLock()  # Make each Redis-style compare and mutation one process step.
        self._authorizations: dict[str, dict[str, Any]] = {}  # Hold owned access records by scope.

    def _owned(self, record: dict[str, Any]) -> dict[str, Any]:  # Enforce and attach record ownership.
        """Return an owned record and reject a record from another test run."""
        copied = deepcopy(record)  # Isolate the stored value from the caller.
        owner = copied.get("test_run_id")  # Read the owner before this store adds one.
        if owner not in (None, self.test_run_id):  # Another E2E server owns this record.
            raise ValueError("The record belongs to a different E2E test run.")  # Reject cross-process data.
        copied["test_run_id"] = self.test_run_id  # Make ownership explicit on every stored record.
        return copied  # The caller stores the protected copy.

    def write_run(self, run: dict[str, Any]) -> bool:  # Store one owned run record.
        """Store one owned run record."""
        logger.info("Store one E2E run record")  # Record the process-owned write before it starts.
        owned = self._owned(run)  # Reject a record from another test run.
        run_id = str(owned["run_id"])
        prior = self._runs.get(run_id)
        owned["_rev"] = str(int(str(prior.get("_rev", "0"))) + 1) if prior is not None else "1"
        self._runs[run_id] = owned  # Store the run under its business identifier.
        logger.debug("The E2E run store now holds %s record(s)", len(self._runs))  # Report a safe count.
        return True  # Match the production run store write contract.

    @property
    def transaction_lock(self) -> RLock:
        """Return the process lock for one atomic run and action write."""
        return self._lock_guard

    def read_run(self, run_id: str) -> dict[str, Any] | None:  # Read one owned run record.
        """Return one owned run record."""
        logger.info("Read one E2E run record")  # Record the process-owned read before it starts.
        record = self._runs.get(run_id)  # An absent identifier returns no record.
        result = deepcopy(record) if record is not None else None  # Protect the stored record from edits.
        logger.debug("The E2E run read found a record: %s", result is not None)  # Report no record data.
        return result  # Give the route an isolated copy.

    def runs_for_site(self, site_id: str) -> list[dict[str, Any]]:  # List owned runs for one site.
        """Return all owned runs for one site."""
        logger.info("List E2E run records for one site")  # Record the process-owned scan.
        rows = [deepcopy(row) for row in self._runs.values() if row.get("site_id") == site_id]  # Filter safely.
        logger.debug("The E2E site run list holds %s record(s)", len(rows))  # Report a safe count.
        return rows  # Preserve insertion order for deterministic tests.

    def list_runs(  # List one page of owned run records.
        self, site_id: str = "", limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Return one ordered page of owned run records."""
        logger.info("List one E2E run record page")  # Record the process-owned scan.
        rows = list(self._runs.values())  # Preserve deterministic insertion order.
        scoped = [row for row in rows if not site_id or row.get("site_id") == site_id]  # Apply the site filter.
        page = [deepcopy(row) for row in scoped[offset : offset + limit]]  # Return only the requested page.
        logger.debug("The E2E run page holds %s record(s)", len(page))  # Report a safe count.
        return page  # Give the route isolated copies.

    def write_capture(self, capture: dict[str, Any]) -> bool:  # Store one owned capture record.
        """Store one owned capture record."""
        logger.info("Store one E2E capture record")  # Record the process-owned write.
        owned = self._owned(capture)  # Reject a capture from another test run.
        self._captures[str(owned["capture_id"])] = owned  # Store the capture under its business identifier.
        logger.debug("The E2E capture store now holds %s record(s)", len(self._captures))  # Report a safe count.
        return True  # Match the production capture write contract.

    def load_capture(self, capture_id: str) -> CaptureLoad:  # Read one owned capture result.
        """Return one owned capture in the production result shape."""
        logger.info("Read one E2E capture record")  # Record the process-owned read.
        record = self._captures.get(capture_id)  # An absent identifier returns no record.
        result = CaptureLoad(  # Return the same shape as the production capture loader.
            deepcopy(record), record is not None, "" if record is not None else "capture_not_found"
        )
        logger.debug("The E2E capture read found a record: %s", record is not None)  # Report no record data.
        return result  # Give both capture routes the expected result shape.

    def list_captures(  # List one page of owned capture records.
        self, site_id: str = "", limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Return one ordered page of owned capture records."""
        logger.info("List one E2E capture record page")  # Record the process-owned scan.
        rows = list(self._captures.values())  # Preserve deterministic insertion order.
        scoped = [row for row in rows if not site_id or row.get("site_id") == site_id]  # Apply the site filter.
        page = [deepcopy(row) for row in scoped[offset : offset + limit]]  # Return only the requested page.
        logger.debug("The E2E capture page holds %s record(s)", len(page))  # Report a safe count.
        return page  # Give the route isolated copies.

    def set_authorization(self, scope: str, allowed: bool) -> None:  # Store one owned access decision.
        """Store one process-owned authorization decision."""
        logger.info("Store one E2E authorization decision")  # Record the access update.
        self._authorizations[scope] = {  # Keep ownership on every access record.
            "test_run_id": self.test_run_id,  # Bind the decision to this E2E server.
            "allowed": bool(allowed),  # Keep the explicit fail-closed decision.
        }
        logger.debug("The E2E access store now holds %s decision(s)", len(self._authorizations))  # Safe count.

    def authorization(self, scope: str) -> bool:  # Read one owned access decision.
        """Return one process-owned authorization decision."""
        logger.info("Read one E2E authorization decision")  # Record the access read.
        record = self._authorizations.get(scope) or self._authorizations.get(scope.split(":", 2)[0] + ":write")
        allowed = bool(record and record.get("test_run_id") == self.test_run_id and record.get("allowed"))  # Validate.
        logger.debug("The E2E authorization decision is allowed: %s", allowed)  # Report the safe result.
        return allowed  # The route can enforce the current decision.

    def set(self, key: str, value: str, **options: Any) -> bool:  # Store one owned lock value.
        """Store one Redis-style lock value in the process."""
        logger.info("Store one E2E lock record")  # Record the lock write.
        with self._lock_guard:  # Keep the conditional check and the write atomic.
            exists = key in self._locks  # Read the current key once inside the guard.
            if options.get("nx") and exists:  # Redis NX refuses an overwrite.
                return False  # The caller then reports that another owner holds the site.
            if options.get("xx") and not exists:  # Redis XX refuses a missing key.
                return False  # A refresh must not recreate an expired lock.
            self._locks[key] = {  # Keep ownership beside the serialized lock value.
                "test_run_id": self.test_run_id,  # Bind the lock to this E2E server.
                "value": value,  # Preserve the production lock serialization.
            }
        logger.debug("The E2E lock store now holds %s record(s)", len(self._locks))  # Report a safe count.
        return True  # Match the Redis set result used by the lock service.

    def get(self, key: str) -> str | None:  # Read one owned lock value.
        """Return one Redis-style lock value."""
        logger.info("Read one E2E lock record")  # Record the lock read.
        with self._lock_guard:  # Read a stable record while another request can mutate it.
            record = self._locks.get(key)  # An absent lock returns no owned record.
            value = str(record["value"]) if record and record.get("test_run_id") == self.test_run_id else None
        logger.debug("The E2E lock read found a record: %s", value is not None)  # Report no lock content.
        return value  # Give the lock service its serialized record.

    def eval(self, script: str, key_count: int, *values: Any) -> int:  # Run the lock service compare scripts.
        """Run one Redis-style lock script as an atomic process operation."""
        if key_count != 1 or len(values) < 2:  # The shipped lock service uses one key and at least one argument.
            raise ValueError("The E2E lock script shape is not supported.")  # Fail closed on an unknown script.
        key = str(values[0])  # The first value after the key count is the Redis key.
        expected_token = str(values[1])  # Every shipped script compares this lock token.
        with self._lock_guard:  # Keep the read, comparison, and mutation atomic.
            record = self._locks.get(key)  # Read the current owned lock once.
            current = str(record["value"]) if record and record.get("test_run_id") == self.test_run_id else None
            if "redis.call('DEL'" in script:  # The release script deletes only a matching lock.
                if current is None:
                    return 2  # Match the shipped script result for an absent key.
                if self._lock_token(current) != expected_token:
                    return 0  # A different owner now holds the site.
                del self._locks[key]  # Delete only the matching owned record.
                return 1  # Report the successful release.
            if len(values) < 3:  # Refresh and takeover both require a replacement record.
                raise ValueError("The E2E lock script replacement is missing.")
            if current is None and "if not current then return 0" in script:
                return 0  # A refresh must not recreate an absent lock.
            if current is not None and self._lock_token(current) != expected_token:
                return 0  # Neither refresh nor takeover can replace another token.
            self._locks[key] = {"test_run_id": self.test_run_id, "value": str(values[2])}
            return 1  # Match the successful refresh or takeover result.

    @staticmethod
    def _lock_token(value: str) -> str:  # Read the token from one serialized lock record.
        """Return the lock token from one serialized record."""
        try:  # A damaged record must match no caller.
            decoded = json.loads(value)  # The shipped lock record uses JSON text.
        except (TypeError, ValueError):
            return ""  # An unreadable record cannot authorize a mutation.
        return str(decoded.get("lock_token", "")) if isinstance(decoded, dict) else ""

    def ping(self) -> bool:  # Report process-owned lock store readiness.
        """Report that the process-owned lock store is available."""
        logger.info("Probe the E2E lock store")  # Record the readiness action.
        logger.debug("The E2E lock store answered the probe")  # Confirm the in-process result.
        return True  # No external service is necessary.

    def newest_precheck(self, site_id: str) -> str:  # Find one reusable owned pre-check.
        """Return the newest verified pre-check identifier for one site."""
        logger.info("Find the newest E2E pre-check capture")  # Record the process-owned scan.
        matches = [row for row in self._captures.values() if self._is_precheck(row, site_id)]  # Keep safe matches.
        result = str(matches[-1].get("capture_id", "")) if matches else ""  # Use stable insertion order.
        logger.debug("The E2E pre-check search found a capture: %s", bool(result))  # Report no identifier.
        return result  # An empty value means that no reusable pre-check exists.

    @staticmethod
    def _is_precheck(record: dict[str, Any], site_id: str) -> bool:  # Check safe pre-check reuse fields.
        """Report whether one owned capture is a verified pre-check for one site."""
        same_site = record.get("site_id") == site_id  # Match the requested site first.
        pre_role = record.get("role") == "pre"  # Accept only the pre-check role.
        verified = record.get("capture_status") == "verified"  # Accept only complete stored captures.
        return same_site and pre_role and verified  # Require every safe reuse condition.

    def write_capture_edge(self, run_id: str, capture_id: str, role: str) -> None:  # Link owned records.
        """Link one process-owned capture to one process-owned run."""
        logger.info("Link one E2E capture record to one run record")  # Record the in-process update.
        run = self._runs.get(run_id)  # An absent run leaves no edge to write.
        if run is None:  # Fail closed when the run does not belong to this store.
            raise ValueError("The E2E run record does not exist.")  # Prevent a dangling process-owned edge.
        run[f"{role}_capture_id"] = capture_id  # Keep the link on the owned run record.
        logger.debug("Linked one E2E capture record to one run record")  # Confirm the safe update.
