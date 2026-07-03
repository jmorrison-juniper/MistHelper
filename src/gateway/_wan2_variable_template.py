"""Template-analysis + template-modification cluster for wan2_variable.

Holds template config fetch, port-pattern matching, parallel analysis,
and the per-template API application flow. Split out of
:class:`GatewayWan2VariableMigrator` so the parent stays under
STRUCT-LENGTH while individual helpers keep CC/length budgets.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import concurrent.futures  # WHY: as_completed for parallel template fetches
import logging  # WHY: audit-log every fetch/apply outcome
import traceback  # WHY: capture stack trace on unexpected mistapi failures
from concurrent.futures import ThreadPoolExecutor  # WHY: parallelize template config fetches
from typing import Any  # WHY: mistapi responses/configs are heterogenous dicts

from tqdm import tqdm  # WHY: progress bars over template lists

from ._wan2_variable_cluster import _ClusterBase  # WHY: parent-proxy pattern shared with peers


class _Wan2VariableTemplate(_ClusterBase):
    """Template analysis + application helpers."""

    def _fetch_template_config(self, template_info: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch and analyze a single template for port changes."""
        import mistapi  # pylint: disable=import-outside-toplevel  # WHY: lazy import breaks cycle

        tid = template_info["id"]  # WHY: template ID used in API path
        name = template_info["name"]  # WHY: friendly name for logs
        try:  # WHY: mistapi calls raise on transport failure
            config = self._get_template_config_dict(mistapi, tid, name)  # WHY: extracted for CC budget
            if config is None:  # WHY: nested helper handled all error paths
                return None  # WHY: propagate no-op signal
            return self._build_change_record(template_info, config, name)  # WHY: extracted for CC budget
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: mistapi failures vary
            logging.error("Error analyzing template %s: %s", name, exc)  # WHY: audit trail
            logging.error(traceback.format_exc())  # WHY: preserve stack for post-mortem
            print(f"\n  !? Error analyzing template '{name}': {exc}")  # WHY: user feedback
            return None  # pylint: disable=useless-return  # WHY: explicit None for readability

    def _get_template_config_dict(self, mistapi_mod: Any, tid: str, name: str) -> dict[str, Any] | None:
        """Fetch template config and return only if it is a valid dict."""
        logging.debug("Fetching template configuration for %s", name)  # WHY: trace call site
        resp = mistapi_mod.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(self._apisession, self._org_id, tid)
        config = resp.data if hasattr(resp, "data") else {}  # WHY: guard missing .data attr
        if not isinstance(config, dict):  # WHY: only dict-shaped configs are actionable
            logging.warning("Template %s returned invalid data structure", name)  # WHY: audit malformed row
            return None  # WHY: caller returns no change record
        return config  # WHY: pass through to change-record builder

    def _build_change_record(
        self,
        template_info: dict[str, Any],
        config: dict[str, Any],
        name: str,
    ) -> dict[str, Any] | None:
        """Return a change-record dict if template needs edits, else None."""
        port_config = config.get("port_config", {})  # WHY: attribute we intend to mutate
        if not isinstance(port_config, dict):  # WHY: skip malformed port_config shapes
            logging.debug("Template %s has no port_config", name)  # WHY: trace no-op path
            return None  # WHY: no work needed
        ports_to_replace = self._find_matching_ports(port_config, name)  # WHY: filter to matching keys
        if not ports_to_replace:  # WHY: nothing to migrate on this template
            return None  # WHY: filter out of results
        return {
            "id": template_info["id"],  # WHY: retain for API update path
            "name": name,  # WHY: retain for logs/reports
            "site_count": template_info["site_count"],  # WHY: retain for impact metrics
            "config": config,  # WHY: passed to _apply_single_template
            "ports_to_replace": ports_to_replace,  # WHY: exact edits to apply
        }

    def _find_matching_ports(
        self,
        port_config: dict[str, Any],
        template_name: str,
    ) -> list[tuple[str, str]]:
        """Find port keys matching the search pattern."""
        search = self._search_pattern  # WHY: alias for readability
        replace = self._replacement_value  # WHY: alias for readability
        replacements: list[tuple[str, str]] = []  # WHY: accumulator for return
        for key in port_config:  # WHY: scan every configured port key
            match = self._classify_port_key(key, search, replace, template_name)  # WHY: extracted for CC budget
            if match is not None:  # WHY: skip keys that need manual review or don't match
                replacements.append(match)  # WHY: record planned edit
        return replacements  # WHY: caller applies edits later

    @staticmethod
    def _classify_port_key(
        key: str,
        search: str,
        replace: str,
        template_name: str,
    ) -> tuple[str, str] | None:
        """Return (old, new) tuple for a key, or None if unmatched/complex."""
        if key == search:  # WHY: exact match on primary key
            return (key, replace)  # WHY: simple rename
        if key.startswith(f"{search}."):  # WHY: subinterface variant
            suffix = key[len(search) :]  # WHY: preserve subinterface tail
            new_key = f"{replace}{suffix}"  # WHY: rebuild key under new prefix
            logging.info("Found subinterface in template %s: %s -> %s", template_name, key, new_key)  # WHY: audit
            return (key, new_key)  # WHY: rename with suffix retained
        if search in key:  # WHY: complex pattern needs manual review
            logging.warning("Found complex port pattern in template %s: %s", template_name, key)  # WHY: audit
            print(f"\n  !? Template '{template_name}'" f" uses complex port pattern: '{key}'")  # WHY: user warn
            print("     This requires manual review" " - cannot automatically replace")  # WHY: guidance
        return None  # WHY: unmatched or complex - no automatic edit

    def _analyze_templates_parallel(self, templates_to_modify: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch and analyze templates in parallel."""
        print(f"\n  Analyzing templates for {self._search_pattern}" " port configurations...")  # WHY: banner
        max_workers = min(10, len(templates_to_modify))  # WHY: cap concurrency to protect API
        logging.info(
            "Fetching %s template configurations in parallel (max %s workers)",
            len(templates_to_modify),
            max_workers,
        )  # WHY: audit scope
        return self._collect_template_futures(templates_to_modify, max_workers)  # WHY: extracted for length

    def _collect_template_futures(
        self,
        templates_to_modify: list[dict[str, Any]],
        max_workers: int,
    ) -> list[dict[str, Any]]:
        """Run the ThreadPoolExecutor loop and return non-empty results."""
        results: list[dict[str, Any]] = []  # WHY: accumulator for return
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # WHY: bounded parallelism
            future_map = {executor.submit(self._fetch_template_config, t): t for t in templates_to_modify}
            for future in tqdm(
                concurrent.futures.as_completed(future_map),
                total=len(templates_to_modify),
                desc="Analyzing templates",
                unit="template",
            ):  # WHY: user-visible progress bar
                result = future.result()  # WHY: propagate task exceptions
                if result:  # WHY: filter out no-op templates
                    results.append(result)  # WHY: retain only actionable rows
        return results  # WHY: caller passes to preview/apply

    def _apply_template_changes(self, templates_with_changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply port_config changes to templates via API."""
        import mistapi  # pylint: disable=import-outside-toplevel  # WHY: lazy import breaks cycle

        print("\n  Applying template modifications...")  # WHY: banner
        results: list[dict[str, Any]] = []  # WHY: accumulator for return
        for tmpl in tqdm(
            templates_with_changes,
            desc="Updating templates",
            unit="template",
        ):  # WHY: iterate every candidate with progress bar
            results.append(self._apply_single_template(tmpl, mistapi))  # WHY: delegate to per-template helper
        return results  # WHY: caller aggregates for report

    def _apply_single_template(
        self,
        tmpl: dict[str, Any],
        mistapi_mod: Any,
    ) -> dict[str, Any]:
        """Apply changes to a single template."""
        result = self._init_apply_result(tmpl)  # WHY: extracted for length budget
        try:  # WHY: mistapi calls raise on transport failure
            self._perform_template_edit(tmpl, result, mistapi_mod)  # WHY: extracted for CC budget
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: mistapi failures vary
            result["status"] = "ERROR"  # WHY: report path
            result["error"] = str(exc)  # WHY: record failure text
            logging.error("Error updating template %s: %s", tmpl["name"], exc)  # WHY: audit trail
            logging.error(traceback.format_exc())  # WHY: preserve stack
        return result  # WHY: caller appends to results list

    @staticmethod
    def _init_apply_result(tmpl: dict[str, Any]) -> dict[str, Any]:
        """Build the initial per-template result dict with default fields."""
        return {
            "template_name": tmpl["name"],  # WHY: report label
            "template_id": tmpl["id"],  # WHY: cross-ref for device migration
            "site_count": tmpl["site_count"],  # WHY: impact metric
            "status": "",  # WHY: populated by branches below
            "changes_made": "",  # WHY: filled on success
            "error": "",  # WHY: filled on failure/skip
        }

    def _perform_template_edit(
        self,
        tmpl: dict[str, Any],
        result: dict[str, Any],
        mistapi_mod: Any,
    ) -> None:
        """Apply changes and set result status; may raise on API failure."""
        port_config = tmpl["config"].get("port_config", {})  # WHY: mutate this dict in place
        changes_list = self._rename_template_ports(port_config, tmpl["ports_to_replace"], tmpl["name"])
        if not changes_list:  # WHY: no keys matched at apply time
            result["status"] = "SKIPPED"  # WHY: report path
            result["error"] = "No matching ports found in configuration"  # WHY: explain
            return  # WHY: nothing to send to API
        tmpl["config"]["port_config"] = port_config  # WHY: ensure mutation persists (paranoia)
        result["changes_made"] = "; ".join(changes_list)  # WHY: summary for report
        self._commit_template_or_dry_run(tmpl, result, mistapi_mod)  # WHY: extracted for CC budget

    @staticmethod
    def _rename_template_ports(
        port_config: dict[str, Any],
        ports_to_replace: list[tuple[str, str]],
        name: str,
    ) -> list[str]:
        """Rename port_config keys in place and return human-readable diffs."""
        changes_list: list[str] = []  # WHY: accumulator for return
        for old_key, new_key in ports_to_replace:  # WHY: iterate every planned edit
            if old_key in port_config:  # WHY: guard concurrent template mutation
                port_config[new_key] = port_config.pop(old_key)  # WHY: rename preserves value
                changes_list.append(f"'{old_key}' -> '{new_key}'")  # WHY: diff line
                logging.debug("Template %s: Replaced %s with %s", name, old_key, new_key)  # WHY: trace
        return changes_list  # WHY: caller stores on result

    def _commit_template_or_dry_run(
        self,
        tmpl: dict[str, Any],
        result: dict[str, Any],
        mistapi_mod: Any,
    ) -> None:
        """Send API update or mark dry-run; populates result status/error."""
        if self._dry_run:  # WHY: dry-run bypasses API mutation
            result["status"] = "DRY-RUN"  # WHY: report path
            logging.info(
                "DRY-RUN: Would update template %s with changes: %s", tmpl["name"], result["changes_made"]
            )  # WHY: audit
            return  # WHY: no API call in dry-run
        logging.debug("Updating template %s via API", tmpl["name"])  # WHY: trace call site
        resp = mistapi_mod.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate(
            self._apisession,
            self._org_id,
            tmpl["id"],
            body=tmpl["config"],
        )  # WHY: single mistapi update call
        self._record_update_status(resp, tmpl["name"], result)  # WHY: extracted to keep length under budget

    @staticmethod
    def _record_update_status(resp: Any, name: str, result: dict[str, Any]) -> None:
        """Populate result status/error from a template update response."""
        if resp.status_code == 200:  # WHY: 200 == success per Mist API
            result["status"] = "SUCCESS"  # WHY: report path
            logging.info("Successfully updated template %s", name)  # WHY: audit success
            return  # WHY: no error data to record
        result["status"] = "FAILED"  # WHY: any non-200 is a failure
        result["error"] = f"API returned status {resp.status_code}"  # WHY: capture code
        logging.error("Failed to update template %s: status %s", name, resp.status_code)  # WHY: audit
