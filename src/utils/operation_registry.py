"""OperationRegistry -- centralised menu-option classification.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 13).
Replaces the inline ``unsafe_options`` and ``interactive_read_only_options``
dictionaries with a single authoritative source for --test/--testinteractive
routing.

Categories
----------
safe             Automated GET -- runs in ``--test``
interactive_safe Read-only but needs site/device -- runs in ``--testinteractive``
destructive      Modifies state -- always skipped
wip              Work in progress -- unstable
resource_intensive  Takes >1 h or hits rate limits
websocket        Requires WebSocket + interactive selection
continuous_loop  Never terminates without user stop
interactive      Needs user input not automatable
unregistered     Fail-closed fallback (feature 1020) -- returned by ``get`` for any option
                 absent from ``_REGISTRY``. A SKIP_CATEGORIES member, never written into
                 ``_REGISTRY`` by hand, so an unclassified option is never auto-run.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import logging  # WHY: warn when an option is not registered so drift is detectable in test logs.
from collections.abc import Iterable  # WHY: accept any iterable of option strings in the option-list helpers.

# WHY: `dict[str, str]` covers both {"category": ...} and {"category": ..., "skip_reason": ...} entries.
_OptionEntry = dict[str, str]


def _natural_option_sort_key(option: str) -> float:
    """Sort key that treats an ``aN`` suffix as a decimal so ``26a`` sorts just after ``26``.

    The legacy inline sort used ``float(x.replace("a", ".1"))``. Keeping the same key preserves
    the historical ordering the guardrail tests rely on.
    """
    return float(option.replace("a", ".1"))


def _sort_options(options: Iterable[str]) -> list[str]:
    """Return options in the historical natural order used by systematic-test runners."""
    return sorted(options, key=_natural_option_sort_key)


class OperationRegistry:
    """Centralised classification of all menu operations.

    Each entry maps a menu option string to a dict with ``category`` and optional
    ``skip_reason``.  ``get`` fails **closed** for unregistered options (feature 1020):
    it returns the ``unregistered`` category (a SKIP_CATEGORIES member) and emits a warning,
    so a forgotten/unclassified option is never auto-run in ``--test``/``--testinteractive``.
    """

    _REGISTRY: dict[str, _OptionEntry] = {
        # --- control --------------------------------------------------------
        "0": {"category": "interactive", "skip_reason": "Exit option"},
        # --- resource intensive ---------------------------------------------
        "19": {
            "category": "resource_intensive",
            "skip_reason": "Port-level statistics - extremely resource intensive (8+ hours)",
        },
        "59": {
            "category": "resource_intensive",
            "skip_reason": "Site configurations - hits API rate limits after 7+ hours",
        },
        # --- websocket ------------------------------------------------------
        "102": {
            "category": "websocket",
            "skip_reason": "WebSocket ping - requires interactive site and device selection",
        },
        "103": {
            "category": "websocket",
            "skip_reason": "WebSocket traceroute - requires interactive site and device selection",
        },
        "104": {
            "category": "websocket",
            "skip_reason": "WebSocket release DHCP - requires interactive site and device selection",
        },
        "105": {
            "category": "websocket",
            "skip_reason": "WebSocket cable test - requires interactive site and device selection",
        },
        "118": {
            "category": "websocket",
            "skip_reason": "WebSocket bounce port - requires interactive site and device selection",
        },
        "119": {
            "category": "websocket",
            "skip_reason": "WebSocket ARP - requires interactive site and device selection",
        },
        "120": {
            "category": "websocket",
            "skip_reason": "WebSocket service ping - requires interactive site and device selection",
        },
        "121": {
            "category": "websocket",
            "skip_reason": "WebSocket ARP command - requires interactive site and device selection",
        },
        # --- interactive (needs user input, not automatable) -----------------
        "134": {
            "category": "interactive",
            "skip_reason": "Packet capture - requires interactive configuration and site selection",
        },
        "135": {
            "category": "interactive",
            "skip_reason": "Packet capture - requires interactive configuration and MxEdge ID",
        },
        "136": {"category": "interactive", "skip_reason": "MSP export - requires interactive MSP selection"},
        "137": {
            "category": "interactive",
            "skip_reason": "Firmware upgrade status - requires interactive scope selection",
        },
        "138": {"category": "interactive", "skip_reason": "CSV comparison - requires interactive file selection"},
        "139": {
            "category": "interactive",
            "skip_reason": "Marvis troubleshooting - requires interactive option selection",
        },
        "92": {"category": "interactive_safe", "skip_reason": "Interactive site selection"},
        "93": {"category": "interactive_safe", "skip_reason": "Interactive site inventory browser"},
        "94": {"category": "interactive_safe", "skip_reason": "Interactive device stats viewer"},
        "95": {"category": "interactive_safe", "skip_reason": "Interactive device tests viewer"},
        "96": {"category": "interactive_safe", "skip_reason": "Interactive device config viewer"},
        "140": {"category": "interactive", "skip_reason": "Interactive CLI shell session"},
        "141": {"category": "interactive", "skip_reason": "Interactive TUI API browser - keyboard navigation required"},
        "148": {
            "category": "interactive",
            "skip_reason": "WLAN RADIUS timer management - requires interactive site selection",
        },
        "149": {
            "category": "interactive",
            "skip_reason": "Requires interactive site selection for WAN2 variable configuration",
        },
        "150": {
            "category": "interactive",
            "skip_reason": "Requires interactive template selection for configuration extraction",
        },
        "142": {
            "category": "interactive",
            "skip_reason": "Maps Manager - requires interactive Dash web server and browser",
        },
        "143": {"category": "interactive", "skip_reason": "Requires interactive login with email/password credentials"},
        "144": {"category": "interactive", "skip_reason": "MSP Inventory Export - requires MSP privileges via --login"},
        # --- interactive_safe (read-only, need site/device, automatable) -----
        "62": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "65": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "60": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "61": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "63": {"category": "interactive_safe", "skip_reason": "Requires site and device selection"},
        "64": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "69": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "66": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "67": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "68": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "73": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "74": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "75": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "76": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "77": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "78": {"category": "interactive_safe", "skip_reason": "Requires site and device selection"},
        "79": {"category": "interactive_safe", "skip_reason": "Requires site and client selection"},
        # --- continuous loop ------------------------------------------------
        "151": {"category": "continuous_loop", "skip_reason": "Continuous loop operation"},
        "152": {"category": "continuous_loop", "skip_reason": "Continuous data collection loop"},
        # --- resource intensive (file/support) ------------------------------
        "100": {
            "category": "resource_intensive",
            "skip_reason": "File processing operation - potentially resource intensive",
        },
        "101": {
            "category": "resource_intensive",
            "skip_reason": "Support package generation - potentially resource intensive",
        },
        # --- long-running exports (52-week time windows) --------------------
        "97": {"category": "resource_intensive", "skip_reason": "52-week device events export - long-running"},
        "98": {"category": "resource_intensive", "skip_reason": "52-week audit logs export - long-running"},
        "99": {"category": "resource_intensive", "skip_reason": "All-site gateway configs export - long-running"},
        # --- destructive ----------------------------------------------------
        "154": {"category": "destructive", "skip_reason": "DESTRUCTIVE: AP firmware upgrade operation"},
        "158": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Device reboot operation"},
        "161": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Virtual chassis conversion"},
        "162": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Virtual chassis conversion - bulk operation"},
        "175": {
            "category": "destructive",
            "skip_reason": "DESTRUCTIVE: Enhanced SSH Command Runner - runs arbitrary commands, "
            "requires interactive host and command input",
        },
        "176": {
            "category": "destructive",
            "skip_reason": "DESTRUCTIVE: SSH Runner by gateway template - runs arbitrary commands, "
            "requires interactive template and command input",
        },
        "155": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Switch firmware upgrade operation"},
        "156": {"category": "destructive", "skip_reason": "DESTRUCTIVE: SSR firmware upgrade operation"},
        "163": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Updates gateway templates with WAN2 variable"},
        "164": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Applies gateway template configuration"},
        "171": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Creates 137 test sites from CSV"},
        "172": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Creates country-specific RF templates"},
        "173": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Creates device profiles for AP models"},
        "174": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Assigns APs to device profiles"},
        "165": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clones gateway templates by state/country"},
        "166": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Configures WAN probe override on templates"},
        "167": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Configures WAN probe on device port overrides"},
        "157": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Org-level AP firmware upgrade"},
        "168": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Site Auto-Upgrade Configuration"},
        "169": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Site Analytics Configuration"},
        "170": {
            "category": "destructive",
            "skip_reason": "DESTRUCTIVE: Bulk RADIUS WLAN Configuration - modifies WLAN auth settings",
        },
        # Device Utility Commands (123-157)
        "123": {"category": "websocket", "skip_reason": "WebSocket traceroute - interactive site/device"},
        "106": {"category": "websocket", "skip_reason": "WebSocket OSPF neighbors - interactive gateway"},
        "107": {"category": "websocket", "skip_reason": "WebSocket OSPF interfaces - interactive gateway"},
        "108": {"category": "websocket", "skip_reason": "WebSocket OSPF database - interactive gateway"},
        "109": {"category": "websocket", "skip_reason": "WebSocket OSPF summary - interactive gateway"},
        "110": {"category": "websocket", "skip_reason": "WebSocket show sessions - interactive gateway"},
        "111": {"category": "websocket", "skip_reason": "WebSocket show service path - interactive gateway"},
        "112": {"category": "websocket", "skip_reason": "WebSocket BGP summary - interactive device"},
        "113": {"category": "websocket", "skip_reason": "WebSocket ARP table - interactive device"},
        "114": {"category": "websocket", "skip_reason": "WebSocket DHCP leases - interactive device"},
        "115": {"category": "websocket", "skip_reason": "WebSocket 802.1X table - interactive switch"},
        "116": {"category": "websocket", "skip_reason": "WebSocket EVPN database - interactive device"},
        "117": {"category": "websocket", "skip_reason": "WebSocket DNS resolution - interactive gateway"},
        "124": {"category": "interactive", "skip_reason": "Monitor traffic streaming - interactive port + Ctrl+C"},
        "125": {"category": "interactive", "skip_reason": "Run top streaming - interactive device + Ctrl+C"},
        "128": {"category": "interactive", "skip_reason": "Locate device - interactive device selection"},
        "129": {"category": "interactive", "skip_reason": "Unlocate device - interactive device selection"},
        "159": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Bounce port - disrupts traffic"},
        "122": {"category": "websocket", "skip_reason": "WebSocket cable test - interactive switch/port"},
        "160": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Reprovision - pushes fresh config"},
        "130": {"category": "interactive", "skip_reason": "Re-adopt device - interactive switch selection"},
        "131": {"category": "interactive", "skip_reason": "ZTP password - interactive device selection"},
        "132": {"category": "interactive", "skip_reason": "Config CLI commands - interactive switch"},
        "133": {"category": "interactive", "skip_reason": "Upload support file - interactive device/type"},
        "177": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear ARP cache"},
        "178": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear BGP routes"},
        "179": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear session"},
        "180": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear MAC table"},
        "181": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear BPDU errors"},
        "182": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear learned MACs from port"},
        "183": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clear policy hit count"},
        "184": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Release DHCP lease"},
        "185": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Release SSR DHCP lease"},
        "126": {"category": "interactive", "skip_reason": "Poll switch stats - interactive switch"},
        "127": {"category": "interactive", "skip_reason": "Create device snapshot - interactive switch"},
        "26": {"category": "safe"},
        "145": {"category": "interactive", "skip_reason": "Interactive multi-phase workflow with write-capable phases"},
        "89": {"category": "interactive_safe"},
        "90": {"category": "interactive_safe"},
        "91": {"category": "interactive_safe"},
        "146": {"category": "interactive", "skip_reason": "Interactive VPN pod management with API writes"},
        "147": {"category": "interactive", "skip_reason": "Interactive VPN builder with API writes"},
        "153": {
            "category": "resource_intensive",
            "skip_reason": "Bulk org data collection - runs 57 API calls, resource intensive",
        },
        "70": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "71": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "72": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "88": {"category": "interactive_safe", "skip_reason": "Requires AP model selection"},
        "25": {"category": "safe"},
        "196": {"category": "safe"},
        "197": {"category": "interactive_safe", "skip_reason": "Requires site + client + VLAN selection"},
        "198": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "199": {"category": "interactive_safe", "skip_reason": "Requires site + webhook selection"},
        "200": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "201": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "202": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "203": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "186": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Deletes all generated cache CSV files"},
        "58": {"category": "safe"},
        "187": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Creates config objects in destination org"},
        # Site Stats, Metrics & Channel Planning (178-185)
        "80": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "81": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "82": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "83": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "84": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "85": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "86": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        "23": {"category": "safe"},
        # HA Gateway Cluster Info (186)
        "87": {"category": "interactive_safe", "skip_reason": "Requires site selection"},
        # Org Device Inventory Summary (187) - fully automated, no user input required
        "13": {"category": "safe"},
        # ------------------------------------------------------------------
        # Feature 1020 (safe --test clean run): explicit classification of the
        # 60 previously-unregistered menu_actions keys. Each category was
        # decided from the handler's real read-only versus state-changing
        # behavior (see research.md R1). Read-only exporters are "safe";
        # heavy sweeps are "resource_intensive". Write/create operations are
        # "destructive". Ticket viewing prompts for a selection so it is
        # "interactive". This removes reliance on the fail-closed default for
        # any currently-reachable option.
        # ------------------------------------------------------------------
        # --- read-only org/site/device/template/admin exports (safe) --------
        "1": {"category": "safe"},  # OrgSiteExporter.sites - read-only site list export.
        "2": {"category": "safe"},  # OrgSiteExporter.sites_with_location - read-only export.
        "3": {"category": "safe"},  # OrgSiteExporter.sites_list_api - read-only list-API export.
        "4": {"category": "safe"},  # Guest users export - read-only CSV export.
        "5": {"category": "safe"},  # OrgExportUtils.e911_report - read-only report export.
        "6": {"category": "safe"},  # Site config analysis scan - read-only deviation report.
        "7": {"category": "safe"},  # Site inventory health analysis - read-only report.
        "8": {"category": "safe"},  # OrgInventoryExporter.inventory - read-only export.
        "9": {"category": "safe"},  # OrgInventoryExporter.devices - read-only export.
        "10": {"category": "safe"},  # OrgInventoryExporter.devices_with_site_info - read-only export.
        "11": {"category": "safe"},  # OrgInventoryExporter.gateways_with_site_info - read-only export.
        "12": {"category": "safe"},  # OrgInventoryExporter.combined_inventory_with_site_info - read-only.
        "15": {"category": "safe"},  # OrgDeviceStatsExporter.device_stats - read-only export.
        "16": {"category": "safe"},  # OrgDeviceStatsExporter.vpn_peer_stats - read-only export.
        "17": {"category": "safe"},  # OrgDeviceStatsExporter.switch_vc_stats - read-only export.
        "20": {"category": "safe"},  # OrgAlarmEventExporter.alarms - read-only export.
        "21": {"category": "safe"},  # OrgAlarmEventExporter.device_events - read-only export.
        "22": {"category": "safe"},  # Audit logs export - read-only export.
        "24": {"category": "safe"},  # OrgClientSecurityExporter.security_events - read-only export.
        "27": {"category": "safe"},  # OrgClientSecurityExporter.wireless_clients - read-only export.
        "28": {"category": "safe"},  # OrgClientSecurityExporter.wired_clients - read-only export.
        "29": {"category": "safe"},  # OrgClientSecurityExporter.rogue_clients - read-only export.
        "30": {"category": "safe"},  # OrgClientSecurityExporter.rogue_aps - read-only export.
        "31": {"category": "safe"},  # Gateway management overlay IPs - read-only export.
        "32": {"category": "safe"},  # Gateway templates - read-only export.
        "33": {"category": "safe"},  # GatewayTestExporter.synthetic_tests - read-only export.
        "34": {"category": "safe"},  # GatewayTestExporter.test_results_by_site - read-only export.
        "35": {"category": "safe"},  # WAN override compliance report - read-only (verified: WanOverrideWalker.walk).
        "36": {"category": "safe"},  # WAN port IP conflict analysis - read-only (verified: analyze + export report).
        "37": {"category": "safe"},  # OrgTemplateExporter.all_templates - read-only export.
        "38": {"category": "safe"},  # OrgTemplateExporter.network_templates - read-only export.
        "39": {"category": "safe"},  # OrgTemplateExporter.rf_templates - read-only export.
        "40": {"category": "safe"},  # OrgTemplateExporter.ap_templates - read-only export.
        "41": {"category": "safe"},  # OrgTemplateExporter.switch_templates - read-only export.
        "42": {"category": "safe"},  # OrgAdminExporter.licenses - read-only export.
        "43": {"category": "safe"},  # OrgAdminExporter.usage - read-only export.
        "44": {"category": "safe"},  # OrgConfigExporter.psks - read-only export.
        "45": {"category": "safe"},  # OrgConfigExporter.webhooks - read-only export.
        "46": {"category": "safe"},  # OrgConfigExporter.wlans - read-only export.
        "47": {"category": "safe"},  # OrgAdminExporter.api_tokens - read-only export.
        "48": {"category": "safe"},  # OrgAdminExporter.admins - read-only export.
        "49": {"category": "safe"},  # OrgAdminExporter.sso - read-only export.
        "50": {"category": "safe"},  # OrgConfigExporter.mx_edges - read-only export.
        "51": {"category": "safe"},  # OrgExportUtils.sle_metrics - read-only export.
        "52": {"category": "safe"},  # OrgExportUtils.sites_sle_summary - read-only export.
        "53": {"category": "safe"},  # OrgExportUtils.insight_metrics - read-only export.
        "54": {"category": "safe"},  # Const definitions export - read-only export.
        "55": {"category": "safe"},  # OrgExportUtils.ospf_stats - read-only export.
        "56": {"category": "safe"},  # OrgExportUtils.jsi_pbn - read-only export.
        "57": {"category": "safe"},  # OrgExportUtils.jsi_sirt - read-only export.
        "204": {"category": "safe"},  # OrgExportUtils.jsi_assets - read-only export (spec 865 / #1373).
        "205": {"category": "safe"},  # OrgExportUtils.mist_edge_events - read-only export (spec 866 / #1374).
        "188": {"category": "safe"},  # OrgTicketManager.list_tickets - read-only ticket list export (no selection).
        "193": {"category": "safe"},  # OrgTicketManager.export_ticket_details - read-only (exports all, no selection).
        "195": {"category": "safe"},  # Site address audit - self-described READ-ONLY report.
        # --- heavy sweeps (resource_intensive) ------------------------------
        "14": {
            "category": "resource_intensive",
            "skip_reason": "Virtual chassis conversion status for all switches - resource intensive",
        },
        "18": {
            "category": "resource_intensive",
            "skip_reason": "Gateway device stats with freshness check - resource intensive",
        },
        # --- ticket write operations (destructive) --------------------------
        "189": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Creates a new organization support ticket"},
        "190": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Adds a comment to a live support ticket"},
        "191": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Updates fields on an existing support ticket"},
        "194": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clone Device Config to Gateway Template"},
        "206": {
            "category": "destructive",
            "skip_reason": "DESTRUCTIVE: Modifies org synthetic_test.custom_probes",
        },
        "207": {
            "category": "destructive",
            "skip_reason": (
                "DESTRUCTIVE: Menu 207 mutates AP-to-device-profile bindings across every "
                "site in the selected organization; requires a live Mist test tenant."
            ),
        },
        "208": {
            "category": "destructive",
            "skip_reason": (
                "DESTRUCTIVE: Menu 208 reverts a prior AP-to-device-profile migration by "
                "reassigning each listed AP back to its original device profile; "
                "requires the backup file written by menu 207."
            ),
        },
        # --- ticket viewer (interactive selection) --------------------------
        "192": {"category": "interactive", "skip_reason": "View support ticket - requires interactive selection"},
    }

    # Wave 1 deterministic baseline map used by routing guardrail tests.
    # This remains intentionally small and representative for compliance checks.
    WAVE1_ENTRY_ROUTING_BASELINE: dict[str, str] = {
        "102": "websocket",
        "62": "interactive_safe",
        "97": "resource_intensive",
        "120": "websocket",
        "154": "destructive",
        "158": "destructive",
        "156": "destructive",
        "141": "interactive",
        "26": "safe",
        "58": "safe",
        "187": "destructive",
    }

    # Wave 1 deterministic safety-boundary baseline used by classification guardrails.
    # Feature 1020: the former "9999" sentinel was a key absent from menu_actions that only
    # read True under the old fail-open default. Replaced with real safe key "13" now that the
    # default is fail-closed (an unregistered key like "9999" is now correctly is_safe()==False).
    WAVE1_SAFETY_CLASSIFICATION_BASELINE: dict[str, list[str]] = {
        "safe_true": ["26", "58", "13"],
        "safe_false": ["120", "154", "158", "155", "156", "187"],
        "interactive_safe_true": ["62"],
        "interactive_safe_false": ["154", "141", "187"],
        "destructive_markers": ["154", "158", "155", "156", "171", "159", "187"],
    }

    # Categories that are safe for --test (fully automated, no user input)
    SAFE_CATEGORIES = frozenset({"safe"})
    # Categories that are safe for --testinteractive (need site but automatable)
    INTERACTIVE_SAFE_CATEGORIES = frozenset({"interactive_safe"})
    # Categories always skipped
    SKIP_CATEGORIES = frozenset(
        {
            "destructive",
            "wip",
            "resource_intensive",
            "websocket",
            "continuous_loop",
            "interactive",
            # Feature 1020: fail-closed fallback category for any option absent from _REGISTRY.
            # Membership here excludes it from both SAFE_CATEGORIES and INTERACTIVE_SAFE_CATEGORIES,
            # so an unclassified option can never run in --test or --testinteractive.
            "unregistered",
        }
    )

    @classmethod
    def get(cls, option: str) -> _OptionEntry:
        """Return classification for *option*.

        Registered options return their explicit entry. Unregistered options fail **closed**:
        they return the ``unregistered`` category (a SKIP_CATEGORIES member) rather than defaulting
        to ``safe``, so an unclassified/forgotten menu option is never auto-run (feature 1020).
        """
        entry = cls._REGISTRY.get(str(option))
        if entry is not None:
            return entry
        # WHY: fail closed - an unknown option must never be treated as safe-to-run automatically.
        logging.warning(
            "OperationRegistry: option %s not registered, failing closed as 'unregistered' (not run)", option
        )
        return {
            "category": "unregistered",
            "skip_reason": "Unregistered menu option - fail-closed pending classification",
        }

    @classmethod
    def is_safe(cls, option: str) -> bool:
        """True if *option* can run in ``--test`` mode."""
        return cls.get(option)["category"] in cls.SAFE_CATEGORIES

    @classmethod
    def is_interactive_safe(cls, option: str) -> bool:
        """True if *option* can run in ``--testinteractive`` mode."""
        return cls.get(option)["category"] in cls.INTERACTIVE_SAFE_CATEGORIES

    @classmethod
    def skip_reason(cls, option: str) -> str:
        """Return skip reason or empty string."""
        return cls.get(option).get("skip_reason", "")

    @classmethod
    def skip_category(cls, option: str) -> str:
        """Return skip category name."""
        return cls.get(option)["category"]

    @classmethod
    def safe_options(cls, all_options: Iterable[str]) -> list[str]:
        """Return sorted list of options safe for ``--test``."""
        return _sort_options(o for o in all_options if cls.is_safe(o))

    @classmethod
    def interactive_safe_options(cls, all_options: Iterable[str]) -> list[str]:
        """Return sorted list of options safe for ``--testinteractive``."""
        return _sort_options(o for o in all_options if cls.is_interactive_safe(o))

    @classmethod
    def unsafe_options(cls, all_options: Iterable[str]) -> list[str]:
        """Return sorted list of options NOT safe for ``--test``."""
        return _sort_options(o for o in all_options if not cls.is_safe(o))

    @classmethod
    def registered_options(cls) -> set[str]:
        """Return the set of all explicitly-registered option keys.

        Feature 1020: the exhaustive menu/registry coverage guardrail asserts this is a superset of
        every ``MistHelper.menu_actions`` key, so any menu addition without a matching classification
        fails CI immediately instead of silently falling through to the fail-closed default.
        """
        return set(cls._REGISTRY.keys())

    @classmethod
    def wave1_entry_routing_baseline(cls) -> dict[str, str]:
        """Return a copy of the Wave 1 routing baseline map for deterministic tests."""
        return dict(cls.WAVE1_ENTRY_ROUTING_BASELINE)

    @classmethod
    def wave1_safety_classification_baseline(cls) -> dict[str, list[str]]:
        """Return a copy of the Wave 1 safety classification baseline for deterministic tests."""
        return {key: list(values) for key, values in cls.WAVE1_SAFETY_CLASSIFICATION_BASELINE.items()}
