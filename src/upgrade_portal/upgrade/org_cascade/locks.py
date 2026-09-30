"""Renew and release every site lock of one multi-site operation.

Why:
    Issue #3333. A multi-site submission stored each site lock, but no code
    renewed those locks after the cloud accepted the child jobs. The phase
    watch can last for hours and includes the post-check stage. This lease
    renews every stored lock at the contract interval for the life of that
    watch.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Mapping, MutableMapping
from datetime import UTC, datetime
from typing import Any

from src.upgrade_portal.runtime import lock
from src.upgrade_portal.upgrade.org_cascade.record import OrgPhaseStore

logger = logging.getLogger(__name__)  # One logger for the multi-site lock lease.


class OrgOperationLockLease:
    """Renew all site locks until the phase watch releases them."""

    def __init__(self, store: Any, operation_id: str, client: Any) -> None:
        """Keep the durable operation, the lock client, and the renewal thread.

        Args:
            store: The run store that holds the operation.
            operation_id: The operation that owns every site lock.
            client: The lock store client that each renewal uses.
        """
        self._operation_id = operation_id  # Every read and log line names this operation.
        self._client = client  # The request binds the client before the background thread starts.
        self._records = OrgPhaseStore(store, operation_id, self._now_text)  # Use the existing bounded writer.
        self._stop = threading.Event()  # The watch thread wakes the renewal thread during shutdown.
        self._thread: threading.Thread | None = None  # Start creates one renewal thread for this lease.

    def start(self) -> None:
        """Start the renewal thread when this lease has no live thread."""
        if self._thread is not None and self._thread.is_alive():  # One phase watch needs one renewal thread.
            return  # The live thread already renews every stored site.
        logger.info("org cascade: start the site lock lease of %s", self._operation_id)  # Before the start.
        self._stop.clear()  # A resumed watch must not inherit the stop flag of an earlier thread.
        self._thread = threading.Thread(  # A daemon thread cannot hold the portal open during shutdown.
            target=self._run, name=f"org-locks-{self._operation_id[-8:]}", daemon=True
        )
        self._thread.start()  # The first renewal occurs after one contract interval.
        logger.debug("org cascade: started the site lock lease of %s", self._operation_id)  # After the start.

    def stop(self) -> None:
        """Stop the renewal thread without releasing a lock."""
        self._stop.set()  # Wake an interval wait at once.
        thread = self._thread  # Keep one stable reference while the thread can end.
        if thread is not None and thread is not threading.current_thread():  # Never join the current thread.
            thread.join(timeout=5)  # The event wait wakes at once, so five seconds detects a stuck thread.
        logger.debug("org cascade: stopped the site lock lease of %s", self._operation_id)  # After the stop.

    def renew(self) -> int:
        """Renew each readable stored lock, and return the renewal count."""
        record = self._records.read() or {}  # Read the latest lock map before every renewal round.
        stored = record.get("site_locks")  # The operation owns the durable lock copies.
        if not isinstance(stored, Mapping):  # A damaged record has no lock that this lease can renew.
            return 0  # The next status read still shows the damaged operation.
        renewed = 0  # Count the accepted renewal calls for the log and the tests.
        for site_id, value in stored.items():  # Renew every selected site during the same round.
            renewed += int(self._renew_one(record, str(site_id), value))  # One failed site does not skip the others.
        logger.debug("org cascade: renewed %d site lock(s) of %s", renewed, self._operation_id)  # After the round.
        return renewed  # The caller can verify that the round reached every valid lock.

    def release(self) -> None:
        """Stop renewal, release every stored lock, and clear the durable map."""
        self.stop()  # No renewal can race with the release calls below.
        record = self._records.read() or {}  # Read the newest tokens before the release.
        stored = record.get("site_locks")  # The durable map is the release scope.
        if not isinstance(stored, Mapping) or not stored:  # An empty map means another path already released.
            return  # No lock store call or record write is necessary.
        logger.info("org cascade: release %d site lock(s) of %s", len(stored), self._operation_id)  # Before.
        for site_id, value in stored.items():  # Give back every selected site after the post-check stage.
            self._release_one(record, str(site_id), value)  # One failed release does not skip the other sites.
        self._records.update(OrgOperationLockLease._clear)  # A restart then sees no lock left to release.
        logger.debug("org cascade: released the site lock scope of %s", self._operation_id)  # After the release.

    def _run(self) -> None:
        """Renew all locks after each contract interval until the watch stops."""
        while not self._stop.wait(lock.HEARTBEAT_SECONDS):  # The contract fixes a 60-second renewal interval.
            logger.info("org cascade: renew the site locks of %s", self._operation_id)  # Before the round.
            if self.renew() == 0:  # No readable lock means this thread has no useful work.
                logger.warning("org cascade: the operation %s has no readable site lock", self._operation_id)

    def _renew_one(self, operation: Mapping[str, Any], site_id: str, value: object) -> bool:
        """Renew one stored site lock, and keep a fault inside this site."""
        saved = OrgOperationLockLease._saved(value)  # Rebuild the lock record without exposing its token.
        if saved is None or saved.run_id != self._operation_id:  # Refuse a damaged or foreign run binding.
            logger.warning("org cascade: site %s has no matching lock for %s", site_id, self._operation_id)
            return False  # The other site locks still receive this renewal round.
        key = lock.build_key(str(operation.get("org_id", "")), site_id)  # Build the existing organization key.
        try:  # A lock store fault on one site must not stop renewal of another site.
            lock.refresh_site_lock(key, saved, self._client)  # Compare the token and extend the lock life.
        except lock.SiteLockError as error:  # A lost lock or quiet store stays visible in the log.
            logger.warning("org cascade: site %s renewal reported %s", site_id, error.code)
            return False  # Firmware already in progress cannot be recalled.
        except Exception as error:  # Keep broad: one unexpected client fault must not skip another site.
            logger.error("org cascade: site %s renewal stopped with %s", site_id, type(error).__name__)
            return False  # The next interval can retry this site.
        logger.info("org cascade: renewed site %s for %s", site_id, self._operation_id)  # After the renewal.
        return True  # The round renewed this site.

    def _release_one(self, operation: Mapping[str, Any], site_id: str, value: object) -> None:
        """Release one stored site lock, and keep a fault inside this site."""
        saved = OrgOperationLockLease._saved(value)  # Rebuild the lock record without exposing its token.
        if saved is None or saved.run_id != self._operation_id:  # Never release a foreign lock record.
            logger.warning("org cascade: site %s has no releasable lock for %s", site_id, self._operation_id)
            return  # The lease clears the damaged stored copy after the other releases.
        key = lock.build_key(str(operation.get("org_id", "")), site_id)  # Build the existing organization key.
        try:  # A failed release must not stop the release of another selected site.
            lock.release_site_lock(key, saved, self._client)  # Compare the token before the delete.
        except lock.SiteLockError as error:  # A takeover or quiet store leaves no safe retry in this close.
            logger.warning("org cascade: site %s release reported %s", site_id, error.code)
            return  # The remaining sites still receive a release.
        except Exception as error:  # Keep broad: one unexpected client fault must not skip another site.
            logger.error("org cascade: site %s release stopped with %s", site_id, type(error).__name__)
            return  # The remaining sites still receive a release.
        logger.info("org cascade: released site %s for %s", site_id, self._operation_id)  # After the release.

    @staticmethod
    def _saved(value: object) -> lock.LockRecord | None:
        """Return one stored lock record, or None for a damaged value."""
        return lock.LockRecord.from_json(json.dumps(value)) if isinstance(value, Mapping) else None  # Decode safely.

    @staticmethod
    def _clear(record: MutableMapping[str, Any]) -> None:
        """Clear the durable lock map after every release attempt."""
        record["site_locks"] = {}  # A restart must not release these tokens a second time.

    @staticmethod
    def _now_text() -> str:
        """Return the present UTC time for the bounded record writer."""
        return datetime.now(UTC).isoformat()  # Match the timestamp shape of the other operation writes.
