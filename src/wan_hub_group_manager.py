"""WAN Hub Group Number Manager — Menu 163.

Manage the pod (group number) field on VPN paths associated with
WAN Hub Profiles (gateway device profiles). NOC engineers pick a
profile from an alphabetized list, then set or clear the pod value
across all matching VPN paths.  # module purpose

External module pattern for menu extraction from monolith.  # design note
"""

from __future__ import annotations  # postponed annotations for typing

import copy  # deep copy objects before mutating
import logging  # structured logging for operations
from collections.abc import Callable  # typing for callable parameters
from typing import Any, cast  # generic Any type and cast helper for typing

import mistapi  # Mist API helper package
import mistapi.api.v1.orgs.deviceprofiles  # device profile API bindings
import mistapi.api.v1.orgs.vpns  # VPN API bindings


class WanHubGroupNumberManager:
    """Interactive manager for WAN Hub Profile group numbers (pod values)."""

    POD_MIN = 1  # minimum allowed pod value
    POD_MAX = 128  # maximum allowed pod value
    POD_DEFAULT = 1  # default pod value if none specified

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        safe_input_func: Callable[..., str] | None = None,
    ) -> None:
        """Initialize with API session, org ID, and optional input function."""
        # Store provided Mist API session and org identifier for subsequent API calls.
        self.apisession = apisession  # Mist API session object
        self.org_id = org_id  # organization id to scope API calls
        # Allow injection of a safe_input function for testing or alternate UIs;
        # fall back to a simple stdin-based implementation when not provided.
        self._safe_input = safe_input_func or self._fallback_input  # input helper

    # ------------------------------------------------------------------
    # Entry point (called from menu_actions)
    # ------------------------------------------------------------------

    @staticmethod
    def execute(
        apisession: Any,
        get_org_id_func: Callable[[], str | None],
        safe_input_func: Callable[..., str] | None,
    ) -> None:
        """Static entry point called by menu_actions lambda."""
        org_id = get_org_id_func()  # resolve org id using provided helper
        if not org_id:  # guard: exit if no org selected
            print("! No organization selected. Exiting.")  # user-visible message
            return
        manager = WanHubGroupNumberManager(apisession, org_id, safe_input_func)  # instantiate manager
        manager.run()  # run interactive workflow

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main workflow: fetch, display, select, act."""
        print("\n=== WAN Hub Group Number Manager ===")  # CLI header
        logging.info("Starting WAN Hub Group Number Manager")  # log start

        profiles = self._fetch_profiles()  # fetch gateway profiles
        if not profiles:  # nothing to operate on
            print("! No WAN Hub Profiles found in this organization.")
            return

        vpns, all_vpns = self._fetch_hub_spoke_vpns()  # fetch hub-spoke vpn objects
        if not vpns:  # no hub-spoke vpns found
            self._report_no_hub_spoke(all_vpns)  # inform user what was found
            return

        vpn_data = self._build_vpn_data(profiles, vpns)  # precompute matching paths per profile
        self._display_profile_list(profiles, vpn_data)  # show profiles with pod summary

        selected = self._prompt_profile_selection(profiles)  # prompt user to pick a profile
        if selected is None:  # user cancelled
            return

        self._prompt_action(selected, vpn_data)  # show actions menu for selected profile

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self) -> list[dict[str, Any]]:
        """Fetch gateway device profiles, sorted alphabetically."""
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )  # request gateway device profiles
            # Expand paginated response into a single list for ease of processing.
            profiles: list[dict[str, Any]] = mistapi.get_all(
                response=response, mist_session=self.apisession
            )  # collect paginated pages
            profiles.sort(key=lambda profile: profile.get("name", "").lower())  # sort by name
            logging.debug("Fetched %d gateway profiles", len(profiles))  # debug log
            return profiles  # return list
        except Exception:
            logging.error("Failed to fetch device profiles", exc_info=True)  # log exception
            print("! Error retrieving WAN Hub Profiles. Check API connectivity.")  # user message
            return []  # return empty list on error

    def _fetch_hub_spoke_vpns(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch org VPNs filtered to hub_spoke type.

        Returns (hub_spoke_vpns, all_vpns) so callers can report what was found.
        """
        try:
            # Retrieve all VPNs in the org then filter to hub_spoke topology.
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)  # list all org VPNs
            all_vpns = mistapi.get_all(response=response, mist_session=self.apisession)  # expand pages
            hub_spoke = [vpn for vpn in all_vpns if vpn.get("type") == "hub_spoke"]  # filter by type
            logging.debug(
                "Fetched %d hub-spoke VPNs out of %d total",
                len(hub_spoke),
                len(all_vpns),
            )  # debug
            return hub_spoke, all_vpns  # return tuple
        except Exception:
            logging.error("Failed to fetch org VPNs", exc_info=True)  # log error
            print("! Error retrieving VPN definitions. Check API connectivity.")  # user message
            return [], []  # return empty lists on error

    @staticmethod
    def _report_no_hub_spoke(all_vpns: list[dict[str, Any]]) -> None:
        """Tell the user what VPN types were found instead of hub_spoke."""
        if not all_vpns:  # no VPNs at all
            print("! No VPN definitions found in this organization.")
            return
        type_counts: dict[str, int] = {}  # count vpn types
        for vpn in all_vpns:  # accumulate counts
            vpn_type = vpn.get("type", "unknown") or "unknown"
            type_counts[vpn_type] = type_counts.get(vpn_type, 0) + 1
        summary = ", ".join(f"{count} {vtype}" for vtype, count in sorted(type_counts.items()))  # summary string
        print(f"! No hub-spoke VPN definitions found. Found {len(all_vpns)} VPN(s): {summary}.")  # print summary

    # ------------------------------------------------------------------
    # Path matching
    # ------------------------------------------------------------------

    def _find_matching_paths(
        self,
        profile_name: str,
        vpns: list[dict[str, Any]],
    ) -> list[tuple[str, str, str, int]]:
        """Find VPN paths whose key starts with '{profile_name}-'.

        Returns list of (vpn_id, vpn_name, path_key, current_pod) tuples.
        """
        # Match any VPN path key beginning with '<profile_name>-' to identify
        # paths that were derived from the gateway profile's name. Return tuples
        # of (vpn_id, vpn_name, path_key, pod_value) for downstream processing.
        matches = []  # result list
        prefix = f"{profile_name}-"  # prefix to match on path keys
        for vpn in vpns:  # iterate vpn objects
            vpn_id = vpn.get("id", "")  # vpn id
            vpn_name = vpn.get("name", "")  # vpn name
            paths = vpn.get("paths", {})  # paths mapping
            for path_key, path_value in paths.items():  # iterate path entries
                if path_key.startswith(prefix):  # match prefix
                    pod = path_value.get("pod", self.POD_DEFAULT)  # extract pod value
                    matches.append((vpn_id, vpn_name, path_key, pod))  # add tuple
        return matches  # return matches

    def _build_vpn_data(
        self,
        profiles: list[dict[str, Any]],
        vpns: list[dict[str, Any]],
    ) -> dict[str, list[tuple[str, str, str, int]]]:
        """Pre-compute matching paths for every profile."""
        data = {}  # mapping profile_name -> list of matches
        for profile in profiles:  # iterate profiles
            name = profile.get("name", "")  # profile name
            data[name] = self._find_matching_paths(name, vpns)  # compute matches
        return data  # return mapping

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _display_profile_list(
        self,
        profiles: list[dict[str, Any]],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:
        """Print numbered, alphabetized profile list with pod values."""
        # Show a compact list so NOC operator can pick by index.
        print("\n  WAN Hub Profiles:")  # header
        for index, profile in enumerate(profiles, start=1):  # enumerate profiles
            name = profile.get("name", "")  # profile name
            matches = vpn_data.get(name, [])  # matching paths
            pod_display = self._format_pod_display(matches)  # formatted pod string
            print(f"   {index}. {name:<30s} {pod_display}")  # formatted line
        print()  # newline

    @staticmethod
    def _format_pod_display(
        matches: list[tuple[str, str, str, int]],
    ) -> str:
        """Format pod value for display, detecting inconsistencies."""
        if not matches:
            return "Pod: -- (no VPN paths)"  # no paths
        pod_values = {pod for (_, _, _, pod) in matches}  # unique pod values set
        if len(pod_values) == 1:  # single pod value
            pod = pod_values.pop()
            label = "default (1)" if pod == 1 else str(pod)
            return f"Pod: {label}"
        sorted_pods = sorted(pod_values)  # mixed values
        return f"Pod: MIXED {sorted_pods}"

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------

    def _prompt_profile_selection(
        self,
        profiles: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Prompt user to select a profile by index number."""
        # Prompt until a valid numeric selection is provided or user cancels.
        count = len(profiles)  # number of profiles
        while True:  # loop until valid selection or cancel
            choice = self._safe_input(
                f"  Select profile (1-{count}) or 'q' to cancel: ",
                context="wan_hub_profile_select",
            )  # prompt
            if choice.lower() == "q":  # cancel
                print("  Cancelled.")
                return None
            try:
                index = int(choice)  # parse integer
            except ValueError:
                print(f"  Please enter a number between 1 and {count}.")
                continue
            if 1 <= index <= count:  # valid range
                selected = profiles[index - 1]  # select profile
                print(f"  Selected: {selected.get('name', '')}")
                return selected
            print(f"  Please enter a number between 1 and {count}.")  # invalid

    def _prompt_action(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:
        """Show set/clear/cancel menu for the selected profile."""
        # Present a short action menu for the selected profile.
        name = profile.get("name", "")  # profile name
        matches = vpn_data.get(name, [])  # matching path tuples

        if not matches:  # nothing to update
            print(f"  No VPN paths found for profile '{name}'.")
            return

        self._log_inconsistent_pods(name, matches)  # warn if inconsistent
        pod_display = self._format_pod_display(matches)  # formatted pod info

        print(f"\n  Profile: {name}")  # display selected profile info
        print(f"  Current {pod_display}  ({len(matches)} VPN paths)")  # counts
        print("\n  Actions:")  # action menu
        print("   1. Set new pod value")
        print("   2. Clear pod (reset to default 1)")
        print("   3. Cancel")

        choice = self._safe_input("  Select action (1-3): ", context="wan_hub_action_select")  # prompt
        if choice == "1":
            self._prompt_set_pod(profile, vpn_data)  # set pod
        elif choice == "2":
            self.clear_pod(profile, vpn_data)  # clear pod
        else:
            print("  Cancelled.")  # cancel

    def _prompt_set_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:
        """Prompt for new pod value and execute set."""
        # Request a numeric pod value and validate bounds before applying.
        raw = self._safe_input(
            f"  Enter new pod value ({self.POD_MIN}-{self.POD_MAX}): ",
            context="wan_hub_pod_input",
        )  # get raw input
        try:
            new_pod = int(raw)  # parse int
        except ValueError:
            print(f"  Pod value must be between {self.POD_MIN} and {self.POD_MAX}.")
            return
        if not (self.POD_MIN <= new_pod <= self.POD_MAX):  # validate range
            print(f"  Pod value must be between {self.POD_MIN} and {self.POD_MAX}.")
            return
        confirm = self._safe_input(
            f"  Update all matching paths to pod {new_pod}? (y/N): ",
            context="wan_hub_confirm_set",
        )  # confirmation
        if confirm.lower() != "y":
            print("  Cancelled.")
            return
        self.set_pod(profile, vpn_data, new_pod)  # perform update

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def set_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
        new_pod: int,
    ) -> None:
        """Batch-update all matching VPN paths to new_pod value."""
        # Group matches by VPN and perform the batched update.
        name = profile.get("name", "")  # profile name
        matches = vpn_data.get(name, [])  # matching paths
        if not matches:  # nothing to update
            print(f"  No VPN paths found for profile '{name}'.")
            return

        vpn_updates = self._group_by_vpn(matches, new_pod)  # group changes by vpn id
        self._apply_vpn_updates(vpn_updates, name, new_pod)  # apply updates

    def clear_pod(
        self,
        profile: dict[str, Any],
        vpn_data: dict[str, list[tuple[str, str, str, int]]],
    ) -> None:
        """Reset pod to default (1) on all matching paths."""
        name = profile.get("name", "")  # profile name
        matches = vpn_data.get(name, [])  # matching paths
        pod_values = {pod for (_, _, _, pod) in matches}  # current pod values
        if pod_values == {self.POD_DEFAULT}:  # already default
            print(f"  Pod for '{name}' is already at default (1). No action needed.")
            return
        confirm = self._safe_input(
            f"  Reset pod to default (1) on {len(matches)} paths? (y/N): ",
            context="wan_hub_confirm_clear",
        )  # confirmation
        if confirm.lower() != "y":
            print("  Cancelled.")
            return
        self.set_pod(profile, vpn_data, self.POD_DEFAULT)  # reset pod

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def _group_by_vpn(
        self,
        matches: list[tuple[str, str, str, int]],
        new_pod: int,
    ) -> dict[str, dict[str, Any]]:
        """Group path updates by VPN id for batch API calls."""
        # Build map of vpn_id -> {name, paths[]} to minimize number of API
        # update calls (one per VPN) performed below.
        vpn_map: dict[str, dict[str, Any]] = {}  # vpn_id -> {name, paths}
        for vpn_id, vpn_name, path_key, _current in matches:  # collect paths per vpn
            if vpn_id not in vpn_map:
                vpn_map[vpn_id] = {"name": vpn_name, "paths": []}
            vpn_map[vpn_id]["paths"].append(path_key)  # append path key
        return vpn_map  # return map

    def _apply_vpn_updates(
        self,
        vpn_updates: dict[str, dict[str, Any]],
        profile_name: str,
        new_pod: int,
    ) -> None:
        """Apply pod updates to each VPN object via API."""
        total_updated = 0  # counter
        for vpn_id, info in vpn_updates.items():  # iterate VPNs to update
            vpn_name = info["name"]  # vpn name
            path_keys = info["paths"]  # list of path keys
            try:
                updated = self._update_single_vpn(vpn_id, path_keys, new_pod)  # update single VPN
                total_updated += updated  # accumulate
                logging.info(
                    "Updated %d paths in VPN '%s' to pod %d",
                    updated,
                    vpn_name,
                    new_pod,
                )  # log per-VPN update
            except Exception:
                logging.error("Failed to update VPN '%s'", vpn_name, exc_info=True)  # log failure
                print(f"  Error updating VPN '{vpn_name}'. Check logs for details.")
                return
        print(f"  Updated {total_updated} paths for '{profile_name}' to pod {new_pod}.")  # summary

    def _update_single_vpn(
        self,
        vpn_id: str,
        path_keys: list[str],
        new_pod: int,
    ) -> int:
        """Fetch, modify, and push a single VPN object."""
        # Retrieve latest VPN object, modify the selected path entries, then
        # push the full VPN object back to Mist API to persist changes.
        response = mistapi.api.v1.orgs.vpns.getOrgVpn(
            self.apisession, self.org_id, vpn_id
        )  # fetch vpn
        # Normalize APIResponse.data when present; cast to dict for static type checkers
        vpn_obj = getattr(response, "data", response)  # normalize
        vpn_copy = cast(dict, copy.deepcopy(vpn_obj))  # ensure typing.Registry: dict
        paths = vpn_copy.get("paths", {})  # get paths mapping
        count = 0  # updated paths counter
        for key in path_keys:  # modify specified keys
            if key in paths:
                paths[key]["pod"] = new_pod  # set new pod value
                count += 1
        mistapi.api.v1.orgs.vpns.updateOrgVpn(
            self.apisession, self.org_id, vpn_id, body=vpn_copy
        )  # push update
        return count  # return number updated

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _log_inconsistent_pods(
        self,
        name: str,
        matches: list[tuple[str, str, str, int]],
    ) -> None:
        """Warn if a profile's VPN paths have different pod values."""
        pod_values = {pod for (_, _, _, pod) in matches}  # unique pod set
        if len(pod_values) > 1:  # inconsistent pods
            sorted_pods = sorted(pod_values)  # sort for display
            logging.warning("Paths for %s have mixed pod values: %s", name, sorted_pods)  # log warning
            print(
                f"  Warning: Paths for {name} have mixed pod values "
                f"({', '.join(str(p) for p in sorted_pods)}). "
                "All will be updated to the new value."
            )  # user warning

    @staticmethod
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:
        """Fallback input when safe_input is not provided."""
        try:
            return input(prompt).strip()  # basic input fallback
        except EOFError:
            logging.info("EOF detected in wan_hub_group_manager")  # log EOF
            return ""  # return empty
        except KeyboardInterrupt:
            print("\n  Interrupted.")  # handle ctrl-c
            return ""  # return empty
