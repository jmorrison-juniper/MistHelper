"""WAN Hub-Spoke VPN Builder -- Menu 164.

Create hub-spoke VPN overlay definitions from gateway device profiles.
NOC engineers select profiles, assign hub/spoke roles, review
auto-generated VPN path keys with pod numbers, confirm, and the VPN
is created via API.  Optionally updates each profile's port_config
with vpn_paths references to the new VPN.

Follows the external-module pattern established by Menu 163
(``src/operations/wan/wan_hub_group_manager.py``).
"""

from __future__ import annotations  # WHY: enable PEP 563 postponed annotations so future syntax works on 3.9+.

import logging  # WHY: structured operator diagnostics (info/debug/exception) for CLI workflow.
import re  # WHY: regex extraction of trailing pod digits from profile names.
from collections.abc import Callable  # WHY: precise typing for injected safe_input callable.
from typing import Any  # WHY: mistapi returns opaque dicts. Any keeps boundary honest without leaking types.

import mistapi  # WHY: shared API session helper (get_all pagination).
import mistapi.api.v1.orgs.deviceprofiles  # WHY: gateway device profile list/get/update endpoints.
import mistapi.api.v1.orgs.vpns  # WHY: org VPN list/create endpoints.

logger = logging.getLogger(__name__)  # WHY: module logger identifies the WAN VPN builder in shared logs.

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

CANCEL_TOKEN = "q"  # nosec B105 - The value is the prompt sentinel that aborts the VPN name flow.
CONFIRM_TOKEN = "CREATE"  # nosec B105 - The value is the typed word that arms VPN creation.
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
            logger.error("! No organization selected. Exiting.")  # WHY: single-line operator hint before returning.
            return  # WHY: nothing more to do without an org context.
        builder = WanVpnBuilder(apisession, org_id, safe_input_func)  # WHY: bind session/org/input for this run.
        builder.run()  # WHY: hand off to the interactive workflow.

    # ------------------------------------------------------------------
    # Main workflow (US1 + US2 + US3 orchestration)
    # ------------------------------------------------------------------

    def run(self) -> None:  # WHY: top-level orchestrator. Kept small by delegating to focused helpers.
        """Main workflow: fetch, display, build, preview, create."""
        logger.warning(
            "\n=== WAN Hub-Spoke VPN Builder ==="
        )  # WHY: banner delimits this menu action in the operator log.
        logger.info("Starting WAN Hub-Spoke VPN Builder")  # WHY: capture entry timestamp for troubleshooting.

        profiles = self._load_profiles_or_none()  # WHY: fetch profiles and short-circuit on empty inventory.
        if profiles is None:  # WHY: helper already emitted operator message. Nothing more to do.
            return  # WHY: propagate abort without further prompts.

        vpn_name = self._prompt_name_after_display(profiles)  # WHY: show existing VPNs then collect unique name.
        if vpn_name is None:  # WHY: user cancelled the name prompt.
            return  # WHY: silent return. Helper already printed the cancel message.

        assignments = self._collect_role_and_pod_assignments(profiles)  # WHY: gather full role+pod set in one step.
        if assignments is None:  # WHY: cancelled during role or pod prompts.
            return  # WHY: nothing to build without at least one active assignment.

        vpn_body = self._build_vpn_body(vpn_name, assignments)  # WHY: assemble API payload from validated inputs.
        if not self._display_preview(vpn_name, vpn_body):  # WHY: require explicit CREATE token before mutating org.
            logger.warning("  VPN creation cancelled.")  # WHY: operator-visible confirmation of cancellation.
            return  # WHY: honor the operator's decision not to proceed.

        self._create_and_optionally_update(vpn_name, vpn_body, assignments)  # WHY: perform side-effects together.

    def _load_profiles_or_none(self) -> list[Any] | None:  # WHY: split so run() stays short and testable.
        """Fetch gateway profiles. Return None and warn if inventory is empty."""
        profiles = self._fetch_profiles()  # WHY: API call is isolated for test-time monkeypatch.
        if not profiles:  # WHY: empty list means org has no gateway profiles -> abort with hint.
            logger.warning("! No gateway device profiles found in this organization.")  # WHY: actionable operator hint.
            return None  # WHY: sentinel triggers early return in run().
        return profiles  # WHY: hand the fetched list to the workflow.

    def _prompt_name_after_display(self, profiles: list[Any]) -> str | None:  # WHY: keeps run() body flat.
        """Fetch existing VPNs, display them, then prompt for a unique VPN name."""
        existing_vpns = self._fetch_existing_vpns()  # WHY: needed both for display and uniqueness check.
        if existing_vpns is None:  # WHY: an unavailable inventory cannot prove that a new name is unique.
            logger.warning("! VPN inventory is unavailable. The builder will stop.")  # WHY: explain the safe abort.
            return None  # WHY: stop before prompts or organization changes.
        self._display_existing_vpns(existing_vpns)  # WHY: operator sees current overlays before naming a new one.
        existing_names = [vpn["name"].strip() for vpn in existing_vpns]  # WHY: normalize names for duplicate checks.
        vpn_name = self._prompt_vpn_name(existing_names)  # WHY: enforce uniqueness before profile selection.
        if vpn_name is not None:  # WHY: only render the profile table if the user is proceeding.
            self._display_profile_list(profiles)  # WHY: show profile inventory once a valid name is chosen.
        return vpn_name  # WHY: None propagates cancellation to the caller.

    def _collect_role_and_pod_assignments(  # WHY: chains role prompt then pod prompt, propagates cancel.
        self, profiles: list[Any]
    ) -> list[dict[str, Any]] | None:
        """Run role prompt then pod prompt. Propagate None on cancellation."""
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
        logger.info(
            "  VPN '%s' created successfully. ID: %s", vpn_name, vpn_id
        )  # WHY: operator confirmation of success.
        logger.info("VPN '%s' created with ID %s", vpn_name, vpn_id)  # WHY: audit trail of created id.
        self._prompt_profile_updates(vpn_id, vpn_name, assignments)  # WHY: optional US2 profile linkage.

    # ------------------------------------------------------------------
    # Pure-logic helpers (Phase 2 foundational)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_wan_suffix(interface_name: str) -> str:  # WHY: pure helper. Safe to call from any thread.
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
        wan_interfaces: list[str] = []  # WHY: collect WAN uplinks. Order established by sort() below.
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
        profile = assignment["profile"]  # WHY: extract once. Used for name + port_config lookups.
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
            logger.info("Fetching gateway profiles for %s", self.org_id)  # WHY: identify the org before its read.
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                self.apisession, self.org_id, type="gateway"
            )  # WHY: only gateway-type profiles are eligible for VPN membership.
            logger.debug("Received gateway profile response")  # WHY: confirm the request before status validation.
            profiles = self._collect_profiles_from_pages(response)  # WHY: reject any failed page before using data.
            if profiles is None:  # WHY: one failed page invalidates the complete inventory.
                return []  # WHY: stop before partial data reaches the VPN workflow.
            logger.debug("Read %d gateway profiles", len(profiles))  # WHY: report the pagination result.
            logger.info("Sorting %d gateway profiles", len(profiles))  # WHY: mark the display-order transform.
            profiles.sort(key=lambda profile: profile.get("name", "").lower())  # WHY: preserve case-insensitive order.
            logger.debug("Sorted %d gateway profiles", len(profiles))  # WHY: report the sort result.
            return profiles  # WHY: sorted list surfaces to run() for display.
        except Exception as error:  # WHY: keep broad so the menu can display with incomplete profile data.
            logging.exception(
                "Failed to fetch device profiles after %s: %s",
                type(error).__name__,
                error,
            )  # WHY: capture the profile read fault for post-mortem.
            logging.error("! Error retrieving gateway device profiles. Check API connectivity.")  # WHY: operator hint.
            return []  # WHY: empty result triggers the graceful abort branch in run().

    def _collect_profiles_from_pages(self, response: Any) -> list[Any] | None:
        """Return all profile pages only when each SDK response succeeds."""
        profiles: list[Any] = []  # WHY: stage data until every page passes validation.
        current_response = response  # WHY: inspect the first page before reading its data.
        while current_response is not None:  # WHY: validate each page before accepting its profiles.
            page_profiles = self._validated_profile_page(current_response)  # WHY: validate status and data together.
            if page_profiles is None:  # WHY: any invalid page invalidates the complete inventory.
                return None  # WHY: malformed later pages must not allow partial VPN configuration.
            profiles.extend(page_profiles)  # WHY: hold page data until all following pages pass.
            if not getattr(current_response, "next", None):  # WHY: finish only when the SDK has no next page.
                break  # WHY: no more response pages remain.
            logger.info("Fetching the next gateway profile page")  # WHY: record each additional SDK request.
            current_response = mistapi.get_next(self.apisession, current_response)  # WHY: use the SDK for pagination.
            logger.debug("Received the next gateway profile page")  # WHY: record completion before status validation.
            if current_response is None:  # WHY: a missing page is an incomplete inventory, not a valid end.
                logger.error("Gateway profile pagination ended before the next page arrived")  # WHY: report truncation.
                return None  # WHY: discard earlier pages when pagination stops unexpectedly.
        return profiles  # WHY: expose data only after every page has passed validation.

    @staticmethod
    def _validated_profile_page(response: Any) -> list[Any] | None:
        """Return page profiles only when its status and result shape are valid."""
        status_code = getattr(response, "status_code", None)  # WHY: read status before response data.
        status_is_successful = isinstance(status_code, int) and 200 <= status_code < 300  # WHY: accept only 2xx.
        if not status_is_successful:  # WHY: reject failed or unknown page status.
            logger.error("Gateway profile page failed with HTTP status %s", status_code)  # WHY: report the failure.
            return None  # WHY: discard staged inventory if this page failed.
        response_data = getattr(response, "data", None)  # WHY: read page data only after status validation.
        page_profiles = (
            response_data
            if isinstance(response_data, list)
            else (response_data.get("results") if isinstance(response_data, dict) else None)
        )  # WHY: accept SDK lists or Mist result dictionaries.
        if not isinstance(page_profiles, list):  # WHY: require complete profile data on every page.
            logger.error("Gateway profile page has no valid results list")  # WHY: report malformed page data.
            return None  # WHY: prevent malformed later pages from allowing partial configuration.
        return page_profiles  # WHY: pass only a validated page to the staged inventory.

    def _fetch_existing_vpns(self) -> list[Any] | None:  # WHY: distinguish valid emptiness from unavailable data.
        """Fetch complete org VPN definitions or return None when any page fails."""
        try:  # WHY: keep transport errors inside this read-only boundary.
            logger.info("Fetching organization VPNs for %s", self.org_id)  # WHY: record the inventory read.
            response = mistapi.api.v1.orgs.vpns.listOrgVpns(self.apisession, self.org_id)  # WHY: use the Mist SDK.
            vpns = self._collect_vpns_from_pages(response)  # WHY: validate all pages before names reach the workflow.
            if vpns is None:  # WHY: a failed page invalidates the complete inventory.
                logger.error("Organization VPN inventory is incomplete")  # WHY: record why creation must stop.
                return None  # WHY: do not convert an incomplete list into an empty one.
            logger.debug("Fetched %d organization VPNs", len(vpns))  # WHY: summarize the validated inventory.
            return vpns  # WHY: preserve complete data for display and duplicate checks.
        except Exception as error:  # WHY: a raised SDK error also means inventory is unavailable.
            logging.exception(
                "Failed to fetch organization VPNs after %s: %s",
                type(error).__name__,
                error,
            )  # WHY: retain exception context for operator review.
            logging.error("! Error retrieving VPN definitions. Check API connectivity.")  # WHY: show the read failure.
            return None  # WHY: prevent a failed read from allowing VPN creation.

    def _collect_vpns_from_pages(self, response: Any) -> list[Any] | None:
        """Return VPN definitions only when every declared page succeeds."""
        if response is None:  # WHY: no first response cannot prove that the inventory is empty.
            logger.error("Organization VPN list returned no response")  # WHY: report the missing SDK result.
            return None  # WHY: keep missing data distinct from a successful empty page.
        vpns: list[Any] = []  # WHY: stage records until every page passes validation.
        seen_next_links: set[str] = set()  # WHY: stop pagination when the SDK repeats a page link.
        prior_header_state: tuple[int, int, int] | None = None  # WHY: detect metadata changes across pages.
        page_count = 0  # WHY: distinguish first-page metadata from later-page metadata.
        current_response = response  # WHY: validate each page before accepting its data.
        while current_response is not None:  # WHY: consume every page declared by the SDK.
            page_vpns = self._validated_vpn_page(current_response)  # WHY: check status and result shape together.
            if page_vpns is None:  # WHY: any invalid page makes earlier staged rows incomplete.
                return None  # WHY: discard partial inventory before duplicate checks.
            headers_ok, header_state = self._validated_pagination_headers(current_response)  # WHY: check SDK metadata.
            if not headers_ok:  # WHY: malformed header pagination can hide additional VPN records.
                return None  # WHY: do not treat the SDK's default next=None as proof of completion.
            if not self._pagination_headers_are_consistent(
                prior_header_state, header_state, page_count
            ):  # WHY: page totals, limits, and indexes must describe one stable inventory.
                logger.error("Organization VPN pagination headers are inconsistent")  # WHY: report the invalid state.
                return None  # WHY: inconsistent pages cannot prove complete duplicate-name coverage.
            prior_header_state = header_state  # WHY: compare the next page with this validated page.
            page_count += 1  # WHY: identify the next response as a later page.
            vpns.extend(page_vpns)  # WHY: stage only data from a validated page.
            page_ok, next_response = self._fetch_next_vpn_page(  # WHY: validate links before requesting another page.
                current_response, seen_next_links
            )
            if not page_ok:  # WHY: invalid or repeated links cannot prove a complete inventory.
                return None  # WHY: prevent unsafe duplicate-name checks.
            if next_response is None:  # WHY: no next link means the validated inventory is complete.
                return vpns  # WHY: expose all staged records only after the final page.
            current_response = next_response  # WHY: validate the next response before accepting its records.
        return None  # WHY: an unexpected missing response cannot prove inventory completeness.

    @staticmethod
    def _validated_pagination_headers(
        response: Any,
    ) -> tuple[bool, tuple[int, int, int] | None]:
        """Validate Mist pagination headers and their next-link decision."""
        headers = getattr(response, "headers", None)  # WHY: native SDK responses retain transport headers.
        if headers is None:  # WHY: simple SDK wrappers can represent non-header pagination.
            return True, None  # WHY: let the next link determine whether another page exists.
        raw_values = WanVpnBuilder._read_pagination_header_values(headers)  # WHY: preserve missing values explicitly.
        if raw_values is None:  # WHY: an invalid header container cannot establish pagination state.
            return False, None  # WHY: stop before duplicate-name checks.
        values_ok, header_state = WanVpnBuilder._parse_pagination_header_values(raw_values)  # WHY: validate counters.
        if not values_ok or header_state is None:  # WHY: headerless pages need no SDK link comparison.
            return values_ok, header_state  # WHY: preserve valid no-header responses and reject invalid values.
        if not WanVpnBuilder._sdk_next_link_matches_headers(response, header_state):  # WHY: detect SDK parse gaps.
            return False, None  # WHY: header and SDK state must agree before the inventory is accepted.
        return True, header_state  # WHY: caller verifies stable counters across the page sequence.

    @staticmethod
    def _read_pagination_header_values(headers: Any) -> tuple[Any, Any, Any] | None:
        """Read the three Mist page headers without hiding malformed containers."""
        header_names = ("X-Page-Total", "X-Page-Limit", "X-Page-Page")  # WHY: SDK pagination uses all three values.
        try:  # WHY: reject malformed header containers rather than assuming a final page.
            raw_values = tuple(headers.get(name) for name in header_names)  # WHY: preserve missing values explicitly.
        except AttributeError:  # WHY: an invalid header object cannot establish pagination state.
            logger.error("Organization VPN page has invalid pagination headers")  # WHY: report malformed SDK metadata.
            return None  # WHY: stop before duplicate-name checks.
        return raw_values  # WHY: let the parser distinguish absent and incomplete headers.

    @staticmethod
    def _parse_pagination_header_values(
        raw_values: tuple[Any, Any, Any],
    ) -> tuple[bool, tuple[int, int, int] | None]:
        """Parse complete, in-range page counters."""
        if all(value is None for value in raw_values):  # WHY: no page headers means a legitimate single-page response.
            return True, None  # WHY: preserve unpaginated endpoint responses.
        if not WanVpnBuilder._pagination_headers_are_complete(raw_values):  # WHY: require all three values.
            logger.error("Organization VPN pagination headers are incomplete")  # WHY: report missing header values.
            return False, None  # WHY: missing metadata cannot prove inventory completeness.
        header_state = WanVpnBuilder._pagination_header_integers(raw_values)  # WHY: parse all SDK page counters.
        if header_state is None:  # WHY: malformed counters must not look like a final page.
            return False, None  # WHY: reject unparseable pagination state.
        if not WanVpnBuilder._pagination_header_state_is_valid(header_state):  # WHY: reject invalid counter ranges.
            logger.error("Organization VPN pagination headers contain invalid ranges")  # WHY: report bad counters.
            return False, None  # WHY: invalid ranges cannot describe a complete list.
        return True, header_state  # WHY: caller verifies stable counters across the page sequence.

    @staticmethod
    def _pagination_headers_are_complete(raw_values: tuple[Any, Any, Any]) -> bool:
        """Return whether every pagination header is a nonblank string."""
        return all(  # WHY: reject empty and non-text counters before integer parsing.
            isinstance(value, str) and bool(value.strip())  # WHY: require nonblank strings.
            for value in raw_values  # WHY: validate each of the three page counters.
        )

    @staticmethod
    def _pagination_header_integers(raw_values: tuple[Any, Any, Any]) -> tuple[int, int, int] | None:
        """Convert complete header values to integer counters."""
        try:  # WHY: SDK int conversion failures otherwise leave next=None.
            return (  # WHY: keep the exact SDK counter order in a fixed-size tuple.
                int(raw_values[0]),  # WHY: convert the declared VPN count.
                int(raw_values[1]),  # WHY: convert the page size.
                int(raw_values[2]),  # WHY: convert the current page number.
            )
        except ValueError:  # WHY: malformed counters must not look like a final page.
            logger.error("Organization VPN pagination headers contain invalid integers")  # WHY: report parse failure.
            return None  # WHY: reject unparseable pagination state.

    @staticmethod
    def _pagination_header_state_is_valid(header_state: tuple[int, int, int]) -> bool:
        """Check that the page counters describe a valid page in the declared inventory."""
        total, limit, page = header_state  # WHY: name the counters for range checks.
        if total < 0 or limit <= 0 or page <= 0:  # WHY: valid totals are nonnegative and page values are positive.
            return False  # WHY: invalid ranges cannot describe a complete list.
        last_page = max(1, (total + limit - 1) // limit)  # WHY: include one page for an empty inventory.
        if page > last_page:  # WHY: an out-of-range page cannot belong to this inventory.
            logger.error("Organization VPN page number exceeds the declared total")  # WHY: report inconsistent counts.
            return False  # WHY: stop when header counts disagree.
        return True  # WHY: counters describe an in-range page.

    @staticmethod
    def _sdk_next_link_matches_headers(
        response: Any,
        header_state: tuple[int, int, int],
    ) -> bool:
        """Require the SDK next link to match the validated page counters."""
        total, limit, page = header_state  # WHY: name the counters for the SDK pagination comparison.
        has_next = limit * page < total  # WHY: match the SDK pagination rule for a remaining page.
        next_link = getattr(response, "next", None)  # WHY: compare the SDK's computed link with the headers.
        if has_next != bool(next_link):  # WHY: the SDK can leave next unset after invalid header parsing.
            logger.error("Organization VPN pagination headers disagree with the SDK next link")  # WHY: report mismatch.
            return False  # WHY: header and SDK state must agree before the inventory is accepted.
        return True  # WHY: SDK link behavior matches the parsed header counters.

    @staticmethod
    def _pagination_headers_are_consistent(
        prior_state: tuple[int, int, int] | None,
        current_state: tuple[int, int, int] | None,
        page_count: int,
    ) -> bool:
        """Require header pagination to start at page one and remain stable across pages."""
        if current_state is None:  # WHY: headerless pagination must remain headerless on each page.
            return prior_state is None  # WHY: mixed metadata cannot prove complete pagination.
        if prior_state is None:  # WHY: the first response establishes the pagination mode.
            return page_count == 0 and current_state[2] == 1  # WHY: initial header pages must start at page one.
        same_total = current_state[0] == prior_state[0]  # WHY: each page must declare the same inventory size.
        same_limit = current_state[1] == prior_state[1]  # WHY: each page must use the same page size.
        next_page = current_state[2] == prior_state[2] + 1  # WHY: page indexes must advance by one.
        return same_total and same_limit and next_page  # WHY: require one coherent header sequence.

    def _fetch_next_vpn_page(self, response: Any, seen_next_links: set[str]) -> tuple[bool, Any | None]:
        """Fetch the next page or report whether the current page completes inventory."""
        if not hasattr(response, "next"):  # WHY: missing pagination metadata cannot prove that no page remains.
            logger.error("Organization VPN page has no pagination metadata")  # WHY: report incomplete response shape.
            return False, None  # WHY: stop rather than accept a possibly partial inventory.
        next_link = response.next  # WHY: read the SDK page link after validating its presence.
        if next_link is None:  # WHY: the SDK marks the final page with no next link.
            return True, None  # WHY: signal complete pagination without another request.
        if not isinstance(next_link, str) or not next_link.strip():  # WHY: only a usable URL can fetch a page.
            logger.error("Organization VPN page has an invalid next link")  # WHY: report malformed pagination data.
            return False, None  # WHY: stop when the next page cannot be identified.
        if next_link in seen_next_links:  # WHY: a repeated URL can otherwise loop without end.
            logger.error("Organization VPN pagination repeated a next link")  # WHY: report the bounded stop.
            return False, None  # WHY: repeated links cannot prove a complete inventory.
        seen_next_links.add(next_link)  # WHY: remember each requested page URL for cycle detection.
        logger.info("Fetching the next organization VPN page")  # WHY: record each additional SDK request.
        next_response = mistapi.get_next(self.apisession, response)  # WHY: keep pagination on the SDK.
        logger.debug("Received the next organization VPN page")  # WHY: record completion before page validation.
        if next_response is None:  # WHY: a missing declared page means the inventory is truncated.
            logger.error("Organization VPN pagination ended before a declared page arrived")  # WHY: report truncation.
            return False, None  # WHY: do not expose earlier pages as a complete list.
        return True, next_response  # WHY: the caller validates this page before accepting its records.

    @staticmethod
    def _validated_vpn_page(response: Any) -> list[Any] | None:
        """Return VPN definitions only when one response page has valid status and data."""
        status_code = getattr(response, "status_code", None)  # WHY: require status evidence before reading the body.
        status_is_successful = isinstance(status_code, int) and 200 <= status_code < 300  # WHY: accept only 2xx.
        if not status_is_successful:  # WHY: an error body may contain data that is not a full inventory.
            logger.error("Organization VPN page failed with HTTP status %s", status_code)  # WHY: report the failure.
            return None  # WHY: prevent failed-page data from reaching the builder.
        response_data = getattr(response, "data", None)  # WHY: read page data only after status validation.
        has_sdk_error = isinstance(response_data, dict) and bool(response_data.get("error"))  # WHY: reject SDK errors.
        if has_sdk_error:  # WHY: the SDK logs truthy errors as failures.
            logger.error("Organization VPN page contains an error payload")  # WHY: report the SDK error shape.
            return None  # WHY: do not accept results from a response the SDK marks as an error.
        page_vpns = (
            response_data
            if isinstance(response_data, list)
            else (response_data.get("results") if isinstance(response_data, dict) else None)
        )  # WHY: accept SDK lists and Mist result dictionaries.
        if not isinstance(page_vpns, list):  # WHY: a missing results list cannot prove inventory completeness.
            logger.error("Organization VPN page has no valid results list")  # WHY: report the malformed page.
            return None  # WHY: malformed responses must not act like empty inventories.
        if not WanVpnBuilder._vpn_records_have_usable_names(page_vpns):  # WHY: every VPN needs a checkable name.
            return None  # WHY: an unnamed record can hide a duplicate.
        return page_vpns  # WHY: pass only validated VPN definitions to pagination.

    @staticmethod
    def _vpn_records_have_usable_names(vpn_records: list[Any]) -> bool:
        """Require every inventory record to provide a nonblank string name."""
        for vpn_record in vpn_records:  # WHY: one uncheckable VPN invalidates duplicate-name coverage.
            if not isinstance(vpn_record, dict):  # WHY: a non-object record cannot provide a reliable name.
                logger.error("Organization VPN page contains a non-object record")  # WHY: report malformed data.
                return False  # WHY: do not treat an unknown record as safe inventory.
            vpn_name = vpn_record.get("name")  # WHY: read the field used to reject duplicate names.
            if not isinstance(vpn_name, str) or not vpn_name.strip():  # WHY: missing or blank names are uncheckable.
                logger.error("Organization VPN record has no usable name")  # WHY: report incomplete duplicate data.
                return False  # WHY: stop before a new VPN can hide a collision.
        return True  # WHY: every record can participate in duplicate-name validation.

    def _create_vpn(self, vpn_body: dict[str, Any]) -> dict[str, Any] | None:  # WHY: isolated for tests.
        """Create VPN via API. Returns created VPN dict or None on failure."""
        try:  # WHY: convert any API error into a None return so run() can bail out cleanly.
            response = mistapi.api.v1.orgs.vpns.createOrgVpn(self.apisession, self.org_id, body=vpn_body)  # WHY: POST.
            created: dict[str, Any] = response.data if hasattr(response, "data") else response  # WHY: dual shape.
            logger.info("VPN created via API: %s", created.get("id", ""))  # WHY: id logged for correlation.
            return created  # WHY: caller extracts the new vpn id for profile updates.
        except Exception as error:  # WHY: keep broad because a VPN create write can have an unknown outcome.
            logging.exception(
                "Failed to create VPN after %s: %s",
                type(error).__name__,
                error,
            )  # WHY: capture the unknown write outcome in the operator log.
            logging.error("! Error creating VPN. Check API connectivity and input.")  # WHY: user-actionable feedback.
            return None  # WHY: caller treats None as "abort without further side-effects".

    # ------------------------------------------------------------------
    # User interaction — display helpers (US1 + US3)
    # ------------------------------------------------------------------

    def _display_existing_vpns(self, vpns: list[Any]) -> None:  # WHY: read-only display step before naming.
        """Display summary table of existing VPNs."""
        if not vpns:  # WHY: no rows to render -> print a friendly placeholder instead of an empty table.
            logger.warning(
                "\n  No existing VPN definitions in this organization."
            )  # WHY: prevent confusing blank output.
            return  # WHY: early return keeps the empty case simple.
        logger.warning(  # WHY: consolidated header lines emit as a single logging record for atomic output.
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
            logger.warning("  %-4d %-30s %-12s %6d", index, name, vpn_type, path_count)  # WHY: aligned row output.
        logger.warning("")  # WHY: blank line separates table from the next prompt.

    def _display_profile_list(self, profiles: list[Any]) -> None:  # WHY: shows inventory prior to role prompt.
        """Show numbered profile list with WAN/LAN interface counts."""
        logger.warning(  # WHY: consolidated header lines emit as a single logging record.
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
            logger.warning(
                "  %-4d %-30s %4d %4d%s", index, name, wan_count, lan_count, warning
            )  # WHY: aligned row output.
        logger.warning("")  # WHY: blank line separates table from the next prompt.

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
        logger.warning(  # WHY: consolidated preview header emits as a single logging record.
            "\n  === VPN Preview ===\n  Name: %s\n  Type: %s\n  Path Selection: %s\n  Total Paths: %d",
            vpn_name,
            vpn_body.get("type", ""),
            vpn_body.get("path_selection", {}),
            path_count,
        )
        if path_count > self.PATH_WARN_THRESHOLD:  # WHY: flag likely misconfiguration before it hits the API.
            logger.warning(  # WHY: multi-line warning is easier to scan than one long line.
                "  WARNING: Path count (%d) exceeds %d. This may indicate an unusually large configuration.",
                path_count,
                self.PATH_WARN_THRESHOLD,
            )

    @staticmethod
    def _print_preview_paths(paths: dict[str, Any]) -> None:  # WHY: pure printer for the path list.
        """Print the sorted list of generated path keys with pod annotations."""
        logger.warning("\n  Path Keys:")  # WHY: header labels the list that follows.
        for key in sorted(paths.keys()):  # WHY: sorted output is easier to eyeball during review.
            pod = paths[key].get("pod", "")  # WHY: default empty string keeps output stable for edge shapes.
            logger.warning("    %s (pod: %s)", key, pod)  # WHY: indent + annotation aids visual scanning.
        logger.warning("")  # WHY: blank line separates list from the next prompt.

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
                logger.warning("  Cancelled.")  # WHY: audible confirmation of cancellation.
                return None  # WHY: signal caller to abort the workflow.
            if outcome == "empty":  # WHY: reject blank so we always send a real value to the API.
                logger.warning("  VPN name cannot be empty.")  # WHY: guide operator to retype.
                continue  # WHY: re-prompt without leaving the loop.
            if outcome == "duplicate":  # WHY: prevent silent collision with an existing overlay.
                logger.warning("  VPN name '%s' already exists. Choose a different name.", name)  # WHY: actionable.
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
        logger.warning("  Assign roles to each profile (H=Hub, S=Spoke, K=Skip):")  # WHY: prompt legend for operators.
        assignments = [  # WHY: list comprehension pairs each profile with a role decision.
            self._prompt_role_for_profile(index, profile)  # WHY: per-profile prompt lives in its own helper.
            for index, profile in enumerate(profiles, start=1)
        ]
        if self._has_any_active(assignments):  # WHY: at least one Hub or Spoke required to build a VPN.
            return assignments  # WHY: return the fully-populated assignment list to the caller.
        return self._handle_all_skipped(profiles)  # WHY: dedicated branch handles retry/cancel messaging.

    def _prompt_role_for_profile(  # WHY: per-profile role loop. Keeps the caller's list-comp clean.
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
            logger.warning("    Please enter H (Hub), S (Spoke), or K (Skip).")  # WHY: guide operator on invalid input.

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
        logger.warning("  All profiles skipped. At least one must be Hub or Spoke.")  # WHY: explain why we retry.
        retry = (  # WHY: normalized y/N answer determines whether we loop.
            self._safe_input("  Try again? (y/N): ", context=CTX_RETRY_ROLES).strip().lower()
        )
        if retry == RETRY_YES:  # WHY: recurse to give the operator another chance.
            return self._prompt_role_assignments(profiles)  # WHY: same profiles, fresh set of role decisions.
        logger.warning("  Cancelled.")  # WHY: operator-visible confirmation of cancel decision.
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
        return assignments  # WHY: mutation happens in-place. Return for chaining convenience.

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
            if value is not None:  # WHY: parser returns None on invalid input. Error already printed.
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
            logger.warning(
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
        is_wan = True  # WHY: preserved from original behavior. WAN interfaces get cross-connects when hub.
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
            logger.info("Updated profile '%s' with vpn_paths for VPN '%s'", profile_name, vpn_name)  # WHY: audit.
            return True  # WHY: caller counts True as one success.
        except Exception as error:  # WHY: keep broad so one profile write does not abort the batch.
            logging.exception(
                "Failed to update profile '%s' after %s: %s",
                profile_name,
                type(error).__name__,
                error,
            )  # WHY: keep the per-profile write fault for support.
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
        existing.update(new_entries)  # WHY: additive. Never removes references to unrelated VPNs.
        port_config[interface_name]["vpn_paths"] = existing  # WHY: assign back so partial dicts get promoted.

    def _push_profile_update(self, profile_id: str, body: dict[str, Any]) -> None:  # WHY: PUT wrapper for tests.
        """Send the mutated profile body back to Mist (retained for external test patchability)."""
        # WHY: keep this method so downstream monkeypatches keep working. Body/id are validated here.
        if not isinstance(profile_id, str) or not profile_id:  # WHY: reject empty ids pre-HTTP.
            raise ValueError("profile_id must be a non-empty string")  # WHY: fast failure protects the org.
        if not isinstance(body, dict):  # WHY: mistapi expects a dict body. Caller mistakes get caught early.
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
        logger.warning(
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
            logger.warning("  Skipping profile updates.")  # WHY: operator-visible confirmation of the skip.
            return False  # WHY: caller returns without touching profiles.
        return True  # WHY: explicit y -> proceed with the profile-update loop.

    def _run_profile_updates(  # WHY: performs the actual per-profile update loop and tallies results.
        self, vpn_name: str, non_skip: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """Iterate assignments, calling _update_single_profile. Return (success, fail) tally."""
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
    def _fallback_input(prompt: str, **_kwargs: Any) -> str:  # WHY: default injected input. Used when no wrapper.
        """Fallback input when safe_input is not provided.

        Delegates to the canonical EOF-safe wrapper instead of a second hand-rolled
        input() (issue #452: clears CONV-INPUT, identical degrade-to-empty behavior).
        """
        from src.foundation.support.utils.input_utils import (
            InputUtils,
        )  # WHY: local import avoids any import cycle at module load.

        return InputUtils.safe_input(prompt, context=CTX_FALLBACK)  # WHY: EOF-safe; '' on EOF/interrupt.
