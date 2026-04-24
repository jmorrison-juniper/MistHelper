"""WAN Hub Group Number Manager — Menu 163.

Manage the pod (group number) field on VPN paths associated with
WAN Hub Profiles (gateway device profiles).  NOC engineers pick a
profile from an alphabetized list, then set or clear the pod value
across all matching VPN paths.

This is the first menu operation implemented as an external module
under ``src/``, establishing the pattern for future extractions from
the MistHelper monolith.
"""

import copy
import logging

import mistapi
import mistapi.api.v1.orgs.deviceprofiles
import mistapi.api.v1.orgs.vpns


class WanHubGroupNumberManager:
    """Interactive manager for WAN Hub Profile group numbers (pod values)."""

    POD_MIN = 1
    POD_MAX = 128
    POD_DEFAULT = 1

    def __init__(self, apisession, org_id: str, safe_input_func=None):
        self.apisession = apisession
        self.org_id = org_id
        self._safe_input = safe_input_func or self._fallback_input

    # ------------------------------------------------------------------
    # Entry point (called from menu_actions)
    # ------------------------------------------------------------------

    @staticmethod
    def execute(apisession, get_org_id_func, safe_input_func):
        """Static entry point called by menu_actions lambda."""
        org_id = get_org_id_func()
        if not org_id:
            print("! No organization selected. Exiting.")
            return
        manager = WanHubGroupNumberManager(apisession, org_id, safe_input_func)
        manager.run()

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self):
        """Main workflow: fetch, display, select, act."""
        print("\n=== WAN Hub Group Number Manager ===")
        logging.info("Starting WAN Hub Group Number Manager")

        profiles = self._fetch_profiles()
        if not profiles:
            print("! No WAN Hub Profiles found in this organization.")
            return

        vpns, all_vpns = self._fetch_hub_spoke_vpns()
        if not vpns:
            self._report_no_hub_spoke(all_vpns)
            return

        vpn_data = self._build_vpn_data(profiles, vpns)
        self._display_profile_list(profiles, vpn_data)

        selected = self._prompt_profile_selection(profiles)
        if selected is None:
            return

        self._prompt_action(selected, vpn_data)

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self):
        """Fetch gateway device profiles, sorted alphabetically."""
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )
            profiles = mistapi.get_all(response=response, mist_session=self.apisession)
            profiles.sort(key=lambda profile: profile.get("name", "").lower())
            logging.debug("Fetched %d gateway profiles", len(profiles))
            return profiles
        except Exception:
            logging.error("Failed to fetch device profiles", exc_info=True)
            print("! Error retrieving WAN Hub Profiles. Check API connectivity.")
            return []

    def _fetch_hub_spoke_vpns(self):
        """Fetch org VPNs filtered to hub_spoke type.

        Returns (hub_spoke_vpns, all_vpns) so callers can report what was found.
        """
        try:
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)
            all_vpns = mistapi.get_all(response=response, mist_session=self.apisession)
            hub_spoke = [vpn for vpn in all_vpns if vpn.get("type") == "hub_spoke"]
            logging.debug("Fetched %d hub-spoke VPNs out of %d total", len(hub_spoke), len(all_vpns))
            return hub_spoke, all_vpns
        except Exception:
            logging.error("Failed to fetch org VPNs", exc_info=True)
            print("! Error retrieving VPN definitions. Check API connectivity.")
            return [], []

    @staticmethod
    def _report_no_hub_spoke(all_vpns):
        """Tell the user what VPN types were found instead of hub_spoke."""
        if not all_vpns:
            print("! No VPN definitions found in this organization.")
            return
        type_counts = {}
        for vpn in all_vpns:
            vpn_type = vpn.get("type", "unknown") or "unknown"
            type_counts[vpn_type] = type_counts.get(vpn_type, 0) + 1
        summary = ", ".join(f"{count} {vtype}" for vtype, count in sorted(type_counts.items()))
        print(f"! No hub-spoke VPN definitions found. Found {len(all_vpns)} VPN(s): {summary}.")

    # ------------------------------------------------------------------
    # Path matching
    # ------------------------------------------------------------------

    def _find_matching_paths(self, profile_name, vpns):
        """Find VPN paths whose key starts with '{profile_name}-'.

        Returns list of (vpn_id, vpn_name, path_key, current_pod) tuples.
        """
        matches = []
        prefix = f"{profile_name}-"
        for vpn in vpns:
            vpn_id = vpn.get("id", "")
            vpn_name = vpn.get("name", "")
            paths = vpn.get("paths", {})
            for path_key, path_value in paths.items():
                if path_key.startswith(prefix):
                    pod = path_value.get("pod", self.POD_DEFAULT)
                    matches.append((vpn_id, vpn_name, path_key, pod))
        return matches

    def _build_vpn_data(self, profiles, vpns):
        """Pre-compute matching paths for every profile."""
        data = {}
        for profile in profiles:
            name = profile.get("name", "")
            data[name] = self._find_matching_paths(name, vpns)
        return data

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _display_profile_list(self, profiles, vpn_data):
        """Print numbered, alphabetized profile list with pod values."""
        print("\n  WAN Hub Profiles:")
        for index, profile in enumerate(profiles, start=1):
            name = profile.get("name", "")
            matches = vpn_data.get(name, [])
            pod_display = self._format_pod_display(matches)
            print(f"   {index}. {name:<30s} {pod_display}")
        print()

    @staticmethod
    def _format_pod_display(matches):
        """Format pod value for display, detecting inconsistencies."""
        if not matches:
            return "Pod: -- (no VPN paths)"
        pod_values = {pod for (_, _, _, pod) in matches}
        if len(pod_values) == 1:
            pod = pod_values.pop()
            label = "default (1)" if pod == 1 else str(pod)
            return f"Pod: {label}"
        sorted_pods = sorted(pod_values)
        return f"Pod: MIXED {sorted_pods}"

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------

    def _prompt_profile_selection(self, profiles):
        """Prompt user to select a profile by index number."""
        count = len(profiles)
        while True:
            choice = self._safe_input(
                f"  Select profile (1-{count}) or 'q' to cancel: ",
                context="wan_hub_profile_select",
            )
            if choice.lower() == "q":
                print("  Cancelled.")
                return None
            try:
                index = int(choice)
            except ValueError:
                print(f"  Please enter a number between 1 and {count}.")
                continue
            if 1 <= index <= count:
                selected = profiles[index - 1]
                print(f"  Selected: {selected.get('name', '')}")
                return selected
            print(f"  Please enter a number between 1 and {count}.")

    def _prompt_action(self, profile, vpn_data):
        """Show set/clear/cancel menu for the selected profile."""
        name = profile.get("name", "")
        matches = vpn_data.get(name, [])

        if not matches:
            print(f"  No VPN paths found for profile '{name}'.")
            return

        self._log_inconsistent_pods(name, matches)
        pod_display = self._format_pod_display(matches)

        print(f"\n  Profile: {name}")
        print(f"  Current {pod_display}  ({len(matches)} VPN paths)")
        print("\n  Actions:")
        print("   1. Set new pod value")
        print("   2. Clear pod (reset to default 1)")
        print("   3. Cancel")

        choice = self._safe_input("  Select action (1-3): ", context="wan_hub_action_select")
        if choice == "1":
            self._prompt_set_pod(profile, vpn_data)
        elif choice == "2":
            self.clear_pod(profile, vpn_data)
        else:
            print("  Cancelled.")

    def _prompt_set_pod(self, profile, vpn_data):
        """Prompt for new pod value and execute set."""
        raw = self._safe_input(
            f"  Enter new pod value ({self.POD_MIN}-{self.POD_MAX}): ",
            context="wan_hub_pod_input",
        )
        try:
            new_pod = int(raw)
        except ValueError:
            print(f"  Pod value must be between {self.POD_MIN} and {self.POD_MAX}.")
            return
        if not (self.POD_MIN <= new_pod <= self.POD_MAX):
            print(f"  Pod value must be between {self.POD_MIN} and {self.POD_MAX}.")
            return
        confirm = self._safe_input(
            f"  Update all matching paths to pod {new_pod}? (y/N): ",
            context="wan_hub_confirm_set",
        )
        if confirm.lower() != "y":
            print("  Cancelled.")
            return
        self.set_pod(profile, vpn_data, new_pod)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def set_pod(self, profile, vpn_data, new_pod):
        """Batch-update all matching VPN paths to new_pod value."""
        name = profile.get("name", "")
        matches = vpn_data.get(name, [])
        if not matches:
            print(f"  No VPN paths found for profile '{name}'.")
            return

        vpn_updates = self._group_by_vpn(matches, new_pod)
        self._apply_vpn_updates(vpn_updates, name, new_pod)

    def clear_pod(self, profile, vpn_data):
        """Reset pod to default (1) on all matching paths."""
        name = profile.get("name", "")
        matches = vpn_data.get(name, [])
        pod_values = {pod for (_, _, _, pod) in matches}
        if pod_values == {self.POD_DEFAULT}:
            print(f"  Pod for '{name}' is already at default (1). No action needed.")
            return
        confirm = self._safe_input(
            f"  Reset pod to default (1) on {len(matches)} paths? (y/N): ",
            context="wan_hub_confirm_clear",
        )
        if confirm.lower() != "y":
            print("  Cancelled.")
            return
        self.set_pod(profile, vpn_data, self.POD_DEFAULT)

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def _group_by_vpn(self, matches, new_pod):
        """Group path updates by VPN id for batch API calls."""
        vpn_map = {}
        for vpn_id, vpn_name, path_key, _current in matches:
            if vpn_id not in vpn_map:
                vpn_map[vpn_id] = {"name": vpn_name, "paths": []}
            vpn_map[vpn_id]["paths"].append(path_key)
        return vpn_map

    def _apply_vpn_updates(self, vpn_updates, profile_name, new_pod):
        """Apply pod updates to each VPN object via API."""
        total_updated = 0
        for vpn_id, info in vpn_updates.items():
            vpn_name = info["name"]
            path_keys = info["paths"]
            try:
                updated = self._update_single_vpn(vpn_id, path_keys, new_pod)
                total_updated += updated
                logging.info(
                    "Updated %d paths in VPN '%s' to pod %d",
                    updated,
                    vpn_name,
                    new_pod,
                )
            except Exception:
                logging.error("Failed to update VPN '%s'", vpn_name, exc_info=True)
                print(f"  Error updating VPN '{vpn_name}'. Check logs for details.")
                return
        print(f"  Updated {total_updated} paths for '{profile_name}' to pod {new_pod}.")

    def _update_single_vpn(self, vpn_id, path_keys, new_pod):
        """Fetch, modify, and push a single VPN object."""
        response = mistapi.api.v1.orgs.vpns.getOrgVpn(self.apisession, self.org_id, vpn_id)
        vpn_obj = response.data if hasattr(response, "data") else response
        vpn_copy = copy.deepcopy(vpn_obj)
        paths = vpn_copy.get("paths", {})
        count = 0
        for key in path_keys:
            if key in paths:
                paths[key]["pod"] = new_pod
                count += 1
        mistapi.api.v1.orgs.vpns.updateOrgVpn(self.apisession, self.org_id, vpn_id, body=vpn_copy)
        return count

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _log_inconsistent_pods(self, name, matches):
        """Warn if a profile's VPN paths have different pod values."""
        pod_values = {pod for (_, _, _, pod) in matches}
        if len(pod_values) > 1:
            sorted_pods = sorted(pod_values)
            logging.warning("Paths for %s have mixed pod values: %s", name, sorted_pods)
            print(
                f"  Warning: Paths for {name} have mixed pod values "
                f"({', '.join(str(p) for p in sorted_pods)}). "
                "All will be updated to the new value."
            )

    @staticmethod
    def _fallback_input(prompt, **kwargs):
        """Fallback input when safe_input is not provided."""
        try:
            return input(prompt).strip()
        except EOFError:
            logging.info("EOF detected in wan_hub_group_manager")
            return ""
        except KeyboardInterrupt:
            print("\n  Interrupted.")
            return ""
