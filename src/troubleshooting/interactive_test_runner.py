"""Workflow extraction for interactive-safe menu systematic test execution."""

from __future__ import annotations

import inspect
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class InteractiveTestRunner:
    """Run interactive-safe operation tests while preserving legacy operator output."""

    menu_actions: dict[str, tuple[Any, str]]
    operation_registry: Any
    telemetry_emitter_cls: Any
    config_utils: Any
    mistapi_module: Any
    apisession: Any
    org_id_getter: Any
    org_id_setter: Any

    def _resolve_test_site(self, org_id: str) -> tuple[str | None, str]:
        """Resolve test site from environment selector or first available site."""
        logging.info("Resolving interactive-test site for org_id=%s", org_id)  # Log before test-site resolution begins.
        site_selector = os.getenv(
            "MIST_INTERACTIVE_TEST_SITE", ""
        ).strip()  # Read optional environment override for deterministic test-site selection.
        logging.debug(
            "Environment selector MIST_INTERACTIVE_TEST_SITE='%s'", site_selector
        )  # Log resolved selector value for diagnostics.
        test_site_name = "Unknown"  # Initialize safe fallback name used if lookup fails.
        test_site_id = None  # Initialize safe fallback ID used when no site is found.
        if site_selector:
            logging.info(
                "Selector provided; fetching organization sites for selector match"
            )  # Log before full-site list API call.
            sites_response = self.mistapi_module.api.v1.orgs.sites.listOrgSites(
                self.apisession, org_id, limit=1000
            )  # Fetch org sites so selector can resolve by id or name.
            sites_data = self.mistapi_module.get_all(
                response=sites_response, mist_session=self.apisession
            )  # Resolve paginated site response into iterable list.
            logging.debug(
                "Fetched %d sites while resolving selector", len(sites_data) if sites_data else 0
            )  # Log selector-lookup dataset size.
            matching_site = next(  # Find first site matching selector by UUID or case-insensitive name.
                (
                    site
                    for site in sites_data
                    if site.get("id") == site_selector or site.get("name", "").lower() == site_selector.lower()
                ),
                None,
            )
            if matching_site:
                test_site_id = matching_site["id"]  # Store matched site ID for downstream interactive-safe operations.
                test_site_name = matching_site.get(
                    "name", "Unknown"
                )  # Store matched site name for user-visible context.
                print(
                    f"   Using test site from MIST_INTERACTIVE_TEST_SITE: {test_site_name} ({test_site_id})"
                )  # Preserve legacy explicit selector-success message.
                logging.debug(
                    "Selector matched site_id=%s site_name=%s", test_site_id, test_site_name
                )  # Log selector match details.
            else:
                print(
                    f"   Warning: MIST_INTERACTIVE_TEST_SITE='{site_selector}' not found; "
                    "falling back to first available site."
                )
                logging.warning(
                    "INTERACTIVE_TEST: MIST_INTERACTIVE_TEST_SITE '%s' not found; using first available site.",
                    site_selector,
                )
        if not test_site_id:
            logging.info(
                "Resolving fallback test site using first available org site"
            )  # Log before fallback site lookup API call.
            sites_response = self.mistapi_module.api.v1.orgs.sites.listOrgSites(
                self.apisession, org_id, limit=1
            )  # Request first available site as deterministic fallback.
            if sites_response.data and len(sites_response.data) > 0:
                test_site_id = sites_response.data[0]["id"]  # Capture fallback site UUID for test execution.
                test_site_name = sites_response.data[0].get(
                    "name", "Unknown"
                )  # Capture fallback site name for visibility.
                print(
                    f"   Using first available test site: {test_site_name} ({test_site_id})"
                )  # Preserve legacy fallback message output.
        logging.debug(
            "Resolved interactive test site_id=%s site_name=%s", test_site_id, test_site_name
        )  # Log final resolution result for caller context.
        return test_site_id, test_site_name  # Return resolved site context used by execute() workflow.

    def _print_suite_header(self) -> None:
        """Print suite banner preserved verbatim from legacy execute() output."""
        print(" Starting interactive test of MistHelper menu options...")  # Preserve legacy header text.
        print("  Note: This tests read-only operations requiring site/device/client selection")  # Preserve note.
        print(f"! Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")  # Preserve start-time line.
        print("=" * 80)  # Preserve legacy visual divider.

    def _build_option_lists(self) -> tuple[list[str], list[str], list[str]]:
        """Return (all_options, interactive_options, skip_list) using stable legacy ordering."""
        logging.info("Building interactive option lists from menu actions")  # Log before list-build action.
        all_options = sorted(
            self.menu_actions.keys(), key=lambda option: float(option.replace("a", ".1"))
        )  # Preserve legacy float-key ordering.
        interactive_options = self.operation_registry.interactive_safe_options(all_options)  # Filter safe options.
        skip_list = [
            option for option in all_options if not self.operation_registry.is_interactive_safe(option)
        ]  # Build skip list mirroring legacy filter.
        logging.debug(
            "Built option lists: %d interactive, %d skipped", len(interactive_options), len(skip_list)
        )  # Log list-build result.
        return all_options, interactive_options, skip_list  # Return triple consumed by execute().

    def _print_option_listings(self, interactive_options: list[str], skip_list: list[str]) -> None:
        """Print the tested-and-skipped option listings preserving legacy formatting."""
        print(f"! Found {len(interactive_options)} interactive read-only options to test")  # Preserve count line.
        print(f"! {len(skip_list)} options will be skipped")  # Preserve skip-count line.
        print()  # Preserve blank line spacing.
        print(" Testing interactive read-only operations:")  # Preserve tested section header.
        for option in interactive_options:
            if option in self.menu_actions:
                _, description = self.menu_actions[option]  # Resolve description for option listing.
                print(f"   {option:>3}: {description}")  # Preserve per-option tested listing.
        print()  # Preserve spacing between sections.
        print(" Skipping non-interactive-safe operations:")  # Preserve skipped section header.
        for option in skip_list:
            if option in self.menu_actions:
                reason = self.operation_registry.skip_reason(option)  # Resolve registry skip reason.
                if reason:
                    print(f"   {option:>3}: {reason}")  # Preserve per-option skip-reason listing.
        print()  # Preserve spacing before telemetry setup.

    def _create_emitter(self) -> tuple[Any, Any]:
        """Initialize telemetry emitter; return (emitter, path) tuple."""
        logging.info("Creating telemetry emitter for interactive test run")  # Log before emitter setup.
        telemetry_path = self.telemetry_emitter_cls.timestamped_path("data")  # Generate timestamped path.
        emitter = self.telemetry_emitter_cls(telemetry_path)  # Construct emitter instance.
        logging.debug("Telemetry emitter initialized with path: %s", telemetry_path)  # Log emitter destination.
        return emitter, telemetry_path  # Return tuple so callers do not depend on emitter attribute layout.

    def _emit_skip_events(self, emitter: Any, skip_list: list[str]) -> int:
        """Emit telemetry skip events for non-interactive-safe options and return skip count."""
        skip_count = 0  # Initialize skip counter.
        for option in skip_list:
            if option in self.menu_actions:
                _, op_name = self.menu_actions[option]  # Resolve op-name for skip event payload.
                logging.info("Emitting telemetry skip event for option %s", option)  # Log before skip emission.
                emitter.emit_test_skip(
                    option,
                    op_name,
                    self.operation_registry.skip_reason(option),
                    self.operation_registry.skip_category(option),
                    "interactive",
                )  # Emit skip event for option.
                skip_count += 1  # Increment skip counter.
        logging.debug("Emitted %d skip telemetry events", skip_count)  # Log skip emission summary.
        return skip_count  # Return count for summary reporting.

    def _ensure_org_id(self) -> str:
        """Return cached org_id or resolve and persist a new one."""
        org_id = self.org_id_getter()  # Retrieve cached org_id.
        if not org_id:
            logging.info("No cached org_id present; resolving via config utils")  # Log before resolution.
            org_id = self.config_utils.get_cached_or_prompted_org_id()  # Resolve org_id via utils.
            self.org_id_setter(org_id)  # Persist resolved org_id.
            logging.debug("Resolved and stored org_id=%s", org_id)  # Log resolution result.
        return org_id  # Return org_id for downstream site resolution.

    def _resolve_site_or_close(self, org_id: str, emitter: Any) -> tuple[str | None, str]:
        """Resolve test site context; close emitter and return (None, '') on failure paths."""
        try:
            print("   Fetching test site for interactive operations...")  # Preserve legacy cue.
            test_site_id, test_site_name = self._resolve_test_site(org_id)  # Resolve test site.
            if test_site_id:
                logging.info(
                    "INTERACTIVE_TEST: Using test site_id=%s name=%s", test_site_id, test_site_name
                )  # Log selected site context.
                return test_site_id, test_site_name  # Return resolved context on success.
            print("[ERROR] No sites found in organization - cannot run interactive tests")  # Preserve no-site error.
            logging.error("INTERACTIVE_TEST: No sites available for testing")  # Log no-site terminal condition.
        except Exception as error:
            print(f"[ERROR] Failed to fetch test site: {error}")  # Preserve fetch-failure message.
            logging.error("INTERACTIVE_TEST: Failed to fetch test site: %s", error)  # Log exception context.
        logging.info("Closing telemetry emitter after site-resolution failure")  # Log before close on failure.
        emitter.close()  # Close emitter to flush events on failure path.
        logging.debug("Telemetry emitter closed after site-resolution failure")  # Log close completion.
        return None, ""  # Signal caller to abort suite.

    def _invoke_option(self, option: str, test_site_id: str | None) -> None:
        """Invoke a single menu option callable with prepared kwargs."""
        function, _description = self.menu_actions[option]  # Resolve callable for option.
        signature = inspect.signature(function)  # Inspect signature to gate kwargs injection.
        invoke_kwargs: dict[str, Any] = {}  # Initialize kwargs payload.
        if "site_id" in signature.parameters:
            invoke_kwargs["site_id"] = test_site_id  # Inject resolved site when callable accepts it.
        logging.debug("Invoking option %s with kwargs=%s", option, invoke_kwargs)  # Log invocation kwargs.
        function(**invoke_kwargs)  # Execute target interactive-safe operation.

    def _run_single_option(self, index: int, total: int, option: str, test_site_id: str | None, emitter: Any) -> bool:
        """Run a single interactive option, emit telemetry, and return True on success."""
        _function, description = self.menu_actions[option]  # Resolve description for progress output.
        print(
            f"   [{index:2}/{total}] Testing option {option:>3}: {description[:60]}..."
        )  # Preserve per-option progress line.
        logging.info("Emitting telemetry start event for option %s", option)  # Log before start emission.
        emitter.emit_test_start(option, description, "interactive")  # Emit start event.
        logging.debug("Telemetry start event emitted for option %s", option)  # Log start emission completion.
        op_start = time.time()  # Capture per-option start timestamp.
        logging.info(
            "INTERACTIVE_TEST: Starting test of menu option %s description='%s'", option, description
        )  # Log before invocation.
        try:
            self._invoke_option(option, test_site_id)  # Invoke the menu callable.
            duration = time.time() - op_start  # Compute success duration.
            print(f"   [SUCCESS] Option {option} completed successfully")  # Preserve success message.
            logging.info("Emitting telemetry pass event for option %s", option)  # Log before pass emission.
            emitter.emit_test_pass(option, description, duration, "interactive")  # Emit pass event.
            logging.debug("Telemetry pass event emitted for option %s", option)  # Log pass completion.
            logging.info("INTERACTIVE_TEST: Successfully completed menu option %s", option)  # Log success.
            return True  # Signal success to caller.
        except Exception as error:
            duration = time.time() - op_start  # Compute failure duration.
            print(f"   [FAILED]  Option {option} failed: {str(error)[:100]}...")  # Preserve failure message.
            logging.info("Emitting telemetry fail event for option %s", option)  # Log before fail emission.
            emitter.emit_test_fail(option, description, duration, error, "interactive")  # Emit fail event.
            logging.debug("Telemetry fail event emitted for option %s", option)  # Log fail completion.
            logging.error("INTERACTIVE_TEST: Failed menu option %s: %s", option, error)  # Log option failure.
            return False  # Signal failure to caller.

    def _run_option_loop(
        self, interactive_options: list[str], test_site_id: str | None, emitter: Any
    ) -> tuple[int, int]:
        """Iterate interactive options, executing each and tallying successes/failures."""
        success_count = 0  # Initialize success counter.
        error_count = 0  # Initialize failure counter.
        total = len(interactive_options)  # Cache total for progress display.
        for index, option in enumerate(interactive_options, 1):
            if option not in self.menu_actions:
                continue  # Skip options missing from dispatch table.
            if self._run_single_option(index, total, option, test_site_id, emitter):
                success_count += 1  # Increment success counter on pass.
            else:
                error_count += 1  # Increment failure counter on fail.
            time.sleep(1)  # Preserve legacy pacing delay between options.
        return success_count, error_count  # Return tally for summary reporting.

    def _finalize_telemetry(
        self,
        emitter: Any,
        total_ops: int,
        success_count: int,
        error_count: int,
        skip_count: int,
        total_time: float,
    ) -> None:
        """Emit summary event, close emitter, and enforce retention policy."""
        logging.info("Emitting telemetry summary for interactive test suite")  # Log before summary emission.
        emitter.emit_test_summary(
            total_ops, success_count, error_count, skip_count, total_time, "interactive"
        )  # Emit aggregate metrics.
        logging.debug("Telemetry summary event emitted successfully")  # Log summary completion.
        logging.info("Closing telemetry emitter after interactive suite completion")  # Log before close.
        emitter.close()  # Flush pending events.
        logging.debug("Telemetry emitter closed successfully")  # Log close completion.
        logging.info("Applying telemetry retention policy")  # Log before retention enforcement.
        emitter.enforce_retention()  # Prune old telemetry files.
        logging.debug("Telemetry retention policy enforcement completed")  # Log retention completion.

    def _print_summary(
        self,
        success_count: int,
        error_count: int,
        skip_count: int,
        interactive_total: int,
        total_time: float,
        telemetry_path: Any,
    ) -> bool:
        """Print the legacy summary block and return overall suite pass/fail status."""
        print()  # Preserve blank line before summary.
        print("=" * 80)  # Preserve summary separator line.
        print(" Interactive Test Summary:")  # Preserve summary title.
        print(f"   Successful operations: {success_count}")  # Preserve success count line.
        print(f"   Failed operations: {error_count}")  # Preserve failure count line.
        print(f"   Skipped operations: {skip_count}")  # Preserve skip count line.
        print(
            f"   Total interactive read-only coverage: {success_count}/{interactive_total} "
            f"({success_count / interactive_total * 100:.1f}%)"
        )  # Preserve coverage formatting.
        print(f"   Total execution time: {total_time:.2f} seconds")  # Preserve duration line.
        print(f"   Telemetry written to: {telemetry_path}")  # Preserve telemetry-path line.
        print("   Detailed logs in: script.log")  # Preserve log-guidance line.
        if error_count == 0:
            print("   All tested interactive operations completed successfully!")  # Preserve all-pass banner.
            logging.info(
                "INTERACTIVE_TEST: All %s tested operations completed successfully in %.2fs",
                success_count,
                total_time,
            )
            return True  # Return pass status.
        print(f"   {error_count} operations failed - check logs for details")  # Preserve failure summary line.
        logging.warning("INTERACTIVE_TEST: %s operations failed out of %s tested", error_count, interactive_total)
        return False  # Return failure status.

    def execute(self) -> bool:
        """Run the interactive-safe systematic test suite."""
        logging.info("Starting interactive-safe systematic test suite")  # Log suite entry boundary.
        start_time = time.time()  # Capture suite start timestamp.
        self._print_suite_header()  # Emit legacy header block.
        all_options, interactive_options, skip_list = self._build_option_lists()  # Build option lists.
        self._print_option_listings(interactive_options, skip_list)  # Emit option listings.
        emitter, telemetry_path = self._create_emitter()  # Initialize telemetry emitter; capture path.
        skip_count = self._emit_skip_events(emitter, skip_list)  # Emit skip events and tally count.
        org_id = self._ensure_org_id()  # Resolve org_id with cache fallback.
        test_site_id, _site_name = self._resolve_site_or_close(org_id, emitter)  # Resolve site context.
        if not test_site_id:
            return False  # Abort because prerequisite site could not be resolved.
        print()  # Preserve spacing before per-option execution loop.
        success_count, error_count = self._run_option_loop(
            interactive_options, test_site_id, emitter
        )  # Execute option loop.
        total_time = time.time() - start_time  # Compute total suite runtime.
        self._finalize_telemetry(
            emitter, len(all_options), success_count, error_count, skip_count, total_time
        )  # Emit summary, close emitter, enforce retention.
        return self._print_summary(
            success_count, error_count, skip_count, len(interactive_options), total_time, telemetry_path
        )  # Print summary and return suite status.
