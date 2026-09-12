"""Static menu operation descriptions for the web portal.

Provides operation metadata without requiring MistHelper imports
or API authentication. Used by wsgi.py to populate the operations
list when the portal starts independently from MistHelper CLI.
"""

MENU_DESCRIPTIONS = {
    "1": "Export all organization alarms from the past day",
    "2": "Export all device events from the past 24 hours",
    "3": "Export audit logs for the organization (last 24 hours)",
    "4": "Export gateway management overlay IPs grouped by template",
    "5": "Show MAC table on switch device via WebSocket",
    "6": "Show forwarding table on gateway device via WebSocket",
    "7": "Show routing table on switches via WebSocket",
    "8": "Show SSR/SRX routing table via dedicated API",
    "9": "Start Site Packet Capture",
    "10": "Start Organization Packet Capture",
    "11": "Export a list of all sites in the organization",
    "12": "Export the full inventory of devices in the organization",
    "13": "Export statistics for all devices in the organization",
    "14": "Export port-level statistics for switches and gateways",
    "15": "Export VPN peer path statistics for the organization",
    "16": "Export synthetic test results for all gateways",
    "17": "Export a list of all devices in the organization",
    "18": "Export configuration settings for all sites",
    "19": "Export all synthetic test results for gateways",
    "20": "Export a list of sites with location and timezone info",
    "21": "Export a list of gateways with associated site info",
    "22": "Export a list of all devices with associated site info",
    "23": "Export current and historical guest users to CSV",
    "24": "Export all switch virtual chassis stats to CSV",
    "25": "Export combined inventory with site info by calendar week",
    "26": "Export gateway templates from the organization",
    "27": "Export all sites using the list sites API endpoint",
    "28": "Find gateway ports overridden from template",
    "29": "Export port statistics for a selected site",
    "30": "Export client statistics for a selected site",
    "31": "Export device list for a selected site",
    "32": "Export device statistics for a selected site",
    "33": "Export virtual chassis info for a selected switch device",
    "34": "Export currently connected WiFi clients for a selected site",
    "35": "Export all organization templates",
    "36": "Export network template information for the organization",
    "37": "Export RF template information for the organization",
    "38": "Export AP template information for the organization",
    "39": "Export switch template information for the organization",
    "40": "Export wireless client statistics for the organization",
    "41": "Export wired client statistics for the organization",
    "42": "Export security events for the organization",
    "43": "Export rogue client detections for the organization",
    "44": "Export rogue AP detections for the organization",
    "45": "Export license information for the organization",
    "46": "Export PSK (Pre-Shared Key) information",
    "47": "Export webhook configuration for the organization",
    "48": "Export WLAN configuration for the organization",
    "49": "Export WLAN configuration for a selected site",
    "50": "Export beacon information for a selected site",
    "51": "Export map information for a selected site",
    "52": "Export zone information for a selected site",
    "53": "Export SLE metrics insights for a selected site",
    "54": "Export API token information for the organization",
    "55": "Export administrator information for the organization",
    "56": "MSP info (requires MSP-level API access)",
    "57": "Export SSO information for the organization",
    "58": "Export license usage information for the organization",
    "59": "Export MX Edge information for the organization",
    "60": "Check firmware upgrade status across organization",
    "61": "Compare inventory data with external CSV file",
    "62": "Interactive Marvis AI troubleshooting",
    "63": "WIP: Export org device events from last 52 weeks",
    "64": "WIP: Export ALL audit logs (last 52 weeks)",
    "65": "WIP: Export config details for all gateway devices",
    "70": "Select a site (used by other functions)",
    "71": "View device inventory for a selected site",
    "72": "View statistics for a selected device at a site",
    "73": "View synthetic test stats for a selected gateway",
    "74": "View configuration details for a selected device",
    "75": "Loop refresh of core datasets",
    "76": "Run continuous data collection loop",
    "77": "Process and merge SFP Module CSV files",
    "78": "Generate support package for each site",
    "79": "Execute a CLI command on a gateway or switch",
    "80": "Run ARP command on an AP via WebSocket",
}


def build_static_menu_actions() -> dict:
    """Build a menu_actions dict with descriptions for listing only.

    Returns a dict compatible with OperationExecutor.build_category_list().
    Callables are set to None since execution requires full MistHelper init.
    """
    return {key: (None, desc) for key, desc in MENU_DESCRIPTIONS.items()}
