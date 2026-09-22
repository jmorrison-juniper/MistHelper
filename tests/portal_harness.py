"""Shared harness that drives the MistHelper operations portal like a human.

Why this exists:
    The portal protects every write with a CSRF token that only a real browser
    session carries, so an agent cannot exercise an operation through a raw HTTP
    call. Every journey below therefore runs through the rendered page.

What one journey records:
    The rendered label, the parameter controls the page offers, the time the run
    takes, the terminal state, and the readable shape of the result. A defect is
    any gap between what the page promises and what it delivers.

Page facts this harness relies on, measured on 2026-09-21:
    The page renders 18 `.accordion-item` panels, one for each category, in the
    same order the API returns. Each panel holds its own `li[data-menu]` rows.
    Those rows exist in the DOM while the panel is collapsed, so a wait must ask
    for the attached state rather than the visible state. The run control is
    `#runBtn`.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import time
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright

PORTAL_URL = "http://127.0.0.1:8055"
ARTIFACT_ROOT = pathlib.Path("data/portal-test-artifacts")

# A run that passes this bound is reported as a performance defect. An operator
# abandons a page long before the hard timeout below.
SLOW_RUN_SECONDS = 45.0
RUN_TIMEOUT_SECONDS = 210.0


@dataclasses.dataclass
class Defect:
    """One operator-facing problem found during a journey."""

    category: str
    menu_number: str
    kind: str
    severity: str
    summary: str
    evidence: str
    screenshot: str = ""

    def as_dict(self) -> dict[str, str]:
        """Return the defect as a plain record for the report file."""
        return dataclasses.asdict(self)


class DefectLog:
    """Collect defects and timings for one category, then write them to disk."""

    def __init__(self, category: str, round_number: int) -> None:
        # Name the category so several agents write without colliding.
        self.category = category
        self.round_number = round_number
        self.defects: list[Defect] = []
        self.timings: list[dict[str, Any]] = []
        slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        self.path = ARTIFACT_ROOT / f"round{round_number}" / f"{slug}.json"

    def add(
        self,
        menu_number: str,
        kind: str,
        severity: str,
        summary: str,
        evidence: str,
        screenshot: str = "",
    ) -> None:
        """Record one defect against one operation."""
        self.defects.append(Defect(self.category, menu_number, kind, severity, summary, evidence, screenshot))
        print(f"    DEFECT [{severity}] #{menu_number} {kind}: {summary}")

    def time(self, menu_number: str, label: str, seconds: float, state: str) -> None:
        """Record how long one run took and how it ended."""
        self.timings.append(
            {
                "menu_number": menu_number,
                "label": label,
                "seconds": round(seconds, 2),
                "state": state,
            }
        )

    def write(self) -> pathlib.Path:
        """Write the report and return its path."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "category": self.category,
            "round": self.round_number,
            "defect_count": len(self.defects),
            "defects": [d.as_dict() for d in self.defects],
            "timings": self.timings,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  wrote {self.path} ({len(self.defects)} defects, {len(self.timings)} timings)")
        return self.path


class PortalHarness:
    """Drive the operations page through a real browser."""

    def __init__(self, log: DefectLog, headless: bool = True) -> None:
        # Hold the log so every journey records into one report.
        self.log = log
        self.headless = headless
        self.console_errors: list[str] = []
        self._play = None
        self._browser = None
        self.page: Page | None = None
        self._panel: Locator | None = None

    def __enter__(self) -> PortalHarness:
        """Start a browser and load the operations page."""
        self._play = sync_playwright().start()
        self._browser = self._play.chromium.launch(headless=self.headless)
        self.page = self._browser.new_page(viewport={"width": 1440, "height": 900})
        self.page.on("console", self._record_console)
        self.page.goto(f"{PORTAL_URL}/operations", wait_until="networkidle", timeout=60000)
        # The rows render collapsed, so ask for attachment, not visibility.
        self.page.wait_for_selector("li[data-menu]", state="attached", timeout=30000)
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the browser even when a journey raised."""
        if self._browser:
            self._browser.close()
        if self._play:
            self._play.stop()

    def _record_console(self, message: Any) -> None:
        """Keep every console error, because a broken script hides no message."""
        if message.type == "error":
            self.console_errors.append(message.text[:200])

    def shot(self, name: str) -> str:
        """Save a screenshot and return its path for the report."""
        safe = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        path = ARTIFACT_ROOT / f"round{self.log.round_number}" / f"{safe}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        assert self.page is not None
        self.page.screenshot(path=str(path))
        return str(path)

    def open_category(self, category: str) -> bool:
        """Expand the panel whose heading names this category."""
        assert self.page is not None
        buttons = self.page.locator(".accordion-button")
        for index in range(buttons.count()):
            heading = " ".join(buttons.nth(index).inner_text().split())
            if heading.startswith(category):
                buttons.nth(index).click()
                self.page.wait_for_timeout(500)
                self._panel = self.page.locator(".accordion-item").nth(index)
                return True
        self.log.add(
            "-",
            "missing",
            "high",
            f"Category '{category}' has no panel on the page",
            f"read {buttons.count()} accordion headings and none started with the name",
        )
        return False

    def listed_numbers(self) -> list[str]:
        """Return the menu numbers this category renders, in render order."""
        panel = self._panel
        if panel is None:
            return []
        rows = panel.locator("li[data-menu]")
        return [rows.nth(i).get_attribute("data-menu") or "" for i in range(rows.count())]

    def rendered_label(self, menu_number: str) -> str:
        """Return the text the page shows for one operation."""
        assert self.page is not None
        row = self.page.locator(f'li[data-menu="{menu_number}"]')
        return " ".join(row.first.inner_text().split()) if row.count() else ""

    def declared_category(self, menu_number: str) -> str:
        """Return the safety category the row carries."""
        assert self.page is not None
        row = self.page.locator(f'li[data-menu="{menu_number}"]')
        if row.count() == 0:
            return ""
        return row.first.get_attribute("data-category") or ""

    def select_operation(self, menu_number: str) -> bool:
        """Click one operation and report whether the row responded."""
        assert self.page is not None
        row = self.page.locator(f'li[data-menu="{menu_number}"]')
        if row.count() == 0:
            self.log.add(
                menu_number,
                "missing",
                "high",
                f"Operation #{menu_number} is not present on the page",
                "li[data-menu] selector found no element",
            )
            return False
        if not row.first.is_visible():
            self.log.add(
                menu_number,
                "usability",
                "medium",
                f"Operation #{menu_number} stays hidden after its category opened",
                "row is attached but not visible",
            )
            return False
        row.first.click()
        self.page.wait_for_timeout(600)
        return True

    def parameter_controls(self) -> list[str]:
        """Return a description of each visible parameter control."""
        assert self.page is not None
        found: list[str] = []
        for selector in ("select", "input[type=text]", "input[type=number]", "textarea"):
            controls = self.page.locator(selector)
            for index in range(controls.count()):
                control = controls.nth(index)
                if not control.is_visible():
                    continue
                name = control.get_attribute("name") or control.get_attribute("id") or ""
                if name in ("", "themeSelect"):
                    continue
                found.append(f"{selector}:{name}")
        return found

    def run_operation(self, menu_number: str) -> str:
        """Run one operation and return its terminal state."""
        assert self.page is not None
        if not self.select_operation(menu_number):
            return "unreachable"

        label = self.rendered_label(menu_number)
        run_button = self.page.locator("#runBtn")
        if run_button.count() == 0 or not run_button.first.is_visible():
            self.log.add(
                menu_number,
                "missing",
                "high",
                f"#{menu_number} offers no run control after selection",
                f"rendered label: {label[:80]}",
                self.shot(f"norun-{menu_number}"),
            )
            return "no-run-control"

        if run_button.first.is_disabled():
            # A disabled control is correct when a required answer is missing.
            controls = self.parameter_controls()
            self.log.time(menu_number, label[:70], 0.0, "blocked")
            return "blocked-needs-input" if controls else "blocked-no-reason"

        started = time.monotonic()
        run_button.first.click()

        state = "unknown"
        deadline = started + RUN_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            body = self.page.inner_text("body").lower()
            if "completed" in body or "finished" in body:
                state = "completed"
                break
            if "failed" in body or "traceback" in body:
                state = "failed"
                break
            self.page.wait_for_timeout(1000)
        else:
            state = "timeout"

        elapsed = time.monotonic() - started
        self.log.time(menu_number, label[:70], elapsed, state)

        if state == "timeout":
            self.log.add(
                menu_number,
                "performance",
                "high",
                f"#{menu_number} did not reach a terminal state in {RUN_TIMEOUT_SECONDS:.0f}s",
                f"label: {label[:80]}",
                self.shot(f"timeout-{menu_number}"),
            )
        elif state == "failed":
            self.log.add(
                menu_number,
                "runtime",
                "high",
                f"#{menu_number} reported a failure",
                f"elapsed {elapsed:.1f}s, label: {label[:80]}",
                self.shot(f"failed-{menu_number}"),
            )
        elif elapsed > SLOW_RUN_SECONDS:
            self.log.add(
                menu_number,
                "performance",
                "medium",
                f"#{menu_number} took {elapsed:.1f}s to finish",
                f"state {state}, label: {label[:80]}",
            )

        return state
