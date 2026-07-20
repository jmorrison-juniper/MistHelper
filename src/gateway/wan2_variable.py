"""Gateway WAN2 variable migration for MistHelper.

Extracts update_gateway_templates_wan2_variable (Menu #104) from
MistHelper.py into a class with dependency injection for testability.

Implementation is split across helper-cluster modules under
``src/gateway/_wan2_variable_*.py`` so the parent stays under the
STRUCT-LENGTH budget while each cluster keeps CC/length budgets:

* :mod:`._wan2_variable_io` - CSV loading, filtering, headers.
* :mod:`._wan2_variable_selection` - user template pick / direction UX.
* :mod:`._wan2_variable_template` - template fetch + edit apply.
* :mod:`._wan2_variable_device` - per-device override migration.
* :mod:`._wan2_variable_reporting` - audit CSV + final summary block.

The parent orchestrates the flow via :meth:`execute`; every private
helper referenced there is provided by one of the clusters and reached
through the class-level ``__getattr__`` proxy defined below.
"""

# pylint: disable=logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: audit-log the top-level DESTRUCTIVE menu entry point
from collections.abc import Callable  # WHY: type aliases for DI callables
from dataclasses import dataclass  # WHY: bundle 10 injected deps into a frozen struct
from typing import Any  # WHY: mistapi handle + heterogenous helpers

from ._wan2_variable_device import _Wan2VariableDevice  # WHY: per-device override migration cluster
from ._wan2_variable_io import _Wan2VariableIO  # WHY: CSV loading + header cluster
from ._wan2_variable_reporting import _Wan2VariableReporting  # WHY: audit + summary cluster
from ._wan2_variable_selection import _Wan2VariableSelection  # WHY: selection + confirmation cluster
from ._wan2_variable_template import _Wan2VariableTemplate  # WHY: template fetch/apply cluster


@dataclass(frozen=True)
class Wan2VariableDeps:
    """Injected dependencies for :class:`GatewayWan2VariableMigrator`.

    Bundles the 10 dependencies into a single frozen dataclass so
    construction sites and tests build one struct instead of passing 10
    kwargs, and so the parent ``__init__`` fits the STRUCT-PARAMS limit.
    """

    org_id: str  # WHY: Mist organization ID used in every API path
    apisession: Any  # WHY: mistapi.APISession handle
    site_exclude_prefix: str  # WHY: SECURITY prefix filter applied to site rows
    check_and_generate_csv_fn: Callable[..., Any]  # WHY: cache check/generation entry point
    generate_templates_fn: Callable[..., Any]  # WHY: gateway templates CSV generator
    generate_sites_fn: Callable[..., Any]  # WHY: sites CSV generator
    get_csv_path_fn: Callable[[str], str]  # WHY: resolves CSV filenames to full paths
    save_data_fn: Callable[..., Any]  # WHY: writes audit rows to disk
    input_fn: Callable[[str], str] | None = None  # WHY: overrideable stdin reader (defaults to builtin)
    execute_fn: Callable[..., Any] | None = None  # WHY: optional fast-mode parallel executor (1012 SC-003 rename)


class GatewayWan2VariableMigrator:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Migrate gateway templates between hardcoded ports and WAN2 variable.

    Supports bidirectional operation:

    - APPLY: Replace hardcoded 'ge-0/0/1' with {{wan2_interface}} variable
    - REVERT: Replace {{wan2_interface}} with hardcoded 'ge-0/0/1'

    Both modes preserve device-level static IP overrides by migrating
    port_config keys on individual devices. Implementation lives in the
    ``_wan2_variable_*`` cluster modules; this class holds the orchestration
    entry point and shared state.
    """

    def __init__(self, deps: Wan2VariableDeps) -> None:
        """Initialize with the injected :class:`Wan2VariableDeps` bundle.

        Args:
            deps: Frozen dataclass carrying the 10 dependency callables/objects
                consumed by the various migration flows.
        """
        self._unpack_deps(deps)  # WHY: split for STRUCT-LENGTH budget
        # Runtime state populated during execute()
        self._search_pattern = ""  # WHY: set by direction prompt (apply/revert)
        self._replacement_value = ""  # WHY: set by direction prompt (apply/revert)
        self._operation_mode = ""  # WHY: "apply" or "revert"
        self._dry_run = False  # WHY: preview vs live mode toggle
        # WHY: bundle clusters in a single tuple so parent stays inside R0902 gate
        self._clusters: tuple[Any, ...] = (
            _Wan2VariableIO(self),  # WHY: CSV loading + header cluster binding
            _Wan2VariableSelection(self),  # WHY: interactive selection cluster binding
            _Wan2VariableTemplate(self),  # WHY: template fetch/apply cluster binding
            _Wan2VariableDevice(self),  # WHY: per-device override cluster binding
            _Wan2VariableReporting(self),  # WHY: audit + summary cluster binding
        )

    def _unpack_deps(self, deps: Wan2VariableDeps) -> None:
        """Unpack the :class:`Wan2VariableDeps` bundle into private attrs."""
        self._org_id = deps.org_id  # WHY: exposed for cluster proxy lookups
        self._apisession = deps.apisession  # WHY: mistapi session shared across clusters
        self._site_exclude_prefix = deps.site_exclude_prefix  # WHY: SECURITY exclusion prefix
        self._check_csv = deps.check_and_generate_csv_fn  # WHY: cache freshness helper
        self._gen_templates = deps.generate_templates_fn  # WHY: templates CSV generator
        self._gen_sites = deps.generate_sites_fn  # WHY: sites CSV generator
        self._get_csv_path = deps.get_csv_path_fn  # WHY: resolves CSV names to paths
        self._save_data = deps.save_data_fn  # WHY: audit CSV writer
        self._input_fn = deps.input_fn or input  # WHY: default to builtin input()
        self._pool_fn = (
            deps.execute_fn
        )  # WHY: fast-mode parallel executor (may be None); renamed from connection_pool_fn per 1012 SC-003

    def __getattr__(self, name: str) -> Any:
        """Proxy cluster-attribute access to helper clusters.

        Python only invokes ``__getattr__`` when normal lookup fails, so
        this method resolves cluster method calls (``self._load_csv_data``,
        ``self._apply_template_changes`` etc.) without explicit delegator
        wrappers. The class-level ``hasattr`` check on ``type(cluster)``
        avoids invoking the cluster's own ``__getattr__`` (which would
        proxy back to this class and cause infinite recursion for unknown
        attrs).
        """
        for cluster in self.__dict__.get("_clusters", ()):  # WHY: iterate bundled clusters
            if hasattr(type(cluster), name):  # WHY: class-level lookup avoids cluster __getattr__ recursion
                return getattr(cluster, name)  # WHY: bound method resolves through cluster
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")  # WHY: standard miss

    def execute(self, fast: bool = False, dry_run: bool = False) -> None:
        """Run the WAN2 variable migration workflow.

        Args:
            fast: Enable parallel processing with connection pooling.
            dry_run: Preview changes without modifying anything.
        """
        self._dry_run = dry_run  # WHY: propagate mode to every cluster helper
        self._print_header()  # WHY: banner (IO cluster)
        logging.warning("Menu #104 DESTRUCTIVE: Update Gateway Templates WAN2 Variable operation started")  # WHY: audit
        data = self._load_csv_data()  # WHY: template + site CSVs (IO cluster)
        if data is None:  # WHY: no templates -> abort
            return  # WHY: caller stops workflow
        template_rows, sites, site_counts = data  # WHY: destructure triple
        outcome = self._select_and_analyze(template_rows, site_counts)  # WHY: extract for CC budget
        if outcome is None:  # WHY: user cancelled or no changes found
            return  # WHY: caller stops workflow
        selected, changes = outcome  # WHY: split branches from selection phase
        if not self._preview_and_confirm(changes):  # WHY: typed-MIGRATE gate (Selection cluster)
            return  # WHY: user declined confirmation
        self._run_and_report(changes, sites, fast)  # WHY: apply + device migration + reports
        del selected  # WHY: keep name in scope to signal intent even after use

    def _select_and_analyze(
        self,
        template_rows: list[dict[str, str]],
        site_counts: dict[str, int],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
        """Run selection + direction prompts, then analyze templates."""
        selected = self._display_and_select_templates(template_rows, site_counts)  # WHY: user pick
        if selected is None:  # WHY: cancelled
            return None
        direction = self._select_operation_direction()  # WHY: apply vs revert prompt
        if direction is None:  # WHY: cancelled
            return None
        self._operation_mode, self._search_pattern, self._replacement_value = direction  # WHY: propagate
        changes = self._analyze_templates_parallel(selected)  # WHY: fan-out fetch + filter
        if not changes:  # WHY: nothing to do
            self._log_no_changes_needed()  # WHY: helper prints + logs
            return None
        return selected, changes  # WHY: caller advances to preview/apply

    def _log_no_changes_needed(self) -> None:
        """Log the 'no templates require modification' outcome."""
        logging.info("\n  No templates found with %s port configurations.", self._search_pattern)  # WHY: user feedback
        logging.info("  No changes needed.")  # WHY: closing line
        logging.info("Menu #104: No templates require modification (searched for %s)", self._search_pattern)

    def _run_and_report(
        self,
        changes: list[dict[str, Any]],
        sites: list[dict[str, str]],
        fast: bool,
    ) -> None:
        """Apply template changes, migrate devices, then emit reports."""
        results = self._apply_template_changes(changes)  # WHY: send template edits to API
        migrated_ids = {r["template_id"] for r in results if r["status"] == "SUCCESS"}  # WHY: filter to successes
        devices = self._find_devices_needing_migration(sites, migrated_ids)  # WHY: candidate device rows
        device_results = self._run_device_migrations(devices, fast)  # WHY: per-device migration
        self._generate_reports(results, device_results, devices)  # WHY: CSV + summary blocks
