"""Selection cluster for :mod:`src.gateway.wan2_variable`.

Handles interactive template list display, template selection parsing,
operation direction prompt, and the preview/confirmation UX. Split out so
the parent stays under STRUCT-LENGTH and each helper obeys CC/length
budgets.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import logging  # WHY: audit-log user selections
from typing import Any  # WHY: template rows are heterogenous dicts

from ._wan2_variable_cluster import _ClusterBase  # WHY: parent-proxy pattern shared with peers


class _Wan2VariableSelection(_ClusterBase):
    """Template selection and operation-direction helpers."""

    def _display_and_select_templates(
        self,
        template_rows: list[dict[str, str]],
        site_counts: dict[str, int],
    ) -> list[dict[str, Any]] | None:
        """Display templates with site counts and get user selection."""
        sorted_rows = sorted(
            template_rows,
            key=lambda t: t.get("name", "Unnamed Template").lower(),
        )  # WHY: alphabetical order for stable indexed selection
        print(f"\n  Available Gateway Templates ({len(sorted_rows)}):")  # WHY: user header
        template_list = self._build_template_list(sorted_rows, site_counts)  # WHY: side-effect + return
        return self._prompt_template_selection(template_list)  # WHY: hand off to prompt helper

    @staticmethod
    def _build_template_list(
        sorted_rows: list[dict[str, str]],
        site_counts: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Build the numbered template display list and return it."""
        template_list: list[dict[str, Any]] = []  # WHY: accumulator for return value
        for idx, tmpl in enumerate(sorted_rows, start=1):  # WHY: 1-indexed for user prompt
            tid = tmpl.get("id", "")  # WHY: guard missing id field
            name = tmpl.get("name", "Unnamed Template")  # WHY: default label for unnamed rows
            count = site_counts.get(tid, 0)  # WHY: 0 sites for unassigned templates
            template_list.append({"id": tid, "name": name, "site_count": count})  # WHY: uniform record shape
            print(f"   [{idx}] {name} ({count} sites)")  # WHY: numbered display line
        return template_list  # WHY: caller passes to prompt

    def _prompt_template_selection(self, template_list: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Prompt user for template selection."""
        self._print_selection_instructions()  # WHY: keeps this fn under complexity budget
        raw = self._input_fn("\n  Selection: ").strip().lower()  # WHY: normalize input
        if raw == "cancel":  # WHY: explicit cancel escape hatch
            return self._log_selection_cancel()  # WHY: helper prints + returns None
        selected = self._resolve_selection(raw, template_list)  # WHY: dispatch to parser helper
        if selected is None:  # WHY: parser reported invalid input already
            return None  # WHY: propagate cancel to caller
        if not selected:  # WHY: empty selection after filter
            print(" No templates selected.")  # WHY: user feedback
            return None  # WHY: nothing to do
        self._print_selection_summary(selected)  # WHY: echo selection back for confirmation
        return selected  # WHY: caller uses for analysis

    @staticmethod
    def _print_selection_instructions() -> None:
        """Print the multi-line selection prompt block."""
        print("\n  Template Selection:")  # WHY: section header
        print("   Enter template numbers to modify" " (comma-separated, e.g., 1,3,5)")  # WHY: usage hint
        print("   Or 'all' to modify all templates")  # WHY: shortcut hint
        print("   Or 'cancel' to abort")  # WHY: escape-hatch hint

    @staticmethod
    def _log_selection_cancel() -> None:
        """Print cancel confirmation and audit-log the abort."""
        print(" Operation cancelled.")  # WHY: user feedback
        logging.info("Menu #104 cancelled by user at template selection")  # WHY: audit line

    def _resolve_selection(
        self,
        raw: str,
        template_list: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Convert the raw user string into a list of selected templates."""
        if raw == "all":  # WHY: shortcut for full modification
            return template_list  # WHY: entire list selected
        try:  # WHY: guard non-numeric input
            indices = [int(i.strip()) - 1 for i in raw.split(",")]  # WHY: 1-indexed -> 0-indexed
            return [template_list[i] for i in indices if 0 <= i < len(template_list)]  # WHY: bounds-safe
        except (ValueError, IndexError) as exc:  # WHY: bad token / out-of-range hit
            print(f" Invalid selection: {exc}")  # WHY: user feedback
            logging.error("Invalid template selection in Menu #104: %s", exc)  # WHY: audit trail
            return None  # WHY: signal parse failure

    @staticmethod
    def _print_selection_summary(selected: list[dict[str, Any]]) -> None:
        """Echo the selected templates and total site count back to the user."""
        total = sum(t["site_count"] for t in selected)  # WHY: aggregate impact
        print(f"\n  Selected {len(selected)} templates for modification:")  # WHY: summary header
        for tmpl in selected:  # WHY: enumerate each selection
            print(f"   - {tmpl['name']} ({tmpl['site_count']} sites)")  # WHY: name + impact
        print(f"\n  Total sites affected: {total}")  # WHY: final impact line

    def _select_operation_direction(
        self,
    ) -> tuple[str, str, str] | None:
        """Prompt for apply or revert direction."""
        self._print_direction_prompt()  # WHY: extracted for CC/length budget
        choice = self._input_fn("\n  Select operation [1/2/cancel]: ").strip().lower()  # WHY: normalize input
        if choice == "cancel":  # WHY: explicit cancel escape hatch
            return self._log_direction_cancel()  # WHY: helper prints + returns None
        result = self._direction_for_choice(choice)  # WHY: map choice to direction tuple
        if result is not None:  # WHY: valid choice
            return result  # WHY: caller unpacks triple
        print(" Invalid selection. Operation cancelled.")  # WHY: user feedback on invalid token
        logging.info("Menu #104 cancelled - invalid operation direction")  # WHY: audit trail
        return None  # WHY: signal cancel to caller

    @staticmethod
    def _print_direction_prompt() -> None:
        """Print the two-option direction prompt block."""
        print("\n  Operation Direction:")  # WHY: section header
        print("   [1] Replace hardcoded ports with" " {{wan2_interface}} variable (standard migration)")
        print("   [2] Replace {{wan2_interface}} variable" " with hardcoded 'ge-0/0/1' (revert/undo)")
        print("   [cancel] Abort operation")  # WHY: escape-hatch hint

    @staticmethod
    def _log_direction_cancel() -> None:
        """Print cancel confirmation and audit-log the abort."""
        print(" Operation cancelled.")  # WHY: user feedback
        logging.info("Menu #104 cancelled by user at operation direction selection")  # WHY: audit line

    @staticmethod
    def _direction_for_choice(choice: str) -> tuple[str, str, str] | None:
        """Return the (mode, search, replace) tuple for a valid choice, else None."""
        if choice == "2":  # WHY: revert path replaces variable -> hardcoded
            print("\n  !? REVERT MODE: Will replace {{wan2_interface}}" " with hardcoded 'ge-0/0/1'")
            logging.info("Menu #104: User selected REVERT mode (variable -> hardcoded)")  # WHY: audit
            return ("revert", "{{wan2_interface}}", "ge-0/0/1")  # WHY: reverse direction
        if choice == "1":  # WHY: apply path replaces hardcoded -> variable
            print("\n  APPLY MODE: Will replace hardcoded 'ge-0/0/1'" " with {{wan2_interface}} variable")
            logging.info("Menu #104: User selected APPLY mode (hardcoded -> variable)")  # WHY: audit
            return ("apply", "ge-0/0/1", "{{wan2_interface}}")  # WHY: forward direction
        return None  # WHY: signal invalid choice

    def _preview_and_confirm(self, templates_with_changes: list[dict[str, Any]]) -> bool:
        """Show preview and get user confirmation."""
        count = len(templates_with_changes)  # WHY: template modification count
        total_sites = sum(t["site_count"] for t in templates_with_changes)  # WHY: aggregate impact
        self._print_preview_body(templates_with_changes)  # WHY: extracted for length budget
        print(f"\n  {'=' * 70}")  # WHY: visual separator before footer
        self._print_preview_footer(count, total_sites)  # WHY: extracted for length budget
        print(f"  {'=' * 70}")  # WHY: closing separator
        return self._collect_confirmation()  # WHY: single-place cancel check

    def _print_preview_body(self, templates_with_changes: list[dict[str, Any]]) -> None:
        """Print the per-template change preview lines."""
        count = len(templates_with_changes)  # WHY: header count
        print(f"\n  Preview of Changes" f" ({self._operation_mode.upper()} mode):")  # WHY: banner
        print(f"  {count} templates will be modified:")  # WHY: header line
        for tmpl in templates_with_changes:  # WHY: enumerate every candidate
            print(f"\n   Template: {tmpl['name']}")  # WHY: name line
            print(f"   Sites Affected: {tmpl['site_count']}")  # WHY: scope line
            print("   Changes:")  # WHY: sub-header for per-port changes
            for old_key, new_key in tmpl["ports_to_replace"]:  # WHY: iterate planned edits
                print(f"     Port key '{old_key}' -> '{new_key}'")  # WHY: diff line

    def _print_preview_footer(self, count: int, total_sites: int) -> None:
        """Print the mode-specific footer for the preview screen."""
        if self._dry_run:  # WHY: dry-run gets non-destructive copy
            print(f"  >> DRY-RUN: Would modify {count} templates")  # WHY: preview count
            print(f"  >> affecting {total_sites} sites")  # WHY: preview scope
            print("  >> No confirmation needed in dry-run mode" " - proceeding with preview")
            return  # WHY: skip confirmation copy for dry-run
        print(f"  !? CRITICAL: This operation will modify" f" {count} templates")  # WHY: caution copy
        print(f"  !? affecting {total_sites} sites")  # WHY: scope line
        print("  !? Type 'MIGRATE' (all caps) to proceed" " or anything else to cancel")  # WHY: gate

    def _collect_confirmation(self) -> bool:
        """Prompt for the typed-MIGRATE gate; True in dry-run or on match."""
        if self._dry_run:  # WHY: dry-run bypasses the typed-word gate
            return True  # WHY: safe path proceeds without extra confirmation
        confirmation = self._input_fn("\n  Confirmation: ").strip()  # WHY: normalize input
        if confirmation != "MIGRATE":  # WHY: strict-string gate
            print(" Operation cancelled.")  # WHY: user feedback
            logging.info("Menu #104 cancelled by user at final confirmation")  # WHY: audit trail
            return False  # WHY: caller aborts
        return True  # WHY: gate passed, caller proceeds
