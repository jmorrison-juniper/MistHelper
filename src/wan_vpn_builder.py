"""WAN Hub-Spoke VPN Builder -- Menu 164.

Create hub-spoke VPN overlay definitions from gateway device profiles.  # module purpose
NOC engineers select profiles, assign hub/spoke roles, review  # user workflow summary
auto-generated VPN path keys with pod numbers, confirm, and the VPN  # what tool does
is created via API.  Optionally updates each profile's port_config  # optional post-step
with vpn_paths references to the new VPN.  # side-effect description

Follows the external-module pattern established by Menu 163  # design note
(``src/wan_hub_group_manager.py``).
"""

from __future__ import annotations  # enable postponed evaluation of annotations for forward refs

import logging  # standard logging for debug/info/error messages
import re  # regular expressions for pod suggestion parsing
from collections.abc import Callable  # type for callable input functions
from typing import Any  # generic Any type for untyped data structures

import mistapi  # Mist API helper utilities (get_all, response wrappers)
import mistapi.api.v1.orgs.deviceprofiles  # device profile API bindings
import mistapi.api.v1.orgs.vpns  # VPN API bindings


class WanVpnBuilder:
    """Build hub-spoke VPN overlays from gateway device profiles."""

    POD_MIN = 1  # minimum allowed pod/group number
    POD_MAX = 128  # maximum allowed pod/group number
    POD_DEFAULT = 1  # default pod value when not specified
    PATH_WARN_THRESHOLD = 500  # warn when VPN path count exceeds this value

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        safe_input_func: Callable[..., str] | None = None,
    ) -> None:
        """Initialize with API session, org ID, and optional input function."""
        self.apisession = apisession  # store Mist API session for calls
        self.org_id = org_id  # store organization id for scoped API calls
        # prefer provided safe_input_func, fallback to internal helper if None
        self._safe_input = safe_input_func or self._fallback_input

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
        org_id = get_org_id_func()  # resolve org id via provided helper
        if not org_id:  # guard: no org selected
            print("! No organization selected. Exiting.")  # user-visible message
            return
        builder = WanVpnBuilder(apisession, org_id, safe_input_func)  # instantiate builder
        builder.run()  # run interactive workflow

    # ------------------------------------------------------------------
    # Main workflow (US1 + US2 + US3 orchestration)
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main workflow: fetch, display, build, preview, create."""
        print("\n=== WAN Hub-Spoke VPN Builder ===")  # header for interactive UI
        logging.info("Starting WAN Hub-Spoke VPN Builder")  # log start

        profiles = self._fetch_profiles()  # fetch gateway device profiles
        if not profiles:  # nothing to work with
            print("! No gateway device profiles found in this organization.")  # user notice
            return

        existing_vpns = self._fetch_existing_vpns()  # get existing VPN definitions
        self._display_existing_vpns(existing_vpns)  # show summary of existing VPNs

        existing_names = [vpn.get("name", "") for vpn in existing_vpns]  # extract names
        vpn_name = self._prompt_vpn_name(existing_names)  # prompt for new VPN name
        if vpn_name is None:  # user cancelled
            return

        self._display_profile_list(profiles)  # display profiles for role assignment

        assignments = self._prompt_role_assignments(profiles)  # gather hub/spoke/skip choices
        if assignments is None:  # cancelled or invalid
            return

        assignments = self._prompt_pod_values(assignments)  # prompt pod numbers
        if assignments is None:  # cancelled
            return

        vpn_body = self._build_vpn_body(vpn_name, assignments)  # assemble API payload

        confirmed = self._display_preview(vpn_name, vpn_body)  # show preview and confirm
        if not confirmed:  # user declined
            print("  VPN creation cancelled.")
            return

        created_vpn = self._create_vpn(vpn_body)  # call API to create VPN
        if created_vpn is None:  # API failure
            return

        vpn_id = created_vpn.get("id", "")  # extract ID from created object
        print(f"  VPN '{vpn_name}' created successfully. ID: {vpn_id}")  # success message
        logging.info("VPN '%s' created with ID %s", vpn_name, vpn_id)  # log success

        self._prompt_profile_updates(vpn_id, vpn_name, assignments)  # optionally update profiles

    # ------------------------------------------------------------------
    # Pure-logic helpers (Phase 2 foundational)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_wan_suffix(interface_name: str) -> str:
        """Extract the suffix after the last underscore.

        Examples:
            HE_WAN1 -> WAN1
            HE_5G   -> 5G
            WAN1    -> WAN1
        """
        parts = interface_name.rsplit("_", maxsplit=1)  # split on last underscore
        return parts[-1] if len(parts) > 1 else interface_name  # return suffix or original

    @staticmethod
    def _classify_interfaces(
        port_config: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Classify interfaces into WAN and LAN lists.

        Returns (wan_list, lan_list) where each item is the
        interface name string.
        """
        wan_interfaces = []  # collect names flagged as WAN
        lan_interfaces = []  # collect names flagged as LAN
        for name, config in port_config.items():  # iterate over port entries
            usage = config.get("usage", "")  # determine usage tag
            if usage == "wan":  # WAN interface
                wan_interfaces.append(name)
            elif usage == "lan":  # LAN interface
                lan_interfaces.append(name)
        wan_interfaces.sort()  # sort lists for deterministic output
        lan_interfaces.sort()
        return wan_interfaces, lan_interfaces  # return tuple

    @staticmethod
    def _suggest_pod(profile_name: str, fallback: int = 1) -> int:
        """Auto-suggest pod from trailing digits in profile name.

        Examples:
            VREPOL69 -> 69
            SPOKE01  -> 1
            HUB      -> fallback
        """
        match = re.search(r"(\d+)$", profile_name)  # find trailing digits
        if match:
            value = int(match.group(1))  # convert to int
            if WanVpnBuilder.POD_MIN <= value <= WanVpnBuilder.POD_MAX:  # validate range
                return value
        return fallback  # default when no trailing digits or out of range

    # ------------------------------------------------------------------
    # Path generation (US1 core logic)
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_wan_suffixes(
        assignments: list[dict[str, Any]],
    ) -> set[str]:
        """Collect global WAN suffix set from all non-skip assignments."""
        suffixes = set()  # set of unique WAN suffixes used across assignments
        for assignment in assignments:  # scan each assignment
            if assignment["role"] == "skip":  # ignore skipped profiles
                continue
            port_config = assignment["profile"].get("port_config", {})  # port config dict
            wan_interfaces, _ = WanVpnBuilder._classify_interfaces(port_config)  # classify
            for interface_name in wan_interfaces:  # extract suffix for each WAN interface
                suffixes.add(WanVpnBuilder._extract_wan_suffix(interface_name))
        return suffixes  # return collected suffixes

    @staticmethod
    def _generate_hub_paths(
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        suffixes: set[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate hub paths: direct + cross-connects for WAN, direct for LAN."""
        paths = {}  # aggregated paths for this hub profile
        sorted_suffixes = sorted(suffixes)  # deterministic order for cross keys
        for interface_name in wan_interfaces:  # create direct + cross-connect keys for WAN
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
            for suffix in sorted_suffixes:  # cross-connect entries
                cross_key = f"{profile_name}-{interface_name}-{suffix}"
                paths[cross_key] = {"pod": pod}
        for interface_name in lan_interfaces:  # LAN only gets direct keys
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        return paths  # return mapping of path keys to pod assignments

    @staticmethod
    def _generate_spoke_paths(
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate spoke paths: direct paths only for WAN and LAN."""
        paths = {}  # aggregated paths for this spoke profile
        for interface_name in wan_interfaces:  # direct WAN paths only
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        for interface_name in lan_interfaces:  # direct LAN paths only
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        return paths  # return mapping

    def _build_vpn_body(
        self,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the full VPN API request body."""
        suffixes = self._collect_wan_suffixes(assignments)  # global WAN suffix set
        all_paths = {}  # accumulate paths from all profiles
        for assignment in assignments:  # iterate assignments building paths per profile
            if assignment["role"] == "skip":  # ignore skipped profiles
                continue
            profile = assignment["profile"]  # profile dict
            profile_name = profile.get("name", "")  # profile name
            port_config = profile.get("port_config", {})  # port configuration
            wan_list, lan_list = self._classify_interfaces(port_config)  # classify ports
            pod = assignment["pod"]  # pod number for this profile
            if assignment["role"] == "hub":  # hub path generation
                paths = self._generate_hub_paths(profile_name, wan_list, lan_list, suffixes, pod)
            else:  # spoke path generation
                paths = self._generate_spoke_paths(profile_name, wan_list, lan_list, pod)
            all_paths.update(paths)  # merge into global paths map
        return {
            "name": vpn_name,  # VPN name
            "type": "hub_spoke",  # VPN type
            "path_selection": {"strategy": "simple"},  # selection strategy
            "paths": all_paths,  # assembled paths mapping
        }

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self) -> list[Any]:
        """Fetch gateway device profiles, sorted alphabetically."""
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )  # request device profiles of type gateway
            profiles: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)  # read paginated results
            profiles.sort(key=lambda profile: profile.get("name", "").lower())  # sort by lowercase name
            logging.debug("Fetched %d gateway profiles", len(profiles))  # debug log
            return profiles  # return list
        except Exception:
            logging.error("Failed to fetch device profiles", exc_info=True)  # log exception with traceback
            print("! Error retrieving gateway device profiles. Check API connectivity.")  # inform user
            return []  # return empty list on failure

    def _fetch_existing_vpns(self) -> list[Any]:
        """Fetch all org VPN definitions."""
        try:
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)  # list all org VPNs
            vpns: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)  # expand pages
            logging.debug("Fetched %d org VPNs", len(vpns))  # debug count
            return vpns
        except Exception:
            logging.error("Failed to fetch org VPNs", exc_info=True)  # log error
            print("! Error retrieving VPN definitions. Check API connectivity.")  # user message
            return []  # return empty on failure

    def _create_vpn(self, vpn_body: dict[str, Any]) -> dict[str, Any] | None:
        """Create VPN via API. Returns created VPN dict or None on failure."""
        try:
            response = mistapi.api.v1.orgs.vpns.createOrgVpn(self.apisession, self.org_id, body=vpn_body)  # call create API
            created: dict[str, Any] = response.data if hasattr(response, "data") else response  # normalize
            logging.info("VPN created via API: %s", created.get("id", ""))  # log id
            return created  # return created object
        except Exception:
            logging.error("Failed to create VPN", exc_info=True)  # log exception
            print("! Error creating VPN. Check API connectivity and input.")  # inform user
            return None  # creation failed

    # ------------------------------------------------------------------
    # User interaction — display helpers (US1 + US3)
    # ------------------------------------------------------------------

    def _display_existing_vpns(self, vpns: list[Any]) -> None:
        """Display summary table of existing VPNs."""
        if not vpns:
            print("\n  No existing VPN definitions in this organization.")  # nothing to display
            return
        print(f"\n  Existing VPN Definitions ({len(vpns)}):")  # header with count
        print(f"  {'#':<4} {'Name':<30} {'Type':<12} {'Paths':>6}")  # column headings
        print(f"  {'-'*4} {'-'*30} {'-'*12} {'-'*6}")  # separator
        for index, vpn in enumerate(vpns, start=1):  # iterate and print each vpn
            name = vpn.get("name", "")  # vpn name
            vpn_type = vpn.get("type", "unknown")  # vpn type
            path_count = len(vpn.get("paths", {}))  # number of paths
            print(f"  {index:<4} {name:<30} {vpn_type:<12} {path_count:>6}")  # formatted line
        print()  # trailing newline

    def _display_profile_list(self, profiles: list[Any]) -> None:
        """Show numbered profile list with WAN/LAN interface counts."""
        print(f"\n  Gateway Device Profiles ({len(profiles)}):")  # header with count
        print(f"  {'#':<4} {'Profile Name':<30} {'WAN':>4} {'LAN':>4}")  # column headings
        print(f"  {'-'*4} {'-'*30} {'-'*4} {'-'*4}")  # separator
        for index, profile in enumerate(profiles, start=1):  # each profile line
            name = profile.get("name", "")  # profile name
            port_config = profile.get("port_config", {})  # port config dict
            wan_list, lan_list = self._classify_interfaces(port_config)  # classify ports
            wan_count = len(wan_list)  # count wan
            lan_count = len(lan_list)  # count lan
            warning = " (!) No WAN interfaces" if wan_count == 0 else ""  # warn if no WAN
            print(f"  {index:<4} {name:<30} {wan_count:>4} {lan_count:>4}{warning}")  # formatted line
        print()  # trailing newline

    def _display_preview(self, vpn_name: str, vpn_body: dict[str, Any]) -> bool:
        """Display VPN preview and prompt for CREATE confirmation."""
        paths = vpn_body.get("paths", {})
        path_count = len(paths)  # number of generated path keys

        print("\n  === VPN Preview ===")  # preview header
        print(f"  Name: {vpn_name}")  # show name
        print(f"  Type: {vpn_body.get('type', '')}")  # show type
        print(f"  Path Selection: {vpn_body.get('path_selection', {})}")  # show strategy
        print(f"  Total Paths: {path_count}")  # show count
        if path_count > self.PATH_WARN_THRESHOLD:  # warn if many paths
            print(
                f"  WARNING: Path count ({path_count}) exceeds {self.PATH_WARN_THRESHOLD}. "
                "This may indicate an unusually large configuration."
            )
        print("\n  Path Keys:")  # list keys for inspection
        for key in sorted(paths.keys()):  # deterministic order
            pod = paths[key].get("pod", "")  # pod for this path
            print(f"    {key} (pod: {pod})")  # print key and pod
        print()  # blank line

        confirm = self._safe_input(
            "  Type CREATE to confirm, or anything else to cancel: ",
            context="wan_vpn_create_confirm",
        )  # prompt user for explicit CREATE confirmation
        return confirm.strip() == "CREATE"  # return True only when typed exactly

    # ------------------------------------------------------------------
    # User interaction — prompts (US1)
    # ------------------------------------------------------------------

    def _prompt_vpn_name(self, existing_names: list[str]) -> str | None:
        """Prompt for VPN name, validate uniqueness."""
        lower_names = [name.lower() for name in existing_names]  # case-insensitive set
        while True:  # loop until valid name or cancel
            name = self._safe_input(
                "  Enter VPN name (or 'q' to cancel): ",
                context="wan_vpn_name_input",
            ).strip()  # get input and strip whitespace
            if name.lower() == "q":  # cancel
                print("  Cancelled.")
                return None
            if not name:  # empty invalid
                print("  VPN name cannot be empty.")
                continue
            if name.lower() in lower_names:  # uniqueness check
                print(f"  VPN name '{name}' already exists. Choose a different name.")
                continue
            return name  # valid name

    def _prompt_role_assignments(
        self,
        profiles: list[Any],
    ) -> list[dict[str, Any]] | None:
        """Prompt user to assign Hub/Spoke/Skip to each profile."""
        assignments = []  # output assignments list
        print("  Assign roles to each profile (H=Hub, S=Spoke, K=Skip):")  # instruction
        for index, profile in enumerate(profiles, start=1):  # iterate profiles
            name = profile.get("name", "")  # profile name for prompt
            while True:  # prompt loop
                choice = (
                    self._safe_input(
                        f"    {index}. {name} [H/S/K]: ",
                        context="wan_vpn_role_assign",
                    )
                    .strip()
                    .lower()
                )  # normalized input
                if choice in ("h", "hub"):
                    assignments.append({"profile": profile, "role": "hub", "pod": self.POD_DEFAULT})
                    break
                if choice in ("s", "spoke"):
                    assignments.append({"profile": profile, "role": "spoke", "pod": self.POD_DEFAULT})
                    break
                if choice in ("k", "skip"):
                    assignments.append({"profile": profile, "role": "skip", "pod": 0})
                    break
                print("    Please enter H (Hub), S (Spoke), or K (Skip).")  # validation prompt

        non_skip = [a for a in assignments if a["role"] != "skip"]  # check at least one selected
        if not non_skip:
            print("  All profiles skipped. At least one must be Hub or Spoke.")
            retry = self._safe_input("  Try again? (y/N): ", context="wan_vpn_retry_roles").strip().lower()
            if retry == "y":
                return self._prompt_role_assignments(profiles)  # re-run prompts
            print("  Cancelled.")
            return None
        return assignments  # return final assignments

    def _prompt_pod_values(
        self,
        assignments: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Prompt for pod values with auto-suggestion."""
        fallback_counter = 1  # incrementing fallback for suggestions
        for assignment in assignments:  # prompt for each non-skip assignment
            if assignment["role"] == "skip":
                continue
            profile_name = assignment["profile"].get("name", "")  # profile name
            suggested = self._suggest_pod(profile_name, fallback_counter)  # auto-suggest value
            while True:  # input loop
                raw = self._safe_input(
                    f"    Pod for {profile_name} [{suggested}]: ",
                    context="wan_vpn_pod_input",
                ).strip()
                if not raw:  # accept suggested default
                    assignment["pod"] = suggested
                    break
                try:
                    value = int(raw)  # parse integer
                except ValueError:
                    print(f"    Pod must be an integer ({self.POD_MIN}-{self.POD_MAX}).")
                    continue
                if not (self.POD_MIN <= value <= self.POD_MAX):  # range validation
                    print(f"    Pod must be between {self.POD_MIN} and {self.POD_MAX}.")
                    continue
                assignment["pod"] = value  # set provided value
                break
            fallback_counter += 1  # bump fallback for next profile
        return assignments  # return updated assignments

    # ------------------------------------------------------------------
    # Profile update (US2)
    # ------------------------------------------------------------------

    def _build_port_vpn_paths(
        self,
        profile_name: str,
        interface_name: str,
        vpn_name: str,
        role: str,
        suffixes: set[str],
    ) -> dict[str, dict[str, Any]]:
        """Build vpn_paths entries for a single port.

        Returns dict of {PathName.VPNName: {key: N, role: role}} entries.
        """
        vpn_paths = {}  # mapping of vpn path refs to key/role
        is_wan = True  # placeholder: currently treat given interface as WAN for extra paths
        direct_key = f"{profile_name}-{interface_name}"  # base key for this interface
        vpn_ref = f"{direct_key}.{vpn_name}"  # reference used in vpn_paths
        vpn_paths[vpn_ref] = {"key": 0, "role": role}  # direct entry with key 0

        if role == "hub" and is_wan:  # hubs get cross-connect keys for each suffix
            sorted_suffixes = sorted(suffixes)
            for key_index, suffix in enumerate(sorted_suffixes):
                cross_key = f"{profile_name}-{interface_name}-{suffix}"
                cross_ref = f"{cross_key}.{vpn_name}"
                vpn_paths[cross_ref] = {"key": key_index, "role": role}  # incremental key for cross entry
        return vpn_paths  # return constructed vpn_paths for this port

    def _update_single_profile(
        self,
        profile_id: str,
        profile_name: str,
        vpn_name: str,
        assignment: dict[str, Any],
        suffixes: set[str],
    ) -> bool:
        """Fetch fresh profile, merge vpn_paths, push update."""
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile(
                self.apisession, self.org_id, deviceprofile_id=profile_id
            )  # fetch latest profile object from API
            fresh_profile = response.data if hasattr(response, "data") else response  # normalize
            port_config = fresh_profile.get("port_config", {})  # port configuration dict
            role = assignment["role"]  # hub/spoke role

            wan_list, lan_list = self._classify_interfaces(port_config)  # classify interfaces
            for interface_name in wan_list:  # update WAN interfaces vpn_paths
                new_entries = self._build_port_vpn_paths(profile_name, interface_name, vpn_name, role, suffixes)
                existing = port_config[interface_name].get("vpn_paths", {})  # existing map
                existing.update(new_entries)  # merge new entries
                port_config[interface_name]["vpn_paths"] = existing  # write back

            for interface_name in lan_list:  # update LAN interfaces vpn_paths
                direct_key = f"{profile_name}-{interface_name}"
                vpn_ref = f"{direct_key}.{vpn_name}"
                existing = port_config[interface_name].get("vpn_paths", {})
                existing[vpn_ref] = {"key": 0, "role": role}  # single direct entry
                port_config[interface_name]["vpn_paths"] = existing

            mistapi.api.v1.orgs.deviceprofiles.updateOrgDeviceProfile(
                self.apisession,
                self.org_id,
                deviceprofile_id=profile_id,
                body=fresh_profile,
            )  # push updated profile back to API
            logging.info("Updated profile '%s' with vpn_paths for VPN '%s'", profile_name, vpn_name)  # success log
            return True
        except Exception:
            logging.error("Failed to update profile '%s'", profile_name, exc_info=True)  # log exception
            print(f"  ! Error updating profile '{profile_name}'. Check logs.")  # user message
            return False  # indicate failure

    def _prompt_profile_updates(
        self,
        vpn_id: str,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> None:
        """Offer to update each profile's port_config with vpn_paths."""
        non_skip = [a for a in assignments if a["role"] != "skip"]  # profiles to update
        if not non_skip:  # nothing to update
            return

        choice = (
            self._safe_input(
                "  Update device profiles with vpn_paths references? (y/N): ",
                context="wan_vpn_profile_update",
            )
            .strip()
            .lower()
        )  # prompt user
        if choice != "y":  # skip unless explicit 'y'
            print("  Skipping profile updates.")
            return

        suffixes = self._collect_wan_suffixes(assignments)  # compute suffixes for building vpn_paths
        success_count = 0
        fail_count = 0
        for assignment in non_skip:  # apply updates per profile
            profile = assignment["profile"]
            profile_name = profile.get("name", "")
            profile_id = profile.get("id", "")
            result = self._update_single_profile(profile_id, profile_name, vpn_name, assignment, suffixes)
            if result:
                success_count += 1
            else:
                fail_count += 1

        print(f"  Profile updates: {success_count} succeeded, {fail_count} failed.")  # summary

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:
        """Fallback input when safe_input is not provided."""
        try:
            return input(prompt).strip()  # plain input fallback
        except EOFError:
            logging.info("EOF detected in wan_vpn_builder")  # log EOF
            return ""  # empty on EOF
        except KeyboardInterrupt:
            print("\n  Interrupted.")  # user interrupted
            return ""  # return empty
