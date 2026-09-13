"""Hold scripted cloud evidence for one E2E server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each scripted cloud read.
from copy import deepcopy  # Stop a caller from changing a stored cloud answer.
from typing import Any  # Cloud answers contain different JSON-compatible fields.

logger = logging.getLogger(__name__)  # Keep cloud activity tied to this module.


class ScriptedCloudStore:  # Own scripted cloud records for one isolated server process.
    """Own scripted cloud answers for one test run."""

    def __init__(self, test_run_id: str) -> None:  # Bind the empty store to one test owner.
        """Create an empty script table."""
        self.test_run_id = test_run_id  # Bind every cloud script to one E2E server.
        self._scripts: dict[str, dict[str, Any]] = {}  # Hold one owned answer for each call name.

    def write(self, name: str, record: dict[str, Any]) -> None:  # Store one owned cloud script.
        """Store one cloud script and reject a different owner."""
        logger.info("Store one E2E cloud script")  # Record the script write.
        copied = deepcopy(record)  # Isolate the stored script from the caller.
        owner = copied.get("test_run_id")  # Read the supplied owner before adding one.
        if owner not in (None, self.test_run_id):  # Another E2E server owns this script.
            raise ValueError("The record belongs to a different E2E test run.")  # Reject cross-process data.
        copied["test_run_id"] = self.test_run_id  # Make ownership explicit on the stored script.
        self._scripts[name] = copied  # Replace only the named deterministic answer.
        logger.debug("The E2E cloud script store now holds %s record(s)", len(self._scripts))  # Safe count.

    def read(self, name: str, **parameters: Any) -> Any:  # Read one owned cloud script.
        """Return one scripted cloud answer."""
        del parameters  # The script name defines the deterministic answer.
        logger.info("Read one E2E cloud script")  # Record the script read.
        record = self._scripts.get(name)  # An absent script returns an empty cloud list.
        result = deepcopy(record.get("value", [])) if record is not None else []  # Hide the ownership field.
        logger.debug("The E2E cloud script read found a record: %s", record is not None)  # Report no cloud data.
        return result  # Give the route an isolated answer.
