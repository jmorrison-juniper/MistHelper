"""Shared harness that drives the MistHelper operations portal like a human."""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.parse
from datetime import UTC, datetime
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, TimeoutError, sync_playwright

PORTAL_URL = os.environ.get("PORTAL_HARNESS_BASE_URL", "http://127.0.0.1:8055")
ARTIFACT_ROOT = pathlib.Path("data/portal-test-artifacts")
SLOW_RUN_SECONDS = 45.0
RUN_TIMEOUT_SECONDS = 210.0
ROW_READY_SECONDS = 15.0
SELECT_READY_SECONDS = 30.0
TERMINAL_SERVER_STATES = {"completed", "failed"}
ACTIVE_SERVER_STATES = {"pending", "running"}
LOG_START_MARKER = "Output scan marks the run start"
LOG_WALK_MARKERS = ("Output scan reads /app/data for files the run wrote", "collects the files it wrote")
LOG_ASSESS_RE = re.compile(r"Assessing operation (?P<menu>\d+) result evidence")
TIMESTAMP_PATTERNS = (
    re.compile(r"(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?)"),
    re.compile(r"(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)"),
)
INTERNAL_FIELD_RE = re.compile(r"(^[a-z0-9_]+$|_id$|org_id|site_id|device_id)", re.IGNORECASE)


@dataclasses.dataclass(slots=True)
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


@dataclasses.dataclass(slots=True)
class Verdict:
    """The reconciled state for one operation run."""

    verdict: str
    server_state: str
    badge_state: str
    kind: str
    summary: str


@dataclasses.dataclass(slots=True)
class LogPhaseTiming:
    """Timing evidence parsed from the portal log."""

    handler_seconds: float | None = None
    walk_seconds: float | None = None
    error_lines: list[str] = dataclasses.field(default_factory=list)
    traceback_lines: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(slots=True)
class RunRecord:
    """Evidence captured for one operation journey."""

    category: str
    menu_number: str
    label: str
    verdict: str
    server_state: str
    badge_state: str
    total_seconds: float
    handler_seconds: float | None
    walk_seconds: float | None
    screenshots: dict[str, str]
    console_errors: list[str]
    failed_requests: list[dict[str, Any]]
    log_errors: list[str]
    traceback_lines: list[str]
    defects: list[dict[str, str]]
    run_id: str = ""
    browser: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return the record as JSON-ready data."""
        return dataclasses.asdict(self)


class DefectLog:
    """Collect defects and run records for one sweep shard."""

    def __init__(self, category: str, round_number: int) -> None:
        """Store the report identity and output path."""
        self.category = category
        self.round_number = round_number
        self.defects: list[Defect] = []
        self.records: list[RunRecord] = []
        self.path = ARTIFACT_ROOT / f"round{round_number}" / f"{slugify(category) or 'portal'}.json"

    def add(
        self, menu_number: str, kind: str, severity: str, summary: str, evidence: str, screenshot: str = ""
    ) -> None:
        """Record one defect against one operation."""
        self.defects.append(Defect(self.category, menu_number, kind, severity, summary, evidence, screenshot))
        print(f"    DEFECT [{severity}] #{menu_number} {kind}: {summary}", flush=True)

    def record(self, record: RunRecord) -> None:
        """Record one run and fold its defects into the shard."""
        self.records.append(record)
        for item in record.defects:
            self.add(
                str(item.get("menu_number", record.menu_number)),
                str(item.get("kind", "harness")),
                str(item.get("severity", "medium")),
                str(item.get("summary", "Harness defect")),
                str(item.get("evidence", "")),
                str(item.get("screenshot", "")),
            )

    def write(self) -> pathlib.Path:
        """Write the shard report and return its path."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "category": self.category,
            "round": self.round_number,
            "defect_count": len(self.defects),
            "defects": [defect.as_dict() for defect in self.defects],
            "runs": [record.as_dict() for record in self.records],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  wrote {self.path} ({len(self.defects)} defects, {len(self.records)} runs)", flush=True)
        return self.path


def slugify(value: str) -> str:
    """Return a safe artifact name for a human label."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def normalize_server_state(value: str) -> str:
    """Normalize the server run state for comparison."""
    lowered = (value or "").strip().lower()
    if lowered in {"complete", "completed", "success", "finished"}:
        return "completed"
    if lowered in {"error", "failed", "stopped"}:
        return "failed"
    if lowered in ACTIVE_SERVER_STATES:
        return lowered
    return "unknown"


def normalize_badge_state(value: str) -> str:
    """Normalize the visible badge state for comparison."""
    return normalize_server_state(value)


def reconcile_verdict(server_state: str, badge_text: str, run_started: bool = True) -> Verdict:
    """Return a verdict that is bound to the server run."""
    if not run_started:
        badge_state = normalize_badge_state(badge_text)
        return Verdict("did-not-start", "none", badge_state, "did-not-start", "No run_id was returned.")
    server = normalize_server_state(server_state)
    badge = normalize_badge_state(badge_text)
    if server in TERMINAL_SERVER_STATES and badge in TERMINAL_SERVER_STATES and server != badge:
        summary = f"Server state {server!r} does not match badge state {badge!r}."
        return Verdict("status-mismatch", server, badge, "status-mismatch", summary)
    if server in TERMINAL_SERVER_STATES:
        return Verdict(server, server, badge, "", "")
    return Verdict(server or "unknown", server, badge, "", "")


def classify_select_state(attached: bool, panel_open: bool, visible: bool) -> str:
    """Classify a row selection failure without browser access."""
    if not attached:
        return "absent"
    if attached and not panel_open:
        return "opening"
    if attached and panel_open and not visible:
        return "hidden"
    return "ready"


def parse_log_timestamp(line: str) -> datetime | None:
    """Read a timestamp from one log line when the log format provides one."""
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        stamp = match.group("stamp").replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(stamp, fmt)
            except ValueError:
                continue
    return None


def parse_log_phase_timing(lines: list[str], menu_number: str, started_at: datetime | None = None) -> LogPhaseTiming:
    """Parse handler time, file-walk time, and errors for one operation."""
    events: list[tuple[str, datetime, str]] = []
    for line in lines:
        stamp = parse_log_timestamp(line)
        if stamp is None or (started_at is not None and stamp < started_at):
            continue
        if LOG_START_MARKER in line:
            events.append(("start", stamp, line))
        if any(marker in line for marker in LOG_WALK_MARKERS):
            events.append(("walk", stamp, line))
        assess = LOG_ASSESS_RE.search(line)
        if assess and assess.group("menu") == str(menu_number):
            events.append(("assess", stamp, line))
    timing = _pair_log_events(events)
    start_stamp, end_stamp = _run_window(events)
    for line in lines:
        stamp = parse_log_timestamp(line)
        after_start = started_at is None or stamp is None or stamp >= started_at
        in_window = after_start and (
            start_stamp is None or stamp is None or start_stamp <= stamp <= (end_stamp or stamp)
        )
        if in_window and "ERROR" in line:
            timing.error_lines.append(line.strip())
        if in_window and "Traceback" in line:
            timing.traceback_lines.append(line.strip())
    return timing


def _pair_log_events(events: list[tuple[str, datetime, str]]) -> LogPhaseTiming:
    """Pair log events into handler and walk durations."""
    timing = LogPhaseTiming()
    for index, event in enumerate(events):
        if event[0] != "assess":
            continue
        walk = next((candidate for candidate in reversed(events[:index]) if candidate[0] == "walk"), None)
        start = next((candidate for candidate in reversed(events[:index]) if candidate[0] == "start"), None)
        if start and walk and start[1] <= walk[1] <= event[1]:
            timing.handler_seconds = round((walk[1] - start[1]).total_seconds(), 3)
            timing.walk_seconds = round((event[1] - walk[1]).total_seconds(), 3)
            return timing
    return timing


def _run_window(events: list[tuple[str, datetime, str]]) -> tuple[datetime | None, datetime | None]:
    """Return the best timestamp window for one parsed run."""
    for index, event in enumerate(events):
        if event[0] != "assess":
            continue
        start = next((candidate for candidate in reversed(events[:index]) if candidate[0] == "start"), None)
        if start:
            return start[1], event[1]
    return None, None


def read_container_log_tail() -> str:
    """Read the shared container log tail without changing the container."""
    command = ["podman", "exec", "misthelper-app", "sh", "-c", "tail -n 4000 /app/data/script.log"]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError) as error:
        return f"LOG_READ_ERROR: {error}"
    if result.returncode != 0:
        return f"LOG_READ_ERROR: {result.stderr.strip()}"
    return result.stdout


class PortalHarness:
    """Drive the operations page through a real browser."""

    def __init__(self, log: DefectLog, base_url: str = PORTAL_URL, headless: bool = True) -> None:
        """Store harness settings and empty evidence buffers."""
        self.log = log
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self.console_errors: list[str] = []
        self.failed_requests: list[dict[str, Any]] = []
        self.answered_notes: dict[str, list[str]] = {}
        self.browser_label = ""
        self._play = None
        self._browser = None
        self.page: Page | None = None
        self._panel: Locator | None = None
        self._category_name = ""

    def __enter__(self) -> PortalHarness:
        """Start a browser and load the operations page."""
        self._play = sync_playwright().start()
        self._browser = self._launch_browser()
        self.page = self._browser.new_page(viewport={"width": 1440, "height": 900})
        self.page.on("console", self._record_console)
        self.page.on("response", self._record_response)
        self.page.on("requestfailed", self._record_request_failure)
        self.page.goto(f"{self.base_url}/operations", wait_until="networkidle", timeout=60000)
        self.page.wait_for_selector("li[data-menu]", state="attached", timeout=30000)
        print(f"Portal harness browser: {self.browser_label}", flush=True)
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the browser even when a journey raised."""
        self._close_sse()
        if self.page:
            self.page.close()
        if self._browser:
            self._browser.close()
        if self._play:
            self._play.stop()

    def _launch_browser(self):
        """Launch the bundled browser or a local installed browser."""
        assert self._play is not None
        requested = os.environ.get("PORTAL_HARNESS_BROWSER_CHANNEL", "").strip()
        channels: list[str | None] = [requested] if requested else [None, "chrome", "msedge"]
        failures: list[str] = []
        for channel in channels:
            try:
                options: dict[str, Any] = {"headless": self.headless}
                if channel:
                    options["channel"] = channel
                browser = self._play.chromium.launch(**options)
                self.browser_label = channel or "bundled"
                return browser
            except PlaywrightError as error:
                failures.append(f"{channel or 'bundled'}: {str(error).splitlines()[0]}")
        raise RuntimeError("No Playwright browser launched. " + " | ".join(failures))

    def _record_console(self, message: Any) -> None:
        """Keep every console error, because a broken script can hide a control."""
        if message.type == "error":
            self.console_errors.append(message.text[:500])

    def _close_sse(self) -> None:
        """Close the page SSE stream so browser cleanup cannot hang."""
        if self.page is None:
            return
        try:
            self.page.evaluate(
                "() => { if (window.currentSSE) { window.currentSSE.close(); window.currentSSE = null; } }"
            )
        except PlaywrightError:
            return

    def _record_response(self, response: Any) -> None:
        """Keep each HTTP response with an error status."""
        if response.status >= 400:
            self.failed_requests.append({"status": response.status, "url": response.url})

    def _record_request_failure(self, request: Any) -> None:
        """Keep each network request that failed before a response."""
        self.failed_requests.append(
            {"status": "failed", "url": request.url, "error": str(request.failure or "request failed")}
        )

    def reset_run_buffers(self) -> None:
        """Clear evidence that belongs to one operation run."""
        self.console_errors.clear()
        self.failed_requests.clear()

    def shot(self, name: str) -> str:
        """Save a screenshot and return its path for the report."""
        safe = slugify(name) or "screenshot"
        path = ARTIFACT_ROOT / f"round{self.log.round_number}" / f"{safe}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        assert self.page is not None
        self.page.screenshot(path=str(path), full_page=True)
        return str(path)

    def open_category(self, category: str) -> bool:
        """Expand the panel whose heading names this category."""
        assert self.page is not None
        buttons = self.page.locator(".accordion-button")
        for index in range(buttons.count()):
            button = buttons.nth(index)
            heading = " ".join(button.inner_text().split())
            if not heading.startswith(category):
                continue
            self._category_name = category
            self._panel = self.page.locator(".accordion-item").nth(index)
            if "collapsed" in (button.get_attribute("class") or ""):
                button.click()
            self._panel.locator(".accordion-collapse").wait_for(state="visible", timeout=ROW_READY_SECONDS * 1000)
            return True
        self.log.add(
            "-",
            "missing",
            "high",
            f"Category '{category}' has no panel on the page",
            f"read {buttons.count()} headings",
        )
        return False

    def listed_numbers(self) -> list[str]:
        """Return the menu numbers this category renders, in render order."""
        if self._panel is None:
            return []
        rows = self._panel.locator("li[data-menu]")
        return [rows.nth(index).get_attribute("data-menu") or "" for index in range(rows.count())]

    def rendered_label(self, menu_number: str) -> str:
        """Return the text the page shows for one operation."""
        assert self.page is not None
        row = self.page.locator(f'li[data-menu="{menu_number}"]')
        return " ".join(row.first.inner_text().split()) if row.count() else ""

    def select_operation(self, menu_number: str) -> tuple[bool, str]:
        """Click one operation and classify the row reachability result."""
        assert self.page is not None
        row = self.page.locator(f'li[data-menu="{menu_number}"]')
        try:
            row.first.wait_for(state="attached", timeout=ROW_READY_SECONDS * 1000)
        except TimeoutError:
            return False, "absent"
        for _ in range(2):
            panel_open = bool(row.first.evaluate("node => !!node.closest('.accordion-collapse.show')"))
            if not panel_open:
                row.first.evaluate("node => node.closest('.accordion-item').querySelector('.accordion-button').click()")
            try:
                row.first.wait_for(state="visible", timeout=ROW_READY_SECONDS * 1000)
                row.first.click()
                self.page.locator("#selectedOp").wait_for(state="visible", timeout=ROW_READY_SECONDS * 1000)
                return True, "ready"
            except TimeoutError:
                panel_open = bool(row.first.evaluate("node => !!node.closest('.accordion-collapse.show')"))
                state = classify_select_state(True, panel_open, row.first.is_visible())
                if state != "opening":
                    return False, state
        return False, "hidden"

    def parameter_controls(self) -> list[str]:
        """Return a description of each visible parameter control."""
        assert self.page is not None
        found: list[str] = []
        for selector in ("select", "input[type=text]", "input[type=number]", "textarea"):
            controls = self.page.locator(f"#parameterFields {selector}")
            for index in range(controls.count()):
                control = controls.nth(index)
                if control.is_visible():
                    name = control.get_attribute("name") or control.get_attribute("id") or ""
                    found.append(f"{selector}:{name}")
        return found

    def fill_parameters(self, menu_number: str) -> tuple[bool, list[str]]:
        """Answer every required control, so the operation can actually run."""
        assert self.page is not None
        notes: list[str] = []
        answered_all = True
        selects = self.page.locator("#parameterFields select")
        for index in range(selects.count()):
            control = selects.nth(index)
            if not control.is_visible():
                continue
            name = control.get_attribute("name") or control.get_attribute("id") or f"select{index}"
            ready = self._wait_for_select_ready(control)
            options = control.locator("option")
            values = [options.nth(k).get_attribute("value") or "" for k in range(options.count())]
            real = [value for value in values if value.strip()]
            if not ready or not real:
                answered_all = False
                self.log.add(
                    menu_number,
                    "interactivity",
                    "high",
                    f"#{menu_number} asks for '{name}' and offers no choice",
                    f"ready={ready}, disabled={control.is_disabled()}, options={options.count()}",
                    self.shot(f"emptyselect-{menu_number}-{name}"),
                )
                continue
            label = options.nth(values.index(real[0])).inner_text().strip()
            if not label:
                self.log.add(
                    menu_number,
                    "readability",
                    "medium",
                    f"#{menu_number} lists a choice for '{name}' with no readable name",
                    f"value {real[0][:40]!r}",
                )
            control.select_option(real[0])
            self.page.wait_for_function("element => element.value !== ''", arg=control.element_handle(), timeout=5000)
            notes.append(f"{name}={label[:40] or real[0][:40]} ({len(real)} choices)")
        for selector, sample in (("input[type=text]", "1"), ("input[type=number]", "1"), ("textarea", "1")):
            inputs = self.page.locator(f"#parameterFields {selector}")
            for index in range(inputs.count()):
                control = inputs.nth(index)
                if not control.is_visible():
                    continue
                name = control.get_attribute("name") or control.get_attribute("id") or selector
                existing = control.input_value()
                if existing.strip():
                    notes.append(f"{name}={existing[:30]} (prefilled)")
                    continue
                control.fill(sample)
                notes.append(f"{name}={sample} (supplied)")
        return answered_all, notes

    def _wait_for_select_ready(self, control: Locator) -> bool:
        """Wait until a pick list is enabled and no longer shows a loading option."""
        assert self.page is not None
        deadline = time.monotonic() + SELECT_READY_SECONDS
        while time.monotonic() < deadline:
            if control.is_visible() and not control.is_disabled():
                first = control.locator("option").first
                text = first.inner_text().strip().lower() if first.count() else ""
                if "loading" not in text:
                    return True
            self.page.wait_for_timeout(250)
        return False

    def run_operation(self, menu_number: str, registry_description: str = "") -> RunRecord:
        """Run one operation and return full evidence for the reviewer."""
        assert self.page is not None
        self.reset_run_buffers()
        started = time.monotonic()
        log_started_at = datetime.now(UTC).replace(tzinfo=None)
        defects: list[dict[str, str]] = []
        screenshots: dict[str, str] = {}
        label = self.rendered_label(menu_number)
        selected, select_state = self.select_operation(menu_number)
        screenshots["selection"] = self.shot(f"menu-{menu_number}-selection")
        if not selected:
            defects.append(
                self._defect(
                    menu_number,
                    "usability",
                    "high",
                    f"#{menu_number} selection failed",
                    f"select_state={select_state}",
                    screenshots["selection"],
                )
            )
            return self._finish_record(
                menu_number, label, "unreachable", "none", "", started, screenshots, defects, "", log_started_at
            )
        self._check_readability(menu_number, registry_description, defects)
        run_button = self.page.locator("#runBtn")
        cli_state = self._check_cli_only(menu_number, label)
        if cli_state:
            return self._finish_record(
                menu_number, label, cli_state, "none", "", started, screenshots, defects, "", log_started_at
            )
        if run_button.count() == 0 or not run_button.first.is_visible():
            shot = self.shot(f"menu-{menu_number}-no-run-control")
            defects.append(
                self._defect(
                    menu_number,
                    "missing",
                    "high",
                    f"#{menu_number} offers no run control",
                    f"label: {label[:80]}",
                    shot,
                )
            )
            return self._finish_record(
                menu_number, label, "no-run-control", "none", "", started, screenshots, defects, "", log_started_at
            )
        if run_button.first.is_disabled():
            answered, notes = self.fill_parameters(menu_number)
            self.answered_notes[menu_number] = notes
            screenshots["filled"] = self.shot(f"menu-{menu_number}-filled")
            try:
                self.page.wait_for_function(
                    "element => !element.disabled", arg=run_button.first.element_handle(), timeout=5000
                )
            except TimeoutError:
                controls = self.parameter_controls()
                kind = "blocked-needs-input" if controls else "blocked-no-reason"
                if answered:
                    defects.append(
                        self._defect(
                            menu_number,
                            "interactivity",
                            "high",
                            f"#{menu_number} stays disabled after every control is answered",
                            "; ".join(notes)[:250],
                            screenshots["filled"],
                        )
                    )
                return self._finish_record(
                    menu_number, label, kind, "none", "", started, screenshots, defects, "", log_started_at
                )
        else:
            screenshots["filled"] = self.shot(f"menu-{menu_number}-filled")
        run_id, start_error = self._start_run(run_button.first)
        if not run_id:
            badge = self._badge_text()
            verdict = reconcile_verdict("none", badge, run_started=False)
            defects.append(
                self._defect(
                    menu_number,
                    verdict.kind,
                    "high",
                    f"#{menu_number} did not start",
                    start_error or verdict.summary,
                    screenshots.get("filled", ""),
                )
            )
            return self._finish_record(
                menu_number,
                label,
                verdict.verdict,
                verdict.server_state,
                verdict.badge_state,
                started,
                screenshots,
                defects,
                "",
                log_started_at,
            )
        server_state = self._poll_server_status(run_id)
        self._close_sse()
        badge_text = self._badge_text()
        screenshots["terminal"] = self.shot(f"menu-{menu_number}-terminal")
        verdict = reconcile_verdict(server_state, badge_text, run_started=True)
        if verdict.kind:
            defects.append(
                self._defect(
                    menu_number,
                    verdict.kind,
                    "high",
                    f"#{menu_number} status mismatch",
                    verdict.summary,
                    screenshots["terminal"],
                )
            )
        elapsed = time.monotonic() - started
        defects.extend(
            classify_terminal_defects(menu_number, label, verdict.verdict, elapsed, screenshots.get("terminal", ""))
        )
        return self._finish_record(
            menu_number,
            label,
            verdict.verdict,
            verdict.server_state,
            verdict.badge_state,
            started,
            screenshots,
            defects,
            run_id,
            log_started_at,
        )

    def _check_cli_only(self, menu_number: str, label: str) -> str:
        """Return the CLI-only state when the selected row intentionally hides Run."""
        assert self.page is not None
        cli_panel = self.page.locator("#cliOnlyPanel")
        if cli_panel.count() == 0 or not cli_panel.first.is_visible():
            return ""
        message = self.page.locator("#cliOnlyMessage")
        explanation = " ".join(message.first.inner_text().split()) if message.count() else ""
        if explanation:
            return "cli-only"
        self.log.add(
            menu_number,
            "usability",
            "medium",
            f"#{menu_number} hides the run control and gives no reason",
            f"label: {label[:70]}",
            self.shot(f"noreason-{menu_number}"),
        )
        return "cli-only-no-reason"

    def _start_run(self, run_button: Locator) -> tuple[str, str]:
        """Click Run and return the server run identifier."""
        assert self.page is not None
        try:
            with self.page.expect_response(
                lambda response: response.url.endswith("/api/operations/run") and response.request.method == "POST",
                timeout=15000,
            ) as response_info:
                run_button.click()
            response = response_info.value
            data = response.json()
        except (TimeoutError, PlaywrightError, ValueError) as error:
            return "", f"run response was not captured: {error}"
        if response.status >= 400:
            return "", f"run request returned {response.status}: {data}"
        run_id = str(data.get("run_id", ""))
        if not run_id:
            return "", f"run response did not include run_id: {data}"
        return run_id, ""

    def _poll_server_status(self, run_id: str) -> str:
        """Poll the status API until the run reaches a terminal state."""
        assert self.page is not None
        status_url = f"{self.base_url}/api/operations/status/{urllib.parse.quote(run_id)}"
        deadline = time.monotonic() + RUN_TIMEOUT_SECONDS
        last_state = "unknown"
        while time.monotonic() < deadline:
            answer = self.page.context.request.get(status_url, timeout=10000)
            if answer.status >= 400:
                return "unknown"
            payload = answer.json()
            last_state = str(payload.get("status", "unknown"))
            if normalize_server_state(last_state) in TERMINAL_SERVER_STATES:
                return last_state
            self.page.wait_for_timeout(1000)
        return last_state if last_state != "unknown" else "timeout"

    def _badge_text(self) -> str:
        """Return the visible status badge text."""
        assert self.page is not None
        badge = self.page.locator("#statusBadge")
        return " ".join(badge.first.inner_text().split()) if badge.count() else ""

    def _check_readability(self, menu_number: str, registry_description: str, defects: list[dict[str, str]]) -> None:
        """Check visible text for labels, internal names, and truncation."""
        assert self.page is not None
        label = self.rendered_label(menu_number)
        if registry_description and registry_description not in label:
            defects.append(
                self._defect(
                    menu_number,
                    "readability",
                    "medium",
                    f"#{menu_number} row label differs from registry",
                    f"row={label[:120]!r}, registry={registry_description[:120]!r}",
                )
            )
        controls = self.page.locator("#parameterFields select, #parameterFields input, #parameterFields textarea")
        for index in range(controls.count()):
            control = controls.nth(index)
            if not control.is_visible():
                continue
            label_text = self._control_label(control)
            name = control.get_attribute("name") or control.get_attribute("id") or ""
            if not label_text:
                defects.append(
                    self._defect(
                        menu_number,
                        "readability",
                        "medium",
                        f"#{menu_number} has a control with no label",
                        f"control={name}",
                    )
                )
            elif INTERNAL_FIELD_RE.search(label_text) and label_text == name:
                defects.append(
                    self._defect(
                        menu_number,
                        "readability",
                        "medium",
                        f"#{menu_number} exposes an internal field name",
                        f"label={label_text!r}",
                    )
                )
        for selector in ("#parameterFields label", "#statusBadge", "#resultsHead th"):
            self._check_truncated_text(menu_number, selector, defects)

    def _control_label(self, control: Locator) -> str:
        """Return the visible label associated with a control."""
        control_id = control.get_attribute("id") or ""
        assert self.page is not None
        if control_id:
            label = self.page.locator(f'label[for="{control_id}"]')
            if label.count():
                return " ".join(label.first.inner_text().split())
        script = (
            "node => { const label = node.closest('.mb-3, .form-group, div')"
            "?.querySelector('label'); return label ? label.innerText.trim() : ''; }"
        )
        return control.evaluate(script)

    def _check_truncated_text(self, menu_number: str, selector: str, defects: list[dict[str, str]]) -> None:
        """Record a defect for visible text that is horizontally truncated."""
        assert self.page is not None
        items = self.page.locator(selector)
        for index in range(items.count()):
            item = items.nth(index)
            if item.is_visible() and item.evaluate("node => node.scrollWidth > node.clientWidth"):
                text = " ".join(item.inner_text().split())
                defects.append(
                    self._defect(
                        menu_number,
                        "readability",
                        "medium",
                        f"#{menu_number} truncates visible text",
                        f"selector={selector}, text={text[:120]!r}",
                    )
                )

    def _finish_record(
        self,
        menu_number: str,
        label: str,
        verdict: str,
        server_state: str,
        badge_state: str,
        started: float,
        screenshots: dict[str, str],
        defects: list[dict[str, str]],
        run_id: str = "",
        log_started_at: datetime | None = None,
    ) -> RunRecord:
        """Build the final evidence record for one run."""
        if "terminal" not in screenshots and self.page is not None:
            screenshots["terminal"] = self.shot(f"menu-{menu_number}-terminal")
        elapsed = round(time.monotonic() - started, 2)
        log_text = read_container_log_tail()
        log_timing = parse_log_phase_timing(log_text.splitlines(), menu_number, log_started_at)
        record = RunRecord(
            category=self._category_name or self.log.category,
            menu_number=str(menu_number),
            label=label[:160],
            verdict=verdict,
            server_state=server_state,
            badge_state=badge_state,
            total_seconds=elapsed,
            handler_seconds=log_timing.handler_seconds,
            walk_seconds=log_timing.walk_seconds,
            screenshots=screenshots,
            console_errors=list(self.console_errors),
            failed_requests=list(self.failed_requests),
            log_errors=log_timing.error_lines,
            traceback_lines=log_timing.traceback_lines,
            defects=defects,
            run_id=run_id,
            browser=self.browser_label,
        )
        self.log.record(record)
        return record

    def _defect(
        self, menu_number: str, kind: str, severity: str, summary: str, evidence: str, screenshot: str = ""
    ) -> dict[str, str]:
        """Build a JSON-ready defect with the current category."""
        return Defect(
            self._category_name or self.log.category, str(menu_number), kind, severity, summary, evidence, screenshot
        ).as_dict()


def classify_terminal_defects(
    menu_number: str, label: str, verdict: str, elapsed: float, screenshot: str = ""
) -> list[dict[str, str]]:
    """Return defects implied by a terminal verdict and elapsed time."""
    defects: list[dict[str, str]] = []
    if verdict in {"timeout", "pending", "running", "unknown"}:
        defects.append(
            Defect(
                "",
                str(menu_number),
                "performance",
                "high",
                f"#{menu_number} did not reach a terminal state",
                f"elapsed {elapsed:.1f}s, label: {label[:80]}",
                screenshot,
            ).as_dict()
        )
    elif verdict == "failed":
        defects.append(
            Defect(
                "",
                str(menu_number),
                "runtime",
                "high",
                f"#{menu_number} reported a failure",
                f"elapsed {elapsed:.1f}s, label: {label[:80]}",
                screenshot,
            ).as_dict()
        )
    if elapsed > SLOW_RUN_SECONDS and verdict not in {"timeout", "pending", "running", "unknown"}:
        defects.append(
            Defect(
                "",
                str(menu_number),
                "performance",
                "medium",
                f"#{menu_number} took {elapsed:.1f}s to finish",
                f"state {verdict}, label: {label[:80]}",
                screenshot,
            ).as_dict()
        )
    return defects
