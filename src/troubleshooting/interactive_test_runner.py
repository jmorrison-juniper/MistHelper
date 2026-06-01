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

    def execute(self) -> bool:
        """Run the interactive-safe systematic test suite."""
        logging.info(
            "Starting interactive-safe systematic test suite"
        )  # Log suite entry so lifecycle boundaries are visible.
        start_time = time.time()  # Capture suite start timestamp for duration calculation and summary output.
        print(
            " Starting interactive test of MistHelper menu options..."
        )  # Preserve legacy suite header text for operator familiarity.
        print(
            "  Note: This tests read-only operations requiring site/device/client selection"
        )  # Preserve legacy suite note for operator context.
        print(
            f"! Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )  # Preserve legacy human-readable start time output.
        print("=" * 80)  # Preserve legacy visual divider for output readability.
        all_options = sorted(
            self.menu_actions.keys(), key=lambda option: float(option.replace("a", ".1"))
        )  # Build stable menu option order matching existing harness behavior.
        interactive_options = self.operation_registry.interactive_safe_options(
            all_options
        )  # Select options safe for interactive read-only testing.
        skip_list = [
            option for option in all_options if not self.operation_registry.is_interactive_safe(option)
        ]  # Build skip list for non-interactive-safe options.
        logging.debug(
            "Interactive suite has %d testable options and %d skipped options", len(interactive_options), len(skip_list)
        )  # Log option-count summary.
        print(
            f"! Found {len(interactive_options)} interactive read-only options to test"
        )  # Preserve legacy count output for tested options.
        print(f"! {len(skip_list)} options will be skipped")  # Preserve legacy count output for skipped options.
        print()  # Preserve blank-line formatting used by existing terminal output.
        print(" Testing interactive read-only operations:")  # Preserve legacy section header for option list.
        for option in interactive_options:
            if option in self.menu_actions:
                _, description = self.menu_actions[option]  # Retrieve description for user-visible option listing.
                print(f"   {option:>3}: {description}")  # Preserve legacy listing output format for tested options.
        print()  # Preserve spacing between tested and skipped sections.
        print(" Skipping non-interactive-safe operations:")  # Preserve legacy section header for skipped options.
        for option in skip_list:
            if option in self.menu_actions:
                reason = self.operation_registry.skip_reason(
                    option
                )  # Resolve skip reason from operation registry metadata.
                if reason:
                    print(f"   {option:>3}: {reason}")  # Preserve legacy skip-reason output formatting.
        print()  # Preserve spacing before telemetry initialization and execution loop.
        logging.info("Creating telemetry emitter for interactive test run")  # Log before telemetry setup action.
        telemetry_path = self.telemetry_emitter_cls.timestamped_path(
            "data"
        )  # Generate deterministic timestamped telemetry output path.
        emitter = self.telemetry_emitter_cls(
            telemetry_path
        )  # Initialize telemetry emitter used for start/pass/fail/summary events.
        logging.debug(
            "Telemetry emitter initialized with path: %s", telemetry_path
        )  # Log telemetry destination for auditability.
        skip_count = 0  # Initialize skip counter for summary reporting.
        for option in skip_list:
            if option in self.menu_actions:
                _, op_name = self.menu_actions[option]  # Resolve operation name for telemetry skip event payload.
                logging.info(
                    "Emitting telemetry skip event for option %s", option
                )  # Log before skip-event emission action.
                emitter.emit_test_skip(
                    option,
                    op_name,
                    self.operation_registry.skip_reason(option),
                    self.operation_registry.skip_category(option),
                    "interactive",
                )
                skip_count += 1  # Increment skip counter after successful skip-event emission.
        logging.debug("Emitted %d skip telemetry events", skip_count)  # Log skip-event emission result summary.
        success_count = 0  # Initialize success counter for tested operations.
        error_count = 0  # Initialize failure counter for tested operations.
        org_id = self.org_id_getter()  # Retrieve current org_id from shared runtime state.
        if not org_id:
            logging.info(
                "No cached org_id present; resolving org_id via config utils"
            )  # Log before fallback org-id resolution action.
            org_id = (
                self.config_utils.get_cached_or_prompted_org_id()
            )  # Resolve org ID using established runtime resolution pathway.
            self.org_id_setter(org_id)  # Persist resolved org ID back to shared runtime state.
            logging.debug("Resolved and stored org_id=%s", org_id)  # Log org-id resolution result.
        try:
            print(
                "   Fetching test site for interactive operations..."
            )  # Preserve legacy operator cue before test-site resolution.
            test_site_id, test_site_name = self._resolve_test_site(
                org_id
            )  # Resolve test site used by site-aware interactive operations.
            if test_site_id:
                logging.info(
                    "INTERACTIVE_TEST: Using test site_id=%s name=%s", test_site_id, test_site_name
                )  # Log selected test-site context.
            else:
                print(
                    "[ERROR] No sites found in organization - cannot run interactive tests"
                )  # Preserve legacy no-site error for operator visibility.
                logging.error("INTERACTIVE_TEST: No sites available for testing")  # Log no-site terminal condition.
                logging.info(
                    "Closing telemetry emitter after no-site terminal condition"
                )  # Log before telemetry close action.
                emitter.close()  # Close telemetry emitter to flush events before early return.
                logging.debug(
                    "Telemetry emitter closed after no-site terminal condition"
                )  # Log telemetry close completion.
                return False  # Return failure because suite cannot execute without a valid test site.
        except Exception as error:
            print(
                f"[ERROR] Failed to fetch test site: {error}"
            )  # Preserve legacy fetch-failure message for operator visibility.
            logging.error(
                "INTERACTIVE_TEST: Failed to fetch test site: %s", error
            )  # Log site-resolution exception context.
            logging.info(
                "Closing telemetry emitter after test-site resolution exception"
            )  # Log before telemetry close on exception path.
            emitter.close()  # Close telemetry emitter to avoid handle leak on exception path.
            logging.debug("Telemetry emitter closed after site-resolution exception")  # Log telemetry close completion.
            return False  # Return failure because prerequisite test site could not be resolved.
        print()  # Preserve legacy spacing before per-option execution loop.
        for index, option in enumerate(interactive_options, 1):
            if option not in self.menu_actions:
                continue  # Skip options missing from dispatch table to preserve defensive behavior.
            function, description = self.menu_actions[
                option
            ]  # Resolve callable and description for current menu option.
            print(
                f"   [{index:2}/{len(interactive_options)}] Testing option {option:>3}: {description[:60]}..."
            )  # Preserve legacy per-option progress output.
            logging.info(
                "Emitting telemetry start event for option %s", option
            )  # Log before telemetry start-event emission.
            emitter.emit_test_start(
                option, description, "interactive"
            )  # Emit start event so telemetry captures per-option lifecycle.
            logging.debug("Telemetry start event emitted for option %s", option)  # Log start-event emission completion.
            op_start = time.time()  # Capture option start timestamp for duration metrics.
            logging.info(
                "INTERACTIVE_TEST: Starting test of menu option %s description='%s'", option, description
            )  # Log before invoking menu callable.
            try:
                signature = inspect.signature(
                    function
                )  # Inspect callable signature so only supported kwargs are injected.
                invoke_kwargs = {}  # Initialize dynamic kwargs payload for callable invocation.
                if "site_id" in signature.parameters:
                    invoke_kwargs["site_id"] = (
                        test_site_id  # Inject resolved test site when callable supports site-scoped execution.
                    )
                logging.debug(
                    "Invoking option %s with kwargs=%s", option, invoke_kwargs
                )  # Log invocation arguments for diagnosability.
                function(**invoke_kwargs)  # Execute target interactive-safe operation using prepared kwargs.
                duration = time.time() - op_start  # Compute operation duration for telemetry and summary reporting.
                print(
                    f"   [SUCCESS] Option {option} completed successfully"
                )  # Preserve legacy success message for operator visibility.
                success_count += 1  # Increment success counter after successful invocation.
                logging.info(
                    "Emitting telemetry pass event for option %s", option
                )  # Log before telemetry pass-event emission.
                emitter.emit_test_pass(
                    option, description, duration, "interactive"
                )  # Emit pass event with duration for traceable success metrics.
                logging.debug(
                    "Telemetry pass event emitted for option %s", option
                )  # Log pass-event emission completion.
                logging.info(
                    "INTERACTIVE_TEST: Successfully completed menu option %s", option
                )  # Log successful option completion.
            except Exception as error:
                duration = time.time() - op_start  # Compute failure-case duration for telemetry consistency.
                print(
                    f"   [FAILED]  Option {option} failed: {str(error)[:100]}..."
                )  # Preserve legacy truncated failure message for operator readability.
                error_count += 1  # Increment failure counter after exception.
                logging.info(
                    "Emitting telemetry fail event for option %s", option
                )  # Log before telemetry fail-event emission.
                emitter.emit_test_fail(
                    option, description, duration, error, "interactive"
                )  # Emit fail event with error payload for post-run analysis.
                logging.debug(
                    "Telemetry fail event emitted for option %s", option
                )  # Log fail-event emission completion.
                logging.error(
                    "INTERACTIVE_TEST: Failed menu option %s: %s", option, error
                )  # Log option failure for runbook troubleshooting.
            time.sleep(1)  # Preserve one-second pacing delay to avoid rapid-fire API calls during test loops.
        total_time = time.time() - start_time  # Compute total suite runtime for summary and telemetry.
        total_ops = len(all_options)  # Capture total menu-option count for coverage summary calculations.
        logging.info("Emitting telemetry summary for interactive test suite")  # Log before summary-event emission.
        emitter.emit_test_summary(
            total_ops, success_count, error_count, skip_count, total_time, "interactive"
        )  # Emit aggregate run metrics event.
        logging.debug("Telemetry summary event emitted successfully")  # Log summary-event emission completion.
        logging.info(
            "Closing telemetry emitter after interactive suite completion"
        )  # Log before telemetry close action.
        emitter.close()  # Close emitter to flush pending events to disk.
        logging.debug("Telemetry emitter closed successfully")  # Log telemetry close completion.
        logging.info("Applying telemetry retention policy")  # Log before retention policy enforcement action.
        emitter.enforce_retention()  # Enforce retention policy so old telemetry files are pruned.
        logging.debug("Telemetry retention policy enforcement completed")  # Log retention action completion.
        print()  # Preserve blank line before summary section.
        print("=" * 80)  # Preserve legacy summary separator line.
        print(" Interactive Test Summary:")  # Preserve legacy summary title.
        print(f"   Successful operations: {success_count}")  # Preserve legacy success-count output.
        print(f"   Failed operations: {error_count}")  # Preserve legacy failure-count output.
        print(f"   Skipped operations: {skip_count}")  # Preserve legacy skip-count output.
        print(
            f"   Total interactive read-only coverage: {success_count}/{len(interactive_options)} "
            f"({success_count / len(interactive_options) * 100:.1f}%)"
        )  # Preserve legacy coverage summary formatting and calculation behavior.
        print(f"   Total execution time: {total_time:.2f} seconds")  # Preserve legacy duration summary output.
        print(f"   Telemetry written to: {telemetry_path}")  # Preserve telemetry location output for operators.
        print("   Detailed logs in: script.log")  # Preserve guidance for deeper troubleshooting logs.
        if error_count == 0:
            print(
                "   All tested interactive operations completed successfully!"
            )  # Preserve all-pass success banner for operators.
            logging.info(
                "INTERACTIVE_TEST: All %s tested operations completed successfully in %.2fs",
                success_count,
                total_time,
            )
            return True  # Return pass status when all tested options succeeded.
        print(
            f"   {error_count} operations failed - check logs for details"
        )  # Preserve failure summary message when errors occurred.
        logging.warning(
            "INTERACTIVE_TEST: %s operations failed out of %s tested", error_count, len(interactive_options)
        )
        return False  # Return failure status so caller can propagate non-zero exit semantics.
