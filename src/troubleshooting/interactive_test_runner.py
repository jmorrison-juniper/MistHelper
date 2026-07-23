"""Workflow extraction for interactive-safe menu systematic test execution."""

from __future__ import annotations  # WHY: enable PEP 604 union syntax on older runtimes.

import inspect  # WHY: gate site_id kwarg injection based on callable signatures.
import logging  # WHY: emit structured diagnostics for suite orchestration.
import os  # WHY: read MIST_INTERACTIVE_TEST_SITE selector from environment.
import time  # WHY: measure per-option and suite durations.
from dataclasses import dataclass  # WHY: dataclasses bundle related params under the 5-Item Rule.
from datetime import datetime  # WHY: format suite start-time header line.
from typing import Any  # WHY: emitter and registry protocols intentionally unconstrained.

from src.dataclasses.progress_event import TestSummary  # WHY: reuse issue #470 aggregate telemetry container.


class TestSiteSelectorUnresolved(RuntimeError):
    """Raised when ``MIST_INTERACTIVE_TEST_SITE`` is set but resolves to no org site.

    Why:
        Issue #1637 — fail-closed selector contract. Silently falling back to
        the first available site when an operator supplied an explicit
        selector risks running the interactive suite against the wrong
        environment (a different site than the operator intended). This
        exception is the seam ``_resolve_site_or_close`` catches to abort the
        suite cleanly instead of proceeding against an unintended site.
    """


class _LoggedErrorObserver(logging.Handler):
    """Root-logger handler that counts ERROR (or higher) records emitted during an option run.

    Why:
        Issue #1636 — interactive handlers can call ``logging.error(...)`` and
        then swallow the failure by returning None. Without observing those
        records the runner treats the option as a clean pass, inflating the
        pass rate and masking real defects. Attaching this handler scoped to
        the ``_invoke_option`` call gives the runner a deterministic signal
        that a logged-error occurred without an exception being raised, so it
        can route to the failure emitter and keep the exit code accurate.
    """

    def __init__(self) -> None:
        """Configure the handler at ERROR level with a zero-count captured tally."""
        super().__init__(level=logging.ERROR)
        self.error_count = 0  # WHY: cheap monotonic tally; callers only check >0.

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 -- logging.Handler API
        """Increment the captured error tally for each ERROR (or higher) record."""
        if record.levelno >= logging.ERROR:
            self.error_count += 1


@dataclass(frozen=True, slots=True)
class SuiteTallies:  # WHY: bundle counts+timing so summary/finalize signatures stay within 5-param limit.
    """Tallies produced by the interactive-safe option execution loop."""

    success_count: int  # WHY: successful option invocations reported in the summary block.
    error_count: int  # WHY: failed option invocations reported in the summary block.
    skip_count: int  # WHY: options skipped as non-interactive-safe.
    total_time: float  # WHY: wall-clock seconds elapsed running the entire suite.


@dataclass(frozen=True, slots=True)
class SuiteContext:  # WHY: bundle runtime handles to keep run/finalize signatures within 5-param limit.
    """Runtime handles + counters threaded through the finalize phase of a suite run."""

    all_options: list[str]  # WHY: full option universe used for TestSummary total_ops metric.
    interactive_options: list[str]  # WHY: subset actually executed; drives coverage denominator.
    test_site_id: str | None  # WHY: resolved test site injected into interactive callables.
    emitter: Any  # WHY: telemetry emitter that receives per-option and summary events.
    telemetry_path: Any  # WHY: destination path echoed in the operator summary block.
    skip_count: int  # WHY: pre-emitted skip count included in TestSummary metrics.
    start_time: float  # WHY: monotonic origin used to derive total suite runtime.


@dataclass
class InteractiveTestRunner:  # WHY: dependency container avoids global module state for the workflow.
    """Run interactive-safe operation tests while preserving legacy operator output."""

    menu_actions: dict[str, tuple[Any, str]]  # WHY: option-id -> (callable, description) dispatch table.
    operation_registry: Any  # WHY: source of interactive-safe filtering, reasons, and categories.
    telemetry_emitter_cls: Any  # WHY: telemetry emitter factory used to instantiate an emitter.
    config_utils: Any  # WHY: fallback path used to resolve/cache the org id.
    mistapi_module: Any  # WHY: mistapi module used to list org sites for test-site resolution.
    apisession: Any  # WHY: authenticated Mist API session passed to listOrgSites.
    org_id_getter: Any  # WHY: cached org id lookup callable.
    org_id_setter: Any  # WHY: cached org id persistence callable.

    def _fetch_selector_sites(self, org_id: str) -> list[dict[str, Any]]:
        """Fetch full org site list for selector-based test-site resolution."""
        logging.info("Selector provided; fetching organization sites for selector match")  # WHY: log before API call.
        sites_response = self.mistapi_module.api.v1.orgs.sites.listOrgSites(
            self.apisession, org_id, limit=1000
        )  # WHY: fetch full org site set so selector can resolve by id or name.
        sites_data = self.mistapi_module.get_all(
            response=sites_response, mist_session=self.apisession
        )  # WHY: resolve paginated site response into iterable list.
        logging.debug(
            "Fetched %d sites while resolving selector", len(sites_data) if sites_data else 0
        )  # WHY: log dataset size for selector lookup diagnostics.
        return sites_data  # WHY: hand full list to matcher helper for selector comparison.

    @staticmethod
    def _find_selector_match(sites_data: list[dict[str, Any]], site_selector: str) -> dict[str, Any] | None:
        """Return first site matching selector by UUID or case-insensitive name."""
        selector_lower = site_selector.lower()  # WHY: precompute lowered form for name match.
        return next(
            (
                site
                for site in sites_data
                if site.get("id") == site_selector or site.get("name", "").lower() == selector_lower
            ),
            None,
        )  # WHY: single-pass generator scan avoids extra branches in caller.

    @staticmethod
    def _log_selector_miss(site_selector: str) -> None:
        """Log selector-miss banner via ``logging.error`` (fail-closed contract).

        Why:
            Issue #1637 promotes selector-miss from warning to error and
            removes the "falling back" phrasing: when an operator explicitly
            sets ``MIST_INTERACTIVE_TEST_SITE`` we must abort rather than run
            against a different site. The miss is now a terminal condition
            surfaced to the operator before ``TestSiteSelectorUnresolved`` is
            raised.
        """
        logging.error(
            "INTERACTIVE_TEST: MIST_INTERACTIVE_TEST_SITE '%s' did not match any organization site; aborting.",
            site_selector,
        )  # WHY: fail-closed banner (issue #1637).

    def _lookup_selector_site(self, org_id: str, site_selector: str) -> tuple[str, str]:
        """Return site matching the environment selector or raise ``TestSiteSelectorUnresolved``.

        Why:
            Issue #1637 — fail-closed contract. Previously returned
            ``(None, "Unknown")`` on miss which let the caller silently fall
            back to the first available site. Now the miss is a terminal
            condition and callers must handle the exception.

        Args:
            org_id: Organization UUID whose sites are searched.
            site_selector: Operator-supplied UUID or case-insensitive site name.

        Returns:
            Tuple of ``(site_id, site_name)`` for the resolved site.

        Raises:
            TestSiteSelectorUnresolved: When no site matches the selector.
        """
        sites_data = self._fetch_selector_sites(org_id)  # WHY: delegate list fetch to helper.
        matching_site = self._find_selector_match(
            sites_data, site_selector
        )  # WHY: delegate selector matching to helper.
        if not matching_site:
            self._log_selector_miss(site_selector)  # WHY: emit terminal miss banner before raising.
            raise TestSiteSelectorUnresolved(
                f"MIST_INTERACTIVE_TEST_SITE '{site_selector}' did not match any organization site"
            )  # WHY: fail-closed (issue #1637) — do not silently fall back.
        site_id = matching_site["id"]  # WHY: capture matched site id for downstream operations.
        site_name = matching_site.get("name", "Unknown")  # WHY: capture matched site name for context.
        logging.warning(
            "   Using test site from MIST_INTERACTIVE_TEST_SITE: %s (%s)",
            site_name,
            site_id,
        )  # WHY: #886 slice 18/N — legacy selector-success message via logging.warning.
        logging.debug(
            "Selector matched site_id=%s site_name=%s", site_id, site_name
        )  # WHY: log selector match details for traceability.
        return site_id, site_name  # WHY: return resolved selector context to orchestrator.

    def _lookup_first_available_site(self, org_id: str) -> tuple[str | None, str]:
        """Return the first available org site for deterministic fallback selection."""
        logging.info(
            "Resolving fallback test site using first available org site"
        )  # WHY: log before fallback API call.
        sites_response = self.mistapi_module.api.v1.orgs.sites.listOrgSites(
            self.apisession, org_id, limit=1
        )  # WHY: request only the first available site as deterministic fallback.
        if not sites_response.data:
            return None, "Unknown"  # WHY: signal absence of any site so caller can abort.
        site_id = sites_response.data[0]["id"]  # WHY: capture fallback site UUID for test execution.
        site_name = sites_response.data[0].get(
            "name", "Unknown"
        )  # WHY: capture fallback site name for user-visible context.
        logging.warning(
            "   Using first available test site: %s (%s)",
            site_name,
            site_id,
        )  # WHY: #886 slice 18/N — legacy fallback message via logging.warning.
        return site_id, site_name  # WHY: return resolved fallback context to orchestrator.

    def _resolve_test_site(self, org_id: str) -> tuple[str | None, str]:
        """Resolve test site from environment selector or first available site."""
        logging.info("Resolving interactive-test site for org_id=%s", org_id)  # WHY: log entry to test-site resolution.
        site_selector = os.getenv(
            "MIST_INTERACTIVE_TEST_SITE", ""
        ).strip()  # WHY: read optional environment override for deterministic test-site selection.
        logging.debug(
            "Environment selector MIST_INTERACTIVE_TEST_SITE='%s'", site_selector
        )  # WHY: log resolved selector value for diagnostics.
        site_id: str | None = None  # WHY: initialize safe fallback ID used when no site is found.
        site_name = "Unknown"  # WHY: initialize safe fallback name used if lookup fails.
        if site_selector:
            site_id, site_name = self._lookup_selector_site(
                org_id, site_selector
            )  # WHY: delegate selector-based lookup to helper.
        if not site_id:
            site_id, site_name = self._lookup_first_available_site(
                org_id
            )  # WHY: delegate fallback to first-available-site helper.
        logging.debug(
            "Resolved interactive test site_id=%s site_name=%s", site_id, site_name
        )  # WHY: log final resolution result for caller context.
        return site_id, site_name  # WHY: return resolved site context used by execute() workflow.

    def _print_suite_header(self) -> None:
        """Emit the interactive-test suite banner as a single ``logging.warning``.

        Why:
            #886 slice 18/N. Header, note, timestamp, and divider are
            consolidated into one atomic warning so the banner cannot be
            interleaved with other records under concurrent log producers.
        """
        logging.warning(
            " Starting interactive test of MistHelper menu options...\n"
            "  Note: This tests read-only operations requiring site/device/client selection\n"
            "! Test started at: %s\n"
            "%s",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "=" * 80,
        )

    def _build_option_lists(self) -> tuple[list[str], list[str], list[str]]:
        """Return (all_options, interactive_options, skip_list) using stable legacy ordering."""
        logging.info("Building interactive option lists from menu actions")  # WHY: log before list-build action.
        all_options = sorted(
            self.menu_actions.keys(), key=lambda option: float(option.replace("a", ".1"))
        )  # WHY: preserve legacy float-key ordering across sub-option letters.
        interactive_options = self.operation_registry.interactive_safe_options(
            all_options
        )  # WHY: filter to interactive-safe options via registry.
        skip_list = [
            option for option in all_options if not self.operation_registry.is_interactive_safe(option)
        ]  # WHY: build skip list mirroring legacy negative filter.
        logging.debug(
            "Built option lists: %d interactive, %d skipped", len(interactive_options), len(skip_list)
        )  # WHY: log list-build result for diagnostics.
        return all_options, interactive_options, skip_list  # WHY: return triple consumed by execute().

    def _print_tested_options(self, interactive_options: list[str]) -> None:
        """Emit the tested-options listing via a single ``logging.warning``.

        Why:
            #886 slice 18/N. Consolidated into one warning record so the
            listing arrives atomically and cannot be interleaved with other
            log output under concurrent producers.
        """
        lines = [" Testing interactive read-only operations:"]
        for option in interactive_options:
            if option in self.menu_actions:
                _, description = self.menu_actions[option]  # WHY: resolve description for option listing.
                lines.append(f"   {option:>3}: {description}")  # WHY: preserve per-option tested listing.
        logging.warning("%s", "\n".join(lines))

    def _print_skipped_options(self, skip_list: list[str]) -> None:
        """Emit the skipped-options listing via a single ``logging.warning``.

        Why:
            #886 slice 18/N. Consolidated so the skip listing prints as one
            atomic record, matching the tested-listing helper.
        """
        lines = [" Skipping non-interactive-safe operations:"]
        for option in skip_list:
            if option in self.menu_actions:
                reason = self.operation_registry.skip_reason(option)  # WHY: resolve registry skip reason.
                if reason:
                    lines.append(f"   {option:>3}: {reason}")  # WHY: preserve per-option skip-reason listing.
        logging.warning("%s", "\n".join(lines))

    def _print_option_listings(self, interactive_options: list[str], skip_list: list[str]) -> None:
        """Emit the tested-and-skipped option listings via ``logging.warning``.

        Why:
            #886 slice 18/N. Counts and blank-line separators are folded into
            a single warning record; delegated tested/skipped listings each
            emit one further warning to preserve section boundaries.
        """
        logging.warning(
            "! Found %d interactive read-only options to test\n! %d options will be skipped",
            len(interactive_options),
            len(skip_list),
        )  # WHY: preserve count lines as one atomic warning.
        self._print_tested_options(interactive_options)  # WHY: delegate tested-listing emission.
        self._print_skipped_options(skip_list)  # WHY: delegate skipped-listing emission.

    def _create_emitter(self) -> tuple[Any, Any]:
        """Initialize telemetry emitter; return (emitter, path) tuple."""
        logging.info("Creating telemetry emitter for interactive test run")  # WHY: log before emitter setup.
        telemetry_path = self.telemetry_emitter_cls.timestamped_path("data")  # WHY: generate timestamped output path.
        emitter = self.telemetry_emitter_cls(telemetry_path)  # WHY: construct emitter instance.
        logging.debug("Telemetry emitter initialized with path: %s", telemetry_path)  # WHY: log emitter destination.
        return emitter, telemetry_path  # WHY: return tuple so callers do not depend on emitter attrs.

    def _emit_skip_events(self, emitter: Any, skip_list: list[str]) -> int:
        """Emit telemetry skip events for non-interactive-safe options and return skip count."""
        skip_count = 0  # WHY: initialize skip counter for aggregate reporting.
        for option in skip_list:
            if option in self.menu_actions:
                _, op_name = self.menu_actions[option]  # WHY: resolve op-name for skip event payload.
                logging.info("Emitting telemetry skip event for option %s", option)  # WHY: log before skip emission.
                emitter.emit_test_skip(
                    option,
                    op_name,
                    self.operation_registry.skip_reason(option),
                    self.operation_registry.skip_category(option),
                    "interactive",
                )  # WHY: emit skip event capturing option identity + skip metadata.
                skip_count += 1  # WHY: increment skip counter after successful emission.
        logging.debug("Emitted %d skip telemetry events", skip_count)  # WHY: log skip emission summary.
        return skip_count  # WHY: return count for summary reporting.

    def _ensure_org_id(self) -> str:
        """Return cached org_id or resolve and persist a new one."""
        org_id = self.org_id_getter()  # WHY: retrieve cached org_id from injected getter.
        if not org_id:
            logging.info("No cached org_id present; resolving via config utils")  # WHY: log before resolution.
            org_id = self.config_utils.get_cached_or_prompted_org_id()  # WHY: resolve org_id via utils.
            self.org_id_setter(org_id)  # WHY: persist resolved org_id via injected setter.
            logging.debug("Resolved and stored org_id=%s", org_id)  # WHY: log resolution result.
        return org_id  # WHY: return org_id for downstream site resolution.

    def _resolve_site_or_close(self, org_id: str, emitter: Any) -> tuple[str | None, str]:
        """Resolve test site context; close emitter and return (None, '') on failure paths."""
        try:
            logging.warning("   Fetching test site for interactive operations...")  # WHY: #886 s18 legacy cue.
            test_site_id, test_site_name = self._resolve_test_site(org_id)  # WHY: resolve test site.
            if test_site_id:
                logging.info(
                    "INTERACTIVE_TEST: Using test site_id=%s name=%s", test_site_id, test_site_name
                )  # WHY: log selected site context.
                return test_site_id, test_site_name  # WHY: return resolved context on success.
            logging.error(
                "[ERROR] No sites found in organization - cannot run interactive tests"
            )  # WHY: #886 slice 18/N — legacy no-site error via logging.error.
            logging.error("INTERACTIVE_TEST: No sites available for testing")  # WHY: log no-site terminal condition.
        except TestSiteSelectorUnresolved as error:
            logging.error(
                "[ERROR] Aborting interactive tests: %s", error
            )  # WHY: issue #1637 — fail-closed operator banner when explicit selector missed.
        except Exception as error:
            logging.error("[ERROR] Failed to fetch test site: %s", error)  # WHY: #886 s18 fetch-failure msg.
            logging.error("INTERACTIVE_TEST: Failed to fetch test site: %s", error)  # WHY: log exception context.
        logging.info("Closing telemetry emitter after site-resolution failure")  # WHY: log before close on failure.
        emitter.close()  # WHY: close emitter to flush events on failure path.
        logging.debug("Telemetry emitter closed after site-resolution failure")  # WHY: log close completion.
        return None, ""  # WHY: signal caller to abort suite.

    def _invoke_option(self, option: str, test_site_id: str | None) -> None:
        """Invoke a single menu option callable with prepared kwargs."""
        function, _description = self.menu_actions[option]  # WHY: resolve callable for option.
        signature = inspect.signature(function)  # WHY: inspect signature to gate kwargs injection.
        invoke_kwargs: dict[str, Any] = {}  # WHY: initialize kwargs payload.
        if "site_id" in signature.parameters:
            invoke_kwargs["site_id"] = test_site_id  # WHY: inject site when callable accepts it.
        logging.debug(
            "Invoking option %s with kwargs=%s", option, invoke_kwargs
        )  # WHY: log invocation kwargs for diagnostics.
        function(**invoke_kwargs)  # WHY: execute target interactive-safe operation.

    def _emit_option_pass(self, option: str, description: str, duration: float, emitter: Any) -> bool:
        """Emit telemetry pass event and preserve legacy success output for an option."""
        logging.warning("   [SUCCESS] Option %s completed successfully", option)  # WHY: #886 s18 success msg.
        logging.info("Emitting telemetry pass event for option %s", option)  # WHY: log before pass emission.
        emitter.emit_test_pass(option, description, duration, "interactive")  # WHY: emit pass event.
        logging.debug("Telemetry pass event emitted for option %s", option)  # WHY: log pass completion.
        logging.info(
            "INTERACTIVE_TEST: Successfully completed menu option %s", option
        )  # WHY: log operator-facing success.
        return True  # WHY: signal success to caller.

    def _emit_option_fail(self, option: str, description: str, duration: float, error: Exception, emitter: Any) -> bool:
        """Emit telemetry fail event and preserve legacy failure output for an option."""
        logging.warning(
            "   [FAILED]  Option %s failed: %s...", option, str(error)[:100]
        )  # WHY: #886 slice 18/N — failure message via logging.warning with legacy truncation.
        logging.info("Emitting telemetry fail event for option %s", option)  # WHY: log before fail emission.
        emitter.emit_test_fail(
            option, description, duration, error, "interactive"
        )  # WHY: emit fail event with exception context.
        logging.debug("Telemetry fail event emitted for option %s", option)  # WHY: log fail completion.
        logging.error("INTERACTIVE_TEST: Failed menu option %s: %s", option, error)  # WHY: log operator-facing failure.
        return False  # WHY: signal failure to caller.

    def _run_single_option(self, index: int, total: int, option: str, test_site_id: str | None, emitter: Any) -> bool:
        """Run a single interactive option, emit telemetry, and return True on success.

        Why:
            Issue #1636 — a handler that calls ``logging.error(...)`` and then
            returns None must be classified as a failure, not a clean pass.
            The ``_LoggedErrorObserver`` handler is attached to the root logger
            only for the duration of ``_invoke_option`` and torn down before
            emitting the pass/fail event so the runner's own success/failure
            logging does not double-count. If any ERROR-level record is captured
            while no exception was raised, the option is routed to the failure
            emitter with a synthesized ``RuntimeError`` describing the logged
            error condition.
        """
        _function, description = self.menu_actions[option]  # WHY: resolve description for progress output.
        logging.warning(
            "   [%2d/%d] Testing option %3s: %s...", index, total, option, description[:60]
        )  # WHY: #886 slice 18/N — per-option progress line via logging.warning.
        logging.info("Emitting telemetry start event for option %s", option)  # WHY: log before start emission.
        emitter.emit_test_start(option, description, "interactive")  # WHY: emit start event.
        logging.debug("Telemetry start event emitted for option %s", option)  # WHY: log start emission completion.
        op_start = time.time()  # WHY: capture per-option start timestamp.
        logging.info(
            "INTERACTIVE_TEST: Starting test of menu option %s description='%s'", option, description
        )  # WHY: log before invocation.
        observer = _LoggedErrorObserver()  # WHY: #1636 — capture ERROR records emitted by the handler.
        root_logger = logging.getLogger()  # WHY: attach to root so any child logger's ERROR is observed.
        root_logger.addHandler(observer)
        try:
            try:
                self._invoke_option(option, test_site_id)  # WHY: invoke the menu callable.
            finally:
                root_logger.removeHandler(observer)  # WHY: detach before pass/fail emission to avoid self-count.
            if observer.error_count > 0:
                # WHY: #1636 — logged error without an exception is still a failure.
                synthesized = RuntimeError(f"operation logged {observer.error_count} error record(s) without raising")
                return self._emit_option_fail(option, description, time.time() - op_start, synthesized, emitter)
            return self._emit_option_pass(
                option, description, time.time() - op_start, emitter
            )  # WHY: delegate success emission.
        except Exception as error:
            root_logger.removeHandler(observer)  # WHY: idempotent guard on the raise path.
            return self._emit_option_fail(
                option, description, time.time() - op_start, error, emitter
            )  # WHY: delegate failure emission.

    def _run_option_loop(
        self, interactive_options: list[str], test_site_id: str | None, emitter: Any
    ) -> tuple[int, int]:
        """Iterate interactive options, executing each and tallying successes/failures."""
        success_count = 0  # WHY: initialize success counter.
        error_count = 0  # WHY: initialize failure counter.
        total = len(interactive_options)  # WHY: cache total for progress display.
        for index, option in enumerate(interactive_options, 1):
            if option not in self.menu_actions:
                continue  # WHY: skip options missing from dispatch table.
            if self._run_single_option(index, total, option, test_site_id, emitter):
                success_count += 1  # WHY: increment success counter on pass.
            else:
                error_count += 1  # WHY: increment failure counter on fail.
            time.sleep(1)  # WHY: preserve legacy pacing delay between options.
        return success_count, error_count  # WHY: return tally for summary reporting.

    def _finalize_telemetry(self, emitter: Any, tallies: SuiteTallies, total_ops: int) -> None:
        """Emit summary event, close emitter, and enforce retention policy."""
        logging.info("Emitting telemetry summary for interactive test suite")  # WHY: log before summary emission.
        emitter.emit_test_summary(
            TestSummary(
                total_ops,
                tallies.success_count,
                tallies.error_count,
                tallies.skip_count,
                tallies.total_time,
                "interactive",
            )
        )  # WHY: emit aggregate metrics (issue #470: stats bundled into a TestSummary dataclass).
        logging.debug("Telemetry summary event emitted successfully")  # WHY: log summary completion.
        logging.info("Closing telemetry emitter after interactive suite completion")  # WHY: log before close.
        emitter.close()  # WHY: flush pending events.
        logging.debug("Telemetry emitter closed successfully")  # WHY: log close completion.
        logging.info("Applying telemetry retention policy")  # WHY: log before retention enforcement.
        emitter.enforce_retention()  # WHY: prune old telemetry files.
        logging.debug("Telemetry retention policy enforcement completed")  # WHY: log retention completion.

    def _print_summary_stats(self, tallies: SuiteTallies, interactive_total: int, telemetry_path: Any) -> None:
        """Emit the legacy stats block as one atomic ``logging.warning``.

        Why:
            #886 slice 18/N. The 10-line summary block was 10 separate
            ``print()`` calls; consolidating into one warning record
            guarantees the block arrives contiguously in any handler.
        """
        coverage_pct = tallies.success_count / interactive_total * 100  # WHY: precompute coverage %.
        logging.warning(
            "\n%s\n Interactive Test Summary:\n"
            "   Successful operations: %d\n"
            "   Failed operations: %d\n"
            "   Skipped operations: %d\n"
            "   Total interactive read-only coverage: %d/%d (%.1f%%)\n"
            "   Total execution time: %.2f seconds\n"
            "   Telemetry written to: %s\n"
            "   Detailed logs in: script.log",
            "=" * 80,
            tallies.success_count,
            tallies.error_count,
            tallies.skip_count,
            tallies.success_count,
            interactive_total,
            coverage_pct,
            tallies.total_time,
            telemetry_path,
        )

    def _print_summary_verdict(self, tallies: SuiteTallies, interactive_total: int) -> bool:
        """Print final verdict banner and return suite pass/fail status."""
        if tallies.error_count == 0:
            logging.warning("   All tested interactive operations completed successfully!")  # WHY: #886 s18.
            logging.info(
                "INTERACTIVE_TEST: All %s tested operations completed successfully in %.2fs",
                tallies.success_count,
                tallies.total_time,
            )  # WHY: log all-pass suite outcome.
            return True  # WHY: return pass status.
        logging.warning(
            "   %d operations failed - check logs for details", tallies.error_count
        )  # WHY: #886 slice 18/N — failure summary line via logging.warning.
        logging.warning(
            "INTERACTIVE_TEST: %s operations failed out of %s tested",
            tallies.error_count,
            interactive_total,
        )  # WHY: log partial-failure suite outcome.
        return False  # WHY: return failure status.

    def _print_summary(self, tallies: SuiteTallies, interactive_total: int, telemetry_path: Any) -> bool:
        """Print the legacy summary block and return overall suite pass/fail status."""
        self._print_summary_stats(tallies, interactive_total, telemetry_path)  # WHY: delegate stats-block print.
        return self._print_summary_verdict(tallies, interactive_total)  # WHY: delegate verdict print + suite status.

    def _run_and_finalize(self, ctx: SuiteContext) -> bool:
        """Run per-option loop, finalize telemetry, and print the summary block."""
        success_count, error_count = self._run_option_loop(
            ctx.interactive_options, ctx.test_site_id, ctx.emitter
        )  # WHY: execute option loop.
        tallies = SuiteTallies(
            success_count, error_count, ctx.skip_count, time.time() - ctx.start_time
        )  # WHY: bundle tallies for downstream reporting.
        self._finalize_telemetry(
            ctx.emitter, tallies, len(ctx.all_options)
        )  # WHY: emit summary, close emitter, enforce retention.
        return self._print_summary(
            tallies, len(ctx.interactive_options), ctx.telemetry_path
        )  # WHY: print summary and return suite status.

    def execute(self) -> bool:
        """Run the interactive-safe systematic test suite."""
        logging.info("Starting interactive-safe systematic test suite")  # WHY: log suite entry boundary.
        start_time = time.time()  # WHY: capture suite start timestamp.
        self._print_suite_header()  # WHY: emit legacy header block.
        all_options, interactive_options, skip_list = self._build_option_lists()  # WHY: build option lists.
        self._print_option_listings(interactive_options, skip_list)  # WHY: emit option listings.
        emitter, telemetry_path = self._create_emitter()  # WHY: initialize telemetry emitter; capture path.
        skip_count = self._emit_skip_events(emitter, skip_list)  # WHY: emit skip events and tally count.
        org_id = self._ensure_org_id()  # WHY: resolve org_id with cache fallback.
        test_site_id, _site_name = self._resolve_site_or_close(org_id, emitter)  # WHY: resolve site context or abort.
        if not test_site_id:
            return False  # WHY: abort because prerequisite site could not be resolved.
        ctx = SuiteContext(
            all_options, interactive_options, test_site_id, emitter, telemetry_path, skip_count, start_time
        )  # WHY: bundle handles+counters for finalize phase under 5-param limit.
        return self._run_and_finalize(ctx)  # WHY: delegate execution loop + finalize + summary print.
