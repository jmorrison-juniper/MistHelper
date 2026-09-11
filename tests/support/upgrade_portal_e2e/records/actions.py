"""Hold process-owned action records for one E2E server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each process-owned action operation.
from copy import deepcopy  # Stop a caller from changing a stored action.
from typing import Any  # Action records contain different JSON-compatible fields.

logger = logging.getLogger(__name__)  # Keep action activity tied to this module.


class ActionRecordStore:  # Own action records for one isolated server process.
    """Own action records for one test run."""

    def __init__(self, test_run_id: str) -> None:  # Bind the empty store to one test owner.
        """Create an empty action store."""
        self.test_run_id = test_run_id  # Bind every action to one E2E server.
        self._actions: dict[str, dict[str, Any]] = {}  # Hold actions by public identifier.

    def write(self, action: dict[str, Any]) -> bool:  # Store one owned action record.
        """Store one action and reject a different owner."""
        logger.info("Store one E2E action record")  # Record the action write.
        copied = deepcopy(action)  # Isolate the stored record from the caller.
        owner = copied.get("test_run_id")  # Read the supplied owner before adding one.
        if owner not in (None, self.test_run_id):  # Another E2E server owns this action.
            raise ValueError("The record belongs to a different E2E test run.")  # Reject cross-process data.
        copied["test_run_id"] = self.test_run_id  # Make ownership explicit on the stored action.
        self._actions[str(copied["action_id"])] = copied  # Store the action under its public identifier.
        logger.debug("The E2E action store now holds %s record(s)", len(self._actions))  # Report a safe count.
        return True  # Match the action repository write contract.

    def read(self, action_id: str) -> dict[str, Any] | None:  # Read one owned action record.
        """Return one action record."""
        logger.info("Read one E2E action record")  # Record the action read.
        record = self._actions.get(action_id)  # An absent identifier returns no record.
        result = deepcopy(record) if record is not None else None  # Protect the stored action from edits.
        logger.debug("The E2E action read found a record: %s", result is not None)  # Report no action data.
        return result  # Give the caller an isolated copy.

    def list(self) -> list[dict[str, Any]]:  # List owned action records in stable order.
        """Return all action records in insertion order."""
        logger.info("List E2E action records")  # Record the process-owned scan.
        rows = [deepcopy(record) for record in self._actions.values()]  # Protect every stored action.
        logger.debug("The E2E action list holds %s record(s)", len(rows))  # Report a safe count.
        return rows  # Preserve deterministic insertion order.
