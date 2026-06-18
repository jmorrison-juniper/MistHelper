"""Import initialization orchestration extracted from high-complexity import manager method."""

import logging
import time
from typing import Any


class ImportInitializationService:
    """Owns import initialization flow formerly embedded in import manager method."""

    @staticmethod
    def execute(manager: Any, skip_deps: bool = False) -> tuple[bool, dict[str, Any]]:
        """Run complete import initialization flow and return success plus global assignments."""
        if manager._initialization_complete:
            logging.debug("Import initialization already completed, returning cached results")
            return manager._initialization_success, manager._cached_global_assignments

        start_time = time.time()
        logging.info("Initializing global import management system...")

        if skip_deps:
            logging.info("Dependency checking and installation skipped (--skip-deps flag)")
        else:
            if manager.auto_upgrade_uv:
                if not manager._check_uv_installation():
                    manager._install_uv()
                else:
                    manager._upgrade_uv()

        logging.info("Importing required dependencies...")
        if not skip_deps and len(manager.required_packages) > 3:
            manager._import_packages_concurrently(manager.required_packages, required=True, skip_deps=skip_deps)
        else:
            for module_name, package_spec in manager.required_packages.items():
                logging.info(f"  Checking required dependency: {module_name} ({package_spec or 'built-in'})")
                result = manager.import_module_safely(
                    module_name,
                    package_spec,
                    required=True,
                    skip_deps=skip_deps,
                    skip_upgrade=True,
                )
                if result:
                    logging.info(f"  [OK] {module_name}: Available")
                else:
                    logging.error(f"  [FAIL] {module_name}: Failed to import")

        logging.info("Importing optional dependencies...")
        if not skip_deps and len(manager.optional_packages) > 3:
            manager._import_packages_concurrently(manager.optional_packages, required=False, skip_deps=skip_deps)
        else:
            for module_name, package_spec in manager.optional_packages.items():
                logging.info(f"  Checking optional dependency: {module_name} ({package_spec or 'built-in'})")
                result = manager.import_module_safely(
                    module_name,
                    package_spec,
                    required=False,
                    skip_deps=skip_deps,
                    skip_upgrade=True,
                )
                if result:
                    logging.info(f"  [OK] {module_name}: Available")
                else:
                    logging.warning(f"  [WARN] {module_name}: Not available")

        manager._import_special_modules()

        elapsed_time = time.time() - start_time
        total_required = len(manager.required_packages)
        failed_required = len(
            [package_name for package_name in manager.failed_imports if package_name in manager.required_packages]
        )
        successful_required = total_required - failed_required
        optional_imported = len(
            [package_name for package_name in manager.imports.keys() if package_name in manager.optional_packages]
        )

        logging.info(f"Import initialization completed in {elapsed_time:.2f} seconds")
        logging.info(f"Required dependencies: {successful_required}/{total_required} successful")
        logging.info(f"Optional dependencies: {optional_imported}/{len(manager.optional_packages)} available")

        if manager.installed_packages:
            logging.info(f"Newly installed packages: {', '.join(manager.installed_packages)}")

        if manager.failed_imports:
            logging.error(f"Failed imports: {', '.join(manager.failed_imports)}")

        global_assignments = manager._get_global_assignments()

        success = len(manager.failed_imports) == 0
        manager._initialization_complete = True
        manager._initialization_success = success
        manager._cached_global_assignments = global_assignments

        return success, global_assignments
