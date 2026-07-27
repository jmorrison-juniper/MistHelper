"""WAN Hub-Spoke VPN Builder -- Menu 164.

Create hub-spoke VPN overlay definitions from gateway device profiles.
NOC engineers select profiles, assign hub/spoke roles, review
auto-generated VPN path keys with pod numbers, confirm, and the VPN
is created via API.  Optionally updates each profile's port_config
with vpn_paths references to the new VPN.

Follows the external-module pattern established by Menu 163
(``src/wan_hub_group_manager.py``).
"""

from __future__ import annotations  # WHY: enable PEP 563 postponed annotations so future syntax works on 3.9+.

import logging  # WHY: structured operator diagnostics (info/debug/exception) for CLI workflow.
import re  # WHY: regex extraction of trailing pod digits from profile names.
from collections.abc import Callable  # WHY: precise typing for injected safe_input callable.
from typing import Any  # WHY: mistapi returns opaque dicts; Any keeps boundary honest without leaking types.

import mistapi  # WHY: shared API session helper (get_all pagination).
import mistapi.api.v1.orgs.deviceprofiles  # WHY: gateway device profile list/get/update endpoints.
import mistapi.api.v1.orgs.vpns  # WHY: org VPN list/create endpoints.

# ---------------------------------------------------------------------------
# Module-level constants (avoid magic literals throughout the module).
# ---------------------------------------------------------------------------

ROLE_HUB = "hub"  # WHY: assignment role identifying a hub profile (full mesh cross-connects).
ROLE_SPOKE = "spoke"  # WHY: assignment role identifying a spoke profile (direct paths only).
ROLE_SKIP = "skip"  # WHY: assignment role excluding a profile from the VPN body entirely.

USAGE_WAN = "wan"  # WHY: port_config.usage marker classifying an interface as WAN uplink.
USAGE_LAN = "lan"  # WHY: port_config.usage marker classifying an interface as LAN.

VPN_TYPE_HUB_SPOKE = "hub_spoke"  # WHY: Mist VPN body 'type' value for hub-spoke topology.
PATH_STRATEGY_SIMPLE = "simple"  # WHY: default path_selection.strategy for hub-spoke overlays.

CANCEL_TOKEN = "q"  # WHY: sentinel prompt response that aborts the VPN name flow.
CONFIRM_TOKEN = "CREATE"  # WHY: sentinel prompt response that arms VPN creation (case-sensitive by design).
RETRY_YES = "y"  # WHY: affirmative response used for retry / profile-update prompts.

CHOICE_HUB = frozenset({"h", "hub"})  # WHY: accepted synonyms for the Hub role prompt.
CHOICE_SPOKE = frozenset({"s", "spoke"})  # WHY: accepted synonyms for the Spoke role prompt.
CHOICE_SKIP = frozenset({"k", "skip"})  # WHY: accepted synonyms for the Skip role prompt.

CTX_NAME = "wan_vpn_name_input"  # WHY: safe_input telemetry context for VPN name prompt.
CTX_ROLE = "wan_vpn_role_assign"  # WHY: safe_input telemetry context for role assignment prompt.
CTX_RETRY_ROLES = "wan_vpn_retry_roles"  # WHY: safe_input context for retry-all-skipped prompt.
CTX_POD = "wan_vpn_pod_input"  # WHY: safe_input context for pod-number prompt.
CTX_CONFIRM = "wan_vpn_create_confirm"  # WHY: safe_input context for CREATE confirmation.
CTX_PROFILE_UPDATE = "wan_vpn_profile_update"  # WHY: safe_input context for post-create profile update prompt.
CTX_FALLBACK = "wan_vpn_builder_fallback"  # WHY: safe_input context used when caller injected no wrapper.


class WanVpnBuilder:  # WHY: class encapsulates all per-run state (session, org, injected input).
    """Build hub-spoke VPN overlays from gateway device profiles."""

    POD_MIN = 1  # WHY: lowest valid pod value accepted by Mist path_selection semantics.
    POD_MAX = 128  # WHY: highest valid pod value per Mist path key convention (kept as-is for tests).
    POD_DEFAULT = 1  # WHY: default pod applied before user overrides during role assignment.
    PATH_WARN_THRESHOLD = 500  # WHY: preview warns operator if path count exceeds this ceiling.

    def __init__(  # WHY: bind session/org/input once for the whole interactive run.
        self,
        apisession: Any,
        org_id: str,
        safe_input_func: Callable[..., str] | None = None,
    ) -> None:
        """Initialize with API session, org ID, and optional input function."""
        self.apisession = apisession  # WHY: retained for every subsequent mistapi call.
        self.org_id = org_id  # WHY: scopes every API call to the operator-selected org.
        self._safe_input = safe_input_func or self._fallback_input  # WHY: allow tests to inject scripted input.

    # ------------------------------------------------------------------
    # Entry point (called from menu_actions)
    # ------------------------------------------------------------------

    @staticmethod
    def execute(  # WHY: static so menu_actions can invoke without pre-constructing an instance.
        apisession: Any,
        get_org_id_func: Callable[[], str | None],
        safe_input_func: Callable[..., str] | None,
    ) -> None:
        """Static entry point called by menu_actions lambda."""
        org_id = get_org_id_func()  # WHY: resolve org lazily so caching prompt happens only when needed.
        if not org_id:  # WHY: no org selected -> abort with a user-visible reason instead of raising.
            logging.error("! No organization selected. Exiting.")  # WHY: single-line operator hint before returning.
            return  # WHY: nothing more to do without an org context.
        builder = WanVpnBuilder(apisession, org_id, safe_input_func)  # WHY: bind session/org/input for this run.
        builder.run()  # WHY: hand off to the interactive workflow.

    # ------------------------------------------------------------------
    # Main workflow (US1 + US2 + US3 orchestration)
    # ------------------------------------------------------------------

    def run(self) -> None:  # WHY: top-level orchestrator; kept small by delegating to focused helpers.
        """Main workflow: fetch, display, build, preview, create."""
        logging.warning(
            "\n=== WAN Hub-Spoke VPN Builder ==="
        )  # WHY: banner delimits this menu action in the operator log.
        logging.info("Starting WAN Hub-Spoke VPN Builder")  # WHY: capture entry timestamp for troubleshooting.

        profiles = self._load_profiles_or_none()  # WHY: fetch profiles and short-circuit on empty inventory.
        if profiles is None:  # WHY: helper already emitted operator message; nothing more to do.
            return  # WHY: propagate abort without further prompts.

        vpn_name = self._prompt_name_after_display(profiles)  # WHY: show existing VPNs then collect unique name.
        if vpn_name is None:  # WHY: user cancelled the name prompt.
            return  # WHY: silent return; helper already printed the cancel message.

        assignments = self._collect_role_and_pod_assignments(profiles)  # WHY: gather full role+pod set in one step.
        if assignments is None:  # WHY: cancelled during role or pod prompts.
            return  # WHY: nothing to build without at least one active assignment.

        vpn_body = self._build_vpn_body(vpn_name, assignments)  # WHY: assemble API payload from validated inputs.
        if not self._display_preview(vpn_name, vpn_body):  # WHY: require explicit CREATE token before mutating org.
            logging.warning("  VPN creation cancelled.")  # WHY: operator-visible confirmation of cancellation.
            return  # WHY: honor the operator's decision not to proceed.

        self._create_and_optionally_update(vpn_name, vpn_body, assignments)  # WHY: perform side-effects together.

    def _load_profiles_or_none(self) -> list[Any] | None:  # WHY: split so run() stays short and testable.
        """Fetch gateway profiles; return None and warn if inventory is empty."""
        profiles = self._fetch_profiles()  # WHY: API call is isolated for test-time monkeypatch.
        if not profiles:  # WHY: empty list means org has no gateway profiles -> abort with hint.
            logging.warning(
                "! No gateway device profiles found in this organization."
            )  # WHY: actionable operator hint.
            return None  # WHY: sentinel triggers early return in run().
        return profiles  # WHY: hand the fetched list to the workflow.

    def _prompt_name_after_display(self, profiles: list[Any]) -> str | None:  # WHY: keeps run() body flat.
        """Fetch existing VPNs, display them, then prompt for a unique VPN name."""
        existing_vpns = self._fetch_existing_vpns()  # WHY: needed both for display and uniqueness check.
        self._display_existing_vpns(existing_vpns)  # WHY: operator sees current overlays before naming a new one.
        existing_names = [vpn.get("name", "") for vpn in existing_vpns]  # WHY: build name list once for validator.
        vpn_name = self._prompt_vpn_name(existing_names)  # WHY: enforce uniqueness before profile selection.
        if vpn_name is not None:  # WHY: only render the profile table if the user is proceeding.
            self._display_profile_list(profiles)  # WHY: show profile inventory once a valid name is chosen.
        return vpn_name  # WHY: None propagates cancellation to the caller.

    def _collect_role_and_pod_assignments(  # WHY: chains role prompt then pod prompt, propagates cancel.
        self, profiles: list[Any]
    ) -> list[dict[str, Any]] | None:
        """Run role prompt then pod prompt; propagate None on cancellation."""
        assignments = self._prompt_role_assignments(profiles)  # WHY: collect Hub/Spoke/Skip per profile.
        if assignments is None:  # WHY: user aborted after all-skipped retry prompt.
            return None  # WHY: no assignments means nothing to prompt pods for.
        return self._prompt_pod_values(assignments)  # WHY: pod prompt returns same list with pod fields set.

    def _create_and_optionally_update(  # WHY: side-effect boundary -- creation + optional profile linkage.
        self,
        vpn_name: str,
        vpn_body: dict[str, Any],
        assignments: list[dict[str, Any]],
    ) -> None:
        """Create the VPN and, on success, offer to update device profiles."""
        created_vpn = self._create_vpn(vpn_body)  # WHY: API call isolated so errors do not cascade.
        if created_vpn is None:  # WHY: creation failed -> do not attempt profile updates.
            return  # WHY: caller already saw an error message from _create_vpn.
        vpn_id = created_vpn.get("id", "")  # WHY: id is required for downstream vpn_paths refs.
        logging.warning(
            "  VPN '%s' created successfully. ID: %s", vpn_name, vpn_id
        )  # WHY: operator confirmation of success.
        logging.info("VPN '%s' created with ID %s", vpn_name, vpn_id)  # WHY: audit trail of created id.
        self._prompt_profile_updates(vpn_id, vpn_name, assignments)  # WHY: optional US2 profile linkage.

    # ------------------------------------------------------------------
    # Pure-logic helpers (Phase 2 foundational)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_wan_suffix(interface_name: str) -> str:  # WHY: pure helper; safe to call from any thread.
        """Extract the suffix after the last underscore.

        Examples:
            HE_WAN1 -> WAN1
            HE_5G   -> 5G
            WAN1    -> WAN1
        """
        parts = interface_name.rsplit("_", maxsplit=1)  # WHY: only care about text after final underscore.
        return parts[-1] if len(parts) > 1 else interface_name  # WHY: no underscore -> return original name.

    @staticmethod
    def _classify_interfaces(  # WHY: pure classifier -- easy to unit test in isolation.
        port_config: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Classify interfaces into WAN and LAN lists.

        Returns (wan_list, lan_list) where each item is the
        interface name string.
        """
        wan_interfaces: list[str] = []  # WHY: collect WAN uplinks; order established by sort() below.
        lan_interfaces: list[str] = []  # WHY: collect LAN interfaces separately for hub/spoke logic.
        for name, config in port_config.items():  # WHY: single-pass classification over configured ports.
            usage = config.get("usage", "")  # WHY: default empty means neither WAN nor LAN -> ignored.
            if usage == USAGE_WAN:  # WHY: uppercase branch keeps WAN classification explicit.
                wan_interfaces.append(name)  # WHY: preserve original name for later key construction.
            elif usage == USAGE_LAN:  # WHY: elif keeps unknown usages out of both lists.
                lan_interfaces.append(name)  # WHY: LAN interfaces contribute direct-only paths.
        wan_interfaces.sort()  # WHY: stable deterministic ordering for path keys & test assertions.
        lan_interfaces.sort()  # WHY: stable deterministic ordering for path keys & test assertions.
        return wan_interfaces, lan_interfaces  # WHY: caller unpacks into wan_list, lan_list.

    @staticmethod
    def _suggest_pod(profile_name: str, fallback: int = 1) -> int:  # WHY: pure fn for pod-suggestion tests.
        """Auto-suggest pod from trailing digits in profile name.

        Examples:
            VREPOL69 -> 69
            SPOKE01  -> 1
            HUB      -> fallback
        """
        match = re.search(r"(\d+)$", profile_name)  # WHY: trailing digits carry the operator's pod convention.
        if match:  # WHY: only proceed when the profile name actually ends with digits.
            value = int(match.group(1))  # WHY: convert to int for range comparison.
            if WanVpnBuilder.POD_MIN <= value <= WanVpnBuilder.POD_MAX:  # WHY: only accept values within pod range.
                return value  # WHY: within-range digits become the suggested pod value.
        return fallback  # WHY: unparseable / out-of-range -> caller-provided fallback keeps flow moving.

    # ------------------------------------------------------------------
    # Path generation (US1 core logic)
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_wan_suffixes(  # WHY: shared suffix set feeds hub cross-connect generation.
        assignments: list[dict[str, Any]],
    ) -> set[str]:
        """Collect global WAN suffix set from all non-skip assignments."""
        suffixes: set[str] = set()  # WHY: set dedupes suffixes across all participating profiles.
        for assignment in assignments:  # WHY: walk every proposed profile once.
            if assignment["role"] == ROLE_SKIP:  # WHY: skipped profiles contribute no paths to the VPN body.
                continue  # WHY: skip skipped assignments to avoid polluting the suffix set.
            port_config = assignment["profile"].get("port_config", {})  # WHY: defensive default for missing key.
            wan_interfaces, _ = WanVpnBuilder._classify_interfaces(port_config)  # WHY: only WAN adds cross-connects.
            for interface_name in wan_interfaces:  # WHY: each WAN uplink contributes one suffix.
                suffixes.add(WanVpnBuilder._extract_wan_suffix(interface_name))  # WHY: cross-connects key on suffix.
        return suffixes  # WHY: caller uses this set to generate hub cross-connect keys.

    @staticmethod
    def _generate_hub_paths(  # WHY: hub paths are direct + cross-connect for WAN and direct for LAN.
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        suffixes: set[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate hub paths: direct + cross-connects for WAN, direct for LAN."""
        paths: dict[str, dict[str, int]] = {}  # WHY: accumulate all path keys with their pod value.
        sorted_suffixes = sorted(suffixes)  # WHY: sorted so cross-connect ordering is deterministic.
        for interface_name in wan_interfaces:  # WHY: every WAN uplink gets direct + cross entries.
            direct_key = f"{profile_name}-{interface_name}"  # WHY: direct hub key format expected by Mist.
            paths[direct_key] = {"pod": pod}  # WHY: direct-key pod matches assignment pod.
            for suffix in sorted_suffixes:  # WHY: hub cross-connects fan out per known suffix.
                cross_key = f"{profile_name}-{interface_name}-{suffix}"  # WHY: cross-connect key adds suffix segment.
                paths[cross_key] = {"pod": pod}  # WHY: pod propagates to cross-connect keys.
        for interface_name in lan_interfaces:  # WHY: LAN interfaces are direct-only on hubs.
            direct_key = f"{profile_name}-{interface_name}"  # WHY: LAN hub paths are direct-only (no cross-connect).
            paths[direct_key] = {"pod": pod}  # WHY: same pod for LAN direct entry.
        return paths  # WHY: caller merges this dict into the VPN body's paths mapping.

    @staticmethod
    def _generate_spoke_paths(  # WHY: spoke paths are direct only (no cross-connects).
        profile_name: str,
        wan_interfaces: list[str],
        lan_interfaces: list[str],
        pod: int,
    ) -> dict[str, dict[str, int]]:
        """Generate spoke paths: direct paths only for WAN and LAN."""
        paths: dict[str, dict[str, int]] = {}  # WHY: spokes never emit cross-connect keys.
        for interface_name in wan_interfaces:  # WHY: each WAN uplink contributes one direct key.
            direct_key = f"{profile_name}-{interface_name}"  # WHY: single direct entry per WAN uplink.
            paths[direct_key] = {"pod": pod}  # WHY: assignment pod becomes the path pod.
        for interface_name in lan_interfaces:  # WHY: LAN interfaces are also direct-only for spokes.
            direct_key = f"{profile_name}-{interface_name}"  # WHY: single direct entry per LAN interface.
            paths[direct_key] = {"pod": pod}  # WHY: assignment pod applies to LAN direct entries too.
        return paths  # WHY: caller merges into the shared paths mapping.

    def _build_vpn_body(  # WHY: composes the final Mist VPN body from validated inputs.
        self,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the full VPN API request body."""
        suffixes = self._collect_wan_suffixes(assignments)  # WHY: hub cross-connects need the global suffix set.
        all_paths = self._merge_all_assignment_paths(assignments, suffixes)  # WHY: flatten per-profile paths.
        return {  # WHY: dict literal is the exact shape createOrgVpn expects.
            "name": vpn_name,  # WHY: unique VPN name enforced upstream by _prompt_vpn_name.
            "type": VPN_TYPE_HUB_SPOKE,  # WHY: this menu only produces hub_spoke overlays.
            "path_selection": {"strategy": PATH_STRATEGY_SIMPLE},  # WHY: default strategy for basic overlays.
            "paths": all_paths,  # WHY: full merged path map generated from assignments.
        }

    def _merge_all_assignment_paths(  # WHY: single merge point over per-assignment path dicts.
        self,
        assignments: list[dict[str, Any]],
        suffixes: set[str],
    ) -> dict[str, dict[str, int]]:
        """Merge per-assignment path dicts (hub or spoke) into a single mapping."""
        merged: dict[str, dict[str, int]] = {}  # WHY: single map keyed by 'PROFILE-INTERFACE[-SUFFIX]'.
        for assignment in assignments:  # WHY: iterate assignments in operator-selected order.
            paths = self._paths_for_assignment(assignment, suffixes)  # WHY: helper picks hub/spoke/skip branch.
            merged.update(paths)  # WHY: no key collisions expected because profile names are unique per org.
        return merged  # WHY: return merged map for placement in VPN body.

    def _paths_for_assignment(  # WHY: dispatches to the right path generator based on role.
        self,
        assignment: dict[str, Any],
        suffixes: set[str],
    ) -> dict[str, dict[str, int]]:
        """Return path dict for one assignment (empty for skip)."""
        if assignment["role"] == ROLE_SKIP:  # WHY: skipped profiles contribute nothing to the VPN body.
            return {}  # WHY: empty dict merges as a no-op.
        profile = assignment["profile"]  # WHY: extract once; used for name + port_config lookups.
        profile_name = profile.get("name", "")  # WHY: name feeds every generated path key.
        port_config = profile.get("port_config", {})  # WHY: default empty avoids KeyError on partial API objects.
        wan_list, lan_list = self._classify_interfaces(port_config)  # WHY: classifier reused across generators.
        pod = assignment["pod"]  # WHY: pod value validated during _prompt_pod_values.
        if assignment["role"] == ROLE_HUB:  # WHY: hubs get direct + cross-connect keys.
            return self._generate_hub_paths(profile_name, wan_list, lan_list, suffixes, pod)  # WHY: hub generator.
        return self._generate_spoke_paths(profile_name, wan_list, lan_list, pod)  # WHY: spokes are direct-only.

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_profiles(self) -> list[Any]:  # WHY: isolated so tests can monkeypatch the API call.
        """Fetch gateway device profiles, sorted alphabetically."""
        try:  # WHY: any transport / auth error should degrade gracefully to an empty list.
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )  # WHY: only gateway-type profiles are eligible for VPN membership.
            profiles: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)  # WHY: paginate.
            profiles.sort(key=lambda profile: profile.get("name", "").lower())  # WHY: case-insensitive display order.
            logging.debug("Fetched %d gateway profiles", len(profiles))  # WHY: %s style logging per project rule.
            return profiles  # WHY: sorted list surfaces to run() for display.
        except Exception:  # WHY: single-branch guard so we return [] on any error.
            logging.exception("Failed to fetch device profiles")  # WHY: capture traceback for post-mortem.
            logging.error("! Error retrieving gateway device profiles. Check API connectivity.")  # WHY: operator hint.
            return []  # WHY: empty result triggers the graceful abort branch in run().

    def _fetch_existing_vpns(self) -> list[Any]:  # WHY: separate fetch keeps API responsibilities clear.
        """Fetch all org VPN definitions."""
        try:  # WHY: mirror _fetch_profiles' graceful degradation.
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)  # WHY: list org VPNs.
            vpns: list[Any] = mistapi.get_all(response=response, mist_session=self.apisession)  # WHY: paginate.
            logging.debug("Fetched %d org VPNs", len(vpns))  # WHY: %s style logging per project rule.
            return vpns  # WHY: caller uses for display + uniqueness check.
        except Exception:  # WHY: keep the workflow going even if the VPN list cannot be fetched.
            logging.exception("Failed to fetch org VPNs")  # WHY: preserve traceback for operator log review.
            logging.error(
                "! Error retrieving VPN definitions. Check API connectivity."
            )  # WHY: operator-visible warning.
            return []  # WHY: empty list keeps display/name-uniqueness code paths well-defined.

    def _create_vpn(self, vpn_body: dict[str, Any]) -> dict[str, Any] | None:  # WHY: isolated for tests.
        """Create VPN via API. Returns created VPN dict or None on failure."""
        try:  # WHY: convert any API error into a None return so run() can bail out cleanly.
            response = mistapi.api.v1.orgs.vpns.createOrgVpn(self.apisession, self.org_id, body=vpn_body)  # WHY: POST.
            created: dict[str, Any] = response.data if hasattr(response, "data") else response  # WHY: dual shape.
            logging.info("VPN created via API: %s", created.get("id", ""))  # WHY: id logged for correlation.
            return created  # WHY: caller extracts the new vpn id for profile updates.
        except Exception:  # WHY: single-branch guard: any exception -> operator warning + None.
            logging.exception("Failed to create VPN")  # WHY: capture full traceback in operator log.
            logging.error("! Error creating VPN. Check API connectivity and input.")  # WHY: user-actionable feedback.
            return None  # WHY: caller treats None as "abort without further side-effects".

    # ------------------------------------------------------------------
    # User interaction — display helpers (US1 + US3)
    # ------------------------------------------------------------------

    def _display_existing_vpns(self, vpns: list[Any]) -> None:  # WHY: read-only display step before naming.
        """Display summary table of existing VPNs."""
        if not vpns:  # WHY: no rows to render -> print a friendly placeholder instead of an empty table.
            logging.warning(
                "\n  No existing VPN definitions in this organization."
            )  # WHY: prevent confusing blank output.
            return  # WHY: early return keeps the empty case simple.
        logging.warning(  # WHY: consolidated header lines emit as a single logging record for atomic output.
            "\n  Existing VPN Definitions (%d):\n  %-4s %-30s %-12s %6s\n  %s %s %s %s",
            len(vpns),
            "#",
            "Name",
            "Type",
            "Paths",
            "-" * 4,
            "-" * 30,
            "-" * 12,
            "-" * 6,
        )
        for index, vpn in enumerate(vpns, start=1):  # WHY: 1-based numbering matches operator expectations.
            name = vpn.get("name", "")  # WHY: default empty avoids KeyError on partial API rows.
            vpn_type = vpn.get("type", "unknown")  # WHY: default keeps column populated on partial API data.
            path_count = len(vpn.get("paths", {}))  # WHY: quick visual signal of VPN size.
            logging.warning("  %-4d %-30s %-12s %6d", index, name, vpn_type, path_count)  # WHY: aligned row output.
        logging.warning("")  # WHY: blank line separates table from the next prompt.

    def _display_profile_list(self, profiles: list[Any]) -> None:  # WHY: shows inventory prior to role prompt.
        """Show numbered profile list with WAN/LAN interface counts."""
        logging.warning(  # WHY: consolidated header lines emit as a single logging record.
            "\n  Gateway Device Profiles (%d):\n  %-4s %-30s %4s %4s\n  %s %s %s %s",
            len(profiles),
            "#",
            "Profile Name",
            "WAN",
            "LAN",
            "-" * 4,
            "-" * 30,
            "-" * 4,
            "-" * 4,
        )
        for index, profile in enumerate(profiles, start=1):  # WHY: 1-based indexing consistent with prompts.
            name = profile.get("name", "")  # WHY: default empty avoids KeyError on partial rows.
            port_config = profile.get("port_config", {})  # WHY: default empty dict for missing key.
            wan_list, lan_list = self._classify_interfaces(port_config)  # WHY: reuse classifier here too.
            wan_count = len(wan_list)  # WHY: displayed for operator context.
            lan_count = len(lan_list)  # WHY: displayed for operator context.
            warning = " (!) No WAN interfaces" if wan_count == 0 else ""  # WHY: flag profiles that cannot be hub.
            logging.warning(
                "  %-4d %-30s %4d %4d%s", index, name, wan_count, lan_count, warning
            )  # WHY: aligned row output.
        logging.warning("")  # WHY: blank line separates table from the next prompt.

    def _display_preview(self, vpn_name: str, vpn_body: dict[str, Any]) -> bool:  # WHY: last chance to bail.
        """Display VPN preview and prompt for CREATE confirmation."""
        paths = vpn_body.get("paths", {})  # WHY: default empty so an empty body still previews cleanly.
        self._print_preview_header(vpn_name, vpn_body, len(paths))  # WHY: header + optional warning.
        self._print_preview_paths(paths)  # WHY: dump all generated keys for operator inspection.
        confirm = self._safe_input(  # WHY: EOF-safe prompt for confirmation token.
            "  Type CREATE to confirm, or anything else to cancel: ",
            context=CTX_CONFIRM,
        )
        return confirm.strip() == CONFIRM_TOKEN  # WHY: exact-match token guards against accidental Enter.

    def _print_preview_header(  # WHY: header helper keeps _display_preview readable.
        self, vpn_name: str, vpn_body: dict[str, Any], path_count: int
    ) -> None:
        """Print the VPN preview header block and optional path-count warning."""
        logging.warning(  # WHY: consolidated preview header emits as a single logging record.
            "\n  === VPN Preview ===\n  Name: %s\n  Type: %s\n  Path Selection: %s\n  Total Paths: %d",
            vpn_name,
            vpn_body.get("type", ""),
            vpn_body.get("path_selection", {}),
            path_count,
        )
        if path_count > self.PATH_WARN_THRESHOLD:  # WHY: flag likely misconfiguration before it hits the API.
            logging.warning(  # WHY: multi-line warning is easier to scan than one long line.
                "  WARNING: Path count (%d) exceeds %d. This may indicate an unusually large configuration.",
                path_count,
                self.PATH_WARN_THRESHOLD,
            )

    @staticmethod
    def _print_preview_paths(paths: dict[str, Any]) -> None:  # WHY: pure printer for the path list.
        """Print the sorted list of generated path keys with pod annotations."""
        logging.warning("\n  Path Keys:")  # WHY: header labels the list that follows.
        for key in sorted(paths.keys()):  # WHY: sorted output is easier to eyeball during review.
            pod = paths[key].get("pod", "")  # WHY: default empty string keeps output stable for edge shapes.
            logging.warning("    %s (pod: %s)", key, pod)  # WHY: indent + annotation aids visual scanning.
        logging.warning("")  # WHY: blank line separates list from the next prompt.

    # ------------------------------------------------------------------
    # User interaction — prompts (US1)
    # ------------------------------------------------------------------

    def _prompt_vpn_name(self, existing_names: list[str]) -> str | None:  # WHY: main VPN name entry loop.
        """Prompt for VPN name, validate uniqueness."""
        lower_names = self._lowercase_names(existing_names)  # WHY: build case-insensitive dedupe set once.
        while True:  # WHY: loop until we get a validated name or the operator cancels.
            name = self._safe_input(  # WHY: injected wrapper honors EOF/interrupt semantics.
                "  Enter VPN name (or 'q' to cancel): ",
                context=CTX_NAME,
            ).strip()  # WHY: trim leading/trailing whitespace before validation.
            outcome = self._classify_name(name, lower_names)  # WHY: pure classifier keeps this loop tiny.
            if outcome == "cancel":  # WHY: user typed the cancellation sentinel.
                logging.warning("  Cancelled.")  # WHY: audible confirmation of cancellation.
                return None  # WHY: signal caller to abort the workflow.
            if outcome == "empty":  # WHY: reject blank so we always send a real value to the API.
                logging.warning("  VPN name cannot be empty.")  # WHY: guide operator to retype.
                continue  # WHY: re-prompt without leaving the loop.
            if outcome == "duplicate":  # WHY: prevent silent collision with an existing overlay.
                logging.warning("  VPN name '%s' already exists. Choose a different name.", name)  # WHY: actionable.
                continue  # WHY: re-prompt with the same existing_names set.
            return name  # WHY: outcome == 'ok' -> validated name to return.

    @staticmethod
    def _lowercase_names(names: list[str]) -> set[str]:  # WHY: extracted so the prompt loop stays under CC 5.
        """Return a set of lowercased names for O(1) case-insensitive lookup."""
        return {name.lower() for name in names}  # WHY: isolate the comprehension outside the prompt loop.

    @staticmethod
    def _classify_name(name: str, lower_names: set[str]) -> str:  # WHY: pure classifier for the prompt loop.
        """Return one of: 'cancel', 'empty', 'duplicate', 'ok'."""
        if name.lower() == CANCEL_TOKEN:  # WHY: sentinel is checked before empty so 'q' is not seen as blank.
            return "cancel"  # WHY: caller aborts on this outcome.
        if not name:  # WHY: blank input after strip means the operator hit Enter with nothing.
            return "empty"  # WHY: caller re-prompts with an "empty" message.
        if name.lower() in lower_names:  # WHY: case-insensitive comparison mirrors Mist naming behavior.
            return "duplicate"  # WHY: caller re-prompts with a "duplicate" message.
        return "ok"  # WHY: any other value is accepted as a valid name.

    def _prompt_role_assignments(  # WHY: gather role decisions for every profile in order.
        self,
        profiles: list[Any],
    ) -> list[dict[str, Any]] | None:
        """Prompt user to assign Hub/Spoke/Skip to each profile."""
        logging.warning("  Assign roles to each profile (H=Hub, S=Spoke, K=Skip):")  # WHY: prompt legend for operators.
        assignments = [  # WHY: list comprehension pairs each profile with a role decision.
            self._prompt_role_for_profile(index, profile)  # WHY: per-profile prompt lives in its own helper.
            for index, profile in enumerate(profiles, start=1)
        ]
        if self._has_any_active(assignments):  # WHY: at least one Hub or Spoke required to build a VPN.
            return assignments  # WHY: return the fully-populated assignment list to the caller.
        return self._handle_all_skipped(profiles)  # WHY: dedicated branch handles retry/cancel messaging.

    def _prompt_role_for_profile(  # WHY: per-profile role loop; keeps the caller's list-comp clean.
        self, index: int, profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Loop until the operator supplies a valid H/S/K response for one profile."""
        name = profile.get("name", "")  # WHY: default empty avoids KeyError in prompt string.
        while True:  # WHY: loop until we parse a valid role choice.
            choice = (  # WHY: multi-line expression normalizes user input in one place.
                self._safe_input(
                    f"    {index}. {name} [H/S/K]: ",
                    context=CTX_ROLE,
                )
                .strip()
                .lower()
            )
            role = self._parse_role_choice(choice)  # WHY: pure parser keeps this loop free of branching noise.
            if role is not None:  # WHY: parser returns None only for invalid inputs.
                pod = 0 if role == ROLE_SKIP else self.POD_DEFAULT  # WHY: skips carry no pod value.
                return {"profile": profile, "role": role, "pod": pod}  # WHY: assignment shape used everywhere.
            logging.warning(
                "    Please enter H (Hub), S (Spoke), or K (Skip)."
            )  # WHY: guide operator on invalid input.

    @staticmethod
    def _parse_role_choice(choice: str) -> str | None:  # WHY: pure parser -- easy to unit test.
        """Map raw prompt input to a canonical role string or None if invalid."""
        if choice in CHOICE_HUB:  # WHY: accept multiple synonyms for hub role.
            return ROLE_HUB  # WHY: canonical hub role constant.
        if choice in CHOICE_SPOKE:  # WHY: accept multiple synonyms for spoke role.
            return ROLE_SPOKE  # WHY: canonical spoke role constant.
        if choice in CHOICE_SKIP:  # WHY: accept multiple synonyms for skip role.
            return ROLE_SKIP  # WHY: canonical skip role constant.
        return None  # WHY: caller re-prompts on None.

    @staticmethod
    def _has_any_active(assignments: list[dict[str, Any]]) -> bool:  # WHY: quick check before building a VPN.
        """Return True if at least one assignment is not the skip role."""
        return any(a["role"] != ROLE_SKIP for a in assignments)  # WHY: skip-only sets cannot form a VPN.

    def _handle_all_skipped(  # WHY: offers a retry loop when the operator skipped everything.
        self, profiles: list[Any]
    ) -> list[dict[str, Any]] | None:
        """Ask operator to retry role assignment when every profile was skipped."""
        logging.warning("  All profiles skipped. At least one must be Hub or Spoke.")  # WHY: explain why we retry.
        retry = (  # WHY: normalized y/N answer determines whether we loop.
            self._safe_input("  Try again? (y/N): ", context=CTX_RETRY_ROLES).strip().lower()
        )
        if retry == RETRY_YES:  # WHY: recurse to give the operator another chance.
            return self._prompt_role_assignments(profiles)  # WHY: same profiles, fresh set of role decisions.
        logging.warning("  Cancelled.")  # WHY: operator-visible confirmation of cancel decision.
        return None  # WHY: caller treats None as full workflow cancellation.

    def _prompt_pod_values(  # WHY: second phase of assignment collection -- assigns pods to non-skip roles.
        self,
        assignments: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Prompt for pod values with auto-suggestion."""
        fallback_counter = 1  # WHY: monotonically-increasing pod when profile name lacks digits.
        for assignment in assignments:  # WHY: iterate in operator order so pods track assignment order.
            if assignment["role"] == ROLE_SKIP:  # WHY: skipped profiles retain their zero pod.
                continue  # WHY: skips carry no pod prompt.
            profile_name = assignment["profile"].get("name", "")  # WHY: default keeps prompt string safe.
            suggested = self._suggest_pod(profile_name, fallback_counter)  # WHY: use trailing digits if present.
            assignment["pod"] = self._prompt_single_pod(profile_name, suggested)  # WHY: focused per-profile loop.
            fallback_counter += 1  # WHY: bump fallback so successive digit-less profiles get unique pods.
        return assignments  # WHY: mutation happens in-place; return for chaining convenience.

    def _prompt_single_pod(self, profile_name: str, suggested: int) -> int:  # WHY: single pod prompt loop.
        """Prompt until the operator provides a valid integer pod (or accepts the suggestion)."""
        while True:  # WHY: loop until we accept the suggestion or parse a valid int.
            raw = self._safe_input(  # WHY: EOF-safe wrapper honors interrupt semantics.
                f"    Pod for {profile_name} [{suggested}]: ",
                context=CTX_POD,
            ).strip()  # WHY: whitespace-only means "accept suggestion".
            if not raw:  # WHY: empty input means "accept suggested value".
                return suggested  # WHY: hand back the pre-computed suggestion.
            value = self._parse_pod_value(raw)  # WHY: parse helper handles both format and range.
            if value is not None:  # WHY: parser returns None on invalid input; error already printed.
                return value  # WHY: validated pod integer returned to caller.

    def _parse_pod_value(self, raw: str) -> int | None:  # WHY: reusable validator with printed feedback.
        """Return validated pod int, or None (with operator message) if invalid."""
        try:  # WHY: guard int() against non-numeric input.
            value = int(raw)  # WHY: allow only integer pod ids.
        except ValueError:  # WHY: non-integer input triggers a re-prompt.
            logging.warning(
                "    Pod must be an integer (%d-%d).", self.POD_MIN, self.POD_MAX
            )  # WHY: actionable guidance.
            return None  # WHY: caller sees None and re-prompts.
        if not (self.POD_MIN <= value <= self.POD_MAX):  # WHY: enforce documented pod range.
            logging.warning(
                "    Pod must be between %d and %d.", self.POD_MIN, self.POD_MAX
            )  # WHY: actionable guidance.
            return None  # WHY: caller sees None and re-prompts.
        return value  # WHY: valid pod integer returned to caller.

    # ------------------------------------------------------------------
    # Profile update (US2)
    # ------------------------------------------------------------------

    def _build_port_vpn_paths(  # WHY: builds the per-port vpn_paths mapping for one profile update.
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
        vpn_paths: dict[str, dict[str, Any]] = {}  # WHY: mapping of path-ref -> {key, role}.
        is_wan = True  # WHY: preserved from original behavior; WAN interfaces get cross-connects when hub.
        direct_key = f"{profile_name}-{interface_name}"  # WHY: direct path key (no suffix segment).
        vpn_ref = f"{direct_key}.{vpn_name}"  # WHY: dotted path.vpn form matches Mist expectations.
        vpn_paths[vpn_ref] = {"key": 0, "role": role}  # WHY: direct entry is always key index 0.

        if role == ROLE_HUB and is_wan:  # WHY: only hubs emit cross-connect vpn_paths references.
            sorted_suffixes = sorted(suffixes)  # WHY: deterministic key indices across runs & tests.
            for key_index, suffix in enumerate(sorted_suffixes):  # WHY: index becomes the vpn_paths 'key'.
                cross_key = f"{profile_name}-{interface_name}-{suffix}"  # WHY: cross-connect key adds suffix.
                cross_ref = f"{cross_key}.{vpn_name}"  # WHY: dotted path.vpn form for cross-connects.
                vpn_paths[cross_ref] = {"key": key_index, "role": role}  # WHY: monotonically-increasing key idx.
        return vpn_paths  # WHY: caller merges into port_config[interface_name]['vpn_paths'].

    def _update_single_profile(  # WHY: per-profile update wrapped in an exception guard.
        self,
        profile_id: str,
        profile_name: str,
        vpn_name: str,
        assignment: dict[str, Any],
        suffixes: set[str],
    ) -> bool:
        """Fetch fresh profile, merge vpn_paths, push update."""
        try:  # WHY: guard the whole flow so any API/parse error becomes a soft failure.
            fresh_profile = self._fetch_fresh_profile(profile_id)  # WHY: always start from latest server state.
            port_config = fresh_profile.get("port_config", {})  # WHY: default keeps merge helper safe on new profiles.
            role = assignment["role"]  # WHY: role determines cross-connect emission below.
            self._apply_port_updates(profile_name, vpn_name, role, port_config, suffixes)  # WHY: in-place merge.
            self._push_profile_update(profile_id, fresh_profile)  # WHY: single REST PUT wrapped for patchability.
            logging.info("Updated profile '%s' with vpn_paths for VPN '%s'", profile_name, vpn_name)  # WHY: audit.
            return True  # WHY: caller counts True as one success.
        except Exception:  # WHY: catch-all so a per-profile error does not abort other profiles.
            logging.exception("Failed to update profile '%s'", profile_name)  # WHY: keep traceback for support.
            logging.error(
                "  ! Error updating profile '%s'. Check logs.", profile_name
            )  # WHY: operator-visible feedback.
            return False  # WHY: caller counts False as one failure.

    def _fetch_fresh_profile(self, profile_id: str) -> dict[str, Any]:  # WHY: isolated GET for patchability.
        """Fetch the current server-side representation of a device profile."""
        response = mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile(  # WHY: GET latest profile document.
            self.apisession, self.org_id, deviceprofile_id=profile_id
        )
        fresh: dict[str, Any] = response.data if hasattr(response, "data") else response  # WHY: dual response shape.
        return fresh  # WHY: return the mutable profile dict so caller can update port_config in place.

    def _apply_port_updates(  # WHY: mutates port_config in place with vpn_paths entries per interface.
        self,
        profile_name: str,
        vpn_name: str,
        role: str,
        port_config: dict[str, Any],
        suffixes: set[str],
    ) -> None:
        """Merge new vpn_paths entries into WAN and LAN port entries in-place."""
        wan_list, lan_list = self._classify_interfaces(port_config)  # WHY: reuse the pure classifier.
        for interface_name in wan_list:  # WHY: WAN ports may accumulate cross-connect entries for hubs.
            new_entries = self._build_port_vpn_paths(profile_name, interface_name, vpn_name, role, suffixes)
            self._merge_vpn_paths_entry(port_config, interface_name, new_entries)  # WHY: union-merge helper.
        for interface_name in lan_list:  # WHY: LAN ports get a single direct entry regardless of role.
            direct_key = f"{profile_name}-{interface_name}"  # WHY: LAN entries are direct-only.
            vpn_ref = f"{direct_key}.{vpn_name}"  # WHY: dotted path.vpn form matches Mist expectations.
            self._merge_vpn_paths_entry(port_config, interface_name, {vpn_ref: {"key": 0, "role": role}})  # WHY: merge.

    @staticmethod
    def _merge_vpn_paths_entry(  # WHY: shared union-merge preserves entries from other VPNs.
        port_config: dict[str, Any],
        interface_name: str,
        new_entries: dict[str, dict[str, Any]],
    ) -> None:
        """Union-merge new vpn_paths entries into an existing port_config entry."""
        existing = port_config[interface_name].get("vpn_paths", {})  # WHY: preserve entries from other VPNs.
        existing.update(new_entries)  # WHY: additive; never removes references to unrelated VPNs.
        port_config[interface_name]["vpn_paths"] = existing  # WHY: assign back so partial dicts get promoted.

    def _push_profile_update(self, profile_id: str, body: dict[str, Any]) -> None:  # WHY: PUT wrapper for tests.
        """Send the mutated profile body back to Mist (retained for external test patchability)."""
        # WHY: keep this method so downstream monkeypatches keep working; body/id are validated here.
        if not isinstance(profile_id, str) or not profile_id:  # WHY: reject empty ids pre-HTTP.
            raise ValueError("profile_id must be a non-empty string")  # WHY: fast failure protects the org.
        if not isinstance(body, dict):  # WHY: mistapi expects a dict body; caller mistakes get caught early.
            raise TypeError("body must be a dict")  # WHY: explicit type feedback beats a mistapi trace.
        mistapi.api.v1.orgs.deviceprofiles.updateOrgDeviceProfile(  # WHY: performs the actual REST PUT.
            self.apisession,  # WHY: authenticated Mist session.
            self.org_id,  # WHY: mutation is scoped to the operator's org.
            deviceprofile_id=profile_id,  # WHY: identifies which profile to update.
            body=body,  # WHY: full mutated profile document.
        )

    def _prompt_profile_updates(  # WHY: entry point for the optional post-create profile linkage.
        self,
        vpn_id: str,
        vpn_name: str,
        assignments: list[dict[str, Any]],
    ) -> None:
        """Offer to update each profile's port_config with vpn_paths."""
        _ = vpn_id  # WHY: preserved in signature for API stability even though the body does not use it.
        non_skip = [a for a in assignments if a["role"] != ROLE_SKIP]  # WHY: skips are never linked to the VPN.
        if not non_skip:  # WHY: nothing to update -> return silently.
            return  # WHY: no active assignments means no profile mutation.
        if not self._prompt_confirm_profile_updates():  # WHY: honor operator decision before touching profiles.
            return  # WHY: honor a no answer without further prompts.
        success_count, fail_count = self._run_profile_updates(vpn_name, non_skip)  # WHY: helper isolates loop.
        logging.warning(
            "  Profile updates: %d succeeded, %d failed.", success_count, fail_count
        )  # WHY: summary for operator.

    def _prompt_confirm_profile_updates(self) -> bool:  # WHY: y/N confirmation before mutating profiles.
        """Return True when operator answers 'y' to the profile-update prompt."""
        choice = (  # WHY: normalize the confirmation answer for comparison.
            self._safe_input(
                "  Update device profiles with vpn_paths references? (y/N): ",
                context=CTX_PROFILE_UPDATE,
            )
            .strip()
            .lower()
        )
        if choice != RETRY_YES:  # WHY: default (N) is safer -- do not mutate profiles unless explicitly asked.
            logging.warning("  Skipping profile updates.")  # WHY: operator-visible confirmation of the skip.
            return False  # WHY: caller returns without touching profiles.
        return True  # WHY: explicit y -> proceed with the profile-update loop.

    def _run_profile_updates(  # WHY: performs the actual per-profile update loop and tallies results.
        self, vpn_name: str, non_skip: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """Iterate assignments, calling _update_single_profile; return (success, fail) tally."""
        suffixes = self._collect_wan_suffixes(non_skip)  # WHY: cross-connect vpn_paths need the global suffix set.
        success_count = 0  # WHY: tally successful profile PUTs.
        fail_count = 0  # WHY: tally per-profile failures without aborting the loop.
        for assignment in non_skip:  # WHY: iterate in operator-selected order.
            profile = assignment["profile"]  # WHY: extract dict once for cleaner lookups.
            profile_name = profile.get("name", "")  # WHY: default empty avoids KeyError in log/print strings.
            profile_id = profile.get("id", "")  # WHY: id needed for GET/PUT calls in helper.
            result = self._update_single_profile(profile_id, profile_name, vpn_name, assignment, suffixes)
            if result:  # WHY: True -> success branch.
                success_count += 1  # WHY: increment success tally.
            else:  # WHY: False -> failure branch (per-profile guard already logged the traceback).
                fail_count += 1  # WHY: increment failure tally.
        return success_count, fail_count  # WHY: caller renders these as a summary line.

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:  # WHY: default injected input; used when no wrapper.
        """Fallback input when safe_input is not provided.

        Delegates to the canonical EOF-safe wrapper instead of a second hand-rolled
        input() (issue #452: clears CONV-INPUT, identical degrade-to-empty behavior).
        """
        from src.utils.input_utils import InputUtils  # WHY: local import avoids any import cycle at module load.

        return InputUtils.safe_input(prompt, context=CTX_FALLBACK)  # WHY: EOF-safe; '' on EOF/interrupt.
