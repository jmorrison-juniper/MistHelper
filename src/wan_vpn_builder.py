"""WAN Hub-Spoke VPN Builder -- Menu 164.

Create hub-spoke VPN overlay definitions from gateway device profiles.
NOC engineers select profiles, assign hub/spoke roles, review
auto-generated VPN path keys with pod numbers, confirm, and the VPN
is created via API.  Optionally updates each profile's port_config
with vpn_paths references to the new VPN.

Follows the external-module pattern established by Menu 163
(``src/wan_hub_group_manager.py``).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

import mistapi
import mistapi.api.v1.orgs.deviceprofiles
import mistapi.api.v1.orgs.vpns


class WanVpnBuilder:
    """Build hub-spoke VPN overlays from gateway device profiles."""

    POD_MIN = 1
    POD_MAX = 128
    POD_DEFAULT = 1
    PATH_WARN_THRESHOLD = 500

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        safe_input_func: Callable[..., str] | None = None,
    ) -> None:
        """Initialize with API session, org ID, and optional input function."""
        self.apisession = apisession
        self.org_id = org_id
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
        org_id = get_org_id_func()
        if not org_id:
            print("! No organization selected. Exiting.")
            return
        builder = WanVpnBuilder(apisession, org_id, safe_input_func)
        builder.run()

    # ------------------------------------------------------------------
    # Main workflow (US1 + US2 + US3 orchestration)
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main workflow: fetch, display, build, preview, create."""
        print("\n=== WAN Hub-Spoke VPN Builder ===")
        logging.info("Starting WAN Hub-Spoke VPN Builder")

        profiles = self._fetch_profiles()
        if not profiles:
            print("! No gateway device profiles found in this organization.")
            return

        existing_vpns = self._fetch_existing_vpns()
        self._display_existing_vpns(existing_vpns)

        existing_names = [vpn.get("name", "") for vpn in existing_vpns]
        vpn_name = self._prompt_vpn_name(existing_names)
        if vpn_name is None:
            return

        self._display_profile_list(profiles)

        assignments = self._prompt_role_assignments(profiles)
        if assignments is None:
            return

        assignments = self._prompt_pod_values(assignments)
        if assignments is None:
            return

        vpn_body = self._build_vpn_body(vpn_name, assignments)

        confirmed = self._display_preview(vpn_name, vpn_body)
        if not confirmed:
            print("  VPN creation cancelled.")
            return

        created_vpn = self._create_vpn(vpn_body)
        if created_vpn is None:
            return

        vpn_id = created_vpn.get("id", "")
        print(f"  VPN '{vpn_name}' created successfully. ID: {vpn_id}")
        logging.info("VPN '%s' created with ID %s", vpn_name, vpn_id)

        self._prompt_profile_updates(vpn_id, vpn_name, assignments)

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
        parts = interface_name.rsplit("_", maxsplit=1)
        return parts[-1] if len(parts) > 1 else interface_name

    @staticmethod
    def _classify_interfaces(
        port_config: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Classify interfaces into WAN and LAN lists.

        Returns (wan_list, lan_list) where each item is the
        interface name string.
        """
        wan_interfaces = []
        lan_interfaces = []
        for name, config in port_config.items():
            usage = config.get("usage", "")
            if usage == "wan":
                wan_interfaces.append(name)
            elif usage == "lan":
                lan_interfaces.append(name)
        wan_interfaces.sort()
        lan_interfaces.sort()
        return wan_interfaces, lan_interfaces

    @staticmethod
    def _suggest_pod(profile_name: str, fallback: int = 1) -> int:
        """Auto-suggest pod from trailing digits in profile name.

        Examples:
            VREPOL69 -> 69
            SPOKE01  -> 1
            HUB      -> fallback
        """
        match = re.search(r"(\d+)$", profile_name)
        if match:
            value = int(match.group(1))
            if WanVpnBuilder.POD_MIN <= value <= WanVpnBuilder.POD_MAX:
                return value
        return fallback

    # ------------------------------------------------------------------
    # Path generation (US1 core logic)
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_wan_suffixes(
        assignments: list[dict[str, Any]],
    ) -> set[str]:
        """Collect global WAN suffix set from all non-skip assignments."""
        suffixes = set()
        for assignment in assignments:
            if assignment["role"] == "skip":
                continue
            port_config = assignment["profile"].get("port_config", {})
            wan_interfaces, _ = WanVpnBuilder._classify_interfaces(port_config)
            for interface_name in wan_interfaces:
                suffixes.add(WanVpnBuilder._extract_wan_suffix(interface_name))
        return suffixes

    @staticmethod
    def _generate_hub_paths(
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        suffixes: set[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate hub paths: direct + cross-connects for WAN, direct for LAN."""
        paths = {}
        sorted_suffixes = sorted(suffixes)
        for interface_name in wan_interfaces:
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
            for suffix in sorted_suffixes:
                cross_key = f"{profile_name}-{interface_name}-{suffix}"
                paths[cross_key] = {"pod": pod}
        for interface_name in lan_interfaces:
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        return paths

    @staticmethod
    def _generate_spoke_paths(
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate spoke paths: direct paths only for WAN and LAN."""
        paths = {}
        for interface_name in wan_interfaces:
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        for interface_name in lan_interfaces:
            direct_key = f"{profile_name}-{interface_name}"
            paths[direct_key] = {"pod": pod}
        return paths

    def _build_vpn_body(
        self,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the full VPN API request body."""
        suffixes = self._collect_wan_suffixes(assignments)
        all_paths = {}
        for assignment in assignments:
            if assignment["role"] == "skip":
                continue
            profile = assignment["profile"]
            profile_name = profile.get("name", "")
            port_config = profile.get("port_config", {})
            wan_list, lan_list = self._classify_interfaces(port_config)
            pod = assignment["pod"]
            if assignment["role"] == "hub":
                paths = self._generate_hub_paths(profile_name, wan_list, lan_list, suffixes, pod)
            else:
                paths = self._generate_spoke_paths(profile_name, wan_list, lan_list, pod)
            all_paths.update(paths)
        return {
            "name": vpn_name,
            "type": "hub_spoke",
            "path_selection": {"strategy": "simple"},
            "paths": all_paths,
        }

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self) -> list[Any]:
        """Fetch gateway device profiles, sorted alphabetically."""
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )
            profiles: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)
            profiles.sort(key=lambda profile: profile.get("name", "").lower())
            logging.debug("Fetched %d gateway profiles", len(profiles))
            return profiles
        except Exception:
            logging.error("Failed to fetch device profiles", exc_info=True)
            print("! Error retrieving gateway device profiles. Check API connectivity.")
            return []

    def _fetch_existing_vpns(self) -> list[Any]:
        """Fetch all org VPN definitions."""
        try:
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)
            vpns: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)
            logging.debug("Fetched %d org VPNs", len(vpns))
            return vpns
        except Exception:
            logging.error("Failed to fetch org VPNs", exc_info=True)
            print("! Error retrieving VPN definitions. Check API connectivity.")
            return []

    def _create_vpn(self, vpn_body: dict[str, Any]) -> dict[str, Any] | None:
        """Create VPN via API. Returns created VPN dict or None on failure."""
        try:
            response = mistapi.api.v1.orgs.vpns.createOrgVpn(self.apisession, self.org_id, body=vpn_body)
            created: dict[str, Any] = response.data if hasattr(response, "data") else response
            logging.info("VPN created via API: %s", created.get("id", ""))
            return created
        except Exception:
            logging.error("Failed to create VPN", exc_info=True)
            print("! Error creating VPN. Check API connectivity and input.")
            return None

    # ------------------------------------------------------------------
    # User interaction — display helpers (US1 + US3)
    # ------------------------------------------------------------------

    def _display_existing_vpns(self, vpns: list[Any]) -> None:
        """Display summary table of existing VPNs."""
        if not vpns:
            print("\n  No existing VPN definitions in this organization.")
            return
        print(f"\n  Existing VPN Definitions ({len(vpns)}):")
        print(f"  {'#':<4} {'Name':<30} {'Type':<12} {'Paths':>6}")
        print(f"  {'-'*4} {'-'*30} {'-'*12} {'-'*6}")
        for index, vpn in enumerate(vpns, start=1):
            name = vpn.get("name", "")
            vpn_type = vpn.get("type", "unknown")
            path_count = len(vpn.get("paths", {}))
            print(f"  {index:<4} {name:<30} {vpn_type:<12} {path_count:>6}")
        print()

    def _display_profile_list(self, profiles: list[Any]) -> None:
        """Show numbered profile list with WAN/LAN interface counts."""
        print(f"\n  Gateway Device Profiles ({len(profiles)}):")
        print(f"  {'#':<4} {'Profile Name':<30} {'WAN':>4} {'LAN':>4}")
        print(f"  {'-'*4} {'-'*30} {'-'*4} {'-'*4}")
        for index, profile in enumerate(profiles, start=1):
            name = profile.get("name", "")
            port_config = profile.get("port_config", {})
            wan_list, lan_list = self._classify_interfaces(port_config)
            wan_count = len(wan_list)
            lan_count = len(lan_list)
            warning = " (!) No WAN interfaces" if wan_count == 0 else ""
            print(f"  {index:<4} {name:<30} {wan_count:>4} {lan_count:>4}{warning}")
        print()

    def _display_preview(self, vpn_name: str, vpn_body: dict[str, Any]) -> bool:
        """Display VPN preview and prompt for CREATE confirmation."""
        paths = vpn_body.get("paths", {})
        path_count = len(paths)

        print("\n  === VPN Preview ===")
        print(f"  Name: {vpn_name}")
        print(f"  Type: {vpn_body.get('type', '')}")
        print(f"  Path Selection: {vpn_body.get('path_selection', {})}")
        print(f"  Total Paths: {path_count}")
        if path_count > self.PATH_WARN_THRESHOLD:
            print(
                f"  WARNING: Path count ({path_count}) exceeds {self.PATH_WARN_THRESHOLD}. "
                "This may indicate an unusually large configuration."
            )
        print("\n  Path Keys:")
        for key in sorted(paths.keys()):
            pod = paths[key].get("pod", "")
            print(f"    {key} (pod: {pod})")
        print()

        confirm = self._safe_input(
            "  Type CREATE to confirm, or anything else to cancel: ",
            context="wan_vpn_create_confirm",
        )
        return confirm.strip() == "CREATE"

    # ------------------------------------------------------------------
    # User interaction — prompts (US1)
    # ------------------------------------------------------------------

    def _prompt_vpn_name(self, existing_names: list[str]) -> str | None:
        """Prompt for VPN name, validate uniqueness."""
        lower_names = [name.lower() for name in existing_names]
        while True:
            name = self._safe_input(
                "  Enter VPN name (or 'q' to cancel): ",
                context="wan_vpn_name_input",
            ).strip()
            if name.lower() == "q":
                print("  Cancelled.")
                return None
            if not name:
                print("  VPN name cannot be empty.")
                continue
            if name.lower() in lower_names:
                print(f"  VPN name '{name}' already exists. Choose a different name.")
                continue
            return name

    def _prompt_role_assignments(
        self,
        profiles: list[Any],
    ) -> list[dict[str, Any]] | None:
        """Prompt user to assign Hub/Spoke/Skip to each profile."""
        assignments = []
        print("  Assign roles to each profile (H=Hub, S=Spoke, K=Skip):")
        for index, profile in enumerate(profiles, start=1):
            name = profile.get("name", "")
            while True:
                choice = (
                    self._safe_input(
                        f"    {index}. {name} [H/S/K]: ",
                        context="wan_vpn_role_assign",
                    )
                    .strip()
                    .lower()
                )
                if choice in ("h", "hub"):
                    assignments.append({"profile": profile, "role": "hub", "pod": self.POD_DEFAULT})
                    break
                if choice in ("s", "spoke"):
                    assignments.append({"profile": profile, "role": "spoke", "pod": self.POD_DEFAULT})
                    break
                if choice in ("k", "skip"):
                    assignments.append({"profile": profile, "role": "skip", "pod": 0})
                    break
                print("    Please enter H (Hub), S (Spoke), or K (Skip).")

        non_skip = [a for a in assignments if a["role"] != "skip"]
        if not non_skip:
            print("  All profiles skipped. At least one must be Hub or Spoke.")
            retry = self._safe_input("  Try again? (y/N): ", context="wan_vpn_retry_roles").strip().lower()
            if retry == "y":
                return self._prompt_role_assignments(profiles)
            print("  Cancelled.")
            return None
        return assignments

    def _prompt_pod_values(
        self,
        assignments: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Prompt for pod values with auto-suggestion."""
        fallback_counter = 1
        for assignment in assignments:
            if assignment["role"] == "skip":
                continue
            profile_name = assignment["profile"].get("name", "")
            suggested = self._suggest_pod(profile_name, fallback_counter)
            while True:
                raw = self._safe_input(
                    f"    Pod for {profile_name} [{suggested}]: ",
                    context="wan_vpn_pod_input",
                ).strip()
                if not raw:
                    assignment["pod"] = suggested
                    break
                try:
                    value = int(raw)
                except ValueError:
                    print(f"    Pod must be an integer ({self.POD_MIN}-{self.POD_MAX}).")
                    continue
                if not (self.POD_MIN <= value <= self.POD_MAX):
                    print(f"    Pod must be between {self.POD_MIN} and {self.POD_MAX}.")
                    continue
                assignment["pod"] = value
                break
            fallback_counter += 1
        return assignments

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
        vpn_paths = {}
        is_wan = True
        direct_key = f"{profile_name}-{interface_name}"
        vpn_ref = f"{direct_key}.{vpn_name}"
        vpn_paths[vpn_ref] = {"key": 0, "role": role}

        if role == "hub" and is_wan:
            sorted_suffixes = sorted(suffixes)
            for key_index, suffix in enumerate(sorted_suffixes):
                cross_key = f"{profile_name}-{interface_name}-{suffix}"
                cross_ref = f"{cross_key}.{vpn_name}"
                vpn_paths[cross_ref] = {"key": key_index, "role": role}
        return vpn_paths

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
            )
            fresh_profile = response.data if hasattr(response, "data") else response
            port_config = fresh_profile.get("port_config", {})
            role = assignment["role"]

            wan_list, lan_list = self._classify_interfaces(port_config)
            for interface_name in wan_list:
                new_entries = self._build_port_vpn_paths(profile_name, interface_name, vpn_name, role, suffixes)
                existing = port_config[interface_name].get("vpn_paths", {})
                existing.update(new_entries)
                port_config[interface_name]["vpn_paths"] = existing

            for interface_name in lan_list:
                direct_key = f"{profile_name}-{interface_name}"
                vpn_ref = f"{direct_key}.{vpn_name}"
                existing = port_config[interface_name].get("vpn_paths", {})
                existing[vpn_ref] = {"key": 0, "role": role}
                port_config[interface_name]["vpn_paths"] = existing

            mistapi.api.v1.orgs.deviceprofiles.updateOrgDeviceProfile(
                self.apisession,
                self.org_id,
                deviceprofile_id=profile_id,
                body=fresh_profile,
            )
            logging.info("Updated profile '%s' with vpn_paths for VPN '%s'", profile_name, vpn_name)
            return True
        except Exception:
            logging.error("Failed to update profile '%s'", profile_name, exc_info=True)
            print(f"  ! Error updating profile '{profile_name}'. Check logs.")
            return False

    def _prompt_profile_updates(
        self,
        vpn_id: str,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> None:
        """Offer to update each profile's port_config with vpn_paths."""
        non_skip = [a for a in assignments if a["role"] != "skip"]
        if not non_skip:
            return

        choice = (
            self._safe_input(
                "  Update device profiles with vpn_paths references? (y/N): ",
                context="wan_vpn_profile_update",
            )
            .strip()
            .lower()
        )
        if choice != "y":
            print("  Skipping profile updates.")
            return

        suffixes = self._collect_wan_suffixes(assignments)
        success_count = 0
        fail_count = 0
        for assignment in non_skip:
            profile = assignment["profile"]
            profile_name = profile.get("name", "")
            profile_id = profile.get("id", "")
            result = self._update_single_profile(profile_id, profile_name, vpn_name, assignment, suffixes)
            if result:
                success_count += 1
            else:
                fail_count += 1

        print(f"  Profile updates: {success_count} succeeded, {fail_count} failed.")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:
        """Fallback input when safe_input is not provided."""
        try:
            return input(prompt).strip()
        except EOFError:
            logging.info("EOF detected in wan_vpn_builder")
            return ""
        except KeyboardInterrupt:
            print("\n  Interrupted.")
            return ""
