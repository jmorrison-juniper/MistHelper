"""Record the evidence of one operator journey through the upgrade capture portal.

Why:
    Issue #3200 asks for a screenshot at every step, the browser console
    errors, the failed requests, and the time of each step. One recorder class
    collects all of them, so every journey writes the same report shape and a
    reader can compare two journeys line by line.
"""

from __future__ import annotations

import hashlib  # Give two journeys with one safe name two folders.
import json  # Write the journey report as one JSON file.
import logging  # Record each step for the troubleshooting log.
import re  # Turn a step name into a safe file name.
import time  # Measure the wall time of each step.
from collections.abc import Callable  # Type the optional step action.
from dataclasses import asdict, dataclass, field  # Hold one step and one browser event as plain records.
from pathlib import Path  # Build Windows-compatible artifact paths.
from typing import Any  # The Playwright objects carry no stub types in this project.

logger = logging.getLogger(__name__)  # Keep the journey records under this module name.

# WHY: The repository root is four levels above this file. The artifacts stay
# under `data/`, which git ignores, so no screenshot reaches a commit.
REPO_ROOT = Path(__file__).parents[4]  # tests/e2e/upgrade_portal/journeys -> repository root.
ARTIFACT_ROOT = REPO_ROOT / "data" / "test-artifacts" / "upgrade-portal-journeys"  # One folder for all journeys.
NAVIGATION_TIMING = (  # Read the server time and the load time that the browser measured.
    "() => { const n = performance.getEntriesByType('navigation')[0];"
    " return n ? { ttfb: n.responseStart - n.requestStart, load: n.loadEventEnd } : null; }"
)
SAFE_NAME = re.compile(r"[^a-z0-9]+")  # Any run of other characters becomes one dash.
ERROR_STATUS = 400  # A response at or above this status is a failed request.


@dataclass(slots=True)
class JourneyStep:
    """One step of one journey, with its evidence."""

    number: int  # The position of the step, counted from one.
    name: str  # The short name of the step.
    url: str  # The page address after the step.
    seconds: float  # The wall time of the step action.
    screenshot: str  # The path of the full-page screenshot.
    ttfb_ms: float | None = None  # The server time of the last navigation, when the step navigated.


@dataclass(slots=True)
class JourneyEvents:
    """The browser events that one journey collected."""

    console_errors: list[str] = field(default_factory=list)  # Each console message of type error.
    page_errors: list[str] = field(default_factory=list)  # Each script fault that reached the page.
    failed_requests: list[str] = field(default_factory=list)  # Each request that got no answer.
    error_responses: list[str] = field(default_factory=list)  # Each answer with a status of 400 or more.


class JourneyRecorder:
    """Collect the screenshots, the events, and the timings of one journey."""

    def __init__(self, page: Any, journey: str) -> None:
        """Attach the event listeners and prepare the artifact folder.

        Args:
            page: The Playwright page that the journey drives.
            journey: The journey name. It names the artifact folder.
        """
        self.page = page  # The page that every step reads.
        digest = hashlib.sha1(journey.encode("utf-8"), usedforsecurity=False).hexdigest()[:6]  # Keep names unique.
        self.journey = f"{SAFE_NAME.sub('-', journey.lower()).strip('-')}-{digest}"  # A safe, unique folder name.
        self.folder = ARTIFACT_ROOT / self.journey  # One folder for each journey.
        self.folder.mkdir(parents=True, exist_ok=True)  # A second run of the same journey reuses the folder.
        self.steps: list[JourneyStep] = []  # The steps in the order that they ran.
        self.events = JourneyEvents()  # The browser events of the whole journey.
        self._attach()  # Listen before the first step, so no early event goes missing.
        logger.info("Journey %s records evidence in %s", self.journey, self.folder)  # Name the folder once.

    def _attach(self) -> None:
        """Attach one listener for each browser event kind."""
        self.page.on("console", self._console)  # Console messages of the page scripts.
        self.page.on("pageerror", lambda error: self.events.page_errors.append(str(error)))  # Script faults.
        self.page.on("requestfailed", lambda request: self.events.failed_requests.append(request.url))  # No answer.
        self.page.on("response", self._response)  # Every answer, so the recorder can keep the failed ones.

    def _console(self, message: Any) -> None:
        """Keep each console message of type error."""
        if message.type == "error":  # Warnings and logs describe no fault.
            self.events.console_errors.append(message.text)  # The text names the failed call.

    def _response(self, response: Any) -> None:
        """Keep each answer with a status of 400 or more."""
        if response.status >= ERROR_STATUS:  # Keep failed answers only, so the report stays short.
            self.events.error_responses.append(f"{response.status} {response.request.method} {response.url}")

    def step(self, name: str, action: Callable[[], Any] | None = None) -> JourneyStep:
        """Run one step, then take a full-page screenshot and read the timing.

        Args:
            name: The short name of the step.
            action: The step action. None records the page as it stands.

        Returns:
            The recorded step.
        """
        logger.info("Journey %s starts step %s", self.journey, name)  # Log before the action.
        started = time.perf_counter()  # The wall clock of the action alone.
        if action is not None:  # A step with no action records the current page.
            action()  # The journey code performs the operator action.
        seconds = round(time.perf_counter() - started, 3)  # Keep millisecond precision.
        number = len(self.steps) + 1  # Count the steps from one.
        path = self.folder / f"{number:02d}-{SAFE_NAME.sub('-', name.lower()).strip('-')}.png"  # The screenshot file.
        self.page.screenshot(path=str(path), full_page=True)  # The full page, so no section hides below the fold.
        timing = self.page.evaluate(NAVIGATION_TIMING) or {}  # The browser measure of the last navigation.
        ttfb = round(float(timing["ttfb"]), 1) if timing.get("ttfb") is not None else None  # Server time.
        recorded = JourneyStep(number, name, self.page.url, seconds, str(path), ttfb)  # Join the evidence.
        self.steps.append(recorded)  # Keep the step order.
        logger.debug("Journey %s step %s took %s s", self.journey, name, seconds)  # Log after the action.
        return recorded  # A caller may read the screenshot path.

    def finish(self, outcome: str = "passed") -> Path:
        """Write the JSON report of the journey.

        Args:
            outcome: The result that the test reached.

        Returns:
            The path of the report file.
        """
        report = {  # One record holds the whole journey.
            "journey": self.journey,
            "outcome": outcome,
            "steps": [asdict(step) for step in self.steps],
            "events": asdict(self.events),
        }
        path = self.folder / "journey.json"  # One report for each journey folder.
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")  # Readable by a person and a tool.
        logger.info("Journey %s wrote %s steps to %s", self.journey, len(self.steps), path)  # Log the result.
        return path  # The runner reads this file for the index page.
