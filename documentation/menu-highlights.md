# Menu Highlights

Warning: this page is written by hand, so it can fall behind the code.
[The menu reference](menu_reference.md) is generated from
`src/utils/operation_registry.py` and is the authoritative list. Read that page
when the two disagree. Run `python scripts/generate_menu_wiki.py` to rebuild it.

This page names the operations that arrived most recently.

## Recent additions

| Menu | Operation | Category |
|------|-----------|----------|
| 195 | Audit site addresses from a CSV file. Read-only. | `safe` |
| 196 | Export the async organization license claim status | `safe` |
| 197 | Download client packet captures grouped by VLAN | `interactive_safe` |
| 198 | Search site WAN usages (`searchSiteWanUsage`) | `interactive_safe` |
| 199 | Search site webhook deliveries (`searchSiteWebhooksDeliveries`) | `interactive_safe` |
| 200 | Search site guest authorization (`searchSiteGuestAuthorization`) | `interactive_safe` |
| 201 | Search site Mist Edge events (`searchSiteMistEdgeEvents`) | `interactive_safe` |
| 202 | Search site NAC client events (`searchSiteNacClientEvents`) | `interactive_safe` |
| 203 | Search site WAN client events (`searchSiteWanClientEvents`) | `interactive_safe` |
| 204 | Search organization JSI assets and contracts | `safe` |
| 205 | Search organization Mist Edge events. Org peer of menu 201. | `safe` |
| 206 | Manage organization Zscaler synthetic probes | `destructive` |
| 207 | Migrate access points between device profiles | `destructive` |
| 208 | Revert an access point profile migration from a backup | `destructive` |
| 209 | Get the site beacon detail (`getSiteBeacon`) | `interactive_safe` |
| 210 | Export BLE beacons matching an Asset or AssetFilter (`getSiteAssetsOfInterest`) | `interactive_safe` |
| 211 | Get the site asset filter detail (`getSiteAssetFilter`) | `interactive_safe` |
| 212 | Get the site asset detail (`getSiteAsset`) | `interactive_safe` |
| 213 | Export the site application list (`getSiteApplicationList`) | `interactive_safe` |
| 214 | Search site system events (`searchSiteSystemEvents`) | `interactive_safe` |
| 215 | Search site alarms (`searchSiteAlarms`) | `interactive_safe` |
| 216 | Search site tracked assets (`searchSiteAssets`) | `interactive_safe` |
| 217 | Search site BGP peer statistics (`searchSiteBgpStats`) | `interactive_safe` |
| 218 | Search site call quality records (`searchSiteCalls`) | `interactive_safe` |
| 219 | Search site Sky ATP security events (`searchSiteSkyatpEvents`) | `interactive_safe` |
| 220 | Search site wireless client events (`searchSiteWirelessClientEvents`) | `interactive_safe` |
| 221 | Search site WAN clients (`searchSiteWanClients`) | `interactive_safe` |
| 222 | Search site device events (`searchSiteDeviceEvents`) | `interactive_safe` |
| 223 | Search site devices (`searchSiteDevices`) | `interactive_safe` |
| 224 | Search site rogue access point events (`searchSiteRogueEvents`) | `interactive_safe` |
| 225 | Search site OSPF neighbor statistics (`searchSiteOspfStats`) | `interactive_safe` |
| 226 | Search the last site device configurations (`searchSiteDeviceLastConfigs`) | `interactive_safe` |
| 227 | Search site device configuration history (`searchSiteDeviceConfigHistory`) | `interactive_safe` |
| 228 | Search site discovered switches (`searchSiteDiscoveredSwitches`) | `interactive_safe` |
| 229 | Search site zone sessions by zone type (`searchSiteZoneSessions`) | `interactive_safe` |
| 230 | Search organization wireless client sessions (`searchOrgWirelessClientSessions`) | `safe` |
| 231 | Search organization wireless client events (`searchOrgWirelessClientEvents`) | `safe` |
| 232 | Search organization WAN clients (`searchOrgWanClients`) | `safe` |
| 233 | Search organization WAN client events (`searchOrgWanClientEvents`) | `safe` |
| 234 | Search organization system events (`searchOrgSystemEvents`) | `safe` |
| 235 | Run any org-scoped Mist count endpoint (35 operations) | `interactive_safe` |
| 236 | Run any site-scoped Mist count endpoint (32 operations) | `interactive_safe` |
| 237 | Run any MSP-scoped Mist count endpoint (3 operations) | `interactive_safe` |
| 238 | Export the MSP license entitlement, usage, and subscriptions (`listMspLicenses`) | `interactive_safe` |
| 239 | Start the upgrade capture portal on port 8056 | `destructive` |
| 240 | Export one organization security intelligence profile (`getOrgSecIntelProfile`) | `interactive_safe` |

Menu 197 writes to `data/packet_captures/<mac>/vlan_<id>/`. Every other
operation in the table writes through `DataExporter`, so it honors the CSV,
SQLite, and ArangoDB backends.

