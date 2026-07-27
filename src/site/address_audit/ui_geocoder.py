"""Tier-3 Mist-dashboard UI geocoder (feature 1003-site-address-audit).

The Mist site-settings "Location Search" field is a Google Places Autocomplete
widget ("powered by Google"). Typing ``"{business} {address}"`` returns the
suite/unit-corrected retail address the operator sees by hand. This module
drives that field through a real browser and reads back the top suggestion --
WITHOUT ever committing a change (read-only audit).

Three connection modes (all proven to work behind Zscaler SSL inspection, where
Playwright CANNOT download its own Chromium):

  * ``auto`` (default) -- take over an already-running debuggable browser if one
    is present; otherwise spawn a debuggable Edge for the operator, wait for them
    to log into Mist and open a site's settings page, then take it over. This is
    the zero-setup path: the operator never has to start Edge with debug flags.

  * ``attach`` -- take over an already-running, already logged-in browser via the
    Chrome DevTools Protocol. The operator starts a debuggable browser (see
    ``spawn_debuggable_browser``) and logs into Mist once; we reuse that live SSO
    session. No bundled browser download, no stored credentials.

  * ``launch`` -- Playwright launches the system Edge channel
    (``channel="msedge"``, no download) non-headless and pauses for the
    operator to log in interactively before the first lookup.

Selector capture / re-capture procedure (OQ-002 -- the dashboard DOM is NOT
contract-stable):
  1. Selectors are centralized as the dated constants below.
  2. To re-capture: open the Mist site-edit page in a browser, inspect the
     Location Search input and the Google suggestion list, update the constants,
     and re-run the Tier-3 e2e test.
  3. We anchor on Google's own ``.pac-target-input`` / ``.pac-item`` classes,
     which are far more stable than Mist's surrounding markup.

Playwright is an OPTIONAL dependency (declared in ``pyproject.toml`` dev group,
not in ``requirements.txt``). If it is absent the class degrades gracefully:
``is_available()`` returns ``False`` and every lookup returns ``None`` instead
of raising, so the audit still completes on its Tier-1/Tier-2 results.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # Filesystem probing for the Edge executable.
import re  # House-number extraction + suggestion cleanup (defeats the autocomplete lag race).
import secrets  # Unpredictable RNG source for human-like typing jitter (lint-clean, not security-critical).
import shutil  # PATH lookup fallback for the Edge executable.
import subprocess  # Spawn a debuggable browser for CDP takeover.
import tempfile  # Dedicated throwaway profile for the spawned browser.
import time  # Politeness delay between Google Places lookups.
from typing import Any  # Loose typing for Playwright handles (kept import-light).

from src.site.address_audit.models import ResolverResult, UIGeocoderConfig  # Shared dataclasses.
from src.site.address_audit.perf import PhaseTimer  # Per-phase timing to expose slow sub-steps.
from src.site.address_audit.suite_patterns import HASH_UNIT_PATTERN, SUITE_PHRASE_PATTERN  # Shared suite regexes.
from src.utils.input_utils import InputUtils  # EOF-safe operator prompts.

try:  # Optional dependency: Playwright may not be installed in every environment.
    from playwright.sync_api import sync_playwright  # Sync browser-automation entry point.
except ImportError:  # pragma: no cover -- exercised only on hosts without Playwright.
    sync_playwright = None  # type: ignore[assignment]  # Sentinel; is_available() keys off this.

_KEY_JITTER = secrets.SystemRandom()  # Per-keystroke delay source; unpredictable cadence dodges bot heuristics.
_THINKING_PAUSE_EVERY = 7  # Add an occasional longer "thinking" pause every N characters while typing.
_SUITE_GRACE_S = 2.0  # Extra seconds (after the house number matches) to let a typed suite/unit land in the dropdown.
_POLL_INTERVAL_MS = 200  # WHY: cooperative pause between suggestion-list re-reads while waiting for a fresh row.
_CLEAR_SETTLE_MS = 150  # WHY: brief pause after clearing the field so Google tears down the stale dropdown.
_LOCATE_TIMEOUT_FLOOR_MS = 1000  # WHY: minimum per-selector budget when splitting the locate timeout across candidates.
_DEFAULT_CDP_PORT = 9222  # WHY: standard Chrome/Edge remote-debugging port when the endpoint carries no digits.
_DASHBOARD_URL_DEFAULT = "https://manage.mist.com/"  # WHY: default landing page when spawning a debuggable browser.
_EDGE_EXE_NAME = "msedge.exe"  # WHY: Windows Edge binary name probed under both ProgramFiles roots.
_EDGE_INSTALL_TAIL = (
    "Microsoft",
    "Edge",
    "Application",
    _EDGE_EXE_NAME,
)  # WHY: path tail under each ProgramFiles root.
_PROFILE_PREFIX = "misthelper-edge-"  # WHY: throwaway profile dir prefix so we never touch the operator's real profile.

# --- Selector constants (captured 2026-06-29; re-verify if the Mist dashboard UI changes) ---
# Google Places Autocomplete attaches ``pac-target-input`` to the bound input and
# renders suggestions in a ``.pac-container`` of ``.pac-item`` rows. These Google
# classes are stable across sites, so we anchor on them rather than Mist's markup.
INPUT_SELECTORS: tuple[str, ...] = (
    "input.pac-target-input",  # Google's own class on autocomplete-bound inputs (most stable).
    "input[placeholder*='Location Search']",  # Mist's placeholder text from the site-settings screen.
    "input[placeholder*='Location']",  # Looser placeholder fallback.
)
PAC_ITEM_SELECTOR: str = ".pac-container .pac-item"  # Each Google suggestion row in the dropdown.


class MistUIGeocoder:
    """Drive the Mist site-settings Location Search field via a real browser.

    Lifecycle: ``connect()`` -> one or more ``geocode_via_ui(query)`` -> ``close()``.
    All failures are logged and swallowed (return ``None``) so a single flaky
    lookup never aborts the surrounding audit loop (fail-soft, OQ-002).
    """

    def __init__(self, config: UIGeocoderConfig | None = None, perf: PhaseTimer | None = None) -> None:
        """Store configuration and initialize all browser-handle state."""
        self._config = config or UIGeocoderConfig()  # Caller config or Zscaler-safe defaults.
        self._perf = perf or PhaseTimer()  # Timing sink (own no-op timer when the caller passes none).
        self._playwright: Any = None  # Playwright driver handle (set on connect()).
        self._browser: Any = None  # Browser or CDP-attached browser handle.
        self._context: Any = None  # Active browser context (operator session or fresh).
        self._connected: bool = False  # Whether a usable browser is attached.
        self._spawned_proc: Any = None  # Popen handle when we spawned a debuggable Edge (auto mode).
        self._lookups_done: int = 0  # Counter enforcing the per-run max-lookups cap.
        logging.debug("MistUIGeocoder initialized (mode=%s)", self._config.connect_mode)  # Trace init.

    def is_available(self) -> bool:
        """Return True only when the optional Playwright dependency is importable."""
        available = sync_playwright is not None  # Sentinel set at import time.
        logging.debug("MistUIGeocoder.is_available -> %s", available)  # Trace capability check.
        return available  # Callers gate Tier-3 on this before connect().

    def connect(self) -> bool:
        """Establish the browser per ``connect_mode``; return success (never raises)."""
        if not self.is_available():  # Playwright missing -> Tier-3 is simply unavailable.
            logging.warning("Playwright not installed; Tier-3 UI geocoding unavailable")  # Inform operator.
            return False  # Audit continues on Tier-1/Tier-2 results.
        logging.info("Connecting browser in '%s' mode", self._config.connect_mode)  # Action-log start.
        try:
            self._playwright = sync_playwright().start()  # Start the Playwright driver process.
            ok = self._dispatch_connect()  # Branch to attach/launch.
            self._connected = ok  # Record state for the geocode_via_ui guard.
            logging.debug("Browser connect result=%s", ok)  # Action-log outcome.
            return ok  # True when a usable context was established.
        except Exception as exc:  # noqa: BLE001 -- never crash the audit on connect failure.
            logging.warning("Browser connect failed: %s", exc)  # Surface the cause.
            self.close()  # Tidy any partially started driver/browser.
            return False  # Signal Tier-3 unavailable for this run.

    def _dispatch_connect(self) -> bool:
        """Route to the auto, attach, or launch connection strategy."""
        mode = self._config.connect_mode  # Operator-selected strategy (default "auto").
        if mode == "attach":  # Take over an already-running debuggable browser (no spawn).
            return self._connect_attach()  # Reuse the operator's live SSO session.
        if mode == "launch":  # Let Playwright launch a fresh system Edge.
            return self._connect_launch()  # Interactive-login flow.
        return self._connect_auto()  # Default: take over if possible, else spawn one for the operator.

    def _connect_auto(self) -> bool:
        """Take over a debuggable browser if present; otherwise spawn one and take it over."""
        if self._try_attach():  # A debuggable browser is already running -> reuse it.
            return True  # Attached to the operator's existing session.
        logging.info("No debuggable browser found; spawning one for login")  # Action-log the spawn path.
        proc = MistUIGeocoder.spawn_debuggable_browser(self._cdp_port(), self._config.dashboard_url)  # Spawn Edge.
        if proc is None:  # Edge not installed -> fall back to a Playwright launch.
            logging.info("Edge unavailable to spawn; falling back to launch mode")  # Inform operator.
            return self._connect_launch()  # Last-resort interactive launch.
        self._spawned_proc = proc  # Own the spawned browser's lifecycle (terminated on close()).
        self._await_spawn_login()  # Block until the operator logs in and opens a site settings page.
        return self._try_attach()  # Now take over the spawned, logged-in browser over CDP.

    def _try_attach(self) -> bool:
        """Attempt a CDP takeover without raising (used by the auto strategy)."""
        try:
            return self._connect_attach()  # Reuse the standard takeover path.
        except Exception as exc:  # noqa: BLE001 -- a missing endpoint is expected in auto mode.
            logging.info("CDP takeover at %s not available yet: %s", self._config.cdp_endpoint, exc)  # Trace.
            return False  # Signal "no debuggable browser" so the caller can spawn one.

    def _cdp_port(self) -> int:
        """Parse the TCP port from the configured CDP endpoint (default 9222)."""
        tail = self._config.cdp_endpoint.rsplit(":", 1)[-1]  # Text after the final colon.
        digits = "".join(ch for ch in tail if ch.isdigit())  # Keep only the numeric run.
        return int(digits) if digits else _DEFAULT_CDP_PORT  # WHY: parsed port or the documented default.

    def _await_spawn_login(self) -> None:
        """Block until the operator has logged in and opened a site's Location Search page."""
        InputUtils.safe_input(  # Pause the run until the operator confirms readiness.
            "A browser opened. Log into Mist, open a SITE's settings page so the "
            "'Location Search' box is visible, then press Enter to continue: ",
            context="ui_geocoder_spawn_login",
        )
        logging.info("Operator confirmed spawned-browser login; taking over via CDP")  # Action-log gate pass.

    def _connect_attach(self) -> bool:
        """Take over a debuggable browser over CDP and reuse its first context."""
        endpoint = self._config.cdp_endpoint  # DevTools URL of the operator's browser.
        logging.info("Attaching over CDP at %s", endpoint)  # Action-log the takeover target.
        self._browser = self._playwright.chromium.connect_over_cdp(endpoint)  # Attach to the session.
        if not self._browser.contexts:  # A debuggable browser should expose >=1 context.
            logging.warning("No browser context found at CDP endpoint %s", endpoint)  # Nothing to drive.
            return False  # Cannot proceed without a context.
        self._context = self._browser.contexts[0]  # Reuse the operator's context (cookies/SSO intact).
        logging.debug("CDP attach succeeded; %d context(s) present", len(self._browser.contexts))  # Trace.
        return True  # Ready to geocode against the operator's logged-in tab.

    def _connect_launch(self) -> bool:
        """Launch the system Edge channel and pause for interactive login."""
        channel = self._config.browser_channel  # System channel (msedge) -- no Chromium download needed.
        logging.info("Launching system browser channel '%s'", channel)  # Action-log launch.
        self._browser = self._playwright.chromium.launch(channel=channel, headless=self._config.headless)  # Open.
        self._context = self._browser.new_context()  # Fresh context for the interactive session.
        self._await_interactive_login()  # Block until the operator authenticates to Mist.
        logging.debug("Launch-mode context ready after interactive login")  # Trace readiness.
        return True  # Ready to geocode.

    def _await_interactive_login(self) -> None:
        """Open the dashboard and block until the operator confirms login."""
        page = self._context.new_page()  # Tab for the operator to authenticate in.
        timeout_ms = int(self._config.per_lookup_timeout_s * 1000)  # Playwright navigation uses milliseconds.
        page.goto(self._config.dashboard_url, timeout=timeout_ms)  # Navigate to the Mist login/landing page.
        InputUtils.safe_input(  # Pause the run until the operator says they are in.
            "Log into the Mist dashboard in the opened browser, then press Enter to continue: ",
            context="ui_geocoder_login",
        )
        logging.info("Operator confirmed dashboard login; proceeding with UI geocoding")  # Action-log gate pass.

    def ensure_location_field_ready(self, max_prompts: int = 3) -> bool:
        """Probe for the Location Search field; guide the operator until it appears (fail-soft).

        Tier-3 can only read Google's suggestions when the active tab is on a page
        that renders the Location Search input. We probe, and if it is missing we
        ask the operator to open a site's settings page, retrying a few times.
        """
        if not self._connected:  # Nothing to probe without a connection.
            return False  # Caller already handled the disconnected case.
        for attempt in range(1, max_prompts + 1):  # Bounded retries so we never loop forever.
            page = self._active_page()  # Current tab in the operator's context.
            if page is not None and self._field_present(page):  # Location Search input is visible.
                logging.info("Location Search field detected on attempt %d; Tier-3 ready", attempt)  # Ready.
                return True  # Proceed to the per-row lookups.
            InputUtils.safe_input(  # Guide the operator to the correct page, then re-probe.
                "Could not see the 'Location Search' box. In the browser, open a "
                "SITE's settings page where that box is visible, then press Enter: ",
                context="ui_geocoder_navigate",
            )
        logging.info("Location Search field not found after %d prompts; Tier-3 will fail-soft", max_prompts)
        return False  # Lookups will return None; the audit still completes on Tier 1/2.

    def _field_present(self, page: Any) -> bool:
        """Return True when any Location Search input selector matches on ``page``."""
        for selector in INPUT_SELECTORS:  # Probe each candidate selector quickly.
            try:
                if page.query_selector(selector) is not None:  # Immediate (non-waiting) DOM probe.
                    return True  # Found the autocomplete input.
            except Exception as exc:  # noqa: BLE001 -- a transient DOM error must not abort the probe.
                logging.debug("Field probe error for %s: %s", selector, exc)  # Trace and keep probing.
        return False  # No candidate matched on the current page.

    def geocode_via_ui(self, query: str) -> ResolverResult | None:
        """Resolve one address via the dashboard autocomplete; fail-soft to ``None``."""
        if not self._connected:  # Guard: connect() must succeed first.
            logging.warning("geocode_via_ui called before a successful connect(); returning None")  # Misuse.
            return None  # Nothing to drive.
        if self._lookups_done >= self._config.max_lookups:  # Respect the per-run cap.
            logging.warning("UI geocode cap reached (%d); skipping lookup", self._config.max_lookups)  # Capped.
            return None  # Row falls back to its Tier-1/Tier-2 outcome.
        self._lookups_done += 1  # Count this attempt against the cap.
        logging.info("UI geocode lookup %d for query: %s", self._lookups_done, query)  # Action-log start.
        try:
            page = self._active_page()  # Obtain a usable browser tab.
            if page is None:  # No context/page -> cannot proceed.
                return None  # Fail soft.
            suggestions = self._perform_lookup(page, query)  # Type the query and read suggestions.
            with self._perf.phase("ui.politeness"):  # Time the fixed >=1 req/sec courtesy delay.
                time.sleep(self._config.politeness_delay_s)  # >=1 req/sec politeness toward Google.
            return self._build_result(query, suggestions)  # Convert suggestions to a ResolverResult.
        except Exception as exc:  # noqa: BLE001 -- fail soft per OQ-002.
            logging.warning("UI geocode failed for query '%s': %s", query, exc)  # Log and continue.
            return None  # One flaky lookup must not abort the audit.

    def _active_page(self) -> Any:
        """Return a usable page from the active context, or ``None``."""
        if self._context is None:  # No context established.
            logging.debug("No active context for UI geocoding")  # Trace the miss.
            return None  # Caller treats as fail-soft.
        pages = self._context.pages  # Existing tabs in the context.
        if pages:  # Reuse the operator's current tab (attach mode) when present.
            return pages[0]  # First tab should hold the site-edit page.
        return self._context.new_page()  # Otherwise open a fresh tab (launch mode).

    def _perform_lookup(self, page: Any, query: str) -> list[str]:
        """Type ``query``, then read ONLY the suggestion list that belongs to it (stale-safe)."""
        timeout_ms = int(self._config.per_lookup_timeout_s * 1000)  # Playwright uses milliseconds.
        with self._perf.phase("ui.locate_input"):  # Time finding the autocomplete field.
            field = self._locate_input(page, timeout_ms)  # Find the autocomplete input element.
        with self._perf.phase("ui.type_query"):  # Time the human-like typing (usually the biggest cost).
            self._enter_query(page, field, query)  # Focus, clear the stale dropdown, type the new query.
        expected = self._house_number(query)  # House number anchors the fresh-result wait.
        expected_suite = self._suite_id(query)  # Unit id we typed (for example "200"). "" skips the suite wait.
        with self._perf.phase("ui.read_suggestions"):  # Time the fresh-result poll incl. the suite grace.
            texts = self._read_fresh_suggestions(page, expected, timeout_ms, expected_suite)  # Wait for THIS query.
        logging.debug("UI autocomplete returned %d fresh suggestion(s)", len(texts))  # Action-log count.
        return texts  # May be empty -> NO_RESULT (never a stale, wrong answer).

    def _enter_query(self, page: Any, field: Any, query: str) -> None:
        """Focus the field, clear any stale value/dropdown, then type with human-like timing."""
        field.click()  # Focus so Google binds keystrokes.
        field.fill("")  # Clear any previous text.
        self._settle(page, _CLEAR_SETTLE_MS)  # WHY: let Google tear down the previous dropdown before typing.
        self._type_humanlike(field, query)  # Randomized per-key cadence to avoid bot/throttle heuristics.

    def _type_humanlike(self, field: Any, query: str) -> None:
        """Type ``query`` one character at a time with a randomized inter-keystroke delay.

        A fixed-cadence ``type(text, delay=N)`` looks robotic and can trip Google's
        autocomplete throttling / bot detection. We emit each character then sleep a
        random interval bounded by the config, with an occasional longer pause, so
        the input rhythm resembles a person rather than a machine.
        """
        for index, char in enumerate(query):  # Walk the query one character at a time.
            field.type(char)  # Emit a single keystroke into the focused field.
            time.sleep(self._key_delay(index))  # Randomized human-like gap before the next key.

    def _key_delay(self, index: int) -> float:
        """Return a randomized inter-keystroke delay, occasionally adding a 'thinking' pause."""
        low = max(0.0, self._config.min_key_delay_s)  # Lower bound (never negative).
        high = max(low, self._config.max_key_delay_s)  # Upper bound (guarded >= low).
        delay = _KEY_JITTER.uniform(low, high)  # Base per-keystroke jitter.
        if index and index % _THINKING_PAUSE_EVERY == 0:  # Every few characters, pause a touch longer.
            delay += _KEY_JITTER.uniform(low, high)  # Occasional human "thinking" gap.
        return delay  # Seconds to sleep before the next keystroke.

    def _read_fresh_suggestions(self, page: Any, expected: str, timeout_ms: int, expected_suite: str = "") -> list[str]:
        """Poll until the TOP suggestion anchors on ``expected`` (this query's house number).

        Google's autocomplete lags: the previous query's rows persist until the new
        request returns, and the suite (typed last) lags behind the street. We wait
        for the top row to reflect this query, then hold for ``_SUITE_GRACE_S`` for
        the unit to catch up. On timeout we return the best fresh list (or []).
        """
        deadline = time.monotonic() + max(0.0, timeout_ms / 1000.0)  # WHY: absolute wait deadline for the poll loop.
        grace = min(_SUITE_GRACE_S, max(0.0, timeout_ms / 1000.0))  # WHY: bounded window for a lagging suite.
        fresh_fallback, resolved = self._poll_for_fresh_top(page, expected, expected_suite, deadline, grace)
        if resolved is not None:  # WHY: helper accepted the top row (suite present or grace expired).
            return resolved  # Top suggestion accepted for THIS query.
        return self._fresh_timeout_result(fresh_fallback, expected)  # WHY: convert timeout into fallback or NO_RESULT.

    def _poll_for_fresh_top(
        self,
        page: Any,
        expected: str,
        expected_suite: str,
        deadline: float,
        grace: float,
    ) -> tuple[list[str], list[str] | None]:
        """Poll suggestion rows until the top anchors on ``expected`` and the suite catches up.

        Returns ``(fresh_fallback, resolved)`` -- ``resolved`` is set when a row is
        acceptable; ``fresh_fallback`` holds the best house-fresh list seen so far
        for the timeout branch.
        """
        house_ok_at: float | None = None  # WHY: monotonic time the house number first matched (suite grace anchor).
        fresh_fallback: list[str] = []  # WHY: best house-number-fresh list seen (may lack the suite) for timeout.
        while time.monotonic() < deadline:  # WHY: poll until fresh or timed out.
            texts = self._current_suggestions(page)  # Snapshot the current dropdown rows.
            if self._is_fresh_top(texts, expected):  # WHY: only THIS query's street/number qualifies as fresh.
                fresh_fallback = texts  # Remember: street/number belongs to THIS query.
                resolved, house_ok_at = self._evaluate_suite(texts, expected_suite, house_ok_at, grace)
                if resolved is not None:  # WHY: helper decided we can finalize (suite present or grace expired).
                    return fresh_fallback, resolved  # Top suggestion accepted for THIS query.
            self._settle(page, _POLL_INTERVAL_MS)  # Brief pause before re-polling.
        return fresh_fallback, None  # WHY: timed out -- caller handles fallback vs NO_RESULT.

    @staticmethod
    def _is_fresh_top(texts: list[str], expected: str) -> bool:
        """Return True when ``texts`` has a top row that anchors on ``expected`` (or none needed)."""
        if not texts:  # WHY: an empty dropdown cannot be fresh.
            return False  # Keep polling.
        return not expected or MistUIGeocoder._matches_house_number(texts[0], expected)  # WHY: anchor optional.

    def _evaluate_suite(
        self,
        texts: list[str],
        expected_suite: str,
        house_ok_at: float | None,
        grace: float,
    ) -> tuple[list[str] | None, float | None]:
        """Decide whether the fresh top row is final, starts/extends the suite grace, or is skipped.

        Returns ``(resolved, house_ok_at)``. When ``resolved`` is not ``None`` the
        caller must return it immediately; when it is ``None`` the caller keeps
        polling with the (possibly updated) ``house_ok_at`` timestamp.
        """
        if not expected_suite or self._reflects_suite(
            texts[0], expected_suite
        ):  # WHY: suite satisfied or none required.
            return texts, house_ok_at  # Finalize on the top row.
        if house_ok_at is None:  # WHY: first fresh house-number sighting -- start the grace clock.
            return None, time.monotonic()  # Keep polling; anchor the suite grace at now.
        if time.monotonic() - house_ok_at >= grace:  # WHY: grace expired -- accept the base street.
            logging.info("Suite '%s' not shown within grace; using base street", expected_suite)  # Action-log fallback.
            return texts, house_ok_at  # _build_result re-appends the unit we typed.
        return None, house_ok_at  # WHY: still within grace window -- keep polling for the suite.

    @staticmethod
    def _fresh_timeout_result(fresh_fallback: list[str], expected: str) -> list[str]:
        """Return the best fresh list seen before timeout, or [] when nothing fresh was seen."""
        if fresh_fallback:  # WHY: prefer the fresh street over NO_RESULT.
            return fresh_fallback  # Timed out mid-grace but the street/number were correct.
        logging.info("No fresh suggestion for house number '%s' within timeout; skipping (stale-guard)", expected)
        return []  # Fail-soft to NO_RESULT.

    def _current_suggestions(self, page: Any) -> list[str]:
        """Return the non-empty visible texts of the current suggestion rows."""
        items = page.query_selector_all(PAC_ITEM_SELECTOR)  # All suggestion rows in the dropdown.
        return [text for text in (self._item_text(item) for item in items) if text]  # Drop empties.

    @staticmethod
    def _settle(page: Any, millis: int) -> None:
        """Pause via Playwright's clock between polls (no-op-safe in tests)."""
        try:
            page.wait_for_timeout(millis)  # Cooperative wait that yields to the browser event loop.
        except Exception as exc:  # noqa: BLE001 -- a timing helper must never abort the lookup.
            logging.debug("wait_for_timeout ignored: %s", exc)  # Trace and continue.

    @staticmethod
    def _house_number(text: str) -> str:
        """Return the first digit-run (the house number); names like 'T-Mobile' have none."""
        match = re.search(r"\d+", text)  # First run of digits in the query.
        return match.group(0) if match else ""  # House number or empty when none present.

    @staticmethod
    def _matches_house_number(text: str, expected: str) -> bool:
        """Return True when ``expected`` is one of the digit-runs in ``text`` (glue-safe)."""
        return expected in re.findall(r"\d+", text)  # Compare extracted numbers, not a raw substring.

    @staticmethod
    def _suite_phrase(text: str) -> str:
        """Return the full suite/unit phrase from an address/query (for example 'Unit 200', '#3'), or ''.

        Matches an explicit keyword form (``Suite/Ste/Unit/Space/Bldg/Rm/Apt <id>``)
        first, then a bare ``#<id>`` hash form. The id may be alphanumeric with an
        internal hyphen (``A2``, ``1515B``, ``H0004``). Returns the raw matched token
        (whitespace-collapsed) so it can be re-appended verbatim to a suggestion.
        """
        keyword = re.search(
            SUITE_PHRASE_PATTERN, text
        )  # Shared keyword+id form (for example 'Suite 100', 'Ste A2', 'Sute A-103').
        if keyword:  # Prefer the explicit keyword form.
            return re.sub(r"\s+", " ", keyword.group(0)).strip()  # Collapse internal whitespace.
        hashed = re.search(HASH_UNIT_PATTERN, text)  # Bare hash form (for example '#3', '#1515b').
        return hashed.group(0).replace(" ", "") if hashed else ""  # '#<id>' with no gap, or empty.

    @staticmethod
    def _suite_id(text: str) -> str:
        """Return just the bare unit identifier from a suite phrase (for example '200', 'A2', '3'), or ''."""
        phrase = MistUIGeocoder._suite_phrase(text)  # Full phrase such as 'Unit 200' or '#3'.
        if not phrase:  # No suite present.
            return ""  # Nothing to compare/preserve.
        return phrase.split()[-1].lstrip("#")  # Trailing token; '#3' -> '3', 'Unit 200' -> '200'.

    @staticmethod
    def _reflects_suite(text: str, suite: str) -> bool:
        """Return True when ``suite`` appears in ``text`` beyond the leading house number (glue-safe).

        The leading house number is removed first so a unit id that equals the house
        number (``100 Main St Suite 100``) is not falsely considered 'reflected' by
        the base street ``100 Main St``.
        """
        if not suite:  # No suite to look for -> treat as satisfied.
            return True  # Caller wants no suite constraint.
        body = re.sub(r"^\D*\d+(?:-\d+)?", "", text, count=1)  # Drop the leading (possibly hyphenated) house number.
        tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", body)]  # Remaining alnum tokens, lowered.
        return suite.lower() in tokens  # The unit id must appear somewhere after the house number.

    def _locate_input(self, page: Any, timeout_ms: int) -> Any:
        """Probe candidate selectors and return the first matching input element."""
        per_try = max(
            _LOCATE_TIMEOUT_FLOOR_MS, timeout_ms // max(1, len(INPUT_SELECTORS))
        )  # WHY: floored per-candidate budget.
        last_error: Exception | None = None  # Remember the final miss for the raise.
        for selector in INPUT_SELECTORS:  # Try candidates in priority order.
            try:
                return page.wait_for_selector(selector, timeout=per_try)  # First hit wins.
            except Exception as exc:  # noqa: BLE001 -- try the next candidate.
                last_error = exc  # Keep probing.
        raise RuntimeError(f"Location Search input not found: {last_error}")  # All candidates missed.

    @staticmethod
    def _item_text(element: Any) -> str:
        """Return the trimmed visible text of a suggestion row, or empty on error."""
        try:
            return (element.inner_text() or "").strip()  # Visible text of the .pac-item row.
        except Exception:  # noqa: BLE001 -- a stale DOM node yields no text.
            return ""  # Treat as empty so it is filtered out.

    def _build_result(self, query: str, suggestions: list[str]) -> ResolverResult:
        """Turn ranked Google suggestions into a ``ResolverResult`` (cleaned address)."""
        if not suggestions:  # No autocomplete suggestions at all.
            logging.debug("No UI suggestions for query: %s", query)  # Trace the empty result.
            return ResolverResult(query=query, canonical_address=None, source="mist_ui", confidence=0.0)
        top = self._clean_address(suggestions[0])  # Strip the glued business name + trailing country.
        top = self._preserve_query_suite(query, top)  # Keep the unit we typed if Google returned the bare street.
        ambiguous = len(suggestions) > 1  # Multiple hits => mall/strip-center ambiguity.
        confidence = 0.6 if ambiguous else 0.9  # Lower confidence when several candidates exist.
        logging.info("UI geocode top suggestion: %s (ambiguous=%s)", top, ambiguous)  # Action-log result.
        return ResolverResult(
            query=query,  # Echo the query for cache keying.
            canonical_address=top,  # Best suite-corrected, shippable address.
            source="mist_ui",  # Mark the originating tier.
            confidence=confidence,  # Heuristic confidence.
            raw_response={"suggestions": suggestions, "ambiguous": ambiguous},  # Full payload for cache.
        )

    def _preserve_query_suite(self, query: str, suggestion: str) -> str:
        """Re-append the unit we typed when Google returned the SAME building without one.

        Google Places autocomplete often resolves to the street/establishment and
        drops an arbitrary unit typed at the end of the query -- so a suite the CSV
        (and often the SNMP location) confirmed can vanish from the suggestion,
        silently losing shipping-critical data and even reading as ADDRESS_MATCH.
        We restore it, but only when it is safe: we typed a unit, the suggestion
        does not already reflect that unit, the suggestion carries NO other unit
        (a DIFFERENT unit means Google is the authority -- leave it), and the house
        numbers agree (never graft a unit onto a different building).
        """
        suite_id = self._suite_id(query)  # WHY: the unit id we typed (for example "200"); "" when none.
        if self._skip_suite_preservation(query, suggestion, suite_id):  # WHY: guard-clause bundles all no-op cases.
            return suggestion  # Nothing to preserve, already complete, Google authoritative, or different building.
        phrase = self._suite_phrase(query)  # The full 'Unit 200' / '#3' token to restore.
        restored = self._insert_suite(suggestion, phrase)  # Append it to the street segment.
        logging.info("Preserved typed unit '%s' Google omitted: %s", phrase, restored)  # Action-log the restore.
        return restored  # Street from Google, unit preserved from the customer data.

    def _skip_suite_preservation(self, query: str, suggestion: str, suite_id: str) -> bool:
        """Return True when the suggestion should be returned untouched (no unit preservation)."""
        if not suite_id:  # WHY: we never asked about a unit -- nothing to preserve.
            return True
        if self._reflects_suite(suggestion, suite_id):  # WHY: Google already shows our unit.
            return True
        if self._suite_phrase(suggestion):  # WHY: Google returned a DIFFERENT unit -- it is the authority.
            return True
        return self._different_house(query, suggestion)  # WHY: never graft a unit across buildings.

    @staticmethod
    def _different_house(query: str, suggestion: str) -> bool:
        """Return True only when both sides carry a house number and they disagree."""
        query_house = MistUIGeocoder._house_number(query)  # House number we asked about.
        sugg_house = MistUIGeocoder._house_number(suggestion)  # House number Google returned.
        if not query_house or not sugg_house:  # WHY: unknown on either side -- do not treat as different.
            return False  # Cannot rule out same-building; defer to other guards.
        return query_house != sugg_house  # WHY: both known -- disagreement means a different building.

    @staticmethod
    def _insert_suite(address: str, phrase: str) -> str:
        """Append ``phrase`` to the street segment (before the first comma) of ``address``."""
        head, sep, tail = address.partition(",")  # Split off the street line (before the first comma).
        joined = f"{head.rstrip()} {phrase}".strip()  # Street + unit, single-spaced.
        return f"{joined}{sep}{tail}"  # Reattach the city/state/zip remainder unchanged.

    # Street-type suffixes (abbreviated and spelled out) used to split a street glued to a city.
    _STREET_SUFFIXES = (
        r"Hwy|Highway|St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Trl|Trail|Pkwy|Parkway|"
        r"Ln|Lane|Ct|Court|Cir|Circle|Pl|Place|Ter|Terrace|Sq|Square|Way|Loop|Pike|Plz|Plaza|Walk|Run|Row|Path"
    )

    @staticmethod
    def _clean_address(text: str) -> str:
        """Strip a glued leading place/business name and a trailing country from a suggestion.

        Google's ``.pac-item`` rows glue the establishment name to the address with
        no separator (for example ``T-Mobile931 US Highway 331 Ste A2, ..., USA``), glue a
        trailing directional to the city (``...Ave NLive Oak``), and sometimes glue
        the street or a suite number straight to the city (``...HwyFort Pierce``,
        ``...suite 330Brandon``). We drop the trailing country, repair those glued
        boundaries, then drop any leading non-digit run before a ``<house-number>
        <street>`` start -- yielding the clean shippable street line. A real
        camel-cased city (``DeFuniak``) is preserved because only street suffixes
        and digits trigger a split, never a generic lowercase->uppercase boundary.
        The leading house number may be hyphenated (Hawaii's ``74-5450`` grid
        addresses), so the anchor accepts an optional ``-<digits>`` run before the
        street; without this the glued business name survives (``T-Mobile74-5450``).
        """
        s = text.strip()  # Normalize surrounding whitespace.
        s = re.sub(r",?\s*(?:USA|United States)\s*$", "", s, flags=re.IGNORECASE).strip()  # Drop trailing country.
        s = re.sub(r"\b(US|NE|NW|SE|SW|N|S|E|W)([A-Z][a-z])", r"\1 \2", s)  # Split directional glue (NLive).
        s = re.sub(rf"\b({MistUIGeocoder._STREET_SUFFIXES})([A-Z][a-z])", r"\1 \2", s)  # Split street->city (HwyFort).
        s = re.sub(r"(\d)([A-Z][a-z]{2,})", r"\1 \2", s)  # Split a number glued to a city word (330Brandon).
        match = re.match(r"^\D*?(\d+(?:-\d+)?\s+\S.*)$", s)  # "<house-number> <street>" (house# may be hyphenated).
        cleaned = match.group(1) if match else s  # Use the address tail when a real street start is present.
        return cleaned.strip().strip(",").strip() or text.strip()  # Never return empty.

    def close(self) -> None:
        """Tear down browser and driver handles; never raises."""
        logging.debug("Closing MistUIGeocoder browser resources")  # Action-log teardown.
        try:
            if self._browser is not None:  # Disconnect/close the browser if open.
                self._browser.close()  # In attach mode this only drops our CDP connection.
        except Exception as exc:  # noqa: BLE001 -- teardown must not raise.
            logging.debug("Browser close error (ignored): %s", exc)  # Trace and continue.
        try:
            if self._playwright is not None:  # Stop the Playwright driver process.
                self._playwright.stop()  # Release the driver subprocess.
        except Exception as exc:  # noqa: BLE001 -- teardown must not raise.
            logging.debug("Playwright stop error (ignored): %s", exc)  # Trace and continue.
        self._terminate_spawned()  # Close any Edge we spawned ourselves (auto mode).
        self._connected = False  # Reset state so a stale handle is never reused.

    def _terminate_spawned(self) -> None:
        """Terminate the debuggable Edge we spawned in auto mode (never raises)."""
        if self._spawned_proc is None:  # We only own a process when we spawned one.
            return  # Attach/launch modes have nothing to clean up here.
        try:
            self._spawned_proc.terminate()  # Ask the spawned Edge to exit.
            logging.debug("Terminated spawned debuggable Edge (pid=%s)", self._spawned_proc.pid)  # Trace.
        except Exception as exc:  # noqa: BLE001 -- teardown must not raise.
            logging.debug("Spawned Edge terminate error (ignored): %s", exc)  # Trace and continue.
        self._spawned_proc = None  # Drop the handle so close() is idempotent.

    @staticmethod
    def spawn_debuggable_browser(
        cdp_port: int = _DEFAULT_CDP_PORT,
        dashboard_url: str = _DASHBOARD_URL_DEFAULT,
    ) -> subprocess.Popen[bytes] | None:
        """Launch system Edge with remote debugging so it can be taken over via CDP.

        Returns the ``Popen`` handle (caller owns its lifecycle) or ``None`` when
        Edge cannot be located. Uses a throwaway profile so the operator's normal
        Edge profile is never touched; the operator logs into Mist in this window
        once, then ``connect_mode="attach"`` reuses that session.
        """
        edge = MistUIGeocoder._edge_executable()  # Locate the system Edge binary.
        if edge is None:  # No Edge -> cannot offer a takeover target.
            logging.warning("Microsoft Edge not found; cannot spawn a debuggable browser")  # Inform operator.
            return None  # Caller should fall back to launch mode.
        profile = tempfile.mkdtemp(prefix=_PROFILE_PREFIX)  # WHY: dedicated dir so the operator's profile is untouched.
        args = MistUIGeocoder._debuggable_edge_args(edge, cdp_port, profile, dashboard_url)  # Build the CLI flags.
        logging.info("Spawning debuggable Edge on port %d (profile=%s)", cdp_port, profile)  # Action-log spawn.
        proc = subprocess.Popen(args)  # Launch Edge; the operator logs in, then we attach.
        logging.debug("Debuggable Edge started (pid=%s)", proc.pid)  # Trace the PID.
        return proc  # Caller terminates it when the audit finishes.

    @staticmethod
    def _debuggable_edge_args(edge: str, cdp_port: int, profile: str, dashboard_url: str) -> list[str]:
        """Return the Edge CLI argv that enables CDP on ``cdp_port`` in ``profile``."""
        return [  # WHY: Edge CLI flags that enable CDP takeover into an isolated profile.
            edge,  # Edge executable path.
            f"--remote-debugging-port={cdp_port}",  # Expose the DevTools endpoint for connect_over_cdp.
            f"--user-data-dir={profile}",  # Isolate cookies/session in a throwaway profile.
            "--no-first-run",  # Skip Edge's first-run experience.
            "--no-default-browser-check",  # Skip the default-browser nag.
            dashboard_url,  # Open straight to the Mist login/landing page.
        ]

    @staticmethod
    def _edge_executable() -> str | None:
        """Locate ``msedge.exe`` via standard install paths, then PATH."""
        candidates = [  # WHY: standard per-machine Edge install locations on Windows.
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), *_EDGE_INSTALL_TAIL),
            os.path.join(os.environ.get("ProgramFiles", ""), *_EDGE_INSTALL_TAIL),
        ]
        for path in candidates:  # Probe each known location.
            if path and os.path.isfile(path):  # First existing binary wins.
                logging.debug("Edge located at %s", path)  # Trace the hit.
                return path  # Return the absolute path.
        found = shutil.which("msedge")  # Fall back to a PATH lookup.
        logging.debug("Edge PATH lookup -> %s", found)  # Trace the fallback result.
        return found  # May be None if Edge is absent.
