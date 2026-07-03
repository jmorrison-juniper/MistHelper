"""Clear / reset command cluster for :mod:`src.device.utility_commands`.

Owns the 9 destructive clear/reset commands (``clear_arp_cache``,
``clear_bgp_routes``, ``clear_session``, ``clear_mac_table``,
``clear_bpdu_error``, ``clear_learned_macs``, ``clear_policy_hit_count``,
``release_dhcp_lease``, ``release_dhcp_ssr``) plus the two private
helpers (``_build_clear_session_body``, ``_confirm_clear_all_sessions``)
they depend on. Splitting these off
:class:`~src.device.utility_commands.DeviceUtilityCommands` shrinks the
parent below the STRUCT-LENGTH budget and isolates the typed-``CLEAR``
confirmation flow in one focused module.

The parent binds an instance as ``self._clear`` and its ``__getattr__``
proxies unknown lookups here so shared state (dependency callables,
mistapi module) stays transparent. Peer-method calls inside this cluster
route through ``self._method(...)`` and the cluster's ``__getattr__``
delegates to the parent, which resolves via its own ``__getattr__`` to
sibling clusters when needed. Body-builder helpers stay pure so each
public command reads as ``select -> build -> confirm -> dispatch`` at
cyclomatic complexity <= 5.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: exception-level logging when API calls fail
from typing import Any  # WHY: Any narrows the SDK response type

import mistapi  # WHY: direct SDK access mirrors parent module usage

from ._utility_commands_cluster import _ClusterBase  # WHY: shared proxy base


class _UtilityCommandsClear(_ClusterBase):  # WHY: cluster wrapper mirroring earlier phase clusters
    """Wrapper class holding the 9 clear/reset commands and 2 helpers."""

    # ------------------------------------------------------------------
    # clear_arp_cache
    # ------------------------------------------------------------------

    def clear_arp_cache(self) -> None:  # WHY: menu 147 destructive ARP-clear entry
        """Menu 147: Clear ARP cache (typed 'CLEAR' confirmation)."""
        logging.info("Menu #147: Clear ARP Cache")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_arp")  # WHY: pick site + switch/gateway
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body = self._build_arp_body(site_id, device_id)  # WHY: gather ARP filter inputs
        # WHY: typed-CLEAR gate below rejects mistypes to prevent accidental wipes
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear ARP cache: ",
            "CLEAR",
            "clear_arp",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_arp_clear(site_id, device_id, body)  # WHY: run API + report

    def _build_arp_body(self, site_id: str, device_id: str) -> dict[str, Any]:  # WHY: collect optional ARP filters
        """Gather ARP-clear filter inputs (node, port, ip) from the operator."""
        body: dict[str, Any] = {}  # WHY: seed empty; add only supplied filters
        self._add_node_port_filters(body, site_id, device_id, "clear_arp_node")  # WHY: shared helper (dedupes vs show)
        ip_addr = self._safe_input_fn(
            "IP address to clear (Enter for all): ",
            context="clear_arp_ip",
        )  # WHY: optional target IP
        if ip_addr:  # WHY: skip when operator wants all IPs
            body["ip"] = ip_addr  # WHY: constrain to single IP entry
        return body  # WHY: hand assembled filter body to invoker

    def _invoke_arp_clear(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:  # WHY: isolate SDK call
        """Call the SSR ARP-clear SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.clearSiteSsrArpCache(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send ARP-clear request
            self._print_api_result(
                response,
                "ARP cache cleared.",
                "Clear ARP cache failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear ARP cache failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear ARP cache failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # clear_bgp_routes
    # ------------------------------------------------------------------

    def clear_bgp_routes(self) -> None:  # WHY: menu 148 destructive BGP-clear entry
        """Menu 148: Clear BGP routes (typed 'CLEAR' confirmation)."""
        logging.info("Menu #148: Clear BGP Routes")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_bgp", "gateway")  # WHY: gateway-only op
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body = self._build_bgp_body()  # WHY: gather required + optional BGP filters
        if body is None:  # WHY: missing neighbor -> already messaged
            return  # WHY: bail without confirming when input invalid
        # WHY: typed-CLEAR gate below rejects mistypes to prevent accidental wipes
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear BGP routes: ",
            "CLEAR",
            "clear_bgp",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_bgp_clear(site_id, device_id, body)  # WHY: run API + report

    def _build_bgp_body(self) -> dict[str, Any] | None:  # WHY: encapsulate required + optional prompts
        """Gather BGP-clear inputs. Returns None when the required neighbor is missing."""
        neighbor = self._safe_input_fn(
            "BGP neighbor IP (required): ",
            context="clear_bgp_neighbor",
            allow_empty=False,
        )  # WHY: neighbor is mandatory
        if not neighbor:  # WHY: guard against empty submission
            print("! Neighbor IP is required.")  # WHY: signal cancel reason
            return None  # WHY: propagate missing-required signal to caller
        body: dict[str, Any] = {"neighbor": neighbor}  # WHY: seed with required field
        self._maybe_add_bgp_type(body)  # WHY: optional direction filter
        # WHY: optional VRF scope narrows clear to a single VRF instance
        self._maybe_add_input(body, "vrf", "VRF (Enter to skip): ", "clear_bgp_vrf")
        # WHY: optional VC node targets one member of a virtual chassis
        self._maybe_add_input(
            body,
            "node",
            "Node (node0/node1, Enter to skip): ",
            "clear_bgp_node",
        )
        return body  # WHY: hand assembled filter body to invoker

    def _maybe_add_bgp_type(self, body: dict[str, Any]) -> None:  # WHY: validate BGP direction before add
        """Prompt for BGP direction and validate to 'in'/'out' before adding."""
        bgp_type = self._safe_input_fn(
            "Type (in/out, Enter for both): ",
            context="clear_bgp_type",
        )  # WHY: optional direction
        if bgp_type and bgp_type.lower() in ("in", "out"):  # WHY: validate to known values only
            body["type"] = bgp_type.lower()  # WHY: normalize case

    def _maybe_add_input(  # WHY: shared optional-input setter for BGP body
        self,
        body: dict[str, Any],
        key: str,
        prompt: str,
        context: str,
    ) -> None:
        """Read one optional input and only set ``body[key]`` when non-empty."""
        value = self._safe_input_fn(prompt, context=context)  # WHY: EOF-safe optional prompt
        if value:  # WHY: skip when operator submits empty
            body[key] = value  # WHY: only include supplied filters

    def _invoke_bgp_clear(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:  # WHY: isolate SDK call
        """Call the SSR BGP-clear SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.clearSiteSsrBgpRoutes(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send BGP-clear request
            self._print_api_result(
                response,
                "BGP routes cleared.",
                "Clear BGP routes failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear BGP routes failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear BGP routes failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # clear_session
    # ------------------------------------------------------------------

    def clear_session(self) -> None:  # WHY: menu 149 destructive session-clear entry
        """Menu 149: Clear session on SSR/SRX gateway."""
        logging.info("Menu #149: Clear Session")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_session", "gateway")  # WHY: gateway-only op
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body = self._build_clear_session_body()  # WHY: gather session filter
        if body is None:  # WHY: cancelled at CLEAR-ALL prompt
            return  # WHY: honor operator's cancel decision
        # WHY: typed-CLEAR gate below rejects mistypes to prevent accidental wipes
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear session(s): ",
            "CLEAR",
            "clear_session",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_session_clear(site_id, device_id, body)  # WHY: run API + report

    def _invoke_session_clear(
        self,
        site_id: str,
        device_id: str,
        body: dict[str, Any],
    ) -> None:  # WHY: isolate SDK call
        """Call the session-clear SDK and route errors through the shared handler."""
        try:  # WHY: guard SDK/transport failures
            response = mistapi.api.v1.sites.devices.clearSiteDeviceSession(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send session-clear request
            self._print_api_result(
                response,
                "Session(s) cleared.",
                "Clear session failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear session failed: %s", error)  # WHY: audit failure with stack
            self._handle_clear_session_error(error)  # WHY: shared 400-aware error UX

    def _build_clear_session_body(self) -> dict[str, Any] | None:  # WHY: gather + validate session filters
        """Gather clear-session parameters from user input, or return None on cancel."""
        body: dict[str, Any] = {}  # WHY: seed empty; add only supplied filters
        service_name = self._safe_input_fn(
            "Service name to clear (Enter to skip): ",
            context="clear_session_service_name",
        )  # WHY: optional service filter
        session_ids_input = self._safe_input_fn(
            "Session IDs to clear (comma-separated, Enter to skip): ",
            context="clear_session_ids",
        )  # WHY: optional session-id list
        if not self._apply_session_filter(body, service_name, session_ids_input):  # WHY: honor CLEAR-ALL cancel
            return None  # WHY: cancelled at CLEAR-ALL prompt
        # WHY: optional VC node targets one member of a virtual chassis
        self._maybe_add_input(
            body,
            "node",
            "Node (node0/node1, Enter to skip): ",
            "clear_session_node",
        )
        return body  # WHY: hand assembled filter body to invoker

    def _apply_session_filter(  # WHY: pick which filter (service/ids/all) to apply
        self,
        body: dict[str, Any],
        service_name: str,
        session_ids_input: str,
    ) -> bool:
        """Apply session filters. Returns False when operator cancels the CLEAR-ALL prompt."""
        if service_name:  # WHY: prefer service filter when supplied
            body["service_name"] = service_name  # WHY: constrain to one service
            return True  # WHY: filter applied -> caller may proceed
        if session_ids_input:  # WHY: fall back to explicit session id list
            _assign_session_ids(body, session_ids_input)  # WHY: parse comma list + assign
            return True  # WHY: filter applied -> caller may proceed
        return self._confirm_clear_all_sessions()  # WHY: no filter -> confirm CLEAR ALL

    def _confirm_clear_all_sessions(self) -> bool:  # WHY: extra guard for unfiltered clear
        """Confirm clearing ALL sessions when no filter was provided."""
        confirm_all = self._safe_input_fn(
            "No service name or session IDs provided."
            " This may attempt to clear ALL sessions."
            " Type 'CLEAR ALL' to proceed"
            " or press Enter to cancel: ",
            context="clear_session_confirm_all",
        )  # WHY: extra guard against unintended full clears
        if confirm_all != "CLEAR ALL":  # WHY: exact keyword required
            print("Cancelled: No service name or session IDs provided.")  # WHY: signal cancel reason
            return False  # WHY: operator declined CLEAR-ALL
        return True  # WHY: operator explicitly opted into CLEAR-ALL

    # ------------------------------------------------------------------
    # clear_mac_table / clear_bpdu_error / clear_learned_macs
    # ------------------------------------------------------------------

    def clear_mac_table(self) -> None:  # WHY: menu 150 destructive MAC-table clear entry
        """Menu 150: Clear MAC table (typed 'CLEAR' confirmation)."""
        logging.info("Menu #150: Clear MAC Table")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_mac_table")  # WHY: switch/gateway op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body: dict[str, Any] = {}  # WHY: seed empty; only add optional node
        self._maybe_add_input(body, "node", "Node (node0/node1, Enter to skip): ", "clear_mac_node")
        if not self._confirm_destructive("Type 'CLEAR' to clear MAC table: ", "CLEAR", "clear_mac_table"):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_mac_clear(site_id, device_id, body)  # WHY: run API + report

    def _invoke_mac_clear(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:
        """Call the MAC-table-clear SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.clearSiteDeviceMacTable(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send MAC-table clear request
            self._print_api_result(
                response,
                "MAC table cleared.",
                "Clear MAC table failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear MAC table failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear MAC table failed: {error}")  # WHY: surface error to operator

    def clear_bpdu_error(self) -> None:
        """Menu 151: Clear BPDU errors on switch."""
        logging.info("Menu #151: Clear BPDU Errors")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_bpdu_error", "switch")  # WHY: switch-only
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        port_id = self._select_port_optional(site_id, device_id)  # WHY: optional port target
        port_target = port_id if port_id else "all"  # WHY: default to all ports
        if not self._confirm_destructive(
            f"Type 'CLEAR' to clear BPDU errors on port {port_target}: ",
            "CLEAR",
            "clear_bpdu_error",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_bpdu_clear(site_id, device_id, {"port": port_target})  # WHY: run API + report

    def _invoke_bpdu_clear(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:
        """Call the BPDU-clear SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.clearBpduErrorsFromPortsOnSwitch(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send BPDU-clear request
            self._print_api_result(
                response,
                "BPDU errors cleared.",
                "Clear BPDU errors failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear BPDU errors failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear BPDU errors failed: {error}")  # WHY: surface error to operator

    def clear_learned_macs(self) -> None:
        """Menu 152: Clear learned MACs from switch port."""
        logging.info("Menu #152: Clear Learned MACs")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_macs", "switch")  # WHY: switch-only
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        port_with_unit = self._resolve_learned_mac_port(site_id, device_id)  # WHY: pick required port
        if not port_with_unit:  # WHY: empty selection -> already messaged
            return
        if not self._confirm_destructive(
            f"Type 'CLEAR' to clear learned MACs on port {port_with_unit}: ",
            "CLEAR",
            "clear_macs",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_learned_mac_clear(site_id, device_id, port_with_unit)  # WHY: run API + report

    def _resolve_learned_mac_port(self, site_id: str, device_id: str) -> str | None:
        """Pick a required port and normalize ``xe-0/0/0`` -> ``xe-0/0/0.0``."""
        port_id = self._select_port_from_device(site_id, device_id)  # WHY: required port picker
        if not port_id:  # WHY: cancelled or empty selection
            print("! Port selection is required for clearing learned MACs.")  # WHY: signal cancel
            return None
        return port_id if "." in port_id else f"{port_id}.0"  # WHY: SDK requires .unit suffix

    def _invoke_learned_mac_clear(self, site_id: str, device_id: str, port_with_unit: str) -> None:
        """Call the learned-MAC-clear SDK and report success/failure."""
        body: dict[str, Any] = {"ports": [port_with_unit]}  # WHY: single-port list
        try:
            response = mistapi.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send learned-MAC-clear request
            self._print_api_result(
                response,
                f"Learned MACs cleared from port {port_with_unit}.",
                "Clear learned MACs failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear learned MACs failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear learned MACs failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # clear_policy_hit_count
    # ------------------------------------------------------------------

    def clear_policy_hit_count(self) -> None:
        """Menu 153: Clear policy hit count on SSR."""
        # TODO: Returns 400 on DC-West SSR120. Investigate API
        # requirements - may need node param or be unsupported.
        logging.info("Menu #153: Clear Policy Hit Count")  # WHY: audit menu entry
        selection = self._select_site_and_device("clear_policy_hit_count", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body: dict[str, Any] = {}  # WHY: seed empty; only add optional node
        self._maybe_add_input(body, "node", "Node (node0/node1, Enter to skip): ", "clear_policy_node")
        if not self._confirm_destructive(
            "Type 'CLEAR' to clear policy hit count: ",
            "CLEAR",
            "clear_policy_hit_count",
        ):
            return  # WHY: typed-keyword gate aborts on cancel
        self._invoke_policy_clear(site_id, device_id, body)  # WHY: run API + report

    def _invoke_policy_clear(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:
        """Call the policy-hit-count-clear SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.clearSiteDevicePolicyHitCount(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send policy-hit-count-clear request
            self._print_api_result(
                response,
                "Policy hit count cleared.",
                "Clear policy hit count failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Clear policy hit count failed: %s", error)  # WHY: audit failure with stack
            print(f"! Clear policy hit count failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # release_dhcp_lease / release_dhcp_ssr
    # ------------------------------------------------------------------

    def release_dhcp_lease(self) -> None:
        """Menu 154: Release DHCP lease on switch/gateway."""
        logging.info("Menu #154: Release DHCP Lease")  # WHY: audit menu entry
        selection = self._select_site_and_device("release_dhcp")  # WHY: switch/gateway op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body = self._build_dhcp_body(site_id, device_id, "release_dhcp_node")  # WHY: gather port + node
        if body is None:  # WHY: port cancelled -> already messaged
            return
        if not self._confirm_dhcp_release(body["port_id"], "release_dhcp"):  # WHY: y/N gate
            return
        self._invoke_dhcp_release(site_id, device_id, body)  # WHY: run API + report

    def _build_dhcp_body(
        self,
        site_id: str,
        device_id: str,
        node_context: str,
    ) -> dict[str, Any] | None:
        """Build DHCP-release body from a required port pick + optional node."""
        port_id = self._select_port_from_device(site_id, device_id)  # WHY: required port picker
        if not port_id:  # WHY: cancelled or empty selection
            print("! Port selection is required.")  # WHY: signal cancel reason
            return None
        body: dict[str, Any] = {"port_id": port_id}  # WHY: required field first
        self._maybe_add_input(body, "node", "Node (node0/node1, Enter to skip): ", node_context)
        return body

    def _confirm_dhcp_release(self, target: str, context: str) -> bool:
        """Confirm the DHCP-release with a y/N prompt on ``target``."""
        confirm = self._safe_input_fn(
            f"Release DHCP lease on port {target}? (y/N): ",
            context=context,
        )  # WHY: destructive-op confirmation
        if confirm.lower() != "y":  # WHY: anything other than 'y' aborts
            print("! Operation cancelled.")  # WHY: acknowledge cancel
            return False
        return True

    def _invoke_dhcp_release(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:
        """Call the DHCP-release SDK (switch/gateway) and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.releaseSiteDeviceDhcpLease(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send DHCP-release request
            self._print_api_result(
                response,
                f"DHCP lease released on port {body['port_id']}.",
                "Release DHCP lease failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Release DHCP lease failed: %s", error)  # WHY: audit failure with stack
            print(f"! Release DHCP lease failed: {error}")  # WHY: surface error to operator

    def release_dhcp_ssr(self) -> None:
        """Menu 155: Release DHCP lease on SSR/SRX."""
        logging.info("Menu #155: Release DHCP Lease (SSR)")  # WHY: audit menu entry
        selection = self._select_site_and_device("release_dhcp_ssr", "gateway")  # WHY: gateway-only
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        body = self._build_ssr_dhcp_body(site_id, device_id)  # WHY: gather interface + node
        if body is None:  # WHY: interface cancelled -> already messaged
            return
        if not self._confirm_dhcp_release_iface(body["port_id"]):  # WHY: y/N gate on interface
            return
        self._invoke_ssr_dhcp_release(site_id, device_id, body)  # WHY: run API + report

    def _build_ssr_dhcp_body(
        self,
        site_id: str,
        device_id: str,
    ) -> dict[str, Any] | None:
        """Build SSR DHCP-release body from a required interface pick + optional node."""
        port_id = self._select_interface_from_device(site_id, device_id)  # WHY: SSR uses named ifaces
        if not port_id:  # WHY: cancelled or empty selection
            print("! Network interface is required.")  # WHY: signal cancel reason
            return None
        body: dict[str, Any] = {"port_id": port_id}  # WHY: required field first
        self._maybe_add_input(body, "node", "Node (node0/node1, Enter to skip): ", "release_dhcp_ssr_node")
        return body

    def _confirm_dhcp_release_iface(self, iface: str) -> bool:
        """Confirm the SSR DHCP-release with a y/N prompt on ``iface``."""
        confirm = self._safe_input_fn(
            f"Release DHCP lease on interface {iface}? (y/N): ",
            context="release_dhcp_ssr",
        )  # WHY: destructive-op confirmation
        if confirm.lower() != "y":  # WHY: anything other than 'y' aborts
            print("! Operation cancelled.")  # WHY: acknowledge cancel
            return False
        return True

    def _invoke_ssr_dhcp_release(self, site_id: str, device_id: str, body: dict[str, Any]) -> None:
        """Call the SSR DHCP-release SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.releaseSiteSsrDhcpLease(
                self._apisession,
                site_id,
                device_id,
                body,
            )  # WHY: send SSR DHCP-release request
            self._print_api_result(
                response,
                f"SSR DHCP lease released on interface {body['port_id']}.",
                "Release SSR DHCP lease failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Release SSR DHCP lease failed: %s", error)  # WHY: audit failure with stack
            print(f"! Release SSR DHCP lease failed: {error}")  # WHY: surface error to operator


def _assign_session_ids(body: dict[str, Any], raw: str) -> None:
    """Parse a comma-separated session-id string and set ``body['session_ids']`` when non-empty."""
    session_ids = [entry.strip() for entry in raw.split(",") if entry.strip()]  # WHY: drop empties
    if session_ids:  # WHY: guard against pure whitespace/commas
        body["session_ids"] = session_ids  # WHY: only include when at least one id survives
