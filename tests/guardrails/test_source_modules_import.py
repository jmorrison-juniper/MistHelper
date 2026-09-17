"""Guard every module under `src/` against an import failure.

Why:
    An upstream package can rename a name that this repository imports at
    module scope. Issue #2682 holds that case. The `mistapi` package renamed
    `orgs.aos` to `orgs.aoscx`, one module-scope import failed, and every
    pull request turned red at the same time. No test read that import path,
    so the first report came from the continuous integration log.

    This guard imports each module under `src/` and names every failure. The
    guard reports the count it checked, so a reader can tell a real pass from
    an empty scan.
"""

from __future__ import annotations  # Keep annotation evaluation stable during test collection.

import importlib  # Import each discovered module by name.
import logging  # Record each scan step for local diagnosis.
import pkgutil  # Walk the package tree under the source root.
import sys  # Place the repository root on the import path.
from pathlib import Path  # Resolve repository paths on Windows and Linux.

_LOGGER = logging.getLogger(__name__)  # Share one logger for this guard module.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from tests/guardrails.
_SRC_ROOT = _REPO_ROOT / "src"  # Limit the scan to the first-party source tree.

# Each entry names a module that cannot import today, and the issue that holds
# the repair decision. Issue #2885 covers two orphaned upgrade portal routes.
# Remove an entry when its repair lands. The register must never grow without a
# linked issue, because a growing register hides a new defect.
KNOWN_IMPORT_FAILURES: dict[str, int] = {
    "src.upgrade_portal.app.routes.audit": 2885,  # Imports `upgrade_portal.audit`, which does not exist.
    "src.upgrade_portal.app.routes.jwt_auth": 2885,  # Imports `upgrade_portal.auth`, which does not exist.
}


class SourceModuleImporter:
    """Discover and import every module under the source root."""

    @staticmethod
    def ensure_import_path() -> None:
        """Place the repository root at the front of the import path."""
        root_text = str(_REPO_ROOT)  # Compare and insert the path as text.
        if root_text not in sys.path:  # Avoid a duplicate entry on a repeated call.
            sys.path.insert(0, root_text)  # Put the repository root first so `src.` resolves.

    @staticmethod
    def module_names() -> list[str]:
        """Return every module name under the source root."""
        _LOGGER.info("Scanning source modules under %s", _SRC_ROOT)  # Log the scan start.
        names = [  # Collect one dotted name for each module in the tree.
            module.name  # Keep the full dotted name, such as `src.api.api_fetch_utils`.
            for module in pkgutil.walk_packages([str(_SRC_ROOT)], prefix="src.")  # Walk every subpackage.
        ]
        _LOGGER.debug("Found %s source modules", len(names))  # Log the discovered module count.
        return sorted(names)  # Return a stable order so a failure list reads the same each run.

    @staticmethod
    def import_all(names: list[str]) -> dict[str, str]:
        """Import each named module and return one message for each failure."""
        _LOGGER.info("Importing %s source modules", len(names))  # Log the import phase start.
        failures: dict[str, str] = {}  # Hold one short message for each module that failed.
        for name in names:  # Import each module in a stable order.
            try:  # A first-party module must import without an error.
                importlib.import_module(name)  # Run the module body, including every module-scope import.
            except Exception as error:  # An import fault is an ordinary error, never an interpreter exit.
                failures[name] = f"{type(error).__name__}: {error}"  # Record the class and the text.
        _LOGGER.debug("Import phase finished with %s failures", len(failures))  # Log the failure count.
        return failures  # Return the complete failure map for the assertion phase.


def test_every_source_module_imports() -> None:
    """Fail when a module under `src/` cannot import."""
    SourceModuleImporter.ensure_import_path()  # Make `src.` resolvable before the walk.
    names = SourceModuleImporter.module_names()  # Discover every first-party module.
    assert names, f"The guard found no module under {_SRC_ROOT}. The scan read nothing."
    failures = SourceModuleImporter.import_all(names)  # Import each module and collect the failures.
    unexpected = {  # Keep only a failure that no open issue already tracks.
        name: message for name, message in failures.items() if name not in KNOWN_IMPORT_FAILURES
    }
    report = "\n".join(f"  {name}  {message}" for name, message in sorted(unexpected.items()))  # One line each.
    assert not unexpected, (  # A new import failure must stop the build.
        f"Checked {len(names)} modules under src/. " f"{len(unexpected)} module(s) failed to import:\n{report}"
    )
    _LOGGER.info("Checked %s source modules with no unexpected failure", len(names))  # State the measured count.


def test_known_import_failures_still_fail() -> None:
    """Fail when a tracked module imports again, so the register stays honest."""
    SourceModuleImporter.ensure_import_path()  # Make `src.` resolvable before the import attempt.
    tracked = sorted(KNOWN_IMPORT_FAILURES)  # Read the register in a stable order.
    _LOGGER.info("Rechecking %s tracked import failures", len(tracked))  # Log the recheck start.
    repaired = SourceModuleImporter.import_all(tracked)  # Import each tracked module again.
    fixed = [name for name in tracked if name not in repaired]  # A missing failure means the module now imports.
    guidance = ", ".join(f"{name} (issue #{KNOWN_IMPORT_FAILURES[name]})" for name in fixed)  # Name each one.
    assert not fixed, (  # A repaired module must leave the register in the same change.
        f"Rechecked {len(tracked)} tracked modules. "
        f"{len(fixed)} now import and must leave KNOWN_IMPORT_FAILURES: {guidance}"
    )
    _LOGGER.debug("All %s tracked modules still fail to import", len(tracked))  # Log the recheck result.
