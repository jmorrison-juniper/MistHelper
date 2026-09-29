"""Menu operation 287 for RMA device replacement through Mist inventory."""

from __future__ import annotations  # WHY: keep annotations lightweight during import.

import logging  # WHY: log each operator action and result.
import sys  # WHY: detect --dry-run until root wiring passes arguments explicitly.
from pathlib import Path  # WHY: type backup paths in the operation result.

from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: reach shared session and prompts.
from src.inventory.device_replace.client import DeviceReplaceClient  # WHY: one seam wraps Mist API calls.
from src.inventory.device_replace.models import DeviceReplaceLogEntry, DeviceReplaceValidator, InventoryDevice  # WHY.
from src.inventory.device_replace.persistence import DeviceReplacePersistence  # WHY: one seam writes evidence files.

logger = logging.getLogger(__name__)  # WHY: module log records identify menu 287.

CONFIRM_WORD = "REPLACE"  # WHY: destructive replacement requires this exact operator confirmation.


class DeviceReplaceOperation:
    """Run the destructive RMA device replacement workflow."""

    @staticmethod
    def run() -> None:
        """Run menu 287 with shared MistHelper dependencies."""
        logger.info("Menu #287: Starting RMA device replacement")  # WHY: name the destructive operation.
        org_id = str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id())  # WHY: org scope.
        client = DeviceReplaceClient(SourceDependencyResolver.apisession, org_id)  # WHY: Mist API seam.
        persistence = DeviceReplacePersistence()  # WHY: evidence files go under the default data directory.
        dry_run = "--dry-run" in sys.argv  # WHY: integration wiring can pass the existing process flag.
        DeviceReplaceOperation.run_with_dependencies(org_id, client, persistence, dry_run)  # WHY: tested core flow.

    @staticmethod
    def run_with_dependencies(
        org_id: str,
        client: DeviceReplaceClient,
        persistence: DeviceReplacePersistence,
        dry_run: bool,
    ) -> None:
        """Run the replacement workflow with injected dependencies."""
        try:  # WHY: one boundary records operator-readable validation failures.
            devices = client.list_inventory()  # WHY: old and replacement selection both use inventory.
            old_device = DeviceReplaceOperation._select_old_device(devices)  # WHY: operator chooses the source.
            new_device = DeviceReplaceOperation._select_new_device(devices, old_device)  # WHY: operator chooses target.
            DeviceReplaceValidator.validate_pair(old_device, new_device)  # WHY: stop before backup on mismatch.
            DeviceReplaceOperation._print_summary(old_device, new_device, dry_run)  # WHY: operator sees impact.
            configuration = client.get_old_configuration(old_device)  # WHY: backup must contain old configuration.
            backup_path = persistence.write_backup(org_id, old_device, configuration)  # WHY: required before request.
            DeviceReplaceOperation._confirm_and_replace(
                org_id, client, persistence, old_device, new_device, backup_path, dry_run
            )
        except ValueError as error:  # WHY: validation errors should be clear and nonfatal.
            logger.error("RMA device replacement stopped: %s", error)  # WHY: operator sees the exact guard.

    @staticmethod
    def _select_old_device(devices: list[InventoryDevice]) -> InventoryDevice:
        """Prompt for and return the old device."""
        logger.info("Prompting for the old RMA device selector")  # WHY: action log before input.
        selector = SourceDependencyResolver.InputUtils.safe_input(
            "Enter old device MAC address or name: ", context="rma_device_replace_old_device"
        ).strip()
        logger.debug("Received old device selector length=%d", len(selector))  # WHY: do not log the selector itself.
        return DeviceReplaceValidator.find_old_device(devices, selector)  # WHY: model owns deterministic lookup.

    @staticmethod
    def _select_new_device(devices: list[InventoryDevice], old_device: InventoryDevice) -> InventoryDevice:
        """Prompt for and return the replacement device."""
        choices = DeviceReplaceValidator.replacement_choices(devices, old_device)  # WHY: show only valid defaults.
        if not choices:  # WHY: no valid replacement means no backup or request should happen.
            raise ValueError("No unassigned replacement device has the old device type.")  # WHY: operator guard.
        DeviceReplaceOperation._print_choices(choices)  # WHY: operator sees the candidate list.
        logger.info("Prompting for the replacement device choice")  # WHY: action log before input.
        choice = SourceDependencyResolver.InputUtils.safe_input(
            "Enter replacement number or MAC address: ", context="rma_device_replace_new_device"
        ).strip()
        logger.debug("Received replacement selector length=%d", len(choice))  # WHY: do not log the selector itself.
        return DeviceReplaceOperation._resolve_new_choice(choices, choice)  # WHY: support number or MAC input.

    @staticmethod
    def _print_choices(choices: list[InventoryDevice]) -> None:
        """Print the replacement candidates."""
        logger.info("Available unassigned replacement devices:")  # WHY: header for the numbered rows.
        for index, device in enumerate(choices, start=1):  # WHY: one-based choices are easier for operators.
            logger.info("  %d. %s", index, device.label())  # WHY: label includes name, MAC, model, and type.

    @staticmethod
    def _resolve_new_choice(choices: list[InventoryDevice], choice: str) -> InventoryDevice:
        """Return the replacement device selected by number or MAC address."""
        if choice.isdigit():  # WHY: numbered choice is the normal interactive path.
            index = int(choice) - 1  # WHY: convert one-based input to list index.
            if 0 <= index < len(choices):  # WHY: reject out-of-range numbers.
                return choices[index]  # WHY: valid numbered selection.
        normalized = InventoryDevice.normalize_mac(choice)  # WHY: MAC input can include separators.
        for device in choices:  # WHY: support direct MAC entry for copy and paste.
            if device.mac == normalized:  # WHY: match the normalized MAC.
                return device  # WHY: valid MAC selection.
        raise ValueError("Replacement selector did not match an available unassigned device.")  # WHY: stop safely.

    @staticmethod
    def _print_summary(old_device: InventoryDevice, new_device: InventoryDevice, dry_run: bool) -> None:
        """Print the replacement impact summary."""
        logger.info(
            "Old device site=%s name=%s model=%s type=%s",
            old_device.site_id,
            old_device.name,
            old_device.model,
            old_device.device_type,
        )
        logger.info("Old device mac=%s serial=%s", old_device.mac, old_device.serial)  # WHY: physical check.
        logger.info("New device mac=%s serial=%s model=%s", new_device.mac, new_device.serial, new_device.model)  # WHY.
        logger.info("Dry run mode is %s", "enabled" if dry_run else "disabled")  # WHY: operator sees request state.

    @staticmethod
    def _confirm_and_replace(
        org_id: str,
        client: DeviceReplaceClient,
        persistence: DeviceReplacePersistence,
        old_device: InventoryDevice,
        new_device: InventoryDevice,
        backup_path: Path,
        dry_run: bool,
    ) -> None:
        """Confirm the operation and send or skip the replace request."""
        logger.info("Prompting for destructive RMA replacement confirmation")  # WHY: action log before input.
        confirmation = SourceDependencyResolver.InputUtils.safe_input(
            "Type REPLACE to move the old device configuration to the new device: ",
            context="rma_device_replace_confirmation",
        ).strip()
        logger.debug("Received RMA confirmation match=%s", confirmation == CONFIRM_WORD)  # WHY: do not log raw input.
        if confirmation != CONFIRM_WORD:  # WHY: any other input cancels the destructive request.
            DeviceReplaceOperation._write_result(
                org_id, persistence, old_device, new_device, backup_path, "cancelled", "Confirmation did not match."
            )
            return  # WHY: no request is allowed without the exact confirmation.
        request = DeviceReplaceValidator.build_request(old_device, new_device)  # WHY: build only after confirmation.
        if dry_run:  # WHY: dry-run proves the workflow without changing Mist cloud state.
            DeviceReplaceOperation._write_result(
                org_id,
                persistence,
                old_device,
                new_device,
                backup_path,
                "dry_run",
                "Dry run completed. No request was sent.",
            )
            return  # WHY: dry-run stops before the destructive API call.
        result = client.replace_device(request)  # WHY: all safety gates passed, so send one request.
        message = str(result.get("message") or result.get("status") or "Replacement request sent.")  # WHY: row text.
        DeviceReplaceOperation._write_result(org_id, persistence, old_device, new_device, backup_path, "sent", message)

    @staticmethod
    def _write_result(
        org_id: str,
        persistence: DeviceReplacePersistence,
        old_device: InventoryDevice,
        new_device: InventoryDevice,
        backup_path: Path,
        result: str,
        message: str,
    ) -> None:
        """Write one durable operation result row."""
        entry = DeviceReplaceLogEntry(
            DeviceReplacePersistence.timestamp(),
            org_id,
            old_device.mac,
            new_device.mac,
            old_device.device_type,
            new_device.device_type,
            result,
            str(backup_path),
            message,
        )
        persistence.append_log(entry)  # WHY: durable evidence is required for every completed prompt flow.
        logger.info("RMA device replacement result=%s message=%s", result, message)  # WHY: final operator summary.
