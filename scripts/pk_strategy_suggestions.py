"""Auto-generated PK strategy suggestions from probe_pk_strategy.py.

Review each entry, adjust indexes/pk fields as needed,
then paste into ENDPOINT_PRIMARY_KEY_STRATEGIES in MistHelper.py.
"""

SUGGESTED_PK_STRATEGIES = {
    # Live response fields: ['completed', 'incompleted']
    "GetOrgLicenseAsyncClaimStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "GetOrgLicenseAsyncClaimStatus \u2014 no stable key \u2014 internal id assigned (sample fields: completed, incompleted)",
    },
    # Live response fields: ['nodes']
    "GetSiteDeviceHaClusterNode": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "GetSiteDeviceHaClusterNode \u2014 no stable key \u2014 internal id assigned (sample fields: nodes)",
    },
    # Live response fields: ['action', 'created_time', 'dst_allow_wxtags', 'dst_deny_wxtags', 'dst_wxtags', 'enabled', 'for_site', 'id', 'modified_time', 'order', 'org_id', 'site_id', 'src_wxtags', 'template_id', 'template_name']
    "ListSiteWxRulesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "ListSiteWxRulesDerived \u2014 stable UUID entities (sample fields: action, created_time, dst_allow_wxtags, dst_deny_wxtags, dst_wxtags)",
    },
    # Live response fields: ['detail']
    "SubscribeSiteAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "SubscribeSiteAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "UnsubscribeSiteAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "UnsubscribeSiteAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['cmd']
    "adoptOrgJsiDevice": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "adoptOrgJsiDevice \u2014 no stable key \u2014 internal id assigned (sample fields: cmd)",
    },
    # Live response fields: ['detail']
    "convertSiteVirtualChassisToVirtualMac": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "convertSiteVirtualChassisToVirtualMac \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['count', 'type']
    "countOrgAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countOrgAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['count', 'site_id']
    "countOrgAssetsByDistanceField": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "countOrgAssetsByDistanceField \u2014 no stable key \u2014 internal id assigned (sample fields: count, site_id)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgAuditLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgAuditLogs \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['results', 'total']
    "countOrgBgpStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgBgpStats \u2014 no stable key \u2014 internal id assigned (sample fields: results, total)",
    },
    # Live response fields: ['count', 'mac']
    "countOrgDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['count', 'mac']
    "countOrgDeviceLastConfigs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgDeviceLastConfigs \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgDevices \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgGuestAuthorizations": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgGuestAuthorizations \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'model']
    "countOrgInventory": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model"],
        "unique_constraints": [],
        "description": "countOrgInventory \u2014 no stable key \u2014 internal id assigned (sample fields: count, model)",
    },
    # Live response fields: ['claimed', 'device_name', 'has_support', 'master', 'model', 'org_id', 'serial', 'sku', 'status', 'type', 'version', 'warranty', 'warranty_type']
    "countOrgJsiAssetsAndContracts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "org_id", "serial", "status", "type", "version"],
        "unique_constraints": [],
        "description": "countOrgJsiAssetsAndContracts \u2014 no stable key \u2014 internal id assigned (sample fields: claimed, device_name, has_support, master, model)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgMxEdges": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgMxEdges \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'type']
    "countOrgNacClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countOrgNacClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['count', 'type']
    "countOrgNacClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countOrgNacClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgOspfStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgOspfStats \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgOtherDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgOtherDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'mac']
    "countOrgPeerPathStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgPeerPathStats \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgPskPortalLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgPskPortalLogs \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgSiteMxEdgeEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgSiteMxEdgeEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'id']
    "countOrgSites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgSites \u2014 stable UUID entities (sample fields: count, id)",
    },
    # Live response fields: ['count', 'mac']
    "countOrgSwOrGwPorts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgSwOrGwPorts \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgSystemEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgSystemEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgTickets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgTickets \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countOrgTunnelsStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgTunnelsStats \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: []
    "countOrgWanClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgWanClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['count', 'mac']
    "countOrgWanClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgWanClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['count', 'webhook_id']
    "countOrgWebhooksDeliveries": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgWebhooksDeliveries \u2014 no stable key \u2014 internal id assigned (sample fields: count, webhook_id)",
    },
    # Live response fields: ['count', 'device_mac']
    "countOrgWiredClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgWiredClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, device_mac)",
    },
    # Live response fields: ['count', 'type']
    "countOrgWirelessClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countOrgWirelessClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['count', 'last_device']
    "countOrgWirelessClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countOrgWirelessClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, last_device)",
    },
    # Live response fields: ['count', 'mac']
    "countOrgWirelessClientsSessions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countOrgWirelessClientsSessions \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['count', 'type']
    "countSiteAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['ap', 'count']
    "countSiteApps": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteApps \u2014 no stable key \u2014 internal id assigned (sample fields: ap, count)",
    },
    # Live response fields: ['count', 'site_id']
    "countSiteAssets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "countSiteAssets \u2014 no stable key \u2014 internal id assigned (sample fields: count, site_id)",
    },
    # Live response fields: ['results', 'total']
    "countSiteBgpStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteBgpStats \u2014 no stable key \u2014 internal id assigned (sample fields: results, total)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteCalls": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteCalls \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: []
    "countSiteClientFingerprints": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteClientFingerprints \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['ap', 'count']
    "countSiteDeviceConfigHistory": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteDeviceConfigHistory \u2014 no stable key \u2014 internal id assigned (sample fields: ap, count)",
    },
    # Live response fields: ['count', 'model']
    "countSiteDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model"],
        "unique_constraints": [],
        "description": "countSiteDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, model)",
    },
    # Live response fields: ['count', 'mac']
    "countSiteDeviceLastConfig": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countSiteDeviceLastConfig \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteDevices \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'hostname']
    "countSiteDiscoveredSwitches": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["hostname"],
        "unique_constraints": [],
        "description": "countSiteDiscoveredSwitches \u2014 no stable key \u2014 internal id assigned (sample fields: count, hostname)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteGuestAuthorizations": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteGuestAuthorizations \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteMxEdgeEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteMxEdgeEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'type']
    "countSiteNacClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteNacClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['count', 'type']
    "countSiteNacClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteNacClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['detail']
    "countSiteOspfStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteOspfStats \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteOtherDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteOtherDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteRogueEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteRogueEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'type']
    "countSiteServicePathEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteServicePathEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteSkyatpEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteSkyatpEvents \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'mac']
    "countSiteSwOrGwPorts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countSiteSwOrGwPorts \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['count', 'type']
    "countSiteSystemEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteSystemEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: []
    "countSiteWanClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteWanClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['count', 'mac']
    "countSiteWanClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countSiteWanClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['details']
    "countSiteWanUsage": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteWanUsage \u2014 no stable key \u2014 internal id assigned (sample fields: details)",
    },
    # Live response fields: ['distinct', 'end', 'limit', 'results', 'start', 'total']
    "countSiteWebhooksDeliveries": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteWebhooksDeliveries \u2014 no stable key \u2014 internal id assigned (sample fields: distinct, end, limit, results, start)",
    },
    # Live response fields: ['count', 'device_mac']
    "countSiteWiredClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteWiredClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, device_mac)",
    },
    # Live response fields: ['count', 'type']
    "countSiteWirelessClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["type"],
        "unique_constraints": [],
        "description": "countSiteWirelessClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: count, type)",
    },
    # Live response fields: ['count', 'mac']
    "countSiteWirelessClientSessions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "countSiteWirelessClientSessions \u2014 no stable key \u2014 internal id assigned (sample fields: count, mac)",
    },
    # Live response fields: ['count', 'last_device']
    "countSiteWirelessClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "countSiteWirelessClients \u2014 no stable key \u2014 internal id assigned (sample fields: count, last_device)",
    },
    # Live response fields: []
    "exportSiteDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "exportSiteDevices \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['detail']
    "generateSecretFor2faVerification": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "generateSecretFor2faVerification \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['flavor', 'required', 'sitekey']
    "getAdminRegistrationInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getAdminRegistrationInfo \u2014 no stable key \u2014 internal id assigned (sample fields: flavor, required, sitekey)",
    },
    # Live response fields: ['alarmtemplate_id', 'allow_mist', 'created_time', 'id', 'modified_time', 'msp_id', 'name', 'session_expiry']
    "getOrg": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "getOrg \u2014 stable UUID entities (sample fields: alarmtemplate_id, allow_mist, created_time, id, modified_time)",
    },
    # Live response fields: ['cli_commands']
    "getOrgAosRegisterCmd": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgAosRegisterCmd \u2014 no stable key \u2014 internal id assigned (sample fields: cli_commands)",
    },
    # Live response fields: []
    "getOrgApplicationList": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgApplicationList \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "getOrgCapturingStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgCapturingStatus \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "getOrgCrlFile": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgCrlFile \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['status']
    "getOrgE911Report": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getOrgE911Report \u2014 no stable key \u2014 internal id assigned (sample fields: status)",
    },
    # Live response fields: ['adopted', 'bundled_mac', 'connected', 'created_time', 'deviceprofile_id', 'hostname', 'hw_rev', 'id', 'jsi', 'mac', 'magic', 'model', 'modified_time', 'name', 'org_id', 'serial', 'site_id', 'sku', 'type', 'version']
    "getOrgInventory": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["hostname", "mac", "model", "name", "org_id", "serial", "site_id", "type", "version"],
        "unique_constraints": [],
        "description": "getOrgInventory \u2014 stable UUID entities (sample fields: adopted, bundled_mac, connected, created_time, deviceprofile_id)",
    },
    # Live response fields: ['detail']
    "getOrgJseInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgJseInfo \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: []
    "getOrgJseIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgJseIntegration \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['cmd']
    "getOrgJuniperDevicesCommand": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgJuniperDevicesCommand \u2014 no stable key \u2014 internal id assigned (sample fields: cmd)",
    },
    # Live response fields: ['fully_loaded', 'num_devices', 'site_id', 'usages']
    "getOrgLicensesBySite": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "getOrgLicensesBySite \u2014 no stable key \u2014 internal id assigned (sample fields: fully_loaded, num_devices, site_id, usages)",
    },
    # Live response fields: ['entitled', 'evals', 'fully_loaded', 'licenses', 'summary', 'svna_insufficient', 'svna_ui', 'trial_enabled', 'trial_end_time', 'vna_ui', 'wvna_ui']
    "getOrgLicensesSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgLicensesSummary \u2014 no stable key \u2014 internal id assigned (sample fields: entitled, evals, fully_loaded, licenses, summary)",
    },
    # Live response fields: ['cert_providers', 'enabled', 'intune_scep_url', 'jamf_access_token', 'jamf_scep_url', 'jamf_webhook_url']
    "getOrgMistScep": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgMistScep \u2014 no stable key \u2014 internal id assigned (sample fields: cert_providers, enabled, intune_scep_url, jamf_access_token, jamf_scep_url)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'magic', 'model', 'modified_time', 'mxagent_registered', 'mxcluster_id', 'mxedge_mgmt', 'name', 'notes', 'oob_ip_config', 'org_id', 'serial', 'services', 'site_id', 'tunterm_dhcpd_config', 'tunterm_extra_routes', 'tunterm_igmp_snooping_config', 'tunterm_ip_config', 'tunterm_other_ip_configs', 'tunterm_port_config', 'tunterm_registered']
    "getOrgMxEdge": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id"],
        "unique_constraints": [],
        "description": "getOrgMxEdge \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, magic)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'magic', 'model', 'modified_time', 'mxagent_registered', 'mxcluster_id', 'mxedge_mgmt', 'name', 'notes', 'oob_ip_config', 'org_id', 'serial', 'services', 'site_id', 'status', 'tunterm_dhcpd_config', 'tunterm_extra_routes', 'tunterm_igmp_snooping_config', 'tunterm_ip_config', 'tunterm_other_ip_configs', 'tunterm_port_config', 'tunterm_registered']
    "getOrgMxEdgeStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "status"],
        "unique_constraints": [],
        "description": "getOrgMxEdgeStats \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, magic)",
    },
    # Live response fields: ['detail']
    "getOrgMxEdgeUpgradeInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgMxEdgeUpgradeInfo \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['model', 'name', 'user_data']
    "getOrgMxEdgeVmParams": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "name"],
        "unique_constraints": [],
        "description": "getOrgMxEdgeVmParams \u2014 no stable key \u2014 internal id assigned (sample fields: model, name, user_data)",
    },
    # Live response fields: ['results']
    "getOrgNacCrl": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgNacCrl \u2014 no stable key \u2014 internal id assigned (sample fields: results)",
    },
    # Live response fields: ['detail']
    "getOrgOtherDevice": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgOtherDevice \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "getOrgOtherDeviceStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgOtherDeviceStats \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['auto_assignment_manually_trigger_time', 'cacerts', 'cloudshark', 'created_time', 'disable_pcap', 'for_site', 'id', 'installer', 'jcloud_ra', 'juniper_srx', 'junos_shell_access', 'marvis', 'mgmt', 'mist_nac', 'modified_time', 'mxedge_mgmt', 'org_id', 'password_policy', 'security', 'site_id', 'ssr', 'switch', 'synthetic_test', 'tags', 'ui_idle_timeout', 'ui_no_tracking', 'wan_pma', 'wired_pma', 'wireless_pma']
    "getOrgSettings": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "getOrgSettings \u2014 stable UUID entities (sample fields: auto_assignment_manually_trigger_time, cacerts, cloudshark, created_time, disable_pcap)",
    },
    # Live response fields: ['site_id']
    "getOrgSitesSle": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "getOrgSitesSle \u2014 no stable key \u2014 internal id assigned (sample fields: site_id)",
    },
    # Live response fields: []
    "getOrgSkyAtpIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgSkyAtpIntegration \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['cert']
    "getOrgSslProxyCert": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgSslProxyCert \u2014 no stable key \u2014 internal id assigned (sample fields: cert)",
    },
    # Live response fields: ['conductor_cmd', 'registration_code', 'router_shell_cmd']
    "getOrgSsrRegistrationCommands": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgSsrRegistrationCommands \u2014 no stable key \u2014 internal id assigned (sample fields: conductor_cmd, registration_code, router_shell_cmd)",
    },
    # Live response fields: ['alarmtemplate_id', 'allow_mist', 'created_time', 'id', 'modified_time', 'msp_id', 'name', 'num_devices', 'num_devices_connected', 'num_devices_disconnected', 'num_inventory', 'num_sites', 'session_expiry', 'sle']
    "getOrgStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "getOrgStats \u2014 stable UUID entities (sample fields: alarmtemplate_id, allow_mist, created_time, id, modified_time)",
    },
    # Live response fields: ['assetfilter_ids', 'created_time', 'enabled', 'for_site', 'id', 'modified_time', 'name', 'org_id', 'site_id', 'topics', 'type', 'url', 'verify_cert']
    "getOrgWebhook": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "getOrgWebhook \u2014 stable UUID entities (sample fields: assetfilter_ids, created_time, enabled, for_site, id)",
    },
    # Live response fields: []
    "getOrgZscalerIntegration": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getOrgZscalerIntegration \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['name', 'privileges']
    "getSelf": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "getSelf \u2014 no stable key \u2014 internal id assigned (sample fields: name, privileges)",
    },
    # Live response fields: ['request_limit', 'requests', 'seconds']
    "getSelfApiUsage": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSelfApiUsage \u2014 no stable key \u2014 internal id assigned (sample fields: request_limit, requests, seconds)",
    },
    # Live response fields: ['email', 'last_failure_at', 'num_attempts', 'src_ips', 'user_agents']
    "getSelfLoginFailures": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSelfLoginFailures \u2014 no stable key \u2014 internal id assigned (sample fields: email, last_failure_at, num_attempts, src_ips, user_agents)",
    },
    # Live response fields: ['state', 'status']
    "getSiteApAutoOrientation": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getSiteApAutoOrientation \u2014 no stable key \u2014 internal id assigned (sample fields: state, status)",
    },
    # Live response fields: ['status']
    "getSiteApAutoPlacement": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getSiteApAutoPlacement \u2014 no stable key \u2014 internal id assigned (sample fields: status)",
    },
    # Live response fields: ['app_id', 'group', 'key', 'name']
    "getSiteApplicationList": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "getSiteApplicationList \u2014 no stable key \u2014 internal id assigned (sample fields: app_id, group, key, name)",
    },
    # Live response fields: ['_id', '_ttl', 'ap_mac', 'beam', 'by', 'curr_site', 'device_name', 'eddystone_uid_instance', 'eddystone_uid_namespace', 'eddystone_url', 'ibeacon_major', 'ibeacon_minor', 'ibeacon_uuid', 'id', 'last_seen', 'mac', 'manufacture', 'map_id', 'mfg_company_id', 'mfg_data', 'name', 'rssi', 'service_data', 'x', 'y']
    "getSiteAssetsOfInterest": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name"],
        "unique_constraints": [],
        "description": "getSiteAssetsOfInterest \u2014 stable UUID entities (sample fields: _id, _ttl, ap_mac, beam, by)",
    },
    # Live response fields: ['status', 'stop_time']
    "getSiteAutoMapAssignmentStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getSiteAutoMapAssignmentStatus \u2014 no stable key \u2014 internal id assigned (sample fields: status, stop_time)",
    },
    # Live response fields: ['exception', 'query', 'rows', 'uri']
    "getSiteBeamCoverageOverview": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteBeamCoverageOverview \u2014 no stable key \u2014 internal id assigned (sample fields: exception, query, rows, uri)",
    },
    # Live response fields: []
    "getSiteCapturingStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteCapturingStatus \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['band_24', 'band_24_metric', 'band_5', 'band_5_metric', 'band_6', 'band_6_metric', 'rftemplate', 'rftemplate_id', 'rftemplate_name', 'status', 'timestamp']
    "getSiteCurrentChannelPlanning": {
        "type": "composite_pk",
        "primary_key": ["timestamp"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getSiteCurrentChannelPlanning \u2014 event/log time-series records (sample fields: band_24, band_24_metric, band_5, band_5_metric, band_6)",
    },
    # Live response fields: ['?unrecognized?', 'Acer-B3-A20', 'Amazon-KFSUWI', 'Android', 'BLU-GrandM2', 'BlackBerry-BBB100-2', 'BlackBerry-BBD100-2', 'BlackBerry-BBF100-6', 'BlackBerry-BBF100-9', 'Datalogic-MEMOR10', 'EPSON-EMBT3C', 'EssentialProducts-PH-1', 'FUJITSU-F-01J', 'FUJITSU-arrowsM03', 'FUJITSU-arrowsM04', 'Fairphone-FP3', 'GeneralMobile-GM8', 'Gigaset-GS290', 'Google-Pixel', 'Google-Pixel10', 'Google-Pixel10ProXL', 'Google-Pixel2', 'Google-Pixel2XL', 'Google-Pixel3', 'Google-Pixel3XL', 'Google-Pixel3a', 'Google-Pixel3aXL', 'Google-Pixel4', 'Google-Pixel4XL', 'Google-Pixel4a', 'Google-Pixel4a(5G)', 'Google-Pixel5', 'Google-Pixel5a', 'Google-Pixel6', 'Google-Pixel6Pro', 'Google-Pixel6a', 'Google-Pixel7', 'Google-Pixel7Pro', 'Google-Pixel7a', 'Google-Pixel8', 'Google-Pixel8Pro', 'Google-Pixel8a', 'Google-Pixel9', 'Google-Pixel9ProXL', 'Google-Pixel9a', 'Google-PixelXL', 'HMDGlobal-Nokia2.3', 'HMDGlobal-Nokia4.2', 'HMDGlobal-Nokia5.3', 'HMDGlobal-Nokia6.1', 'HMDGlobal-Nokia6.1Plus', 'HMDGlobal-Nokia7.1', 'HMDGlobal-Nokia7.2', 'HMDGlobal-Nokia7plus', 'HMDGlobal-Nokia8.1', 'HMDGlobal-Nokia8.35G', 'HMDGlobal-Nokia9', 'HMDGlobal-NokiaG21', 'HMDGlobal-NokiaG50', 'HMDGlobal-NokiaX20', 'HMDGlobal-NokiaXR20', 'HMDGlobal-TA-1004', 'HMDGlobal-TA-1012', 'HMDGlobal-TA-1025', 'HMDGlobal-TA-1032', 'HMDGlobal-TA-1052', 'HONOR-ELP-NX9', 'HTC-0PJA2', 'HTC-2PS64', 'HTC-2PZC5', 'HTC-831C', 'HTC-HTC10', 'HTC-HTC2PQ910', 'HTC-HTC2PS6200', 'HTC-HTC2Q55100', 'HTC-HTC6525LVW', 'HTC-HTC6545LVW', 'HTC-HTCDesire626', 'HTC-HTCONE', 'HTC-HTCOne', 'HTC-HTCOneA9', 'HTC-HTCOne_M8', 'HTC-HTCOne_M8dualsim', 'HTC-HTCU11', 'HTC-HTCU12life', 'HTC-HTC_2Q4D100', 'HTC-HTC_B810x', 'HTC-HTC_D628u', 'HTC-HTC_D816x', 'HTC-HTC_M10h', 'HTC-HTC_U-3u', 'HTC-HTC_X10u', 'HTC-HTV32', 'HTC-HTV33', 'HUAWEI-ALE-L21', 'HUAWEI-ALP-L09', 'HUAWEI-ALP-L29', 'HUAWEI-ANE-LX1', 'HUAWEI-ANE-LX2J', 'HUAWEI-ATU-L31', 'HUAWEI-BAH-L09', 'HUAWEI-BLA-A09', 'HUAWEI-BLA-L09', 'HUAWEI-BLA-L29', 'HUAWEI-BLN-L22', 'HUAWEI-BND-AL10', 'HUAWEI-BND-L24', 'HUAWEI-BND-L34', 'HUAWEI-BTV-DL09', 'HUAWEI-CLT-L09', 'HUAWEI-CLT-L29', 'HUAWEI-ELE-L09', 'HUAWEI-ELE-L29', 'HUAWEI-ELS-N39', 'HUAWEI-ELS-NX9', 'HUAWEI-EML-AL00', 'HUAWEI-EML-L09', 'HUAWEI-EML-L29', 'HUAWEI-EVA-AL00', 'HUAWEI-EVA-L09', 'HUAWEI-EVR-L29', 'HUAWEI-FIG-LX1', 'HUAWEI-FRD-L02', 'HUAWEI-FRD-L09', 'HUAWEI-FRD-L14', 'HUAWEI-H60-L04', 'HUAWEI-HMA-AL00', 'HUAWEI-HMA-L09', 'HUAWEI-HMA-L29', 'HUAWEI-HUAWEIMT7-TL10', 'HUAWEI-HUAWEIVNS-L31', 'HUAWEI-INE-LX2', 'HUAWEI-JDN2-W09', 'HUAWEI-LIO-L29', 'HUAWEI-LON-AL00', 'HUAWEI-LON-L29', 'HUAWEI-LYA-L09', 'HUAWEI-LYA-L29', 'HUAWEI-MAR-AL00', 'HUAWEI-MAR-LX1A', 'HUAWEI-MAR-LX2', 'HUAWEI-MAR-LX3A', 'HUAWEI-MHA-L29', 'HUAWEI-PCT-L29', 'HUAWEI-PLE-701L', 'HUAWEI-RNE-L21', 'HUAWEI-RNE-L22', 'HUAWEI-RVL-AL09', 'HUAWEI-SHT-W09', 'HUAWEI-SLA-L03', 'HUAWEI-SNE-LX1', 'HUAWEI-STF-AL00', 'HUAWEI-STF-L09', 'HUAWEI-STK-L22', 'HUAWEI-STK-LX1', 'HUAWEI-VKY-L29', 'HUAWEI-VOG-AL00', 'HUAWEI-VOG-AL10', 'HUAWEI-VOG-L09', 'HUAWEI-VOG-L29', 'HUAWEI-VTR-L09', 'HUAWEI-VTR-L29', 'HUAWEI-WAS-LX2J', 'HUAWEI-YAL-L21', 'HXY-BISON', 'Haier-AndromaxA16C3H', 'Haier-HM-N700-FL', 'Honeywell-CK65', 'Honeywell-CT60', 'Huawei-Nexus6P', 'INTEX-INTEXAQUASELFIE', 'InFocus-IF9002', 'InnJoo-InnJoo2LTE', 'Intex-AquaSpeed', 'KYOCERA-602KC', 'KYOCERA-KYV48', 'Kogan-KoganAgora8', 'LENOVO-LenovoK33a42', 'LENOVO-LenovoP2a42', 'LENOVO-LenovoTB3-850M', 'LENOVO-LenovoTB3-X70F', 'LGE-LG-D852', 'LGE-LG-D855', 'LGE-LG-H811', 'LGE-LG-H830', 'LGE-LG-H860', 'LGE-LG-H870', 'LGE-LG-H870DS', 'LGE-LG-H872', 'LGE-LG-H900', 'LGE-LG-H910', 'LGE-LG-H918', 'LGE-LG-H930', 'LGE-LG-H932', 'LGE-LG-K540', 'LGE-LG-K550', 'LGE-LG-LS993', 'LGE-LG-LS997', 'LGE-LG-M700', 'LGE-LG-US998', 'LGE-LGL355DL', 'LGE-LGLS665', 'LGE-LGLS755', 'LGE-LGLS992', 'LGE-LGM-V300S', 'LGE-LGMP260', 'LGE-LGUS991', 'LGE-LM-G710', 'LGE-LM-G710N', 'LGE-LM-G710VM', 'LGE-LM-G810', 'LGE-LM-G820N', 'LGE-LM-G900', 'LGE-LM-K420', 'LGE-LM-Q610(FGN)', 'LGE-LM-Q630', 'LGE-LM-Q630N', 'LGE-LM-Q710(FGN)', 'LGE-LM-Q710.FG', 'LGE-LM-Q730N', 'LGE-LM-V350N', 'LGE-LM-V405', 'LGE-LM-V500', 'LGE-LM-V600', 'LGE-LM-X410(FG)', 'LGE-LML413DL', 'LGE-Nexus5', 'LGE-Nexus5X', 'LGE-RS988', 'LGE-VS9854G', 'LGE-VS986', 'LGE-VS987', 'LGE-VS988', 'LGE-VS995', 'LGE-VS996', 'Lenovo-LenovoL58041', 'Logitec-LZ-AA10', 'MPti_by_imagineear-MPti_by_imagineear', 'Meizu-15Lite', 'Meizu-M6Note', 'Microsoft-SurfaceDuo2', 'Mitac_International_Corp-RuggedMiniTablet', 'Motorola-MotoG3', 'NEC-PC-TE510HAW', 'NewBund-ApolloLite', 'Nothing-A063', 'Nothing-AIN065', 'ONKYO-TA2C-74Z8', 'OPPO-CPH1609', 'OPPO-CPH1707', 'OPPO-CPH1719', 'OPPO-CPH1725', 'OPPO-CPH1803', 'OPPO-CPH1831', 'OPPO-CPH1835', 'OPPO-CPH1851', 'OPPO-CPH1877', 'OPPO-CPH1879', 'OPPO-CPH1903', 'OPPO-CPH1907', 'OPPO-CPH1919', 'OPPO-CPH1920', 'OPPO-CPH1921', 'OPPO-CPH1933', 'OPPO-CPH1937', 'OPPO-CPH1941', 'OPPO-CPH1951', 'OPPO-CPH1979', 'OPPO-CPH1983', 'OPPO-CPH2005', 'OPPO-CPH2009', 'OPPO-CPH2013', 'OPPO-CPH2021', 'OPPO-CPH2065', 'OPPO-CPH2067', 'OPPO-CPH2069', 'OPPO-CPH2091', 'OPPO-CPH2145', 'OPPO-CPH2173', 'OPPO-CPH2195', 'OPPO-CPH2207', 'OPPO-CPH2213', 'OPPO-CPH2305', 'OPPO-CPH2343', 'OPPO-CPH2371', 'OPPO-CPH2499', 'OPPO-F1f', 'OPPO-PCCM00', 'OPPO-X9079', 'OnePlus-A0001', 'OnePlus-AC2001', 'OnePlus-CPH2381', 'OnePlus-CPH2401', 'OnePlus-CPH2413', 'OnePlus-CPH2447', 'OnePlus-CPH2467', 'OnePlus-CPH2487', 'OnePlus-CPH2515', 'OnePlus-CPH2551', 'OnePlus-CPH2573', 'OnePlus-CPH2585', 'OnePlus-CPH2613', 'OnePlus-CPH2649', 'OnePlus-CPH2661', 'OnePlus-CPH2767', 'OnePlus-DE2117', 'OnePlus-DN2101', 'OnePlus-EB2101', 'OnePlus-GM1900', 'OnePlus-GM1901', 'OnePlus-GM1903', 'OnePlus-GM1910', 'OnePlus-GM1911', 'OnePlus-GM1915', 'OnePlus-GM1917', 'OnePlus-HD1900', 'OnePlus-HD1901', 'OnePlus-HD1907', 'OnePlus-IN2013', 'OnePlus-IN2017', 'OnePlus-IN2020', 'OnePlus-IN2023', 'OnePlus-IN2025', 'OnePlus-IV2201', 'OnePlus-KB2001', 'OnePlus-LE2101', 'OnePlus-LE2111', 'OnePlus-LE2115', 'OnePlus-LE2117', 'OnePlus-LE2121', 'OnePlus-NE2211', 'OnePlus-NE2213', 'OnePlus-ONEA2003', 'OnePlus-ONEA2005', 'OnePlus-ONEE1003', 'OnePlus-ONEPLUSA3000', 'OnePlus-ONEPLUSA3003', 'OnePlus-ONEPLUSA3010', 'OnePlus-ONEPLUSA5000', 'OnePlus-ONEPLUSA5010', 'OnePlus-ONEPLUSA6000', 'OnePlus-ONEPLUSA6003', 'OnePlus-ONEPLUSA6010', 'OnePlus-ONEPLUSA6013', 'PANASONIC-FZ-N1', 'PlusOneJapanLimited-FTJ161B', 'PlusOneJapanLimited-FTJ162B', 'Quanta-QTAQZ3', 'Razer-Phone2', 'RealWearinc.-T1100G', 'SGP-Blackphone2', 'SHARP-S1', 'SHARP-SH-01K', 'SHARP-SH-02M', 'SHARP-SH-M05', 'SHARP-SH-M12', 'Simulator-iPhone 5s', 'Simulator-iPhone 7', 'Simulator-iPhone SE', 'Simulator-iPhone11,2', 'Sony-702SO', 'Sony-D2303', 'Sony-D5803', 'Sony-D6503', 'Sony-D6653', 'Sony-E2303', 'Sony-E5823', 'Sony-E6553', 'Sony-E6853', 'Sony-F8132', 'Sony-F8331', 'Sony-F8332', 'Sony-G3116', 'Sony-G3212', 'Sony-G3226', 'Sony-G3426', 'Sony-G8141', 'Sony-G8142', 'Sony-G8232', 'Sony-G8342', 'Sony-G8441', 'Sony-H3133', 'Sony-H4413', 'Sony-H8266', 'Sony-H8296', 'Sony-H8324', 'Sony-J9110', 'Sony-SO-01G', 'Sony-SO-01J', 'Sony-SO-01K', 'Sony-SO-02G', 'Sony-SO-02J', 'Sony-SO-02K', 'Sony-SO-04H', 'Sony-SO-04J', 'Sony-SO-05K', 'Sony-SO-52C', 'Sony-SOG02', 'Sony-SOL26', 'Sony-SOV34', 'Sony-SOV36', 'Sony-SOV37', 'Sony-SOV42', 'Sony-XQ-AT51', 'Sony-XQ-BC52', 'Sony-XQ-BC72', 'Sony-XQ-BE72', 'Sony-XQ-DQ62', 'Sony-XperiaXCompact(AOSP)', 'TCL-5002X', 'TCL-5003D_EEA', 'TCL-5007U', 'TCL-5017B', 'TCL-5024I', 'TCL-5033M', 'TCL-5048I', 'TCL-6062W', 'TCL-6125F', 'TCL-T767H', 'Teclast-M89', 'UMIDIGI-A5_Pro', 'UMIDIGI-A7Pro', 'Unihertz-Jelly-Pro', 'Unihertz-Jelly2', 'VIZIO-XR6M10', 'WIKO-HARRY', 'Wileyfox-Swift2Plus', 'Wingtech-REVVLV+5G', 'Xiaomi-2107113SR', 'Xiaomi-21081111RG', 'Xiaomi-21091116UC', 'Xiaomi-22021211RI', 'Xiaomi-22041216I', 'Xiaomi-22101316I', 'Xiaomi-22101316UG', 'Xiaomi-22101316UP', 'Xiaomi-23028RN4DG', 'Xiaomi-24053PY09I', 'Xiaomi-M2002J9G', 'Xiaomi-M2006C3LG', 'Xiaomi-M2007J17G', 'Xiaomi-M2007J20CG', 'Xiaomi-M2007J3SG', 'Xiaomi-M2007J3SP', 'Xiaomi-M2012K11AG', 'Xiaomi-M2101K6G', 'Xiaomi-M2101K7BG', 'Xiaomi-MI2S', 'Xiaomi-MI5', 'Xiaomi-MI5sPlus', 'Xiaomi-MI6', 'Xiaomi-MI8', 'Xiaomi-MI8Pro', 'Xiaomi-MI8SE', 'Xiaomi-MI9', 'Xiaomi-MIMAX2', 'Xiaomi-MIMAX3', 'Xiaomi-Mi10', 'Xiaomi-Mi4i', 'Xiaomi-Mi9Lite', 'Xiaomi-Mi9T', 'Xiaomi-Mi9TPro', 'Xiaomi-MiA1', 'Xiaomi-MiA2', 'Xiaomi-MiA2Lite', 'Xiaomi-MiA3', 'Xiaomi-MiMIX2', 'Xiaomi-MiMIX2S', 'Xiaomi-MiMIX3', 'Xiaomi-POCOF1', 'Xiaomi-POCOF2Pro', 'Xiaomi-POCOPHONEF1', 'Xiaomi-Redmi3', 'Xiaomi-Redmi4', 'Xiaomi-Redmi4X', 'Xiaomi-Redmi5', 'Xiaomi-Redmi5A', 'Xiaomi-Redmi5Plus', 'Xiaomi-Redmi6', 'Xiaomi-Redmi6Pro', 'Xiaomi-Redmi7A', 'Xiaomi-RedmiK20Pro', 'Xiaomi-RedmiNote3', 'Xiaomi-RedmiNote4', 'Xiaomi-RedmiNote5', 'Xiaomi-RedmiNote5Pro', 'Xiaomi-RedmiNote6Pro', 'Xiaomi-RedmiNote7', 'Xiaomi-RedmiNote7Pro', 'Xiaomi-RedmiNote8', 'Xiaomi-RedmiNote8Pro', 'Xiaomi-RedmiNote8T', 'Xiaomi-RedmiNote9Pro', 'Xiaomi-RedmiNote9ProMax', 'ZTE-A1', 'ZTE-BladeA32019-T', 'ZTE-BladeA32020-T', 'ZTE-BladeA52020-T', 'ZTE-BladeA72019-T', 'ZTE-Z820', 'Zebra Technologies-ET40', 'Zebra Technologies-PS20J', 'Zebra Technologies-TC52X', 'ZebraTechnologies-ET40', 'ZebraTechnologies-ET51', 'ZebraTechnologies-ET65', 'ZebraTechnologies-MC33', 'ZebraTechnologies-MC3300ax', 'ZebraTechnologies-PS20J', 'ZebraTechnologies-TC21', 'ZebraTechnologies-TC51', 'ZebraTechnologies-TC52', 'ZebraTechnologies-TC52X', 'ZebraTechnologies-TC53', 'ZebraTechnologies-TC57', 'ZebraTechnologies-TC58', 'ZebraTechnologies-TC70x', 'ZebraTechnologies-TC72', 'ZebraTechnologies-TC75', 'ZebraTechnologies-TC77', 'asus-ASUS_AI2205_C', 'asus-ASUS_I001DC', 'asus-ASUS_I002D', 'asus-ASUS_I003D', 'asus-ASUS_I006D', 'asus-ASUS_I01WD', 'asus-ASUS_X00HD', 'asus-ASUS_X00PD', 'asus-ASUS_X00QD', 'asus-ASUS_X00RD', 'asus-ASUS_X00TD', 'asus-ASUS_X00TDB', 'asus-ASUS_X013DB', 'asus-ASUS_X017DA', 'asus-ASUS_X01BDA', 'asus-ASUS_Z00AD', 'asus-ASUS_Z00ED', 'asus-ASUS_Z00LDD', 'asus-ASUS_Z010D', 'asus-ASUS_Z012D', 'asus-ASUS_Z012DA', 'asus-ASUS_Z012DC', 'asus-ASUS_Z017DA', 'asus-ASUS_Z01HD', 'asus-ASUS_Z01HDA', 'asus-ASUS_Z01KD', 'asus-ASUS_Z01KDA', 'asus-ASUS_Z01RD', 'asus-Nexus7', 'blackshark-SKW-H0', 'bq-AquarisX5Plus', 'device asset', 'htc-Nexus9', 'iPad 10', 'iPad 3', 'iPad 4', 'iPad 5', 'iPad 5 W', 'iPad 5 WC', 'iPad 7', 'iPad 8', 'iPad Air', 'iPad Air 2', 'iPad Air 5', 'iPad Mini', 'iPad Mini 2G', 'iPad Mini 3', 'iPad Pro 10.5"', 'iPad Pro 10.5-inch', 'iPad Pro 11"', 'iPad Pro 2G', 'iPad Pro 4 12.9"', 'iPad Pro W', 'iPad Pro WC', 'iPad mini 4', 'iPad11,1', 'iPad11,2', 'iPad11,3', 'iPad11,4', 'iPad11,6', 'iPad11,7', 'iPad12,1', 'iPad12,2', 'iPad13,1', 'iPad13,11', 'iPad13,16', 'iPad13,17', 'iPad13,18', 'iPad13,2', 'iPad13,4', 'iPad13,6', 'iPad14,1', 'iPad14,3', 'iPad14,4', 'iPad6,11', 'iPad6,12', 'iPad7,1', 'iPad7,11', 'iPad7,12', 'iPad7,3', 'iPad7,4', 'iPad7,5', 'iPad7,6', 'iPad8,1', 'iPad8,10', 'iPad8,11', 'iPad8,3', 'iPad8,4', 'iPad8,5', 'iPad8,6', 'iPad8,7', 'iPad8,8', 'iPad8,9', 'iPhone 11', 'iPhone 11 Pro Max', 'iPhone 12', 'iPhone 12 Mini', 'iPhone 12 Pro', 'iPhone 12 Pro Max', 'iPhone 13', 'iPhone 13 Mini', 'iPhone 13 Pro', 'iPhone 13 Pro Max', 'iPhone 14', 'iPhone 14 Plus', 'iPhone 14 Pro', 'iPhone 14 Pro Max', 'iPhone 15', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max', 'iPhone 5', 'iPhone 5c', 'iPhone 5s', 'iPhone 6', 'iPhone 6 Plus', 'iPhone 6S Plus', 'iPhone 6s', 'iPhone 6s Plus', 'iPhone 7', 'iPhone 7 Plus', 'iPhone 8', 'iPhone 8 Plus', 'iPhone SE', 'iPhone SE 2nd gen', 'iPhone SE 3nd gen', 'iPhone X', 'iPhone XR', 'iPhone XS', 'iPhone XS Max', 'iPhone10,1', 'iPhone10,2', 'iPhone10,3', 'iPhone10,4', 'iPhone10,5', 'iPhone10,6', 'iPhone11,2', 'iPhone11,6', 'iPhone11,8', 'iPhone12,1', 'iPhone12,3', 'iPhone12,5', 'iPhone12,8', 'iPhone13,1', 'iPhone13,2', 'iPhone13,3', 'iPhone13,4', 'iPhone14,2', 'iPhone14,3', 'iPhone14,4', 'iPhone14,5', 'iPhone14,6', 'iPhone14,7', 'iPhone14,8', 'iPhone15,2', 'iPhone15,3', 'iPhone15,4', 'iPhone15,5', 'iPhone16,1', 'iPhone16,2', 'iPhone17,1', 'iPhone17,2', 'iPhone17,3', 'iPhone17,4', 'iPhone18,1', 'iPhone18,2', 'iPhone18,3', 'iPhone9,2', 'iPod Touch 5G', 'iPod Touch 6G', 'iPod7,1', 'imagineear-Maestrobyimagineear', 'lge-LG-D801', 'motorola-MotoE2(4G-LTE)', 'motorola-MotoG(4)', 'motorola-MotoG(5)', 'motorola-MotoG(5)Plus', 'motorola-MotoG(5S)', 'motorola-MotoG(5S)Plus', 'motorola-MotoG2014LTE', 'motorola-MotoG3-TE', 'motorola-MotoZ(2)', 'motorola-MotoZ2Play', 'motorola-Nexus6', 'motorola-XT1022', 'motorola-XT1033', 'motorola-XT1092', 'motorola-XT1095', 'motorola-XT1585', 'motorola-XT1635-01', 'motorola-XT1635-02', 'motorola-XT1650', 'motorola-XT1663', 'motorola-XT1710-02', 'motorola-motoe(7)power', 'motorola-motoe5plus', 'motorola-motog(30)', 'motorola-motog(40)fusion', 'motorola-motog(6)', 'motorola-motog(6)plus', 'motorola-motog(60)', 'motorola-motog(7)', 'motorola-motog(7)play', 'motorola-motog(7)power', 'motorola-motog(8)plus', 'motorola-motog(8)power', 'motorola-motog(9)play', 'motorola-motog5G(2022)', 'motorola-motog5Gplus', 'motorola-motog625G', 'motorola-motog825G', 'motorola-motogstylus5G-2023', 'motorola-motorolaedge', 'motorola-motorolaedge20', 'motorola-motorolaedge20fusion', 'motorola-motorolaedge20pro', 'motorola-motorolaedge30ultra', 'motorola-motorolaedge40', 'motorola-motorolaone', 'motorola-motorolaone5GUW', 'motorola-motorolaonepower', 'motorola-motox4', 'motorola-motoz3', 'motorola-motoz4', 'nubia-NX733J', 'realme-RMX1921', 'realme-RMX1971', 'realme-RMX1993', 'realme-RMX2020', 'realme-RMX2083', 'realme-RMX2111', 'realme-RMX2121', 'realme-RMX2170', 'realme-RMX3031', 'realme-RMX3360', 'realme-RMX3381', 'realme-RMX3771', 'realme-RMX3780', 'realme-RMX5101', 'samsung-404SC', 'samsung-GT-I9500', 'samsung-GT-I9505', 'samsung-GT-I9506', 'samsung-SAMSUNG-SM-G890A', 'samsung-SAMSUNG-SM-G891A', 'samsung-SAMSUNG-SM-G900A', 'samsung-SAMSUNG-SM-G920A', 'samsung-SAMSUNG-SM-G925A', 'samsung-SAMSUNG-SM-G930A', 'samsung-SAMSUNG-SM-G935A', 'samsung-SAMSUNG-SM-J327A', 'samsung-SAMSUNG-SM-J727A', 'samsung-SAMSUNG-SM-N900A', 'samsung-SAMSUNG-SM-N910A', 'samsung-SAMSUNG-SM-N915A', 'samsung-SAMSUNG-SM-N920A', 'samsung-SC-01K', 'samsung-SC-02H', 'samsung-SC-02L', 'samsung-SC-03L', 'samsung-SC-04J', 'samsung-SC-51A', 'samsung-SCH-I545', 'samsung-SCV35', 'samsung-SCV37', 'samsung-SCV40', 'samsung-SCV43', 'samsung-SCV48', 'samsung-SGH-I317', 'samsung-SM-A025M', 'samsung-SM-A042M', 'samsung-SM-A102U', 'samsung-SM-A105G', 'samsung-SM-A115F', 'samsung-SM-A125F', 'samsung-SM-A127F', 'samsung-SM-A127M', 'samsung-SM-A136U', 'samsung-SM-A146B', 'samsung-SM-A156E', 'samsung-SM-A202F', 'samsung-SM-A205U', 'samsung-SM-A205YN', 'samsung-SM-A217F', 'samsung-SM-A217N', 'samsung-SM-A226B', 'samsung-SM-A233C', 'samsung-SM-A305GN', 'samsung-SM-A305YN', 'samsung-SM-A307GN', 'samsung-SM-A315F', 'samsung-SM-A315G', 'samsung-SM-A315N', 'samsung-SM-A320F', 'samsung-SM-A320FL', 'samsung-SM-A325F', 'samsung-SM-A326U', 'samsung-SM-A346E', 'samsung-SM-A426U', 'samsung-SM-A505F', 'samsung-SM-A505FN', 'samsung-SM-A505U', 'samsung-SM-A505YN', 'samsung-SM-A507FN', 'samsung-SM-A515F', 'samsung-SM-A520F', 'samsung-SM-A525F', 'samsung-SM-A525M', 'samsung-SM-A526B', 'samsung-SM-A526U1', 'samsung-SM-A528B', 'samsung-SM-A530F', 'samsung-SM-A5360', 'samsung-SM-A536E', 'samsung-SM-A546E', 'samsung-SM-A546U', 'samsung-SM-A606Y', 'samsung-SM-A7050', 'samsung-SM-A705F', 'samsung-SM-A705FN', 'samsung-SM-A705MN', 'samsung-SM-A705YN', 'samsung-SM-A715F', 'samsung-SM-A716B', 'samsung-SM-A716S', 'samsung-SM-A716U', 'samsung-SM-A716V', 'samsung-SM-A720F', 'samsung-SM-A725F', 'samsung-SM-A730F', 'samsung-SM-A750F', 'samsung-SM-A750FN', 'samsung-SM-A750GN', 'samsung-SM-A800I', 'samsung-SM-A805F', 'samsung-SM-A920F', 'samsung-SM-C7000', 'samsung-SM-E546B', 'samsung-SM-F415F', 'samsung-SM-F707N', 'samsung-SM-F711B', 'samsung-SM-F711U', 'samsung-SM-F711U1', 'samsung-SM-F721B', 'samsung-SM-F721N', 'samsung-SM-F731B', 'samsung-SM-F731U', 'samsung-SM-F741U1', 'samsung-SM-F916B', 'samsung-SM-F926B', 'samsung-SM-F926U', 'samsung-SM-F926U1', 'samsung-SM-F936B', 'samsung-SM-F936U', 'samsung-SM-F936U1', 'samsung-SM-F946U', 'samsung-SM-F946U1', 'samsung-SM-G390Y', 'samsung-SM-G525F', 'samsung-SM-G530T', 'samsung-SM-G570Y', 'samsung-SM-G610F', 'samsung-SM-G610M', 'samsung-SM-G610Y', 'samsung-SM-G715U', 'samsung-SM-G715U1', 'samsung-SM-G780F', 'samsung-SM-G780G', 'samsung-SM-G781B', 'samsung-SM-G781N', 'samsung-SM-G781U', 'samsung-SM-G781U1', 'samsung-SM-G781V', 'samsung-SM-G892A', 'samsung-SM-G892U', 'samsung-SM-G900F', 'samsung-SM-G900H', 'samsung-SM-G900I', 'samsung-SM-G900P', 'samsung-SM-G900T', 'samsung-SM-G900V', 'samsung-SM-G900W8', 'samsung-SM-G901F', 'samsung-SM-G920F', 'samsung-SM-G920I', 'samsung-SM-G920P', 'samsung-SM-G920T', 'samsung-SM-G920V', 'samsung-SM-G925F', 'samsung-SM-G925T', 'samsung-SM-G925V', 'samsung-SM-G9287', 'samsung-SM-G928F', 'samsung-SM-G928I', 'samsung-SM-G928V', 'samsung-SM-G930F', 'samsung-SM-G930P', 'samsung-SM-G930R4', 'samsung-SM-G930T', 'samsung-SM-G930U', 'samsung-SM-G930V', 'samsung-SM-G930W8', 'samsung-SM-G935F', 'samsung-SM-G935P', 'samsung-SM-G935T', 'samsung-SM-G935U', 'samsung-SM-G935V', 'samsung-SM-G935W8', 'samsung-SM-G950F', 'samsung-SM-G950N', 'samsung-SM-G950U', 'samsung-SM-G950U1', 'samsung-SM-G950W', 'samsung-SM-G955F', 'samsung-SM-G955N', 'samsung-SM-G955U', 'samsung-SM-G955U1', 'samsung-SM-G9600', 'samsung-SM-G960F', 'samsung-SM-G960N', 'samsung-SM-G960U', 'samsung-SM-G960U1', 'samsung-SM-G960W', 'samsung-SM-G9650', 'samsung-SM-G965F', 'samsung-SM-G965N', 'samsung-SM-G965U', 'samsung-SM-G965U1', 'samsung-SM-G965W', 'samsung-SM-G970F', 'samsung-SM-G970U', 'samsung-SM-G970U1', 'samsung-SM-G9730', 'samsung-SM-G973F', 'samsung-SM-G973N', 'samsung-SM-G973U', 'samsung-SM-G973U1', 'samsung-SM-G973W', 'samsung-SM-G9750', 'samsung-SM-G975F', 'samsung-SM-G975N', 'samsung-SM-G975U', 'samsung-SM-G975U1', 'samsung-SM-G975W', 'samsung-SM-G977B', 'samsung-SM-G977N', 'samsung-SM-G977P', 'samsung-SM-G977U', 'samsung-SM-G980F', 'samsung-SM-G981B', 'samsung-SM-G981U', 'samsung-SM-G981U1', 'samsung-SM-G981W', 'samsung-SM-G985F', 'samsung-SM-G9860', 'samsung-SM-G986B', 'samsung-SM-G986U', 'samsung-SM-G986U1', 'samsung-SM-G988B', 'samsung-SM-G988U', 'samsung-SM-G990B2', 'samsung-SM-G990E', 'samsung-SM-G990U1', 'samsung-SM-G991B', 'samsung-SM-G991Q', 'samsung-SM-G991U', 'samsung-SM-G991U1', 'samsung-SM-G996B', 'samsung-SM-G996U', 'samsung-SM-G996U1', 'samsung-SM-G998B', 'samsung-SM-G998U', 'samsung-SM-G998U1', 'samsung-SM-J250G', 'samsung-SM-J320F', 'samsung-SM-J320FN', 'samsung-SM-J500FN', 'samsung-SM-J500H', 'samsung-SM-J530F', 'samsung-SM-J530Y', 'samsung-SM-J600FN', 'samsung-SM-J600G', 'samsung-SM-J610G', 'samsung-SM-J700M', 'samsung-SM-J700T', 'samsung-SM-J727T', 'samsung-SM-J727V', 'samsung-SM-J727VPP', 'samsung-SM-J730F', 'samsung-SM-J730G', 'samsung-SM-J730GM', 'samsung-SM-J737A', 'samsung-SM-J737T', 'samsung-SM-J810F', 'samsung-SM-J810G', 'samsung-SM-J810Y', 'samsung-SM-M146B', 'samsung-SM-M215F', 'samsung-SM-M307F', 'samsung-SM-M315F', 'samsung-SM-M317F', 'samsung-SM-M326B', 'samsung-SM-M336BU', 'samsung-SM-M515F', 'samsung-SM-M536B', 'samsung-SM-N770F', 'samsung-SM-N9005', 'samsung-SM-N900P', 'samsung-SM-N910C', 'samsung-SM-N910G', 'samsung-SM-N910V', 'samsung-SM-N915R4', 'samsung-SM-N9208', 'samsung-SM-N920C', 'samsung-SM-N920I', 'samsung-SM-N920T', 'samsung-SM-N920V', 'samsung-SM-N950F', 'samsung-SM-N950N', 'samsung-SM-N950U', 'samsung-SM-N950U1', 'samsung-SM-N950W', 'samsung-SM-N960F', 'samsung-SM-N960N', 'samsung-SM-N960U', 'samsung-SM-N960U1', 'samsung-SM-N9700', 'samsung-SM-N970F', 'samsung-SM-N970U', 'samsung-SM-N970U1', 'samsung-SM-N971N', 'samsung-SM-N9750', 'samsung-SM-N975F', 'samsung-SM-N975U', 'samsung-SM-N975U1', 'samsung-SM-N976B', 'samsung-SM-N976N', 'samsung-SM-N976U', 'samsung-SM-N976V', 'samsung-SM-N980F', 'samsung-SM-N981B', 'samsung-SM-N981U', 'samsung-SM-N985F', 'samsung-SM-N9860', 'samsung-SM-N986B', 'samsung-SM-N986N', 'samsung-SM-N986U', 'samsung-SM-N986U1', 'samsung-SM-P350', 'samsung-SM-P610', 'samsung-SM-S711U', 'samsung-SM-S721U1', 'samsung-SM-S901B', 'samsung-SM-S901E', 'samsung-SM-S901U', 'samsung-SM-S901U1', 'samsung-SM-S906E', 'samsung-SM-S906U', 'samsung-SM-S908B', 'samsung-SM-S908E', 'samsung-SM-S908U', 'samsung-SM-S908U1', 'samsung-SM-S911B', 'samsung-SM-S911U', 'samsung-SM-S916B', 'samsung-SM-S916U', 'samsung-SM-S918B', 'samsung-SM-S918U', 'samsung-SM-S921B', 'samsung-SM-S926B', 'samsung-SM-S926U', 'samsung-SM-S926U1', 'samsung-SM-S928B', 'samsung-SM-S928U', 'samsung-SM-S928U1', 'samsung-SM-S931B', 'samsung-SM-S931U', 'samsung-SM-S938B', 'samsung-SM-S938U1', 'samsung-SM-T350', 'samsung-SM-T360', 'samsung-SM-T365Y', 'samsung-SM-T380', 'samsung-SM-T560NU', 'samsung-SM-T580', 'samsung-SM-T585', 'samsung-SM-T705', 'samsung-SM-T713', 'samsung-SM-T715Y', 'samsung-SM-T800', 'samsung-SM-T820', 'samsung-SM-T830', 'samsung-SM-T867V', 'samsung-SM-X200', 'samsung-SM-X706B', 'vivo-I2011', 'vivo-I2017', 'vivo-I2217', 'vivo-I2223', 'vivo-I2401', 'vivo-V1814A', 'vivo-V2053', 'vivo-V2055', 'vivo-V2130', 'vivo-V2132', 'vivo-vivo1601', 'vivo-vivo1718', 'vivo-vivo1902', 'vivo-vivo1904', 'vivo-vivo1920', 'zte-Z955A']
    "getSiteDefaultPlfForModels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteDefaultPlfForModels \u2014 no stable key \u2014 internal id assigned (sample fields: ?unrecognized?, Acer-B3-A20, Amazon-KFSUWI, Android, BLU-GrandM2)",
    },
    # Live response fields: ['adopted', 'bgp_config', 'bundled_mac', 'connected', 'created_time', 'deviceprofile_id', 'dhcpd_config', 'disable_auto_config', 'dns_servers', 'dns_suffix', 'evpn_scope', 'evpntopo_id', 'extra_routes', 'extra_routes6', 'gateway_mgmt', 'hostname', 'hw_rev', 'id', 'ip_configs', 'jsi', 'mac', 'magic', 'managed', 'map_id', 'mist_configured', 'model', 'modified_time', 'name', 'notes', 'ntp_servers', 'oob_ip_config', 'org_id', 'ospf_areas', 'ospf_config', 'path_preferences', 'port_config', 'remote_syslog', 'routing_policies', 'serial', 'service_policies', 'simplifiedName', 'site_id', 'sku', 'st_ip_base', 'tag_id', 'tag_uuid', 'tunnel_configs', 'type', 'version', 'vrf_instances']
    "getSiteDevice": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["hostname", "mac", "model", "name", "org_id", "serial", "site_id", "type", "version"],
        "unique_constraints": [],
        "description": "getSiteDevice \u2014 stable UUID entities (sample fields: adopted, bgp_config, bundled_mac, connected, created_time)",
    },
    # Live response fields: ['_errors', 'cli']
    "getSiteDeviceConfigCmd": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteDeviceConfigCmd \u2014 no stable key \u2014 internal id assigned (sample fields: _errors, cli)",
    },
    # Live response fields: []
    "getSiteDeviceIotPort": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteDeviceIotPort \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['_id', '_ttl', 'arp_table_stats', 'auto_upgrade_stat', 'cert_expiry', 'chassis_mac', 'chassis_model', 'chassis_serial', 'config_status', 'config_timestamp', 'config_version', 'cpu_stat', 'created_time', 'deviceprofile_id', 'dhcpd_stat', 'evpntopo_id', 'expiring_certs', 'ext_ip', 'has_pcap', 'hostname', 'hw_rev', 'id', 'if_stat', 'ip', 'ip_stat', 'isp_info', 'last_seen', 'last_trouble', 'mac', 'mac_table_stats', 'map_id', 'memory_stat', 'model', 'modified_time', 'module_stat', 'name', 'notes', 'org_id', 'part_number', 'route_summary_stats', 'serial', 'service_stat', 'service_status', 'site_id', 'spu_stat', 'status', 'tag_id', 'tag_uuid', 'type', 'uptime', 'version']
    "getSiteDeviceStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["hostname", "mac", "model", "name", "org_id", "serial", "site_id", "status", "type", "version"],
        "unique_constraints": [],
        "description": "getSiteDeviceStats \u2014 stable UUID entities (sample fields: _id, _ttl, arp_table_stats, auto_upgrade_stat, cert_expiry)",
    },
    # Live response fields: ['device_type', 'mac', 'msg', 'start_time', 'status', 'type']
    "getSiteDeviceSyntheticTest": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac", "status", "type"],
        "unique_constraints": [],
        "description": "getSiteDeviceSyntheticTest \u2014 no stable key \u2014 internal id assigned (sample fields: device_type, mac, msg, start_time, status)",
    },
    # Live response fields: ['config_type', 'id', 'mac', 'members', 'model', 'num_routing_engines', 'org_id', 'serial', 'site_id', 'status', 'type', 'vc_mac']
    "getSiteDeviceVirtualChassis": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "org_id", "serial", "site_id", "status", "type"],
        "unique_constraints": [],
        "description": "getSiteDeviceVirtualChassis \u2014 stable UUID entities (sample fields: config_type, id, mac, members, model)",
    },
    # Live response fields: ['root_password']
    "getSiteDeviceZtpPassword": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteDeviceZtpPassword \u2014 no stable key \u2014 internal id assigned (sample fields: root_password)",
    },
    # Live response fields: []
    "getSiteDiscoveredAssetByMap": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteDiscoveredAssetByMap \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['config_success', 'version_compliance']
    "getSiteGatewayMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteGatewayMetrics \u2014 no stable key \u2014 internal id assigned (sample fields: config_success, version_compliance)",
    },
    # Live response fields: ['address', 'alarmtemplate_id', 'aptemplate_id', 'country_code', 'created_time', 'gatewaytemplate_id', 'id', 'lat', 'latlng', 'lng', 'modified_time', 'name', 'networktemplate_id', 'org_id', 'rftemplate_id', 'routertemplate_id', 'secpolicy_id', 'sitegroup_ids', 'sitetemplate_id', 'timezone', 'tzoffset']
    "getSiteInfo": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "getSiteInfo \u2014 stable UUID entities (sample fields: address, alarmtemplate_id, aptemplate_id, country_code, created_time)",
    },
    # Live response fields: ['detail']
    "getSiteJseInfo": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteJseInfo \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['org_entitled', 'org_usage', 'svna_eligible', 'svna_ui', 'trial_enabled', 'trial_end_time', 'usage', 'vna_eligible', 'vna_ui', 'wvna_eligible', 'wvna_ui']
    "getSiteLicenseUsage": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteLicenseUsage \u2014 no stable key \u2014 internal id assigned (sample fields: org_entitled, org_usage, svna_eligible, svna_ui, trial_enabled)",
    },
    # Live response fields: ['beacon_id']
    "getSiteMachineLearningCurrentStat": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteMachineLearningCurrentStat \u2014 no stable key \u2014 internal id assigned (sample fields: beacon_id)",
    },
    # Live response fields: ['created_time', 'height', 'height_m', 'id', 'mapstack_floor', 'mapstack_id', 'modified_time', 'name', 'org_id', 'origin_x', 'origin_y', 'ppm', 'site_id', 'thumbnail_url', 'type', 'url', 'wall_path', 'wayfinding_path', 'width', 'width_m']
    "getSiteMap": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "getSiteMap \u2014 stable UUID entities (sample fields: created_time, height, height_m, id, mapstack_floor)",
    },
    # Live response fields: ['status', 'zones']
    "getSiteMapAutoZoneStatus": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["status"],
        "unique_constraints": [],
        "description": "getSiteMapAutoZoneStatus \u2014 no stable key \u2014 internal id assigned (sample fields: status, zones)",
    },
    # Live response fields: ['detail']
    "getSiteMxEdge": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteMxEdge \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "getSiteMxEdgeStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteMxEdgeStats \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: []
    "getSiteRunningSpectrumAnalysis": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteRunningSpectrumAnalysis \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['analytic', 'auto_upgrade', 'config_auto_revert', 'created_time', 'enable_channel_144', 'enable_unii_4', 'engagement', 'for_site', 'gateway_mgmt', 'id', 'juniper_srx', 'led', 'mgmt', 'modified_time', 'mxedge', 'mxtunnel', 'occupancy', 'org_id', 'paloalto_networks', 'persist_config_on_device', 'public_zone_occupancy', 'rogue', 'rtsa', 'site_id', 'skyatp', 'ssh_keys', 'ssr', 'status_portal', 'switch', 'switch_mgmt', 'synthetic_test', 'tunterm_extra_routes', 'tunterm_other_ip_configs', 'uplink_port_config', 'vars', 'wan_vna', 'wids', 'wifi', 'wired_vna', 'wootcloud', 'zone_occupancy_alert']
    "getSiteSetting": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "getSiteSetting \u2014 stable UUID entities (sample fields: analytic, auto_upgrade, config_auto_revert, created_time, enable_channel_144)",
    },
    # Live response fields: ['acl_policies', 'acl_tags', 'additional_config_cmds', 'allow_mist', 'analytic', 'auto_upgrade', 'bgp_config', 'cloudshark', 'config_auto_revert', 'country_code', 'created_time', 'cx_additional_config_cmds', 'dhcp_snooping', 'disabled_system_defined_port_usages', 'dns_servers', 'dns_suffix', 'enable_channel_144', 'enable_unii_4', 'engagement', 'extra_routes', 'extra_routes6', 'for_site', 'gateway_mgmt', 'id', 'juniper_srx', 'led', 'marvis', 'mgmt', 'mist_nac', 'modified_time', 'mxedge', 'mxtunnel', 'networks', 'networktemplate_id', 'networktemplate_name', 'ntp_servers', 'occupancy', 'org_id', 'paloalto_networks', 'password_policy', 'persist_config_on_device', 'port_mirroring', 'port_usages', 'public_zone_occupancy', 'radio_config', 'radius_config', 'remote_syslog', 'rftemplate_id', 'rftemplate_name', 'rogue', 'routing_policies', 'rtsa', 'site_id', 'skyatp', 'snmp_config', 'ssh_keys', 'ssr', 'status_portal', 'switch', 'switch_matching', 'switch_mgmt', 'synthetic_test', 'tags', 'tunterm_extra_routes', 'tunterm_other_ip_configs', 'uplink_port_config', 'use_site_timezone', 'vars', 'vrf_config', 'vrf_instances', 'wan_vna', 'wids', 'wifi', 'wired_vna', 'wootcloud', 'zone_occupancy_alert']
    "getSiteSettingDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "getSiteSettingDerived \u2014 stable UUID entities (sample fields: acl_policies, acl_tags, additional_config_cmds, allow_mist, analytic)",
    },
    # Live response fields: ['async', 'client_name', 'created_time', 'duration', 'end_time', 'frame_count', 'id', 'is_sitesurvey', 'mac', 'map_id', 'map_name', 'modified_time', 'name', 'org_id', 'raw_events', 'ready', 'site_id', 'start_time', 'type', 'url']
    "getSiteSiteRfdiagRecording": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "getSiteSiteRfdiagRecording \u2014 stable UUID entities (sample fields: async, client_name, created_time, duration, end_time)",
    },
    # Live response fields: ['address', 'alarmtemplate_id', 'aptemplate_id', 'country_code', 'created_time', 'gatewaytemplate_id', 'id', 'lat', 'latlng', 'lng', 'modified_time', 'name', 'networktemplate_id', 'num_ap', 'num_ap_connected', 'num_clients', 'num_devices', 'num_devices_connected', 'num_gateway', 'num_gateway_connected', 'num_router', 'num_router_connected', 'num_switch', 'num_switch_connected', 'org_id', 'rftemplate_id', 'routertemplate_id', 'secpolicy_id', 'sitegroup_ids', 'sitetemplate_id', 'timezone', 'tzoffset']
    "getSiteStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "getSiteStats \u2014 stable UUID entities (sample fields: address, alarmtemplate_id, aptemplate_id, country_code, created_time)",
    },
    # Live response fields: ['active_ports_summary', 'config_success', 'version_compliance', 'version_compliance_all_switches']
    "getSiteSwitchesMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteSwitchesMetrics \u2014 no stable key \u2014 internal id assigned (sample fields: active_ports_summary, config_success, version_compliance, version_compliance_all_switches)",
    },
    # Live response fields: ['detail']
    "getSiteWebhook": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "getSiteWebhook \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['action', 'created_time', 'dst_wxtags', 'enabled', 'for_site', 'id', 'modified_time', 'order', 'org_id', 'site_id', 'src_wxtags', 'template_id']
    "getSiteWxRulesUsage": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "getSiteWxRulesUsage \u2014 stable UUID entities (sample fields: action, created_time, dst_wxtags, enabled, for_site)",
    },
    # Live response fields: ['default_enabled', 'display', 'example', 'fields', 'group', 'key', 'severity']
    "listAlarmDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listAlarmDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: default_enabled, display, example, fields, group)",
    },
    # Live response fields: ['detail']
    "listApChannels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listApChannels \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['esl_version', 'model']
    "listApLEslVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model"],
        "unique_constraints": [],
        "description": "listApLEslVersions \u2014 no stable key \u2014 internal id assigned (sample fields: esl_version, model)",
    },
    # Live response fields: ['code', 'description', 'key', 'name']
    "listApLedDefinition": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listApLedDefinition \u2014 no stable key \u2014 internal id assigned (sample fields: code, description, key, name)",
    },
    # Live response fields: ['detail']
    "listApiTokens": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listApiTokens \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['display', 'filters', 'key', 'traffic_type']
    "listAppCategoryDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listAppCategoryDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: display, filters, key, traffic_type)",
    },
    # Live response fields: ['display', 'key', 'traffic_type']
    "listAppSubCategoryDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listAppSubCategoryDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: display, key, traffic_type)",
    },
    # Live response fields: ['app_id', 'group', 'key', 'name']
    "listApplications": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listApplications \u2014 no stable key \u2014 internal id assigned (sample fields: app_id, group, key, name)",
    },
    # Live response fields: ['display', 'key']
    "listClientEventsDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listClientEventsDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: display, key)",
    },
    # Live response fields: ['alpha2', 'certified', 'eu', 'name', 'numeric']
    "listCountryCodes": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listCountryCodes \u2014 no stable key \u2014 internal id assigned (sample fields: alpha2, certified, eu, name, numeric)",
    },
    # Live response fields: ['description', 'display', 'example', 'key']
    "listDeviceEventsDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listDeviceEventsDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: description, display, example, key)",
    },
    # Live response fields: ['ap_type', 'band24', 'band5', 'ce_dfs_ok', 'description', 'disallowed_channels', 'display', 'extio', 'fcc_dfs_ok', 'has_compass', 'has_extio', 'has_height', 'has_module_port', 'has_poe_out', 'has_scanning_radio', 'has_usb', 'has_vble', 'has_wifi_band24', 'has_wifi_band5', 'max_poe_out', 'model', 'other_dfs_ok', 'radios', 'type', 'vble']
    "listDeviceModels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "type"],
        "unique_constraints": [],
        "description": "listDeviceModels \u2014 no stable key \u2014 internal id assigned (sample fields: ap_type, band24, band5, ce_dfs_ok, description)",
    },
    # Live response fields: ['family', 'mfg', 'model', 'os']
    "listFingerprintTypes": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model"],
        "unique_constraints": [],
        "description": "listFingerprintTypes \u2014 no stable key \u2014 internal id assigned (sample fields: family, mfg, model, os)",
    },
    # Live response fields: ['key', 'name', 'ssr_app_id']
    "listGatewayApplications": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listGatewayApplications \u2014 no stable key \u2014 internal id assigned (sample fields: key, name, ssr_app_id)",
    },
    # Live response fields: ['acl-policy', 'activity', 'ap-availability', 'ap-count', 'ap-rf-metrics', 'app-bytes', 'band24-util', 'band5-util', 'band6-util', 'bgp-ribs-metrics', 'bps', 'bytes', 'call-metrics', 'call-user_cpu', 'call-user_feedback', 'call-user_qos', 'channel-util', 'client-auth-latency', 'client-capacity-band24', 'client-capacity-band5', 'client-coverage-band24', 'client-coverage-band5', 'client-dhcp-latency', 'client-rf-metrics', 'client-roam-band24', 'client-roam-band5', 'cpu', 'dns-latency', 'edge-uptime-bar', 'gateway-metrics', 'lte_rssi', 'memory', 'minis-app-metrics', 'minis-probe-stats', 'minis-top-probes', 'nac_metrics', 'network-table-metrics', 'network_connection', 'noise', 'num_aps', 'num_clients', 'num_clients-by-sites', 'num_ips', 'num_mxtunnels', 'num_sessions', 'optic-metrics', 'orgs-sle', 'orgs-sle-filtered', 'port_rx_errors', 'port_tx_errors', 'power_draw', 'rssi', 'rx_bcast', 'rx_bps', 'rx_bytes', 'rx_mcast', 'rx_pkts', 'rx_rates', 'rx_retries', 'sensor', 'sites-sle', 'sites-sle-by-calls', 'sites-sle-filtered', 'sites-sw-metrics', 'sites-wa-metrics', 'sites-wan-assurance-metrics', 'spu', 'spu_memory', 'successful-connect', 'summary', 'switch-metrics', 'time-to-connect', 'top-ap-by-bytes', 'top-ap-by-num_client', 'top-app-by-bytes', 'top-app-by-num_client', 'top-categories-by-bytes', 'top-client', 'top-client-by-num_ssids', 'top-client-by-threats', 'top-client-events-by-type', 'top-client_or_ip-by-bytes', 'top-device-events-by-type', 'top-device-events-count', 'top-gateway-by-bytes', 'top-grouped-apps', 'top-ip', 'top-nac-client-events-by-type', 'top-port-by-bytes', 'top-services-by-bytes', 'top-switch-by-bytes', 'top-wan-apps', 'top-wan-policy-by-bytes', 'top-wired-client-events-by-type', 'top-wlan-by-bytes', 'top-wlan-by-num_client', 'tx_bcast', 'tx_bps', 'tx_bytes', 'tx_mcast', 'tx_pkts', 'tx_rates', 'tx_retries', 'tx_rx_bps', 'uptime-bar', 'vpn_peer', 'vpn_peer-metrics', 'wan_link_health', 'wan_policy_hit_count', 'worst-orgs-by-sle', 'worst-orgs-by-sle-filtered', 'worst-sites-by-calls', 'worst-sites-by-sle', 'worst-sites-by-sle-filtered', 'worst-sites-by-switch-metrics', 'worst-sites-by-wan-assurance-metrics', 'worst-sites-by-wired-assurance-metrics', 'worst-sites-sle-by-calls', 'worst-vpn_peers', '{ctype}-dwell', '{ctype}-loyalty', '{ctype}-visit', '{ctype}-zones']
    "listInsightMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listInsightMetrics \u2014 no stable key \u2014 internal id assigned (sample fields: acl-policy, activity, ap-availability, ap-count, ap-rf-metrics)",
    },
    # Live response fields: []
    "listInstallerAlarmTemplates": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listInstallerAlarmTemplates \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "listInstallerDeviceProfiles": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listInstallerDeviceProfiles \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "listInstallerRfTemplatesNames": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listInstallerRfTemplatesNames \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "listInstallerSiteGroups": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listInstallerSiteGroups \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['key', 'name', 'type']
    "listLicenseTypes": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name", "type"],
        "unique_constraints": [],
        "description": "listLicenseTypes \u2014 no stable key \u2014 internal id assigned (sample fields: key, name, type)",
    },
    # Live response fields: ['checksum', 'label', 'notes', 'os', 'url', 'version']
    "listMarvisClientVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["version"],
        "unique_constraints": [],
        "description": "listMarvisClientVersions \u2014 no stable key \u2014 internal id assigned (sample fields: checksum, label, notes, os, url)",
    },
    # Live response fields: ['description', 'display', 'example', 'key']
    "listMxEdgeEventsDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listMxEdgeEventsDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: description, display, example, key)",
    },
    # Live response fields: ['display', 'model', 'ports']
    "listMxEdgeModels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model"],
        "unique_constraints": [],
        "description": "listMxEdgeModels \u2014 no stable key \u2014 internal id assigned (sample fields: display, model, ports)",
    },
    # Live response fields: ['ap', 'bssid', 'cert_cn', 'cert_expiry', 'cert_issuer', 'cert_san_upn', 'cert_serial', 'cert_subject', 'nas_vendor', 'org_id', 'random_mac', 'site_id', 'ssid', 'timestamp', 'type', 'username', 'wcid']
    "listNacEventsDefinitions": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listNacEventsDefinitions \u2014 event/log time-series records (sample fields: ap, bssid, cert_cn, cert_expiry, cert_issuer)",
    },
    # Live response fields: ['admin_id', 'email', 'first_name', 'last_name', 'privileges', 'two_factor_verified']
    "listOrgAdmins": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgAdmins \u2014 no stable key \u2014 internal id assigned (sample fields: admin_id, email, first_name, last_name, privileges)",
    },
    # Live response fields: ['created_time', 'delivery', 'id', 'modified_time', 'name', 'org_id', 'rules']
    "listOrgAlarmTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgAlarmTemplates \u2014 stable UUID entities (sample fields: created_time, delivery, id, modified_time, name)",
    },
    # Live response fields: ['created_by', 'created_time', 'id', 'key', 'last_used', 'name', 'org_id', 'privileges']
    "listOrgApiTokens": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgApiTokens \u2014 stable UUID entities (sample fields: created_by, created_time, id, key, last_used)",
    },
    # Live response fields: ['mac', 'radio_mac']
    "listOrgApsMacs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "listOrgApsMacs \u2014 no stable key \u2014 internal id assigned (sample fields: mac, radio_mac)",
    },
    # Live response fields: ['created_time', 'id', 'modified_time', 'name', 'org_id']
    "listOrgAptemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgAptemplates \u2014 stable UUID entities (sample fields: created_time, id, modified_time, name, org_id)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "listOrgAuditLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgAuditLogs \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['_version', 'model', 'tag', 'tags', 'version']
    "listOrgAvailableDeviceVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "version"],
        "unique_constraints": [],
        "description": "listOrgAvailableDeviceVersions \u2014 no stable key \u2014 internal id assigned (sample fields: _version, model, tag, tags, version)",
    },
    # Live response fields: ['_version', 'default', 'package', 'version']
    "listOrgAvailableSsrVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["version"],
        "unique_constraints": [],
        "description": "listOrgAvailableSsrVersions \u2014 no stable key \u2014 internal id assigned (sample fields: _version, default, package, version)",
    },
    # Live response fields: ['cert']
    "listOrgCertificates": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgCertificates \u2014 no stable key \u2014 internal id assigned (sample fields: cert)",
    },
    # Live response fields: ['aeroscout', 'ble_config', 'centrak', 'created_time', 'disable_eth1', 'disable_eth2', 'disable_eth3', 'disable_module', 'esl_config', 'id', 'ip_config', 'led', 'mesh', 'modified_time', 'name', 'org_id', 'poe_passthrough', 'radio_config', 'switch_config', 'type', 'uplink_port_config', 'usb_config', 'vars']
    "listOrgDeviceProfiles": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listOrgDeviceProfiles \u2014 stable UUID entities (sample fields: aeroscout, ble_config, centrak, created_time, disable_eth1)",
    },
    # Live response fields: ['mac', 'name']
    "listOrgDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac", "name"],
        "unique_constraints": [],
        "description": "listOrgDevices \u2014 no stable key \u2014 internal id assigned (sample fields: mac, name)",
    },
    # Live response fields: ['_id', '_ttl', 'auto_upgrade_stat', 'ble_stat', 'cert_expiry', 'cpu2_stat', 'cpu_stat', 'created_time', 'deviceprofile_id', 'evpntopo_id', 'expiring_certs', 'height', 'hw_rev', 'id', 'ip', 'last_seen', 'locating', 'mac', 'map_id', 'memory2_stat', 'memory_stat', 'model', 'modified_time', 'module2_stat', 'module_stat', 'name', 'notes', 'org_id', 'orientation', 'orientation_overwrite', 'radio_config', 'serial', 'site_id', 'status', 'switch_redundancy', 'tag_id', 'tag_uuid', 'type', 'uptime', 'version', 'x', 'x_m', 'y', 'y_m']
    "listOrgDevicesStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "status", "type", "version"],
        "unique_constraints": [],
        "description": "listOrgDevicesStats \u2014 stable UUID entities (sample fields: _id, _ttl, auto_upgrade_stat, ble_stat, cert_expiry)",
    },
    # Live response fields: ['num_aps', 'num_gateways', 'num_mxedges', 'num_switches', 'num_unassigned_aps', 'num_unassigned_gateways', 'num_unassigned_switches']
    "listOrgDevicesSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgDevicesSummary \u2014 no stable key \u2014 internal id assigned (sample fields: num_aps, num_gateways, num_mxedges, num_switches, num_unassigned_aps)",
    },
    # Live response fields: ['bgp_config', 'created_time', 'dhcpd_config', 'dns_servers', 'extra_routes', 'gateway_mgmt', 'host_in_policies', 'id', 'ip_configs', 'modified_time', 'name', 'ntp_servers', 'oob_ip_config', 'org_id', 'ospf_areas', 'ospf_config', 'path_preferences', 'port_config', 'remote_syslog', 'routing_policies', 'service_policies', 'tunnel_configs', 'tunnel_provider_options', 'type', 'vrf_instances']
    "listOrgGatewayTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listOrgGatewayTemplates \u2014 stable UUID entities (sample fields: bgp_config, created_time, dhcpd_config, dns_servers, extra_routes)",
    },
    # Live response fields: ['detail']
    "listOrgJsiPastPurchases": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgJsiPastPurchases \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['created_time', 'id', 'mist_nac', 'modified_time', 'name', 'org_id', 'radsec', 'tunterm_ap_subnets', 'tunterm_hosts', 'tunterm_hosts_selection']
    "listOrgMxEdgeClusters": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgMxEdgeClusters \u2014 stable UUID entities (sample fields: created_time, id, mist_nac, modified_time, name)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'magic', 'model', 'modified_time', 'mxagent_registered', 'mxcluster_id', 'mxedge_mgmt', 'name', 'notes', 'oob_ip_config', 'org_id', 'serial', 'services', 'site_id', 'tunterm_dhcpd_config', 'tunterm_extra_routes', 'tunterm_igmp_snooping_config', 'tunterm_ip_config', 'tunterm_other_ip_configs', 'tunterm_port_config', 'tunterm_registered']
    "listOrgMxEdges": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id"],
        "unique_constraints": [],
        "description": "listOrgMxEdges \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, magic)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'magic', 'model', 'modified_time', 'mxagent_registered', 'mxcluster_id', 'mxedge_mgmt', 'name', 'notes', 'oob_ip_config', 'org_id', 'serial', 'services', 'site_id', 'status', 'tunterm_dhcpd_config', 'tunterm_extra_routes', 'tunterm_igmp_snooping_config', 'tunterm_ip_config', 'tunterm_other_ip_configs', 'tunterm_port_config', 'tunterm_registered']
    "listOrgMxEdgesStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "status"],
        "unique_constraints": [],
        "description": "listOrgMxEdgesStats \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, magic)",
    },
    # Live response fields: ['anchor_mxtunnel_ids', 'auto_preemption', 'created_time', 'hello_interval', 'hello_retries', 'id', 'ipsec', 'modified_time', 'mtu', 'mxcluster_ids', 'name', 'org_id', 'protocol', 'vlan_ids']
    "listOrgMxTunnels": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgMxTunnels \u2014 stable UUID entities (sample fields: anchor_mxtunnel_ids, auto_preemption, created_time, hello_interval, hello_retries)",
    },
    # Live response fields: ['action', 'apply_tags', 'created_time', 'enabled', 'id', 'matching', 'modified_time', 'name', 'order', 'org_id']
    "listOrgNacRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgNacRules \u2014 stable UUID entities (sample fields: action, apply_tags, created_time, enabled, id)",
    },
    # Live response fields: ['created_time', 'id', 'match', 'modified_time', 'name', 'org_id', 'type', 'values']
    "listOrgNacTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listOrgNacTags \u2014 stable UUID entities (sample fields: created_time, id, match, modified_time, name)",
    },
    # Live response fields: ['acl_policies', 'acl_tags', 'additional_config_cmds', 'bgp_config', 'created_time', 'cx_additional_config_cmds', 'dhcp_snooping', 'disabled_system_defined_port_usages', 'dns_servers', 'dns_suffix', 'extra_routes', 'extra_routes6', 'id', 'mist_nac', 'modified_time', 'name', 'networks', 'ntp_servers', 'org_id', 'port_mirroring', 'port_usages', 'radius_config', 'remote_syslog', 'routing_policies', 'snmp_config', 'switch_matching', 'switch_mgmt', 'use_site_timezone', 'vrf_config']
    "listOrgNetworkTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgNetworkTemplates \u2014 stable UUID entities (sample fields: acl_policies, acl_tags, additional_config_cmds, bgp_config, created_time)",
    },
    # Live response fields: ['created_time', 'destNats', 'disallow_mist_services', 'id', 'internet_access', 'isolation', 'modified_time', 'name', 'org_id', 'routed_for_networks', 'sourceNats', 'subnet', 'subnet6', 'tenants', 'vpn_access']
    "listOrgNetworks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgNetworks \u2014 stable UUID entities (sample fields: created_time, destNats, disallow_mist_services, id, internet_access)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "listOrgPacketCaptures": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgPacketCaptures \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['description', 'label', 'name', 'url']
    "listOrgPmaDashboards": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listOrgPmaDashboards \u2014 no stable key \u2014 internal id assigned (sample fields: description, label, name, url)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "listOrgPskPortalLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgPskPortalLogs \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['admin_sso_id', 'created_time', 'expire_time', 'for_site', 'id', 'last_used', 'modified_time', 'name', 'notify_expiry', 'notify_on_create_or_edit', 'old_passphrase', 'org_id', 'passphrase', 'portal_id', 'role', 'site_id', 'ssid', 'usage']
    "listOrgPsks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listOrgPsks \u2014 stable UUID entities (sample fields: admin_sso_id, created_time, expire_time, for_site, id)",
    },
    # Live response fields: ['ant_gain_24', 'ant_gain_5', 'ant_gain_6', 'antenna_select', 'band_24', 'band_24_usage', 'band_5', 'band_6', 'country_code', 'created_time', 'id', 'model_specific', 'modified_time', 'name', 'org_id']
    "listOrgRfTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgRfTemplates \u2014 stable UUID entities (sample fields: ant_gain_24, ant_gain_5, ant_gain_6, antenna_select, band_24)",
    },
    # Live response fields: ['action', 'createdBy', 'created_time', 'id', 'idp', 'modified_time', 'name', 'org_id', 'services', 'tenants']
    "listOrgServicePolicies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgServicePolicies \u2014 stable UUID entities (sample fields: action, createdBy, created_time, id, idp)",
    },
    # Live response fields: ['addresses', 'created_time', 'id', 'modified_time', 'name', 'org_id', 'specs', 'traffic_type', 'type']
    "listOrgServices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listOrgServices \u2014 stable UUID entities (sample fields: addresses, created_time, id, modified_time, name)",
    },
    # Live response fields: ['created_time', 'id', 'modified_time', 'name', 'org_id', 'site_ids']
    "listOrgSiteGroups": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgSiteGroups \u2014 stable UUID entities (sample fields: created_time, id, modified_time, name, org_id)",
    },
    # Live response fields: ['address', 'alarmtemplate_id', 'aptemplate_id', 'country_code', 'created_time', 'gatewaytemplate_id', 'id', 'latlng', 'modified_time', 'msp_id', 'name', 'networktemplate_id', 'notes', 'num_ap', 'num_ap_connected', 'num_clients', 'num_devices', 'num_devices_connected', 'num_gateway', 'num_gateway_connected', 'num_router', 'num_router_connected', 'num_switch', 'num_switch_connected', 'org_id', 'rftemplate_id', 'routertemplate_id', 'secpolicy_id', 'sitetemplate_id', 'timezone', 'tzoffset']
    "listOrgSiteStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgSiteStats \u2014 stable UUID entities (sample fields: address, alarmtemplate_id, aptemplate_id, country_code, created_time)",
    },
    # Live response fields: ['analytic', 'appliedSites', 'auto_upgrade', 'config_auto_revert', 'created_time', 'enable_unii_4', 'engagement', 'gateway_mgmt', 'id', 'led', 'mgmt', 'modified_time', 'mxedge', 'name', 'notes', 'org_id', 'persist_config_on_device', 'rftemplate_id', 'rogue', 'rtsa', 'sitegroup_ids', 'sitetemplate_id', 'skyatp', 'ssh_keys', 'ssr', 'status_portal', 'switch_mgmt', 'synthetic_test', 'uplink_port_config', 'vars', 'wids', 'wifi', 'wootcloud']
    "listOrgSiteTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgSiteTemplates \u2014 stable UUID entities (sample fields: analytic, appliedSites, auto_upgrade, config_auto_revert, created_time)",
    },
    # Live response fields: ['address', 'alarmtemplate_id', 'aptemplate_id', 'country_code', 'created_time', 'gatewaytemplate_id', 'id', 'latlng', 'modified_time', 'name', 'networktemplate_id', 'notes', 'org_id', 'rftemplate_id', 'routertemplate_id', 'secpolicy_id', 'sitetemplate_id', 'timezone', 'tzoffset']
    "listOrgSites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgSites \u2014 stable UUID entities (sample fields: address, alarmtemplate_id, aptemplate_id, country_code, created_time)",
    },
    # Live response fields: ['created_time', 'domain', 'id', 'modified_time', 'msp_id', 'name', 'org_id']
    "listOrgSsos": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgSsos \u2014 stable UUID entities (sample fields: created_time, domain, id, modified_time, msp_id)",
    },
    # Live response fields: ['results']
    "listOrgSuppressedAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOrgSuppressedAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: results)",
    },
    # Live response fields: ['applies', 'created_time', 'deviceprofile_ids', 'exceptions', 'filter_by_deviceprofile', 'id', 'modified_time', 'name', 'org_id']
    "listOrgTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgTemplates \u2014 stable UUID entities (sample fields: applies, created_time, deviceprofile_ids, exceptions, filter_by_deviceprofile)",
    },
    # Live response fields: ['created_time', 'defaultScopeId', 'defaultScopeType', 'defaultTimeRange', 'description', 'for_site', 'id', 'isCustomDataboard', 'isEngagement', 'isScopeLinked', 'isTimeRangeLinked', 'modified_time', 'name', 'org_id', 'purpose', 'site_id', 'tiles']
    "listOrgUiSettings": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listOrgUiSettings \u2014 stable UUID entities (sample fields: created_time, defaultScopeId, defaultScopeType, defaultTimeRange, description)",
    },
    # Live response fields: ['created_time', 'id', 'modified_time', 'name', 'org_id', 'paths']
    "listOrgVpns": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listOrgVpns \u2014 stable UUID entities (sample fields: created_time, id, modified_time, name, org_id)",
    },
    # Live response fields: ['assetfilter_ids', 'created_time', 'enabled', 'for_site', 'id', 'modified_time', 'name', 'org_id', 'site_id', 'topics', 'type', 'url', 'verify_cert']
    "listOrgWebhooks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listOrgWebhooks \u2014 stable UUID entities (sample fields: assetfilter_ids, created_time, enabled, for_site, id)",
    },
    # Live response fields: ['acct_interim_interval', 'acct_servers', 'airwatch', 'allow_ipv6_ndp', 'allow_mdns', 'allow_ssdp', 'ap_ids', 'app_limit', 'app_qos', 'apply_to', 'arp_filter', 'auth', 'auth_server_selection', 'auth_servers', 'auth_servers_nas_id', 'auth_servers_nas_ip', 'band_steer', 'bands', 'bonjour', 'cisco_cwa', 'client_limit_down', 'client_limit_down_enabled', 'client_limit_up', 'client_limit_up_enabled', 'coa_servers', 'created_time', 'disable_11ax', 'disable_11be', 'disable_uapsd', 'disable_when_gateway_unreachable', 'disable_wmm', 'dns_server_rewrite', 'dtim', 'dynamic_psk', 'dynamic_vlan', 'enabled', 'for_site', 'hide_ssid', 'hostname_ie', 'hotspot20', 'id', 'interface', 'legacy_overds', 'limit_bcast', 'limit_probe_response', 'max_idletime', 'mist_nac', 'modified_time', 'mxtunnel_id', 'mxtunnel_ids', 'no_static_dns', 'no_static_ip', 'org_id', 'portal', 'portal_allowed_hostnames', 'portal_allowed_subnets', 'portal_api_secret', 'portal_denied_hostnames', 'qos', 'radsec', 'rateset', 'roam_mode', 'schedule', 'site_id', 'ssid', 'template_id', 'use_eapol_v1', 'vlan_enabled', 'vlan_id', 'vlan_ids', 'vlan_pooling', 'wlan_limit_down', 'wlan_limit_down_enabled', 'wlan_limit_up', 'wlan_limit_up_enabled', 'wxtag_ids', 'wxtunnel_id', 'wxtunnel_remote_id']
    "listOrgWlans": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "listOrgWlans \u2014 stable UUID entities (sample fields: acct_interim_interval, acct_servers, airwatch, allow_ipv6_ndp, allow_mdns)",
    },
    # Live response fields: ['action', 'created_time', 'dst_allow_wxtags', 'dst_deny_wxtags', 'dst_wxtags', 'enabled', 'for_site', 'id', 'modified_time', 'name', 'order', 'org_id', 'site_id', 'src_wxtags', 'template_id']
    "listOrgWxRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listOrgWxRules \u2014 stable UUID entities (sample fields: action, created_time, dst_allow_wxtags, dst_deny_wxtags, dst_wxtags)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'match', 'modified_time', 'name', 'op', 'org_id', 'resource_mac', 'site_id', 'type', 'values']
    "listOrgWxTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listOrgWxTags \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, match)",
    },
    # Live response fields: ['display', 'example', 'key']
    "listOtherDeviceEventsDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listOtherDeviceEventsDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: display, example, key)",
    },
    # Live response fields: ['created_time', 'expiring_time', 'id', 'name', 'org_id', 'quota', 'secret']
    "listSdkInvites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSdkInvites \u2014 stable UUID entities (sample fields: created_time, expiring_time, id, name, org_id)",
    },
    # Live response fields: ['admin_id', 'admin_name', 'id', 'message', 'org_id', 'site_id', 'src_ip', 'timestamp', 'user_agent']
    "listSelfAuditLogs": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSelfAuditLogs \u2014 event/log time-series records (sample fields: admin_id, admin_name, id, message, org_id)",
    },
    # Live response fields: ['created_time', 'id', 'modified_time', 'name', 'org_id']
    "listSiteApTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteApTemplatesDerived \u2014 stable UUID entities (sample fields: created_time, id, modified_time, name, org_id)",
    },
    # Live response fields: []
    "listSiteApps": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteApps \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'map_id', 'modified_time', 'name', 'org_id', 'site_id', 'tag_id']
    "listSiteAssets": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteAssets \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, map_id)",
    },
    # Live response fields: ['_id', '_ttl', 'ap_mac', 'beam', 'by', 'created_time', 'curr_site', 'device_name', 'for_site', 'id', 'last_seen', 'mac', 'manufacture', 'map_id', 'mfg_company_id', 'mfg_data', 'modified_time', 'name', 'org_id', 'rssi', 'site_id', 'tag_id', 'x', 'y']
    "listSiteAssetsStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteAssetsStats \u2014 stable UUID entities (sample fields: _id, _ttl, ap_mac, beam, by)",
    },
    # Live response fields: ['_version', 'model', 'tag', 'tags', 'version']
    "listSiteAvailableDeviceVersions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "version"],
        "unique_constraints": [],
        "description": "listSiteAvailableDeviceVersions \u2014 no stable key \u2014 internal id assigned (sample fields: _version, model, tag, tags, version)",
    },
    # Live response fields: ['created_time', 'eddystone_instance', 'eddystone_namespace', 'eddystone_url', 'ibeacon_major', 'ibeacon_minor', 'ibeacon_uuid', 'id', 'mac', 'map_id', 'modified_time', 'name', 'org_id', 'power', 'power_mode', 'site_id', 'type', 'url', 'x', 'x_m', 'y', 'y_m']
    "listSiteBeacons": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteBeacons \u2014 stable UUID entities (sample fields: created_time, eddystone_instance, eddystone_namespace, eddystone_url, ibeacon_major)",
    },
    # Live response fields: ['created_time', 'eddystone_instance', 'eddystone_namespace', 'eddystone_url', 'ibeacon_major', 'ibeacon_minor', 'ibeacon_uuid', 'id', 'mac', 'map_id', 'modified_time', 'name', 'org_id', 'power', 'power_mode', 'site_id', 'type', 'url', 'x', 'x_m', 'y', 'y_m']
    "listSiteBeaconsStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteBeaconsStats \u2014 stable UUID entities (sample fields: created_time, eddystone_instance, eddystone_namespace, eddystone_url, ibeacon_major)",
    },
    # Live response fields: ['aeroscout', 'ble_config', 'centrak', 'created_time', 'disable_eth1', 'disable_eth2', 'disable_eth3', 'disable_module', 'esl_config', 'id', 'ip_config', 'mesh', 'modified_time', 'name', 'org_id', 'poe_passthrough', 'radio_config', 'switch_config', 'type', 'uplink_port_config', 'vars']
    "listSiteDeviceProfilesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listSiteDeviceProfilesDerived \u2014 stable UUID entities (sample fields: aeroscout, ble_config, centrak, created_time, disable_eth1)",
    },
    # Live response fields: ['band24_40mhz_allowed', 'band24_channels', 'band24_enabled', 'band5_channels', 'band5_enabled', 'band6_channels', 'band6_enabled', 'certified', 'code', 'dfs_ok', 'key', 'name', 'unii4_allowed', 'uses', 'uwb_allowed']
    "listSiteDeviceRadioChannels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listSiteDeviceRadioChannels \u2014 no stable key \u2014 internal id assigned (sample fields: band24_40mhz_allowed, band24_channels, band24_enabled, band5_channels, band5_enabled)",
    },
    # Live response fields: ['adopted', 'bundled_mac', 'created_time', 'deviceprofile_id', 'evpn_scope', 'evpntopo_id', 'height', 'hw_rev', 'id', 'locating', 'mac', 'map_id', 'mist_configured', 'model', 'modified_time', 'name', 'notes', 'org_id', 'orientation', 'orientation_overwrite', 'radio_config', 'serial', 'site_id', 'st_ip_base', 'tag_id', 'tag_uuid', 'type', 'x', 'x_m', 'y', 'y_m']
    "listSiteDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteDevices \u2014 stable UUID entities (sample fields: adopted, bundled_mac, created_time, deviceprofile_id, evpn_scope)",
    },
    # Live response fields: ['_id', '_offset_apbasic', '_offset_apstats', '_partition', '_ttl', 'auto_upgrade_stat', 'ble_stat', 'cert_expiry', 'config_reverted', 'cpu_system', 'cpu_user', 'cpu_util', 'created_time', 'deviceprofile_id', 'env_stat', 'esl_stat', 'evpntopo_id', 'expiring_certs', 'ext_ip', 'fwupdate', 'height', 'hw_rev', 'id', 'inactive_wired_vlans', 'iot_stat', 'ip', 'ip_stat', 'l2tp_stat', 'lacp_stat', 'last_seen', 'last_trouble', 'lldp_stat', 'lldp_stats', 'locating', 'mac', 'map_id', 'mem_total_kb', 'mem_used_kb', 'model', 'modified_time', 'mount', 'name', 'notes', 'num_clients', 'num_wlans', 'org_id', 'orientation', 'orientation_overwrite', 'port_stat', 'power_avail', 'power_budget', 'power_constrained', 'power_needed', 'power_opmode', 'power_src', 'power_srcs', 'radio_config', 'radio_stat', 'radius_stat', 'rx_bps', 'rx_bytes', 'rx_pkts', 'serial', 'site_id', 'status', 'switch_redundancy', 'tag_id', 'tag_uuid', 'tx_bps', 'tx_bytes', 'tx_pkts', 'type', 'uptime', 'version', 'x', 'x_m', 'y', 'y_m']
    "listSiteDevicesStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "status", "type", "version"],
        "unique_constraints": [],
        "description": "listSiteDevicesStats \u2014 stable UUID entities (sample fields: _id, _offset_apbasic, _offset_apstats, _partition, _ttl)",
    },
    # Live response fields: ['_id', '_ttl', 'curr_site', 'last_seen', 'mac', 'manufacture', 'map_id', 'x', 'x_m', 'y', 'y_m']
    "listSiteDiscoveredAssets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "listSiteDiscoveredAssets \u2014 no stable key \u2014 internal id assigned (sample fields: _id, _ttl, curr_site, last_seen, mac)",
    },
    # Live response fields: ['ap_redundancy', 'inactive_wired_vlans', 'poe_compliance', 'switch_ap_affinity']
    "listSiteDiscoveredSwitchesMetrics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteDiscoveredSwitchesMetrics \u2014 no stable key \u2014 internal id assigned (sample fields: ap_redundancy, inactive_wired_vlans, poe_compliance, switch_ap_affinity)",
    },
    # Live response fields: ['bgp_config', 'created_time', 'dhcpd_config', 'dns_servers', 'extra_routes', 'gateway_mgmt', 'host_in_policies', 'id', 'ip_configs', 'modified_time', 'name', 'ntp_servers', 'oob_ip_config', 'org_id', 'ospf_areas', 'ospf_config', 'path_preferences', 'port_config', 'remote_syslog', 'routing_policies', 'service_policies', 'tunnel_configs', 'tunnel_provider_options', 'type', 'vrf_instances']
    "listSiteGatewayTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listSiteGatewayTemplatesDerived \u2014 stable UUID entities (sample fields: bgp_config, created_time, dhcpd_config, dns_servers, extra_routes)",
    },
    # Live response fields: ['display', 'display_native', 'key']
    "listSiteLanguages": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteLanguages \u2014 no stable key \u2014 internal id assigned (sample fields: display, display_native, key)",
    },
    # Live response fields: ['created_time', 'height', 'height_m', 'id', 'mapstack_floor', 'mapstack_id', 'modified_time', 'name', 'org_id', 'origin_x', 'origin_y', 'ppm', 'site_id', 'thumbnail_url', 'type', 'url', 'wall_path', 'wayfinding_path', 'width', 'width_m']
    "listSiteMaps": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteMaps \u2014 stable UUID entities (sample fields: created_time, height, height_m, id, mapstack_floor)",
    },
    # Live response fields: ['acl_policies', 'additional_config_cmds', 'bgp_config', 'created_time', 'dhcp_snooping', 'disabled_system_defined_port_usages', 'dns_servers', 'dns_suffix', 'extra_routes', 'extra_routes6', 'id', 'mist_nac', 'modified_time', 'name', 'networks', 'ntp_servers', 'org_id', 'port_mirroring', 'port_usages', 'radius_config', 'remote_syslog', 'routing_policies', 'snmp_config', 'switch_matching', 'switch_mgmt', 'vrf_config']
    "listSiteNetworkTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteNetworkTemplatesDerived \u2014 stable UUID entities (sample fields: acl_policies, additional_config_cmds, bgp_config, created_time, dhcp_snooping)",
    },
    # Live response fields: ['created_time', 'destNats', 'disallow_mist_services', 'id', 'internet_access', 'isolation', 'modified_time', 'name', 'org_id', 'routed_for_networks', 'sourceNats', 'subnet', 'subnet6', 'tenants', 'vlan_id', 'vpn_access']
    "listSiteNetworksDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteNetworksDerived \u2014 stable UUID entities (sample fields: created_time, destNats, disallow_mist_services, id, internet_access)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "listSitePacketCaptures": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSitePacketCaptures \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['band_24', 'band_24_usage', 'band_5', 'band_6', 'country_code', 'created_time', 'id', 'modified_time', 'name', 'org_id']
    "listSiteRfTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteRfTemplatesDerived \u2014 stable UUID entities (sample fields: band_24, band_24_usage, band_5, band_6, country_code)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start']
    "listSiteRoamingEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteRoamingEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start']
    "listSiteRogueAPs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteRogueAPs \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start']
    "listSiteRogueClients": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteRogueClients \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start)",
    },
    # Live response fields: ['detail']
    "listSiteRrmEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteRrmEvents \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['action', 'createdBy', 'created_time', 'id', 'idp', 'modified_time', 'name', 'org_id', 'services', 'tenants']
    "listSiteServicePoliciesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteServicePoliciesDerived \u2014 stable UUID entities (sample fields: action, createdBy, created_time, id, idp)",
    },
    # Live response fields: ['addresses', 'created_time', 'id', 'modified_time', 'name', 'org_id', 'specs', 'traffic_type', 'type']
    "listSiteServicesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "type"],
        "unique_constraints": [],
        "description": "listSiteServicesDerived \u2014 stable UUID entities (sample fields: addresses, created_time, id, modified_time, name)",
    },
    # Live response fields: ['analytic', 'appliedSites', 'auto_upgrade', 'config_auto_revert', 'created_time', 'enable_unii_4', 'engagement', 'gateway_mgmt', 'id', 'led', 'mgmt', 'modified_time', 'mxedge', 'name', 'notes', 'org_id', 'persist_config_on_device', 'rftemplate_id', 'rogue', 'rtsa', 'sitegroup_ids', 'sitetemplate_id', 'skyatp', 'ssh_keys', 'ssr', 'status_portal', 'switch_mgmt', 'synthetic_test', 'uplink_port_config', 'vars', 'wids', 'wifi', 'wootcloud']
    "listSiteSiteTemplatesDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteSiteTemplatesDerived \u2014 stable UUID entities (sample fields: analytic, appliedSites, auto_upgrade, config_auto_revert, created_time)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "listSiteSpectrumAnalysis": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteSpectrumAnalysis \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'start']
    "listSiteTroubleshootCalls": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSiteTroubleshootCalls \u2014 no stable key \u2014 internal id assigned (sample fields: end, start)",
    },
    # Live response fields: ['created_time', 'defaultScopeId', 'defaultScopeType', 'defaultTimeRange', 'description', 'for_site', 'id', 'isCustomDataboard', 'isEngagement', 'isScopeLinked', 'isTimeRangeLinked', 'modified_time', 'name', 'org_id', 'purpose', 'site_id', 'tiles']
    "listSiteUiSettingDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteUiSettingDerived \u2014 stable UUID entities (sample fields: created_time, defaultScopeId, defaultScopeType, defaultTimeRange, description)",
    },
    # Live response fields: ['createdBy', 'created_time', 'id', 'modified_time', 'name', 'org_id', 'paths']
    "listSiteVpnsDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "listSiteVpnsDerived \u2014 stable UUID entities (sample fields: createdBy, created_time, id, modified_time, name)",
    },
    # Live response fields: ['assetfilter_ids', 'created_time', 'enabled', 'for_site', 'id', 'modified_time', 'name', 'org_id', 'site_id', 'topics', 'type', 'url', 'verify_cert']
    "listSiteWebhooks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteWebhooks \u2014 stable UUID entities (sample fields: assetfilter_ids, created_time, enabled, for_site, id)",
    },
    # Live response fields: ['_id', '_ttl', 'annotation', 'ap_id', 'ap_mac', 'assoc_time', 'band', 'bssid', 'channel', 'dual_band', 'family', 'group', 'hostname', 'idle_time', 'ip', 'is_guest', 'key_mgmt', 'last_seen', 'mac', 'manufacture', 'map_id', 'model', 'num_locating_aps', 'os', 'proto', 'psk_id', 'rssi', 'rx_bps', 'rx_bytes', 'rx_pkts', 'rx_rate', 'rx_retries', 'site_id', 'snr', 'ssid', 'tx_bps', 'tx_bytes', 'tx_pkts', 'tx_rate', 'tx_retries', 'uptime', 'vlan_id', 'wlan_id', 'x', 'x_m', 'y', 'y_m']
    "listSiteWirelessClientsStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["hostname", "mac", "model", "site_id"],
        "unique_constraints": [],
        "description": "listSiteWirelessClientsStats \u2014 no stable key \u2014 internal id assigned (sample fields: _id, _ttl, annotation, ap_id, ap_mac)",
    },
    # Live response fields: ['acct_interim_interval', 'acct_servers', 'airwatch', 'allow_ipv6_ndp', 'allow_mdns', 'allow_ssdp', 'ap_ids', 'app_limit', 'app_qos', 'apply_to', 'arp_filter', 'auth', 'auth_server_selection', 'auth_servers', 'auth_servers_nas_id', 'auth_servers_nas_ip', 'band_steer', 'bands', 'block_blacklist_clients', 'bonjour', 'cisco_cwa', 'client_limit_down', 'client_limit_down_enabled', 'client_limit_up', 'client_limit_up_enabled', 'coa_servers', 'created_time', 'disable_11ax', 'disable_11be', 'disable_uapsd', 'disable_when_gateway_unreachable', 'disable_wmm', 'dns_server_rewrite', 'dtim', 'dynamic_psk', 'dynamic_vlan', 'enabled', 'for_site', 'hide_ssid', 'hostname_ie', 'hotspot20', 'id', 'interface', 'isolation', 'l2_isolation', 'legacy_overds', 'limit_bcast', 'limit_probe_response', 'max_idletime', 'mist_nac', 'modified_time', 'mxtunnel_id', 'mxtunnel_ids', 'no_static_dns', 'no_static_ip', 'org_id', 'portal', 'portal_allowed_hostnames', 'portal_allowed_subnets', 'portal_api_secret', 'portal_denied_hostnames', 'portal_template_url', 'qos', 'radsec', 'rateset', 'roam_mode', 'schedule', 'site_id', 'sle_excluded', 'ssid', 'template_id', 'template_name', 'use_eapol_v1', 'vlan_enabled', 'vlan_id', 'vlan_ids', 'vlan_pooling', 'wlan_limit_down', 'wlan_limit_down_enabled', 'wlan_limit_up', 'wlan_limit_up_enabled', 'wxtag_ids', 'wxtunnel_id', 'wxtunnel_remote_id']
    "listSiteWlansDerived": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteWlansDerived \u2014 stable UUID entities (sample fields: acct_interim_interval, acct_servers, airwatch, allow_ipv6_ndp, allow_mdns)",
    },
    # Live response fields: ['action', 'created_time', 'dst_wxtags', 'enabled', 'for_site', 'id', 'modified_time', 'order', 'org_id', 'site_id', 'src_wxtags', 'template_id']
    "listSiteWxRules": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteWxRules \u2014 stable UUID entities (sample fields: action, created_time, dst_wxtags, enabled, for_site)",
    },
    # Live response fields: ['created_time', 'for_site', 'id', 'mac', 'match', 'modified_time', 'name', 'org_id', 'resource_mac', 'site_id', 'type']
    "listSiteWxTags": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "listSiteWxTags \u2014 stable UUID entities (sample fields: created_time, for_site, id, mac, match)",
    },
    # Live response fields: ['created_time', 'id', 'map_id', 'modified_time', 'name', 'org_id', 'site_id', 'vertices', 'vertices_m']
    "listSiteZones": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteZones \u2014 stable UUID entities (sample fields: created_time, id, map_id, modified_time, name)",
    },
    # Live response fields: ['assets_wait', 'clients_wait', 'created_time', 'discovered_assets_wait', 'id', 'map_id', 'modified_time', 'name', 'num_assets', 'num_clients', 'num_discovered_assets', 'num_sdkclients', 'num_unconnected_clients', 'org_id', 'sdkclients_wait', 'site_id', 'unconnected_clients_wait', 'vertices', 'vertices_m']
    "listSiteZonesStats": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "listSiteZonesStats \u2014 stable UUID entities (sample fields: assets_wait, clients_wait, created_time, discovered_assets_wait, id)",
    },
    # Live response fields: ['_vendor_model_id', 'display', 'model', 'type', 'vendor']
    "listSupportedOtherDeviceModels": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "type"],
        "unique_constraints": [],
        "description": "listSupportedOtherDeviceModels \u2014 no stable key \u2014 internal id assigned (sample fields: _vendor_model_id, display, model, type, vendor)",
    },
    # Live response fields: ['display', 'group', 'key']
    "listSystemEventsDefinitions": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listSystemEventsDefinitions \u2014 no stable key \u2014 internal id assigned (sample fields: display, group, key)",
    },
    # Live response fields: ['display', 'dscp', 'failover_policy', 'max_latency', 'max_loss', 'name', 'traffic_class']
    "listTrafficTypes": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["name"],
        "unique_constraints": [],
        "description": "listTrafficTypes \u2014 no stable key \u2014 internal id assigned (sample fields: display, dscp, failover_policy, max_latency, max_loss)",
    },
    # Live response fields: ['for_org', 'has_delivery_results', 'key']
    "listWebhookTopics": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "listWebhookTopics \u2014 no stable key \u2014 internal id assigned (sample fields: for_org, has_delivery_results, key)",
    },
    # Live response fields: []
    "logout": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "logout \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "pingOrgWebhook": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "pingOrgWebhook \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['detail']
    "pingSiteWebhook": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "pingSiteWebhook \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: []
    "pollSiteSwitchStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "pollSiteSwitchStats \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['detail']
    "readoptSiteOctermDevice": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "readoptSiteOctermDevice \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['result']
    "reevaluateOrgAutoAssignment": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "reevaluateOrgAutoAssignment \u2014 no stable key \u2014 internal id assigned (sample fields: result)",
    },
    # Live response fields: []
    "reprovisionSiteAllDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "reprovisionSiteAllDevices \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "reprovisionSiteOctermDevice": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "reprovisionSiteOctermDevice \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: []
    "resetSiteMlStatsByMap": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "resetSiteMlStatsByMap \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['detail']
    "restartOrgMxEdge": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "restartOrgMxEdge \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "restoreSiteDeviceBackupVersion": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "restoreSiteDeviceBackupVersion \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "rotateOrgCertificate": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "rotateOrgCertificate \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['session', 'url']
    "runSiteSrxTopCommand": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "runSiteSrxTopCommand \u2014 no stable key \u2014 internal id assigned (sample fields: session, url)",
    },
    # Live response fields: ['count', 'group', 'id', 'last_seen', 'macs', 'org_id', 'reasons', 'severity', 'site_id', 'timestamp', 'type']
    "searchOrgAlarms": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchOrgAlarms \u2014 event/log time-series records (sample fields: count, group, id, last_seen, macs)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgAssets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgAssets \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgBgpStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgBgpStats \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['ap', 'apfw', 'device_type', 'mac', 'org_id', 'site_id', 'text', 'timestamp', 'type']
    "searchOrgDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchOrgDeviceEvents \u2014 event/log time-series records (sample fields: ap, apfw, device_type, mac, org_id)",
    },
    # Live response fields: ['ap', 'band_24_usage', 'cc_mismatch', 'cert_expiry', 'channel_24', 'channel_5', 'channel_6', 'device_type', 'errors', 'last_config_was_bad', 'mac', 'model', 'name', 'org_id', 'radio_macs', 'radios', 'site_id', 'ssids', 'ssids_24', 'ssids_5', 'ssids_6', 'timestamp', 'uses_mxtunnel', 'version', 'wlan_ids', 'wlans']
    "searchOrgDeviceLastConfigs": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "model", "name", "org_id", "site_id", "version"],
        "unique_constraints": [],
        "description": "searchOrgDeviceLastConfigs \u2014 event/log time-series records (sample fields: ap, band_24_usage, cc_mismatch, cert_expiry, channel_24)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgDevices \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgGuestAuthorization": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgGuestAuthorization \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['last_name_change', 'mac', 'model', 'name', 'org_id', 'serial', 'site_id', 'sku', 'status', 'type', 'version']
    "searchOrgInventory": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac", "model", "name", "org_id", "serial", "site_id", "status", "type", "version"],
        "unique_constraints": [],
        "description": "searchOrgInventory \u2014 no stable key \u2014 internal id assigned (sample fields: last_name_change, mac, model, name, org_id)",
    },
    # Live response fields: ['claimed', 'device_name', 'has_support', 'master', 'model', 'org_id', 'serial', 'sku', 'status', 'type', 'version', 'warranty', 'warranty_type']
    "searchOrgJsiAssetsAndContracts": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["model", "org_id", "serial", "status", "type", "version"],
        "unique_constraints": [],
        "description": "searchOrgJsiAssetsAndContracts \u2014 no stable key \u2014 internal id assigned (sample fields: claimed, device_name, has_support, master, model)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgJsiPbn": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgJsiPbn \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgJsiSirt": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgJsiSirt \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgMistEdgeEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgMistEdgeEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgMxEdges": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgMxEdges \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['ap', 'auth_type', 'bssid', 'device_cert_expiry', 'mac', 'multi_session_id', 'nacrule_id', 'nas_ip', 'nas_vendor', 'org_id', 'port_type', 'random_mac', 'session_id', 'site_id', 'ssid', 'text', 'timestamp', 'type', 'username']
    "searchOrgNacClientEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchOrgNacClientEvents \u2014 event/log time-series records (sample fields: ap, auth_type, bssid, device_cert_expiry, mac)",
    },
    # Live response fields: ['ap', 'auth_type', 'last_ap', 'last_nacrule_id', 'last_nas_vendor', 'last_ssid', 'last_status', 'last_username', 'mac', 'nacrule_id', 'nacrule_matched', 'nas_ip', 'nas_vendor', 'org_id', 'random_mac', 'site_id', 'site_ids', 'ssid', 'timestamp', 'type', 'username']
    "searchOrgNacClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchOrgNacClients \u2014 event/log time-series records (sample fields: ap, auth_type, last_ap, last_nacrule_id, last_nas_vendor)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgOspfStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgOspfStats \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgOtherDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgOtherDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['limit', 'results', 'total']
    "searchOrgPeerPathStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgPeerPathStats \u2014 no stable key \u2014 internal id assigned (sample fields: limit, results, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgPskPortalLogs": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgPskPortalLogs \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['analytic_enabled', 'app_waking', 'asset_enabled', 'auto_upgrade_enabled', 'auto_upgrade_version', 'configs', 'country_code', 'created_time', 'honeypot_enabled', 'id', 'locate_unconnected', 'modified_time', 'name', 'org_id', 'rogue_enabled', 'rtsa_enabled', 'timezone', 'wifi_enabled']
    "searchOrgSites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["name", "org_id"],
        "unique_constraints": [],
        "description": "searchOrgSites \u2014 stable UUID entities (sample fields: analytic_enabled, app_waking, asset_enabled, auto_upgrade_enabled, auto_upgrade_version)",
    },
    # Live response fields: ['active', 'bytes', 'device_interface_type', 'device_type', 'full_duplex', 'jitter', 'lacp_stats', 'latency', 'loss', 'mac', 'mac_count', 'mac_limit', 'media_type', 'neighbor_mac', 'neighbor_port_desc', 'neighbor_system_name', 'org_id', 'poe_disabled', 'poe_on', 'port_desc', 'port_id', 'port_mac', 'port_parent', 'port_usage', 'rx_bcast_pkts', 'rx_bps', 'rx_bytes', 'rx_errors', 'rx_mcast_pkts', 'rx_pkts', 'site_id', 'speed', 'stp_role', 'stp_state', 'timestamp', 'tx_bcast_pkts', 'tx_bps', 'tx_bytes', 'tx_errors', 'tx_mcast_pkts', 'tx_pkts', 'unconfigured', 'up', 'uplink', 'vpn_overlays', 'xcvr_model', 'xcvr_part_number', 'xcvr_serial']
    "searchOrgSwOrGwPorts": {
        "type": "timeseries_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgSwOrGwPorts \u2014 numeric metrics for Redis TimeSeries (sample fields: active, bytes, device_interface_type, device_type, full_duplex)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgSystemEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgSystemEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgTunnelsStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgTunnelsStats \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['id', 'labels', 'mac', 'name', 'notes', 'radius_group', 'vlan']
    "searchOrgUserMacs": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["mac", "name"],
        "unique_constraints": [],
        "description": "searchOrgUserMacs \u2014 stable UUID entities (sample fields: id, labels, mac, name, notes)",
    },
    # Live response fields: ['org_id', 'site_id', 'src', 'timestamp', 'var']
    "searchOrgVars": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgVars \u2014 event/log time-series records (sample fields: org_id, site_id, src, timestamp, var)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchOrgWanClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchOrgWanClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['dhcp_expire_time', 'dhcp_start_time', 'hostname', 'ip', 'ip_src', 'last_hostname', 'last_ip', 'mac', 'mfg', 'network', 'org_id', 'random_mac', 'site_id', 'site_ids', 'timestamp']
    "searchOrgWanClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgWanClients \u2014 event/log time-series records (sample fields: dhcp_expire_time, dhcp_start_time, hostname, ip, ip_src)",
    },
    # Live response fields: ['error', 'id', 'org_id', 'req_headers', 'req_payload', 'req_url', 'resp_body', 'site_id', 'status', 'status_code', 'timestamp', 'topic', 'webhook_id']
    "searchOrgWebhooksDeliveries": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id", "status"],
        "unique_constraints": [],
        "description": "searchOrgWebhooksDeliveries \u2014 event/log time-series records (sample fields: error, id, org_id, req_headers, req_payload)",
    },
    # Live response fields: ['auth_method', 'auth_state', 'client_mac', 'device_mac', 'device_mac_port', 'dhcp_client_options', 'hostname', 'ip', 'ip6', 'last_device_mac', 'last_hostname', 'last_ip', 'last_port_id', 'last_vlan', 'last_vlan_name', 'mac', 'manufacture', 'org_id', 'port_id', 'random_mac', 'site_id', 'timestamp', 'username', 'vlan']
    "searchOrgWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgWiredClients \u2014 event/log time-series records (sample fields: auth_method, auth_state, client_mac, device_mac, device_mac_port)",
    },
    # Live response fields: ['ap', 'band', 'bssid', 'capabilities', 'channel', 'dhcp_latency', 'dhcp_lease_time', 'dhcp_renewal_time', 'dhcp_server', 'dhcp_xid', 'dns_server', 'gateway', 'ip', 'key_mgmt', 'mac', 'num_streams', 'org_id', 'proto', 'random_mac', 'reason_code', 'rssi', 'site_id', 'ssid', 'status_code', 'subnet', 'text', 'time_since_assoc', 'timestamp', 'type', 'type_code', 'vlan', 'wlan_id']
    "searchOrgWirelessClientEvents": {
        "type": "timeseries_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchOrgWirelessClientEvents \u2014 numeric metrics for Redis TimeSeries (sample fields: ap, band, bssid, capabilities, channel)",
    },
    # Live response fields: ['ap', 'band', 'client_family', 'client_ip', 'client_manufacture', 'client_model', 'client_os', 'connect', 'disconnect', 'duration', 'mac', 'org_id', 'random_mac', 'site_id', 'ssid', 'tags', 'timestamp', 'wlan_id']
    "searchOrgWirelessClientSessions": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgWirelessClientSessions \u2014 event/log time-series records (sample fields: ap, band, client_family, client_ip, client_manufacture)",
    },
    # Live response fields: ['ap', 'app_version', 'band', 'device', 'firmware', 'ftc', 'hostname', 'ip', 'last_ap', 'last_firmware', 'last_hostname', 'last_ip', 'last_model', 'last_os', 'last_os_version', 'last_ssid', 'last_vlan', 'last_wlan_id', 'mac', 'model', 'org_id', 'os', 'os_version', 'protocol', 'psk_id', 'psk_name', 'random_mac', 'sdk_version', 'site_id', 'site_ids', 'ssid', 'timestamp', 'username', 'vlan', 'wlan_id']
    "searchOrgWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "model", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchOrgWirelessClients \u2014 event/log time-series records (sample fields: ap, app_version, band, device, firmware)",
    },
    # Live response fields: ['count', 'group', 'id', 'last_seen', 'macs', 'org_id', 'reasons', 'severity', 'site_id', 'timestamp', 'type']
    "searchSiteAlarms": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteAlarms \u2014 event/log time-series records (sample fields: count, group, id, last_seen, macs)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteAssets": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteAssets \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteBgpStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteBgpStats \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteCalls": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteCalls \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: []
    "searchSiteClientFingerprints": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteClientFingerprints \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['ap', 'cc_mismatch', 'channel_24', 'channel_5', 'channel_6', 'errors', 'last_config_was_bad', 'name', 'org_id', 'radio_macs', 'radios', 'site_id', 'ssids', 'ssids_24', 'ssids_5', 'ssids_6', 'timestamp', 'version', 'wlan_ids', 'wlans']
    "searchSiteDeviceConfigHistory": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["name", "org_id", "site_id", "version"],
        "unique_constraints": [],
        "description": "searchSiteDeviceConfigHistory \u2014 event/log time-series records (sample fields: ap, cc_mismatch, channel_24, channel_5, channel_6)",
    },
    # Live response fields: ['ap', 'apfw', 'device_type', 'mac', 'org_id', 'site_id', 'text', 'timestamp', 'type']
    "searchSiteDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteDeviceEvents \u2014 event/log time-series records (sample fields: ap, apfw, device_type, mac, org_id)",
    },
    # Live response fields: ['ap', 'band_24_usage', 'cc_mismatch', 'cert_expiry', 'channel_24', 'channel_5', 'channel_6', 'device_type', 'errors', 'last_config_was_bad', 'mac', 'model', 'name', 'org_id', 'radio_macs', 'radios', 'site_id', 'ssids', 'ssids_24', 'ssids_5', 'ssids_6', 'timestamp', 'uses_mxtunnel', 'version', 'wlan_ids', 'wlans']
    "searchSiteDeviceLastConfigs": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "model", "name", "org_id", "site_id", "version"],
        "unique_constraints": [],
        "description": "searchSiteDeviceLastConfigs \u2014 event/log time-series records (sample fields: ap, band_24_usage, cc_mismatch, cert_expiry, channel_24)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteDevices": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteDevices \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['adopted', 'ap_redundancy', 'aps', 'chassis_id', 'hostname', 'mgmt_addr', 'model', 'org_id', 'site_id', 'system_desc', 'system_name', 'timestamp', 'vendor', 'version']
    "searchSiteDiscoveredSwitches": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["hostname", "model", "org_id", "site_id", "version"],
        "unique_constraints": [],
        "description": "searchSiteDiscoveredSwitches \u2014 event/log time-series records (sample fields: adopted, ap_redundancy, aps, chassis_id, hostname)",
    },
    # Live response fields: ['details', 'org_id', 'scope', 'score', 'site_id', 'timestamp', 'type']
    "searchSiteDiscoveredSwitchesMetrics": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteDiscoveredSwitchesMetrics \u2014 event/log time-series records (sample fields: details, org_id, scope, score, site_id)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteGuestAuthorization": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteGuestAuthorization \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: []
    "searchSiteIotEndpoints": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteIotEndpoints \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteMistEdgeEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteMistEdgeEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['ap', 'auth_type', 'bssid', 'device_cert_expiry', 'mac', 'multi_session_id', 'nacrule_id', 'nas_ip', 'nas_vendor', 'org_id', 'port_type', 'random_mac', 'session_id', 'site_id', 'ssid', 'text', 'timestamp', 'type', 'username']
    "searchSiteNacClientEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteNacClientEvents \u2014 event/log time-series records (sample fields: ap, auth_type, bssid, device_cert_expiry, mac)",
    },
    # Live response fields: ['ap', 'auth_type', 'last_ap', 'last_nacrule_id', 'last_nas_vendor', 'last_ssid', 'last_status', 'last_username', 'mac', 'nacrule_id', 'nacrule_matched', 'nas_ip', 'nas_vendor', 'org_id', 'random_mac', 'site_id', 'site_ids', 'ssid', 'timestamp', 'type', 'username']
    "searchSiteNacClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteNacClients \u2014 event/log time-series records (sample fields: ap, auth_type, last_ap, last_nacrule_id, last_nas_vendor)",
    },
    # Live response fields: ['detail']
    "searchSiteOspfStats": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteOspfStats \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteOtherDeviceEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteOtherDeviceEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteRogueEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteRogueEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['mac', 'model', 'org_id', 'policy', 'port_id', 'site_id', 'text', 'timestamp', 'type']
    "searchSiteServicePathEvents": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "model", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteServicePathEvents \u2014 event/log time-series records (sample fields: mac, model, org_id, policy, port_id)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteSkyatpEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteSkyatpEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['active', 'bytes', 'chassis_mac', 'device_type', 'dpc_active', 'full_duplex', 'lacp_stats', 'last_flapped', 'mac', 'mac_count', 'mac_limit', 'media_type', 'org_id', 'port_id', 'port_mac', 'port_parent', 'port_usage', 'rx_bcast_pkts', 'rx_bps', 'rx_bytes', 'rx_errors', 'rx_mcast_pkts', 'rx_pkts', 'site_id', 'speed', 'stp_role', 'stp_state', 'timestamp', 'tx_bcast_pkts', 'tx_bps', 'tx_bytes', 'tx_errors', 'tx_mcast_pkts', 'tx_pkts', 'unconfigured', 'up', 'uplink', 'xcvr_model', 'xcvr_part_number', 'xcvr_serial']
    "searchSiteSwOrGwPorts": {
        "type": "timeseries_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchSiteSwOrGwPorts \u2014 numeric metrics for Redis TimeSeries (sample fields: active, bytes, chassis_mac, device_type, dpc_active)",
    },
    # Live response fields: ['by', 'curl_response_status', 'device_type', 'dhcp_lease_time', 'id', 'latency', 'mac', 'org_id', 'rx_mbps', 'site_id', 'start_time', 'timestamp', 'tx_mbps', 'type', 'vlan_id']
    "searchSiteSyntheticTest": {
        "type": "composite_pk",
        "primary_key": ["id", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteSyntheticTest \u2014 event/log time-series records (sample fields: by, curl_response_status, device_type, dhcp_lease_time, id)",
    },
    # Live response fields: ['change_cat', 'metadata', 'org_id', 'scope', 'site_id', 'timestamp', 'type']
    "searchSiteSystemEvents": {
        "type": "composite_pk",
        "primary_key": ["site_id", "timestamp"],
        "indexes": ["org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteSystemEvents \u2014 event/log time-series records (sample fields: change_cat, metadata, org_id, scope, site_id)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteWanClientEvents": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteWanClientEvents \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['dhcp_expire_time', 'dhcp_start_time', 'hostname', 'ip', 'ip_src', 'last_hostname', 'last_ip', 'mac', 'mfg', 'network', 'org_id', 'random_mac', 'site_id', 'site_ids', 'timestamp']
    "searchSiteWanClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchSiteWanClients \u2014 event/log time-series records (sample fields: dhcp_expire_time, dhcp_start_time, hostname, ip, ip_src)",
    },
    # Live response fields: ['mac', 'path_weight', 'policy', 'port_id', 'tenant', 'vpn_name']
    "searchSiteWanUsage": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["mac"],
        "unique_constraints": [],
        "description": "searchSiteWanUsage \u2014 no stable key \u2014 internal id assigned (sample fields: mac, path_weight, policy, port_id, tenant)",
    },
    # Live response fields: ['end', 'limit', 'results', 'start', 'total']
    "searchSiteWebhooksDeliveries": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "searchSiteWebhooksDeliveries \u2014 no stable key \u2014 internal id assigned (sample fields: end, limit, results, start, total)",
    },
    # Live response fields: ['auth_method', 'auth_state', 'client_mac', 'device_mac', 'device_mac_port', 'dhcp_client_options', 'hostname', 'ip', 'ip6', 'last_device_mac', 'last_hostname', 'last_ip', 'last_port_id', 'last_vlan', 'last_vlan_name', 'mac', 'manufacture', 'org_id', 'port_id', 'random_mac', 'site_id', 'timestamp', 'username', 'vlan']
    "searchSiteWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchSiteWiredClients \u2014 event/log time-series records (sample fields: auth_method, auth_state, client_mac, device_mac, device_mac_port)",
    },
    # Live response fields: ['ap', 'band', 'bssid', 'channel', 'dns_latency', 'dns_server', 'ip', 'key_mgmt', 'mac', 'num_streams', 'org_id', 'proto', 'random_mac', 'reason_code', 'rssi', 'site_id', 'ssid', 'status_code', 'text', 'time_since_assoc', 'timestamp', 'type', 'type_code', 'vlan', 'wlan_id']
    "searchSiteWirelessClientEvents": {
        "type": "timeseries_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "searchSiteWirelessClientEvents \u2014 numeric metrics for Redis TimeSeries (sample fields: ap, band, bssid, channel, dns_latency)",
    },
    # Live response fields: ['ap', 'band', 'client_family', 'client_ip', 'client_manufacture', 'client_model', 'client_os', 'connect', 'disconnect', 'duration', 'mac', 'org_id', 'random_mac', 'site_id', 'ssid', 'tags', 'timestamp', 'wlan_id']
    "searchSiteWirelessClientSessions": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchSiteWirelessClientSessions \u2014 event/log time-series records (sample fields: ap, band, client_family, client_ip, client_manufacture)",
    },
    # Live response fields: ['ap', 'app_version', 'band', 'device', 'firmware', 'ftc', 'hostname', 'ip', 'last_ap', 'last_firmware', 'last_hostname', 'last_ip', 'last_model', 'last_os', 'last_os_version', 'last_ssid', 'last_vlan', 'last_wlan_id', 'mac', 'model', 'org_id', 'os', 'os_version', 'protocol', 'psk_id', 'psk_name', 'random_mac', 'sdk_version', 'site_id', 'ssid', 'timestamp', 'username', 'vlan', 'wlan_id']
    "searchSiteWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["hostname", "mac", "model", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "searchSiteWirelessClients \u2014 event/log time-series records (sample fields: ap, app_version, band, device, firmware)",
    },
    # Live response fields: ['detail']
    "subscribeOrgAlarmsReports": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "subscribeOrgAlarmsReports \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "syncOrgCradlepointRouters": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "syncOrgCradlepointRouters \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['alert_config_id', 'cp_api_id', 'cp_api_key', 'destination_config_id', 'ecm_api_id', 'ecm_api_key', 'enable_lldp', 'error', 'last_status', 'shared_secret']
    "testOrgCradlepointConnection": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "testOrgCradlepointConnection \u2014 no stable key \u2014 internal id assigned (sample fields: alert_config_id, cp_api_id, cp_api_key, destination_config_id, ecm_api_id)",
    },
    # Live response fields: ['detail']
    "testSiteSsrDnsResolution": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "testSiteSsrDnsResolution \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['detail']
    "toogleSiteDeviceVcRoutingEnginesRole": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "toogleSiteDeviceVcRoutingEnginesRole \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: ['category', 'reason', 'site_id', 'text']
    "troubleshootOrg": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["site_id"],
        "unique_constraints": [],
        "description": "troubleshootOrg \u2014 no stable key \u2014 internal id assigned (sample fields: category, reason, site_id, text)",
    },
    # Live response fields: ['detail']
    "unlinkOrgFromJuniperCustomerId": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "unlinkOrgFromJuniperCustomerId \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: []
    "unregisterOrgMxEdge": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "unregisterOrgMxEdge \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
    # Live response fields: ['detail']
    "unsubscribeOrgAlarmsReports": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "unsubscribeOrgAlarmsReports \u2014 no stable key \u2014 internal id assigned (sample fields: detail)",
    },
    # Live response fields: []
    "unsuppressOrgSuppressedAlarms": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "unsuppressOrgSuppressedAlarms \u2014 no stable key \u2014 internal id assigned (sample fields: )",
    },
}
