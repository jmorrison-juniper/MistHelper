"""Import initialization orchestration extracted from high-complexity import manager method."""

import logging
import time
from typing import Any


class ImportInitializationService:
    """Owns import initialization flow formerly embedded in import manager method."""

    @staticmethod
    def _run_dependency_upgrade(manager: Any, skip_deps: bool) -> None:
        """Check and upgrade/install the uv toolchain unless dependency handling is skipped."""
        if skip_deps:  # --skip-deps short-circuits all dependency tooling
            logging.info("Dependency checking and installation skipped (--skip-deps flag)")  # Trace the skip
            return  # Nothing else to do when skipping
        if manager.auto_upgrade_uv:  # Only manage uv when auto-upgrade is enabled
            if not manager._check_uv_installation():  # uv missing - install it fresh
                manager._install_uv()  # Install the uv toolchain
            else:  # uv already present - upgrade in place
                manager._upgrade_uv()  # Upgrade the existing uv toolchain

    @staticmethod
    def _import_package_group(manager: Any, packages: dict[str, Any], required: bool, skip_deps: bool) -> None:
        """Import one package group (required or optional) concurrently or sequentially."""
        kind = "required" if required else "optional"  # Label used in user-facing log lines
        if not skip_deps and len(packages) > 3:  # Large groups import concurrently for speed
            manager._import_packages_concurrently(packages, required=required, skip_deps=skip_deps)  # Parallel path
            return  # Concurrent path handles its own per-package logging
        for module_name, package_spec in packages.items():  # Small groups import sequentially
            logging.info(
                "  Checking %s dependency: %s (%s)", kind, module_name, package_spec or "built-in"
            )  # Trace check
            result = manager.import_module_safely(
                module_name,
                package_spec,
                required=required,
                skip_deps=skip_deps,
                skip_upgrade=True,
            )  # Attempt the import (no upgrade here. Upgrades happen in the dependency phase)
            if result:  # Import succeeded
                logging.info("  [OK] %s: Available", module_name)  # Trace availability
            elif required:  # Required import failed - this is an error
                logging.error("  [FAIL] %s: Failed to import", module_name)  # Trace required failure
            else:  # Optional import failed - non-fatal warning
                logging.warning("  [WARN] %s: Not available", module_name)  # Trace optional absence

    @staticmethod
    def _log_summary(manager: Any, elapsed_time: float) -> None:
        """Compute and log the import initialization summary counters."""
        total_required = len(manager.required_packages)  # All required package count
        failed_required = len(
            [package_name for package_name in manager.failed_imports if package_name in manager.required_packages]
        )  # Required packages that failed to import
        successful_required = total_required - failed_required  # Required packages that imported successfully
        optional_imported = len(
            [package_name for package_name in manager.imports.keys() if package_name in manager.optional_packages]
        )  # Optional packages that imported successfully

        logging.info("Import initialization completed in %.2f seconds", elapsed_time)  # Trace elapsed time
        logging.info("Required dependencies: %s/%s successful", successful_required, total_required)  # Required summary
        logging.info("Optional dependencies: %s/%s available", optional_imported, len(manager.optional_packages))  # Opt

        if manager.installed_packages:  # Some packages were installed during this run
            logging.info("Newly installed packages: %s", ", ".join(manager.installed_packages))  # List installs

        if manager.failed_imports:  # Some imports failed
            logging.error("Failed imports: %s", ", ".join(manager.failed_imports))  # List failures

    @classmethod
    def execute(cls, manager: Any, skip_deps: bool = False) -> tuple[bool, dict[str, Any]]:
        """Run complete import initialization flow and return success plus global assignments."""
        if manager._initialization_complete:  # Idempotent - return cached results on repeat calls
            logging.debug("Import initialization already completed, returning cached results")  # Trace cache hit
            return manager._initialization_success, manager._cached_global_assignments  # Cached success + assignments

        start_time = time.time()  # Start timing the initialization
        logging.info("Initializing global import management system...")  # Trace workflow start

        cls._run_dependency_upgrade(manager, skip_deps)  # Phase 1: uv toolchain check/install/upgrade

        logging.info("Importing required dependencies...")  # Trace required-import phase
        cls._import_package_group(manager, manager.required_packages, True, skip_deps)  # Phase 2: required imports

        logging.info("Importing optional dependencies...")  # Trace optional-import phase
        cls._import_package_group(manager, manager.optional_packages, False, skip_deps)  # Phase 3: optional imports

        manager._import_special_modules()  # Phase 4: special-case module wiring

        cls._log_summary(manager, time.time() - start_time)  # Phase 5: compute and log the summary

        global_assignments = manager._get_global_assignments()  # Build the global name->object assignments

        success = len(manager.failed_imports) == 0  # Success only when nothing failed to import
        manager._initialization_complete = True  # Mark initialization done (enables the cache path above)
        manager._initialization_success = success  # Cache the success flag
        manager._cached_global_assignments = global_assignments  # Cache the assignments for repeat calls

        return success, global_assignments  # Hand back success plus the global assignments
