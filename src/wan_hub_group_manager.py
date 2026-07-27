"""WAN Hub Group Number Manager - Menu 163.

Manage the pod (group number) field on VPN paths associated with
WAN Hub Profiles (gateway device profiles).  NOC engineers pick a
profile from an alphabetized list, then set or clear the pod value
across all matching VPN paths.

This is the first menu operation implemented as an external module
under ``src/``, establishing the pattern for future extractions from
the MistHelper monolith.
"""

from __future__ import annotations  # WHY: PEP 604 unions on py<3.10 syntax evaluation.

import copy  # WHY: deepcopy VPN objects before mutation so API PATCH sees clean payload.
import logging  # WHY: structured diagnostics for NOC audit trail of pod changes.
from collections.abc import Callable  # WHY: type-hint injected safe_input factory.
from typing import Any  # WHY: opaque mistapi payload / session types.

import mistapi  # WHY: high-level get_all pagination helper is used across fetch methods.
import mistapi.api.v1.orgs.deviceprofiles  # WHY: gateway profile listing endpoint.
import mistapi.api.v1.orgs.vpns  # WHY: VPN CRUD endpoints for pod updates.

# --- Pod range constants -------------------------------------------------
POD_MIN = 1  # WHY: Mist API minimum accepted pod value on VPN path.
POD_MAX = 128  # WHY: Mist API maximum accepted pod value on VPN path.
POD_DEFAULT = 1  # WHY: Mist default when pod is unset; "clear" resets to this.

# --- API discriminator constants ----------------------------------------
_GATEWAY_TYPE = "gateway"  # WHY: filters listOrgDeviceProfiles to WAN gateways only.
_HUB_SPOKE_TYPE = "hub_spoke"  # WHY: only hub-spoke overlays carry pod-tagged paths.
_UNKNOWN_TYPE = "unknown"  # WHY: bucket label when a VPN record lacks a type field.

# --- Safe-input context tags (structured logging correlation) -----------
_CTX_PROFILE_SELECT = "wan_hub_profile_select"  # WHY: correlates profile-picker prompts in audit logs.
_CTX_ACTION_SELECT = "wan_hub_action_select"  # WHY: correlates action-menu prompts in audit logs.
_CTX_POD_INPUT = "wan_hub_pod_input"  # WHY: correlates pod-value entry prompts in audit logs.
_CTX_CONFIRM_SET = "wan_hub_confirm_set"  # WHY: correlates set-confirmation prompts in audit logs.
_CTX_CONFIRM_CLEAR = "wan_hub_confirm_clear"  # WHY: correlates clear-confirmation prompts in audit logs.
_CTX_FALLBACK = "wan_hub_group_fallback"  # WHY: correlates prompts routed through the fallback shim.

# --- User-facing message templates --------------------------------------
_HEADER = "\n=== WAN Hub Group Number Manager ==="  # WHY: menu banner shown at run start.
_MSG_START = "Starting WAN Hub Group Number Manager"  # WHY: startup marker in log for triage timeline.
_MSG_NO_ORG = "! No organization selected. Exiting."  # WHY: pre-flight failure when caller lacks org context.
_MSG_NO_PROFILES = "! No WAN Hub Profiles found in this organization."  # WHY: empty-inventory guardrail.
_MSG_NO_VPNS = "! No VPN definitions found in this organization."  # WHY: empty-VPN guardrail message.
_MSG_ERR_PROFILES = (
    "! Error retrieving WAN Hub Profiles. Check API connectivity."  # WHY: user-visible API failure hint.
)
_MSG_ERR_VPNS = "! Error retrieving VPN definitions. Check API connectivity."  # WHY: user-visible API failure hint.
_MSG_CANCELLED = "  Cancelled."  # WHY: single-source cancel message avoids drift across prompts.
_MSG_HEADING_PROFILES = "\n  WAN Hub Profiles:"  # WHY: heading above the numbered profile list.
_MSG_HEADING_ACTIONS = "\n  Actions:"  # WHY: heading above the set/clear/cancel menu.
_MSG_ACTION_SET = "   1. Set new pod value"  # WHY: action menu item 1 label.
_MSG_ACTION_CLEAR = "   2. Clear pod (reset to default 1)"  # WHY: action menu item 2 label.
_MSG_ACTION_CANCEL = "   3. Cancel"  # WHY: action menu item 3 label.
_MSG_ACTION_PROMPT = "  Select action (1-3): "  # WHY: action-menu input prompt.

# --- Pod display fragments ----------------------------------------------
_POD_NO_PATHS = "Pod: -- (no VPN paths)"  # WHY: sentinel display when no paths match.
_POD_DEFAULT_LABEL = "default (1)"  # WHY: friendlier label for the default value.
_POD_LABEL_PREFIX = "Pod: "  # WHY: shared prefix for uniform display.
_POD_MIXED_PREFIX = "Pod: MIXED "  # WHY: warns operator that paths disagree on pod value.

# --- Confirmation semantics ---------------------------------------------
_CONFIRM_YES = "y"  # WHY: only case-insensitive 'y' proceeds. Anything else cancels.
_QUIT_CHAR = "q"  # WHY: canonical cancel key for the profile picker.


class WanHubGroupNumberManager:  # WHY: single public surface consumed by Menu 163 and tests.
    """Interactive manager for WAN Hub Profile group numbers (pod values)."""

    # WHY: class-level aliases preserve historical public constant surface for callers/tests.
    POD_MIN = POD_MIN  # WHY: public alias retained for test/import compatibility.
    POD_MAX = POD_MAX  # WHY: public alias retained for test/import compatibility.
    POD_DEFAULT = POD_DEFAULT  # WHY: public alias retained for test/import compatibility.

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        safe_input_func: Callable[..., str] | None = None,
    ) -> None:  # WHY: injectable safe_input keeps tests hermetic while defaulting to fallback shim.
        """Initialize with API session, org ID, and optional input function."""
        self.apisession = apisession  # WHY: mistapi session used for every downstream API call.
        self.org_id = org_id  # WHY: pinned org scope avoids re-resolving per API call.
        self._safe_input = safe_input_func or self._fallback_input  # WHY: allow test/menu injection.

    # ------------------------------------------------------------------
    # Entry point (called from menu_actions)
    # ------------------------------------------------------------------

    @staticmethod
    def execute(
        apisession: Any,
        get_org_id_func: Callable[[], str | None],
        safe_input_func: Callable[..., str] | None,
    ) -> None:  # WHY: staticmethod entry point matches menu_actions lambda signature.
        """Static entry point called by menu_actions lambda."""
        org_id = get_org_id_func()  # WHY: resolves org lazily so menu can share cached value.
        if not org_id:  # WHY: guard clause - no org means nothing to manage.
            logging.warning(_MSG_NO_ORG)  # WHY: operator-visible exit reason via logger.
            return  # WHY: bail before constructing a useless manager.
        manager = WanHubGroupNumberManager(apisession, org_id, safe_input_func)  # WHY: build with resolved org.
        manager.run()  # WHY: delegate to the interactive workflow.

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self) -> None:  # WHY: top-level workflow orchestrator called from execute().
        """Main workflow: fetch, display, select, act."""
        logging.warning(_HEADER)  # WHY: operator-visible menu banner via logger.
        logging.info(_MSG_START)  # WHY: emit start marker before any API traffic.

        profiles = self._fetch_profiles()  # WHY: source-of-truth list to display and index against.
        if not profiles:  # WHY: guard clause - no profiles means nothing to configure.
            logging.warning(_MSG_NO_PROFILES)  # WHY: operator-visible empty-list exit via logger.
            return  # WHY: no further work possible.

        vpns, all_vpns = self._fetch_hub_spoke_vpns()  # WHY: need hub_spoke overlays that carry pods.
        if not vpns:  # WHY: guard clause - no hub-spoke overlays means nothing to patch.
            self._report_no_hub_spoke(all_vpns)  # WHY: give operator a helpful breakdown.
            return  # WHY: bail without prompting.

        vpn_data = self._build_vpn_data(profiles, vpns)  # WHY: precompute match sets to avoid repeat scans.
        self._display_profile_list(profiles, vpn_data)  # WHY: render numbered picker with pod hints.

        selected = self._prompt_profile_selection(profiles)  # WHY: capture operator choice or None on cancel.
        if selected is None:  # WHY: honour operator cancel without further prompting.
            return  # WHY: nothing to act on.

        self._prompt_action(selected, vpn_data)  # WHY: hand off to set/clear/cancel branch.

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self) -> list[dict[str, Any]]:  # WHY: encapsulates paginated gateway-profile fetch.
        """Fetch gateway device profiles, sorted alphabetically."""
        try:  # WHY: any mistapi failure must degrade gracefully to empty list.
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type=_GATEWAY_TYPE
            )  # WHY: gateway type narrows to WAN hub candidates only.
            profiles: list[dict[str, Any]] = mistapi.get_all(
                response=response, mist_session=self.apisession
            )  # WHY: get_all walks pagination so long lists are complete.
            profiles.sort(key=lambda profile: profile.get("name", "").lower())  # WHY: alphabetical UX ordering.
            logging.debug("Fetched %d gateway profiles", len(profiles))  # WHY: capacity signal in logs.
            return profiles  # WHY: caller drives display and match building.
        except Exception:  # WHY: broad catch - any API/network fault must not raise into menu loop.
            logging.exception("Failed to fetch device profiles")  # WHY: full traceback for triage.
            logging.error(_MSG_ERR_PROFILES)  # WHY: operator-visible connectivity hint via logger.
            return []  # WHY: empty list flows into no-profiles guard clause.

    def _fetch_hub_spoke_vpns(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:  # WHY: returns hub-spoke subset + total for reporting.
        """Fetch org VPNs filtered to hub_spoke type.

        Returns (hub_spoke_vpns, all_vpns) so callers can report what was found.
        """
        try:  # WHY: mistapi/network faults must degrade to empty tuple, not raise.
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)  # WHY: raw VPN list.
            all_vpns = mistapi.get_all(response=response, mist_session=self.apisession)  # WHY: paginated fetch.
            hub_spoke = [vpn for vpn in all_vpns if vpn.get("type") == _HUB_SPOKE_TYPE]  # WHY: only hub-spoke pods.
            logging.debug(
                "Fetched %d hub-spoke VPNs out of %d total", len(hub_spoke), len(all_vpns)
            )  # WHY: helps triage empty-hub-spoke reports.
            return hub_spoke, all_vpns  # WHY: caller distinguishes 'no VPNs' from 'no hub-spoke VPNs'.
        except Exception:  # WHY: same broad-catch degradation as _fetch_profiles.
            logging.exception("Failed to fetch org VPNs")  # WHY: full traceback for triage.
            logging.error(_MSG_ERR_VPNS)  # WHY: operator-visible connectivity hint via logger.
            return [], []  # WHY: signal both lists empty to caller.

    @staticmethod
    def _report_no_hub_spoke(all_vpns: list[dict[str, Any]]) -> None:  # WHY: helper for empty-hub-spoke UX branch.
        """Tell the user what VPN types were found instead of hub_spoke."""
        if not all_vpns:  # WHY: guard clause - distinguish 'zero VPNs' from 'no hub-spoke'.
            logging.warning(_MSG_NO_VPNS)  # WHY: operator-visible empty-inventory msg via logger.
            return  # WHY: nothing further to summarize.
        type_counts: dict[str, int] = {}  # WHY: histogram of type -> count for operator context.
        for vpn in all_vpns:  # WHY: single-pass tally keeps helper cheap.
            vpn_type = vpn.get("type", _UNKNOWN_TYPE) or _UNKNOWN_TYPE  # WHY: normalise missing/None to 'unknown'.
            type_counts[vpn_type] = type_counts.get(vpn_type, 0) + 1  # WHY: increment counter for that type.
        summary = ", ".join(
            f"{count} {vtype}" for vtype, count in sorted(type_counts.items())
        )  # WHY: deterministic sorted summary aids log diff review.
        logging.warning(
            "! No hub-spoke VPN definitions found. Found %d VPN(s): %s.",
            len(all_vpns),
            summary,
        )  # WHY: operator-visible guidance toward creating a hub_spoke overlay via logger.

    # ------------------------------------------------------------------
    # Path matching
    # ------------------------------------------------------------------

    def _find_matching_paths(
        self,
        profile_name: str,
        vpns: list[dict[str, Any]],
    ) -> list[tuple[str, str, str, int]]:  # WHY: tuple order (vpn_id, vpn_name, path_key, pod) contractual.
        """Find VPN paths whose key starts with '{profile_name}-'.

        Returns list of (vpn_id, vpn_name, path_key, current_pod) tuples.
        """
        matches: list[tuple[str, str, str, int]] = []  # WHY: aggregate across all VPN objects.
        prefix = f"{profile_name}-"  # WHY: trailing hyphen prevents 'DC1' from swallowing 'DC1-BACKUP'.
        for vpn in vpns:  # WHY: scan each VPN's paths dict.
            vpn_id = vpn.get("id", "")  # WHY: needed later to target updateOrgVpn.
            vpn_name = vpn.get("name", "")  # WHY: friendlier reference in error messages.
            paths = vpn.get("paths", {})  # WHY: defensive default for missing/malformed records.
            for path_key, path_value in paths.items():  # WHY: iterate every declared path.
                if path_key.startswith(prefix):  # WHY: profile-scoped prefix match.
                    pod = path_value.get("pod", self.POD_DEFAULT)  # WHY: unset pod treated as default 1.
                    matches.append((vpn_id, vpn_name, path_key, pod))  # WHY: tuple used by callers unchanged.
        return matches  # WHY: caller filters/aggregates further.

    def _build_vpn_data(
        self,
        profiles: list[dict[str, Any]],
        vpns: list[dict[str, Any]],
    ) -> dict[str, list[tuple[str, str, str, int]]]:  # WHY: precomputed cache keyed by profile name.
        """Pre-compute matching paths for every profile."""
        data: dict[str, list[tuple[str, str, str, int]]] = {}  # WHY: profile name -> match list index.
        for profile in profiles:  # WHY: one pass builds display-time cache.
            name = profile.get("name", "")  # WHY: same fallback as _find_matching_paths.
            data[name] = self._find_matching_paths(name, vpns)  # WHY: cache path matches by profile.
        return data  # WHY: consumed by display + action helpers.

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _display_profile_list(
        self,
        profiles: list[dict[str, Any]],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:  # WHY: pure I/O helper - no state mutation, just formatted print.
        """Print numbered, alphabetized profile list with pod values."""
        logging.warning(_MSG_HEADING_PROFILES)  # WHY: operator-visible list heading via logger.
        for index, profile in enumerate(profiles, start=1):  # WHY: 1-based numbering matches prompt.
            name = profile.get("name", "")  # WHY: default matches _build_vpn_data key.
            matches = vpn_data.get(name, [])  # WHY: precomputed match cache lookup.
            pod_display = self._format_pod_display(matches)  # WHY: uniform pod summary.
            logging.warning("   %d. %-30s %s", index, name, pod_display)  # WHY: aligned row via logger.
        logging.warning("")  # WHY: trailing blank line separates list from prompt via logger.

    @staticmethod
    def _format_pod_display(
        matches: list[tuple[str, str, str, int]],
    ) -> str:  # WHY: pure formatter used by display list and action menu.
        """Format pod value for display, detecting inconsistencies."""
        if not matches:  # WHY: distinct sentinel when profile has no VPN paths.
            return _POD_NO_PATHS  # WHY: makes empty result unambiguous.
        pod_values = {pod for (_, _, _, pod) in matches}  # WHY: dedupe to detect uniform vs mixed pods.
        if len(pod_values) == 1:  # WHY: uniform case gets human-friendly label.
            pod = pod_values.pop()  # WHY: extract single value.
            label = _POD_DEFAULT_LABEL if pod == POD_DEFAULT else str(pod)  # WHY: friendlier label for default.
            return f"{_POD_LABEL_PREFIX}{label}"  # WHY: uniform display prefix.
        sorted_pods = sorted(pod_values)  # WHY: deterministic order in mixed message.
        return f"{_POD_MIXED_PREFIX}{sorted_pods}"  # WHY: flags path drift to the operator.

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------

    def _prompt_profile_selection(
        self,
        profiles: list[dict[str, Any]],
    ) -> dict[str, Any] | None:  # WHY: None sentinel signals operator cancel to run().
        """Prompt user to select a profile by index number."""
        count = len(profiles)  # WHY: reused in prompt and range check.
        while True:  # WHY: loop until valid selection or explicit cancel.
            choice = self._safe_input(
                f"  Select profile (1-{count}) or 'q' to cancel: ",
                context=_CTX_PROFILE_SELECT,
            )  # WHY: EOF-safe input with structured context tag.
            if choice.lower() == _QUIT_CHAR:  # WHY: case-insensitive cancel handling.
                logging.warning(_MSG_CANCELLED)  # WHY: operator-visible cancel ack via logger.
                return None  # WHY: sentinel drives run() to exit workflow.
            selected = self._resolve_choice_index(choice, profiles, count)  # WHY: pure parse + range check.
            if selected is not None:  # WHY: valid index found, return match.
                return selected  # WHY: caller uses this profile for subsequent action.
            logging.warning("  Please enter a number between 1 and %d.", count)  # WHY: retry hint via logger.

    @staticmethod
    def _resolve_choice_index(
        choice: str,
        profiles: list[dict[str, Any]],
        count: int,
    ) -> dict[str, Any] | None:  # WHY: pure parser - keeps the input loop small and testable.
        """Parse a 1-based choice string into a profile or None on invalid input."""
        try:  # WHY: non-numeric choices must fall through to retry.
            index = int(choice)  # WHY: convert to zero-based index below.
        except ValueError:  # WHY: alpha input is a normal retry case, not an error.
            return None  # WHY: caller prints retry hint.
        if not (1 <= index <= count):  # WHY: out-of-range index also drives retry.
            return None  # WHY: keep loop responsibility in caller.
        selected = profiles[index - 1]  # WHY: display list is 1-based, list is 0-based.
        logging.warning("  Selected: %s", selected.get("name", ""))  # WHY: selection echo via logger.
        return selected  # WHY: signal success to caller.

    def _prompt_action(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:  # WHY: coordinates display, warning, and table-driven dispatch.
        """Show set/clear/cancel menu for the selected profile."""
        name = profile.get("name", "")  # WHY: canonical name used for lookup + messages.
        matches = vpn_data.get(name, [])  # WHY: precomputed match cache for the profile.
        if not matches:  # WHY: guard clause - nothing to update for this profile.
            logging.warning("  No VPN paths found for profile '%s'.", name)  # WHY: exit reason via logger.
            return  # WHY: bail before any prompts.
        self._log_inconsistent_pods(name, matches)  # WHY: warn operator on drift before choice.
        self._display_action_menu(name, matches)  # WHY: render menu after any inconsistency warning.
        choice = self._safe_input(_MSG_ACTION_PROMPT, context=_CTX_ACTION_SELECT)  # WHY: capture 1/2/3.
        self._dispatch_action(choice, profile, vpn_data)  # WHY: table-driven handler selection.

    def _display_action_menu(
        self,
        name: str,
        matches: list[tuple[str, str, str, int]],
    ) -> None:  # WHY: extracted from _prompt_action so it stays under STRUCT-LENGTH.
        """Print the profile header and set/clear/cancel labels."""
        pod_display = self._format_pod_display(matches)  # WHY: reuse formatter for consistent display.
        logging.warning(
            "\n  Profile: %s\n  Current %s  (%d VPN paths)\n%s\n%s\n%s\n%s",
            name,
            pod_display,
            len(matches),
            _MSG_HEADING_ACTIONS,
            _MSG_ACTION_SET,
            _MSG_ACTION_CLEAR,
            _MSG_ACTION_CANCEL,
        )  # WHY: consolidated action-menu banner via logger.

    def _dispatch_action(
        self,
        choice: str,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:  # WHY: table-driven replaces the historical if/elif ladder (playbook item 2).
        """Table-driven dispatch replaces the historical if/elif ladder."""
        # WHY: self-bound lookup ensures test patches on _prompt_set_pod/clear_pod resolve at call time.
        handlers: dict[str, Callable[[dict[str, Any], dict[str, list[tuple[str, str, str, int]]]], None]] = {
            "1": self._prompt_set_pod,  # WHY: option 1 delegates to pod-value entry flow.
            "2": self.clear_pod,  # WHY: option 2 resets pod to default (1).
        }
        handler = handlers.get(choice)  # WHY: unknown / '3' falls through to cancel branch.
        if handler is None:  # WHY: '3' or garbage input is the cancel path.
            logging.warning(_MSG_CANCELLED)  # WHY: canonical cancel message via logger.
            return  # WHY: no state change.
        handler(profile, vpn_data)  # WHY: invoke selected handler with the profile + cached matches.

    def _prompt_set_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:  # WHY: split from _read_pod_value / _confirm to stay under STRUCT-LENGTH.
        """Prompt for new pod value and execute set."""
        new_pod = self._read_pod_value()  # WHY: parse + range check in one helper.
        if new_pod is None:  # WHY: guard clause - invalid entry already surfaced its own message.
            return  # WHY: caller loop is unchanged.
        confirm_prompt = f"  Update all matching paths to pod {new_pod}? (y/N): "  # WHY: build prompt once.
        if not self._confirm(confirm_prompt, _CTX_CONFIRM_SET):  # WHY: explicit y required to proceed.
            logging.warning(_MSG_CANCELLED)  # WHY: cancel ack via logger.
            return  # WHY: skip API call when operator declines.
        self.set_pod(profile, vpn_data, new_pod)  # WHY: proceed with the batched update.

    def _read_pod_value(self) -> int | None:  # WHY: encapsulates numeric parse + range gate.
        """Prompt for and validate a pod integer within POD_MIN..POD_MAX."""
        raw = self._safe_input(
            f"  Enter new pod value ({self.POD_MIN}-{self.POD_MAX}): ",
            context=_CTX_POD_INPUT,
        )  # WHY: capture raw string entry so we can validate before conversion.
        try:  # WHY: any non-numeric input is a normal validation failure.
            new_pod = int(raw)  # WHY: pod is stored as integer in Mist API.
        except ValueError:  # WHY: friendlier than raising to menu.
            logging.warning(
                "  Pod value must be between %d and %d.", self.POD_MIN, self.POD_MAX
            )  # WHY: rejection hint via logger.
            return None  # WHY: sentinel drives caller cancel path.
        if not (self.POD_MIN <= new_pod <= self.POD_MAX):  # WHY: enforce API-accepted range.
            logging.warning(
                "  Pod value must be between %d and %d.", self.POD_MIN, self.POD_MAX
            )  # WHY: same rejection hint via logger.
            return None  # WHY: consistent None sentinel for both failure modes.
        return new_pod  # WHY: valid integer returned to caller.

    def _confirm(self, prompt: str, context: str) -> bool:  # WHY: y/N gate reused for set + clear flows.
        """Return True only when the operator explicitly answers 'y' (case-insensitive)."""
        answer = self._safe_input(prompt, context=context)  # WHY: reuse injected safe-input for testability.
        return answer.lower() == _CONFIRM_YES  # WHY: y/Y proceeds. Anything else cancels.

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def set_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
        new_pod: int,
    ) -> None:  # WHY: public API - callable from other menus via WanHubGroupNumberManager instance.
        """Batch-update all matching VPN paths to new_pod value."""
        name = profile.get("name", "")  # WHY: index into precomputed cache.
        matches = vpn_data.get(name, [])  # WHY: cached matches from _build_vpn_data.
        if not matches:  # WHY: guard clause - nothing to update.
            logging.warning("  No VPN paths found for profile '%s'.", name)  # WHY: no-op reason via logger.
            return  # WHY: no API call needed.
        vpn_updates = self._group_by_vpn(matches, new_pod)  # WHY: batch by VPN id for fewer API calls.
        self._apply_vpn_updates(vpn_updates, name, new_pod)  # WHY: perform grouped update.

    def clear_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:  # WHY: public API - callable from other menus for pod reset operations.
        """Reset pod to default (1) on all matching paths."""
        name = profile.get("name", "")  # WHY: index into precomputed cache.
        matches = vpn_data.get(name, [])  # WHY: cached matches from _build_vpn_data.
        pod_values = {pod for (_, _, _, pod) in matches}  # WHY: dedupe pods to short-circuit no-ops.
        if pod_values == {self.POD_DEFAULT}:  # WHY: already at default = no-op.
            logging.warning(
                "  Pod for '%s' is already at default (1). No action needed.", name
            )  # WHY: no-op explanation via logger.
            return  # WHY: skip API call and prompt.
        if not self._confirm(
            f"  Reset pod to default (1) on {len(matches)} paths? (y/N): ",
            _CTX_CONFIRM_CLEAR,
        ):  # WHY: destructive reset requires explicit y.
            logging.warning(_MSG_CANCELLED)  # WHY: cancel ack via logger.
            return  # WHY: skip API call.
        self.set_pod(profile, vpn_data, self.POD_DEFAULT)  # WHY: delegate to set_pod with default value.

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def _group_by_vpn(
        self,
        matches: list[tuple[str, str, str, int]],
        new_pod: int,
    ) -> dict[str, dict[str, Any]]:  # WHY: collapse cross-VPN matches into one PATCH per VPN.
        """Group path updates by VPN id for batch API calls."""
        vpn_map: dict[str, dict[str, Any]] = {}  # WHY: vpn_id -> {name, paths[]} accumulator.
        for vpn_id, vpn_name, path_key, _current in matches:  # WHY: current pod ignored - we overwrite.
            if vpn_id not in vpn_map:  # WHY: first path for this vpn seeds the entry.
                vpn_map[vpn_id] = {"name": vpn_name, "paths": []}  # WHY: cache friendly name + empty list.
            vpn_map[vpn_id]["paths"].append(path_key)  # WHY: aggregate path keys per VPN.
        _ = new_pod  # WHY: parameter reserved for future per-VPN branching. Kept for API stability.
        return vpn_map  # WHY: caller iterates once per VPN.

    def _apply_vpn_updates(
        self,
        vpn_updates: dict[str, dict[str, Any]],
        profile_name: str,
        new_pod: int,
    ) -> None:  # WHY: orchestrate per-VPN PATCH loop and print final summary.
        """Apply pod updates to each VPN object via API."""
        total_updated = 0  # WHY: aggregate count across VPNs for final message.
        for vpn_id, info in vpn_updates.items():  # WHY: one PATCH per VPN.
            updated = self._apply_one_vpn(vpn_id, info, new_pod)  # WHY: safe per-VPN mutation.
            if updated is None:  # WHY: None signals failure - abort remaining VPNs.
                return  # WHY: preserve partial-success state for triage.
            total_updated += updated  # WHY: accumulate successful mutation count.
        logging.warning(
            "  Updated %d paths for '%s' to pod %d.",
            total_updated,
            profile_name,
            new_pod,
        )  # WHY: final success summary via logger.

    def _apply_one_vpn(
        self,
        vpn_id: str,
        info: dict[str, Any],
        new_pod: int,
    ) -> int | None:  # WHY: return None on failure so caller can short-circuit.
        """Update a single VPN and log outcome. Return count or None on error."""
        vpn_name = info["name"]  # WHY: friendlier reference in messages.
        path_keys = info["paths"]  # WHY: exact set of keys to overwrite.
        try:  # WHY: isolate per-VPN failure from the loop.
            updated = self._update_single_vpn(vpn_id, path_keys, new_pod)  # WHY: fetch+mutate+push.
            logging.info(
                "Updated %d paths in VPN '%s' to pod %d",
                updated,
                vpn_name,
                new_pod,
            )  # WHY: per-VPN audit trail for NOC change review.
            return updated  # WHY: caller aggregates counts across VPNs.
        except Exception:  # WHY: broad catch - preserves partial-success reporting.
            logging.exception("Failed to update VPN '%s'", vpn_name)  # WHY: full traceback for triage.
            logging.error(
                "  Error updating VPN '%s'. Check logs for details.", vpn_name
            )  # WHY: operator-visible failure hint via logger.
            return None  # WHY: sentinel telling caller to abort remaining VPNs.

    def _update_single_vpn(
        self,
        vpn_id: str,
        path_keys: list[str],
        new_pod: int,
    ) -> int:
        """Fetch, modify, and push a single VPN object."""
        response = mistapi.api.v1.orgs.vpns.getOrgVpn(
            self.apisession, self.org_id, vpn_id
        )  # WHY: read-modify-write pattern requires current VPN body.
        vpn_obj = response.data if hasattr(response, "data") else response  # WHY: raw dict vs response wrapper.
        vpn_copy = copy.deepcopy(vpn_obj)  # WHY: avoid mutating cached API response.
        paths = vpn_copy.get("paths", {})  # WHY: defensive default for malformed records.
        count = 0  # WHY: track how many keys we mutated for aggregate log.
        for key in path_keys:  # WHY: mutate only keys we identified.
            if key in paths:  # WHY: skip stale keys defensively.
                paths[key]["pod"] = new_pod  # WHY: overwrite pod value in-place.
                count += 1  # WHY: increment mutation count.
        mistapi.api.v1.orgs.vpns.updateOrgVpn(
            self.apisession, self.org_id, vpn_id, body=vpn_copy
        )  # WHY: push the whole VPN back per Mist API semantics.
        return count  # WHY: caller aggregates counts across VPNs.

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _log_inconsistent_pods(
        self,
        name: str,
        matches: list[tuple[str, str, str, int]],
    ) -> None:
        """Warn if a profile's VPN paths have different pod values."""
        pod_values = {pod for (_, _, _, pod) in matches}  # WHY: dedupe to detect drift.
        if len(pod_values) <= 1:  # WHY: guard clause - uniform pods need no warning.
            return  # WHY: skip warning fast-path.
        sorted_pods = sorted(pod_values)  # WHY: deterministic ordering in message.
        logging.warning(
            "Paths for %s have mixed pod values: %s", name, sorted_pods
        )  # WHY: raise operations attention to drift.
        logging.warning(
            "  Warning: Paths for %s have mixed pod values (%s). " "All will be updated to the new value.",
            name,
            ", ".join(str(p) for p in sorted_pods),
        )  # WHY: operator-facing warning mirrors the log message via logger.

    @staticmethod
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:
        """Fallback input when safe_input is not provided.

        Delegates to the canonical EOF-safe wrapper so this path is not a second
        hand-rolled input() implementation (issue #452: clears CONV-INPUT, keeps
        identical EOF/interrupt-degrades-to-empty-string behavior).
        """
        from src.utils.input_utils import InputUtils  # WHY: local import avoids import cycle at module load.

        return InputUtils.safe_input(prompt, context=_CTX_FALLBACK)  # WHY: EOF-safe. Returns '' on EOF.
