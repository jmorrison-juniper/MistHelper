"""Reporting cluster for :mod:`src.gateway.wan2_variable`.

Handles audit CSV emission, template/device summary blocks, final guidance
copy for dry-run vs live modes, and the summary log line. Split out so the
parent stays under STRUCT-LENGTH and each print helper stays under
CC/length budgets.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import logging  # WHY: audit-log the summary line at the end of the flow
from typing import Any  # WHY: result payloads are heterogenous dicts

from ._wan2_variable_cluster import _ClusterBase  # WHY: parent-proxy pattern shared with peers


class _Wan2VariableReporting(_ClusterBase):
    """Audit reports + final-summary helpers."""

    def _generate_reports(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Generate audit reports and print final summary."""
        output_file = "GatewayTemplate_WAN2_Migration_Audit.csv"  # WHY: fixed name for audit CSV
        self._save_data(results, output_file)  # WHY: persist template audit via injected saver
        self._print_template_summary(results)  # WHY: banner + counts
        self._print_device_summary(device_results, devices_needing_migration)  # WHY: banner + counts
        self._print_report_paths(output_file, devices_needing_migration)  # WHY: file locations block
        self._print_final_guidance(results, device_results, devices_needing_migration)  # WHY: guidance block

    def _print_template_summary(self, results: list[dict[str, Any]]) -> None:
        """Print template migration summary."""
        if self._dry_run:  # WHY: dry-run gets preview-tone copy
            self._print_template_dry_run(results)  # WHY: extracted for length budget
            return  # WHY: skip live-mode branch
        self._print_template_live(results)  # WHY: extracted for length budget

    @staticmethod
    def _print_template_dry_run(results: list[dict[str, Any]]) -> None:
        """Print the DRY-RUN template summary block."""
        dry_count = sum(1 for r in results if r["status"] == "DRY-RUN")  # WHY: preview counter
        print("\n  WAN2 Variable Migration DRY-RUN Complete!")  # WHY: banner
        print("=" * 70)  # WHY: visual separator
        print("  >> DRY-RUN MODE: No actual changes were made")  # WHY: mode reminder
        print("  TEMPLATE MIGRATION PREVIEW:")  # WHY: section label
        print(f"    Templates Analyzed: {len(results)}")  # WHY: total
        print(f"    Would Be Updated: {dry_count}")  # WHY: preview count
        print(f"    Skipped: {len(results) - dry_count}")  # WHY: derived skip count

    @staticmethod
    def _print_template_live(results: list[dict[str, Any]]) -> None:
        """Print the LIVE-mode template summary block."""
        success = sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: success counter
        failed = len(results) - success  # WHY: derive failure count
        print("\n  WAN2 Variable Migration Complete!")  # WHY: banner
        print("=" * 70)  # WHY: visual separator
        print("  TEMPLATE MIGRATION:")  # WHY: section label
        print(f"    Templates Processed: {len(results)}")  # WHY: total
        print(f"    Successfully Updated: {success}")  # WHY: success count
        print(f"    Failed: {failed}")  # WHY: failure count

    def _print_device_summary(
        self,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print device migration summary section."""
        if not devices_needing_migration:  # WHY: skip block entirely when zero devices affected
            return  # WHY: nothing to summarize
        if self._dry_run:  # WHY: dry-run gets preview-tone copy
            self._print_device_dry_run(device_results)  # WHY: extracted for length budget
            return  # WHY: skip live-mode branch
        self._print_device_live(device_results)  # WHY: extracted for length budget

    @staticmethod
    def _print_device_dry_run(device_results: list[dict[str, Any]]) -> None:
        """Print the DRY-RUN device summary block."""
        dry_count = sum(1 for r in device_results if r["status"] == "DRY-RUN")  # WHY: preview counter
        print("\n  DEVICE OVERRIDE MIGRATION PREVIEW:")  # WHY: section label
        print(f"    Devices Analyzed: {len(device_results)}")  # WHY: total
        print(f"    Would Preserve Static IPs: {dry_count}")  # WHY: preview count
        print(f"    Skipped: {len(device_results) - dry_count}")  # WHY: derived skip count

    @staticmethod
    def _print_device_live(device_results: list[dict[str, Any]]) -> None:
        """Print the LIVE-mode device summary block."""
        success = sum(1 for r in device_results if r["status"] == "SUCCESS")  # WHY: success counter
        failed = len(device_results) - success  # WHY: derive failure count
        print("\n  DEVICE OVERRIDE MIGRATION:")  # WHY: section label
        print(f"    Devices Processed: {len(device_results)}")  # WHY: total
        print(f"    Static IPs Preserved: {success}")  # WHY: success count
        print(f"    Failed: {failed}")  # WHY: failure count

    @staticmethod
    def _print_report_paths(
        output_file: str,
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print report file locations."""
        print("\n  REPORTS:")  # WHY: section label
        print(f"    Template audit: {output_file}")  # WHY: template CSV location
        if devices_needing_migration:  # WHY: only mention device CSV when it exists
            print("    Device migration:" " GatewayDevice_WAN2_Override_Migration.csv")  # WHY: device CSV loc
        print("=" * 70)  # WHY: closing separator

    def _print_final_guidance(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print final guidance and warnings."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: success counter
        failure_count = 0 if self._dry_run else len(results) - success_count  # WHY: dry-run has no failures
        self._dispatch_mode_guidance(results, device_results, devices_needing_migration, success_count)  # WHY: extract
        self._print_template_failure_warning(failure_count)  # WHY: extracted to cut CC
        self._print_device_failure_warning(device_results, devices_needing_migration)  # WHY: device warnings
        self._log_operation_summary(success_count, failure_count, device_results, devices_needing_migration)  # WHY: audit

    def _dispatch_mode_guidance(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
        success_count: int,
    ) -> None:
        """Dispatch to dry-run or live guidance based on operation mode."""
        if self._dry_run:  # WHY: mode-specific guidance
            self._print_dry_run_guidance(results, device_results, devices_needing_migration)  # WHY: preview copy
            return  # WHY: skip live branch
        self._print_live_guidance(success_count, device_results, devices_needing_migration)  # WHY: live copy

    @staticmethod
    def _print_template_failure_warning(failure_count: int) -> None:
        """Print a warning line when any templates failed to update."""
        if failure_count <= 0:  # WHY: silent when no failures
            return  # WHY: nothing to warn
        print(f"\n  !? {failure_count} templates failed" " to update - check audit report")  # WHY: warn

    @staticmethod
    def _print_device_failure_warning(
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print warnings for failed device migrations."""
        if not devices_needing_migration:  # WHY: skip block when no devices considered
            return  # WHY: nothing to warn about
        dev_failed = len(device_results) - sum(1 for r in device_results if r["status"] == "SUCCESS")
        if dev_failed > 0:  # WHY: only warn when at least one device failed
            print(f"\n  !? WARNING: {dev_failed}" " devices failed override migration")  # WHY: caution
            print("  !? These devices may lose" " static IP configurations")  # WHY: impact
            print("  !? Check" " GatewayDevice_WAN2_Override_Migration.csv" " for details")  # WHY: pointer

    def _log_operation_summary(
        self,
        success_count: int,
        failure_count: int,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Log operation summary for audit trail."""
        logging.warning(
            "Menu #104 DESTRUCTIVE operation complete (%s mode): %s templates updated, %s failed",
            self._operation_mode.upper(),
            success_count,
            failure_count,
        )  # WHY: keep parity with original audit line
        if not devices_needing_migration:  # WHY: skip device audit line when zero devices affected
            return  # WHY: no additional log needed
        dev_ok = sum(1 for r in device_results if r["status"] == "SUCCESS")  # WHY: success counter
        dev_fail = len(device_results) - dev_ok  # WHY: derive failure count
        logging.warning(
            "Device override migration (%s mode): %s successful, %s failed",
            self._operation_mode.upper(),
            dev_ok,
            dev_fail,
        )  # WHY: mirrors template audit line

    def _print_dry_run_guidance(
        self,
        results: list[dict[str, Any]],
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print dry-run specific guidance."""
        dry_count = sum(1 for r in results if r["status"] == "DRY-RUN")  # WHY: preview counter
        if dry_count <= 0:  # WHY: skip block when nothing previewed
            return  # WHY: no guidance to print
        print(f"\n  >> DRY-RUN: {dry_count} templates" " WOULD use {{wan2_interface}} variable")  # WHY: preview
        self._print_dry_run_device_lines(device_results, devices_needing_migration)  # WHY: extracted to cut CC
        print("\n  >> To apply these changes," " run without --dry-run flag")  # WHY: nudge
        print("  >> Ensure all affected sites have" " 'wan2_interface' variable set (Menu #103)")  # WHY: prereq

    @staticmethod
    def _print_dry_run_device_lines(
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Emit the device-specific preview lines when devices are in scope."""
        if not devices_needing_migration:  # WHY: silent when no devices affected
            return  # WHY: nothing to preview
        dev_dry = sum(1 for r in device_results if r["status"] == "DRY-RUN")  # WHY: device preview count
        print(f"  >> DRY-RUN: {dev_dry} devices" " WOULD have static IP overrides preserved")  # WHY: preview
        print("  >> DRY-RUN: Port configs WOULD migrate" " from 'ge-0/0/1' to '{{wan2_interface}}'")  # WHY: preview

    @staticmethod
    def _print_live_guidance(
        success_count: int,
        device_results: list[dict[str, Any]],
        devices_needing_migration: list[dict[str, Any]],
    ) -> None:
        """Print live-mode specific guidance."""
        if success_count <= 0:  # WHY: skip block when nothing succeeded
            return  # WHY: no guidance to print
        print(f"\n  !? {success_count} templates" " now use {{wan2_interface}} variable")  # WHY: outcome
        if devices_needing_migration:  # WHY: mention devices only when in scope
            dev_ok = sum(1 for r in device_results if r["status"] == "SUCCESS")  # WHY: device success count
            print(f"  !? {dev_ok} devices had" " static IP overrides preserved")  # WHY: outcome
            print("  !? Port configs migrated" " from 'ge-0/0/1' to '{{wan2_interface}}'")  # WHY: outcome
        print("  !? Ensure all affected sites have" " 'wan2_interface' variable set (Menu #103)")  # WHY: prereq
        print("  !? Sites without the variable" " may experience gateway connectivity issues")  # WHY: caution
