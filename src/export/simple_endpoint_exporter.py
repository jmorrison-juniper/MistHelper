"""SimpleEndpointExporter exports one-identifier Mist endpoints.

Issue #1807 groups simple get and list endpoints by required identifier.
Each table entry names one SDK function that takes only the session, or one
required identifier after the session. The operator selects the operation from
one prompt, and the exporter uses the shared output selector.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy imports avoid a circular MistHelper import.
import logging  # WHY: operators need an action trace for each export.
from dataclasses import dataclass  # WHY: immutable rows keep the operation table clear.
from typing import Any  # WHY: Mist SDK responses have dynamic row shapes.

import mistapi  # WHY: the SDK supplies the endpoint call and pagination helper.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: shared flatten and escape logic keeps exports consistent.
from src.utils.input_utils import InputUtils  # WHY: MSP selection must use the EOF-safe prompt.


@dataclass(frozen=True)
class _SimpleEndpointOp:
    """One simple endpoint operation and its SDK module."""

    operation: str  # The Mist operationId selects the API call and primary-key strategy.
    module: str  # The dotted SDK module lets the resolver import the function lazily.


_NONE_OPS: tuple[_SimpleEndpointOp, ...] = (
    _SimpleEndpointOp("getAdminRegistrationInfo", "mistapi.api.v1.register.recaptcha"),  # Issue #1090.
    _SimpleEndpointOp("getSelf", "mistapi.api.v1.self.self"),  # Issue #1174.
    _SimpleEndpointOp("getSelfLoginFailures", "mistapi.api.v1.self.login_failures"),  # Issue #1175.
    _SimpleEndpointOp("listAlarmDefinitions", "mistapi.api.v1.const.alarm_defs"),  # Issue #1234.
    _SimpleEndpointOp("listAlarmSubscriptions", "mistapi.api.v1.self.subscriptions"),  # Issue #1235.
    _SimpleEndpointOp("listApChannels", "mistapi.api.v1.const.ap_channels"),  # Issue #1236.
    _SimpleEndpointOp("listApiTokens", "mistapi.api.v1.self.apitokens"),  # Issue #1239.
    _SimpleEndpointOp("listApLedDefinition", "mistapi.api.v1.const.ap_led_status"),  # Issue #1238.
    _SimpleEndpointOp("listApLEslVersions", "mistapi.api.v1.const.ap_esl_versions"),  # Issue #1237.
    _SimpleEndpointOp("listAppCategoryDefinitions", "mistapi.api.v1.const.app_categories"),  # Issue #1240.
    _SimpleEndpointOp("listApplications", "mistapi.api.v1.const.applications"),  # Issue #1242.
    _SimpleEndpointOp("listAppSubCategoryDefinitions", "mistapi.api.v1.const.app_subcategories"),  # Issue #1241.
    _SimpleEndpointOp("listClientEventsDefinitions", "mistapi.api.v1.const.client_events"),  # Issue #1243.
    _SimpleEndpointOp("listCountryCodes", "mistapi.api.v1.const.countries"),  # Issue #1244.
    _SimpleEndpointOp("listDeviceEventsDefinitions", "mistapi.api.v1.const.device_events"),  # Issue #1245.
    _SimpleEndpointOp("listDeviceModels", "mistapi.api.v1.const.device_models"),  # Issue #1246.
    _SimpleEndpointOp("listFingerprintTypes", "mistapi.api.v1.const.fingerprint_types"),  # Issue #1247.
    _SimpleEndpointOp("listGatewayApplications", "mistapi.api.v1.const.gateway_applications"),  # Issue #1248.
    _SimpleEndpointOp("listLicenseTypes", "mistapi.api.v1.const.license_types"),  # Issue #1256.
    _SimpleEndpointOp("listMarvisClientVersions", "mistapi.api.v1.const.marvisclient_versions"),  # Issue #1257.
    _SimpleEndpointOp("listMxEdgeEventsDefinitions", "mistapi.api.v1.const.mxedge_events"),  # Issue #1269.
    _SimpleEndpointOp("listMxEdgeModels", "mistapi.api.v1.const.mxedge_models"),  # Issue #1270.
    _SimpleEndpointOp("listNacEventsDefinitions", "mistapi.api.v1.const.nac_events"),  # Issue #1271.
    _SimpleEndpointOp("listOtherDeviceEventsDefinitions", "mistapi.api.v1.const.otherdevice_events"),  # Issue #1304.
    _SimpleEndpointOp("listSiteLanguages", "mistapi.api.v1.const.languages"),  # Issue #1325.
    _SimpleEndpointOp("listSupportedOtherDeviceModels", "mistapi.api.v1.const.otherdevice_models"),  # Issue #1362.
    _SimpleEndpointOp("listSystemEventsDefinitions", "mistapi.api.v1.const.system_events"),  # Issue #1363.
    _SimpleEndpointOp("listTrafficTypes", "mistapi.api.v1.const.traffic_types"),  # Issue #1364.
    _SimpleEndpointOp("listWebhookTopics", "mistapi.api.v1.const.webhook_topics"),  # Issue #1365.
)

_ORG_OPS: tuple[_SimpleEndpointOp, ...] = (
    _SimpleEndpointOp("getOrgAosRegisterCmd", "mistapi.api.v1.orgs.aos"),  # Issue #1108.
    _SimpleEndpointOp("getOrgApplicationList", "mistapi.api.v1.orgs.wxtags"),  # Issue #1110.
    _SimpleEndpointOp("getOrgCapturingStatus", "mistapi.api.v1.orgs.pcaps"),  # Issue #1114.
    _SimpleEndpointOp("getOrgCrlFile", "mistapi.api.v1.orgs.crl"),  # Issue #1115.
    _SimpleEndpointOp("getOrgJseInfo", "mistapi.api.v1.orgs.setting"),  # Issue #1122.
    _SimpleEndpointOp("getOrgJseIntegration", "mistapi.api.v1.orgs.setting"),  # Issue #1123.
    _SimpleEndpointOp("getOrgJuniperDevicesCommand", "mistapi.api.v1.orgs.ocdevices"),  # Issue #1124.
    _SimpleEndpointOp("getOrgLicensesSummary", "mistapi.api.v1.orgs.licenses"),  # Issue #1125.
    _SimpleEndpointOp("getOrgMistScep", "mistapi.api.v1.orgs.setting"),  # Issue #1127.
    _SimpleEndpointOp("getOrgMxEdgeUpgradeInfo", "mistapi.api.v1.orgs.mxedges"),  # Issue #1131.
    _SimpleEndpointOp("getOrgNacCrl", "mistapi.api.v1.orgs.setting"),  # Issue #1134.
    _SimpleEndpointOp("getOrgSettings", "mistapi.api.v1.orgs.setting"),  # Issue #1152.
    _SimpleEndpointOp("getOrgSkyAtpIntegration", "mistapi.api.v1.orgs.setting"),  # Issue #1154.
    _SimpleEndpointOp("getOrgSslProxyCert", "mistapi.api.v1.orgs.ssl_proxy_cert"),  # Issue #1155.
    _SimpleEndpointOp("getOrgSsrRegistrationCommands", "mistapi.api.v1.orgs.ssr"),  # Issue #1158.
    _SimpleEndpointOp("getOrgStats", "mistapi.api.v1.orgs.stats"),  # Issue #1160.
    _SimpleEndpointOp("getOrgZscalerIntegration", "mistapi.api.v1.orgs.setting"),  # Issue #1170.
    _SimpleEndpointOp("listInstallerAlarmTemplates", "mistapi.api.v1.installer.orgs.alarmtemplates"),  # Issue #1249.
    _SimpleEndpointOp("listInstallerDeviceProfiles", "mistapi.api.v1.installer.orgs.deviceprofiles"),  # Issue #1250.
    _SimpleEndpointOp(
        "listInstallerListOfRecentlyClaimedDevices", "mistapi.api.v1.installer.orgs.devices"
    ),  # Issue #1251.
    _SimpleEndpointOp("listInstallerRfTemplatesNames", "mistapi.api.v1.installer.orgs.rftemplates"),  # Issue #1253.
    _SimpleEndpointOp("listInstallerSiteGroups", "mistapi.api.v1.installer.orgs.sitegroups"),  # Issue #1254.
    _SimpleEndpointOp("listInstallerSites", "mistapi.api.v1.installer.orgs.sites"),  # Issue #1255.
    _SimpleEndpointOp("listOrgAAMWProfiles", "mistapi.api.v1.orgs.aamwprofiles"),  # Issue #1272.
    _SimpleEndpointOp("listOrgAntivirusProfiles", "mistapi.api.v1.orgs.avprofiles"),  # Issue #1273.
    _SimpleEndpointOp("listOrgApsMacs", "mistapi.api.v1.orgs.devices"),  # Issue #1274.
    _SimpleEndpointOp("listOrgAssetFilters", "mistapi.api.v1.orgs.assetfilters"),  # Issue #1275.
    _SimpleEndpointOp("listOrgAssets", "mistapi.api.v1.orgs.assets"),  # Issue #1276.
    _SimpleEndpointOp("listOrgAssetsStats", "mistapi.api.v1.orgs.stats"),  # Issue #1277.
    _SimpleEndpointOp("listOrgCertificates", "mistapi.api.v1.orgs.cert"),  # Issue #1278.
    _SimpleEndpointOp("listOrgDevicesSummary", "mistapi.api.v1.orgs.devices"),  # Issue #1280.
    _SimpleEndpointOp("listOrgDeviceUpgrades", "mistapi.api.v1.orgs.devices"),  # Issue #1279.
    _SimpleEndpointOp("listOrgEvpnTopologies", "mistapi.api.v1.orgs.evpn_topologies"),  # Issue #1281.
    _SimpleEndpointOp("listOrgGuestAuthorizations", "mistapi.api.v1.orgs.guests"),  # Issue #1282.
    _SimpleEndpointOp("listOrgIdpProfiles", "mistapi.api.v1.orgs.idpprofiles"),  # Issue #1283.
    _SimpleEndpointOp("listOrgIssuedClientCertificates", "mistapi.api.v1.orgs.setting"),  # Issue #1284.
    _SimpleEndpointOp("listOrgJsiDevices", "mistapi.api.v1.orgs.jsi"),  # Issue #1285.
    _SimpleEndpointOp("listOrgJsiPastPurchases", "mistapi.api.v1.orgs.jsi"),  # Issue #1286.
    _SimpleEndpointOp("listOrgMarvisClientInvites", "mistapi.api.v1.orgs.marvisinvites"),  # Issue #1287.
    _SimpleEndpointOp("listOrgMxEdgeClusters", "mistapi.api.v1.orgs.mxclusters"),  # Issue #1288.
    _SimpleEndpointOp("listOrgMxEdgeUpgrades", "mistapi.api.v1.orgs.mxedges"),  # Issue #1289.
    _SimpleEndpointOp("listOrgMxTunnels", "mistapi.api.v1.orgs.mxtunnels"),  # Issue #1290.
    _SimpleEndpointOp("listOrgOtherDevices", "mistapi.api.v1.orgs.otherdevices"),  # Issue #1292.
    _SimpleEndpointOp("listOrgPmaDashboards", "mistapi.api.v1.orgs.pma"),  # Issue #1293.
    _SimpleEndpointOp("listOrgPskPortalLogs", "mistapi.api.v1.orgs.pskportals"),  # Issue #1294.
    _SimpleEndpointOp("listOrgPskPortals", "mistapi.api.v1.orgs.pskportals"),  # Issue #1295.
    _SimpleEndpointOp("listOrgSiteGroups", "mistapi.api.v1.orgs.sitegroups"),  # Issue #1296.
    _SimpleEndpointOp("listOrgSsoRoles", "mistapi.api.v1.orgs.ssoroles"),  # Issue #1298.
    _SimpleEndpointOp("listOrgSuppressedAlarms", "mistapi.api.v1.orgs.alarmtemplates"),  # Issue #1299.
    _SimpleEndpointOp("listOrgUiSettings", "mistapi.api.v1.orgs.uisettings"),  # Issue #1300.
    _SimpleEndpointOp("listOrgWxRules", "mistapi.api.v1.orgs.wxrules"),  # Issue #1301.
    _SimpleEndpointOp("listOrgWxTags", "mistapi.api.v1.orgs.wxtags"),  # Issue #1302.
    _SimpleEndpointOp("listOrgWxTunnels", "mistapi.api.v1.orgs.wxtunnels"),  # Issue #1303.
    _SimpleEndpointOp("listSdkInvites", "mistapi.api.v1.orgs.sdkinvites"),  # Issue #1305.
    _SimpleEndpointOp("listSdkTemplates", "mistapi.api.v1.orgs.sdktemplates"),  # Issue #1306.
)

_SITE_OPS: tuple[_SimpleEndpointOp, ...] = (
    _SimpleEndpointOp("getSiteBeamCoverageOverview", "mistapi.api.v1.sites.location"),  # Issue #1180.
    _SimpleEndpointOp("getSiteCallsSummary", "mistapi.api.v1.sites.stats"),  # Issue #1181.
    _SimpleEndpointOp("getSiteCapturingStatus", "mistapi.api.v1.sites.pcaps"),  # Issue #1182.
    _SimpleEndpointOp("getSiteCurrentChannelPlanning", "mistapi.api.v1.sites.rrm"),  # Issue #1183.
    _SimpleEndpointOp("getSiteDefaultPlfForModels", "mistapi.api.v1.sites.location"),  # Issue #1185.
    _SimpleEndpointOp("getSiteGatewayMetrics", "mistapi.api.v1.sites.stats"),  # Issue #1191.
    _SimpleEndpointOp("getSiteJseInfo", "mistapi.api.v1.sites.setting"),  # Issue #1196.
    _SimpleEndpointOp("getSiteLicenseUsage", "mistapi.api.v1.sites.licenses"),  # Issue #1197.
    _SimpleEndpointOp("getSiteMachineLearningCurrentStat", "mistapi.api.v1.sites.location"),  # Issue #1198.
    _SimpleEndpointOp("getSiteRunningSpectrumAnalysis", "mistapi.api.v1.sites.analyze_spectrum"),  # Issue #1207.
    _SimpleEndpointOp("getSiteSettingDerived", "mistapi.api.v1.sites.setting"),  # Issue #1210.
    _SimpleEndpointOp("getSiteSiteRfdiagRecording", "mistapi.api.v1.sites.rfdiags"),  # Issue #1211.
    _SimpleEndpointOp("getSiteStats", "mistapi.api.v1.sites.stats"),  # Issue #1220.
    _SimpleEndpointOp("getSiteSwitchesMetrics", "mistapi.api.v1.sites.stats"),  # Issue #1221.
    _SimpleEndpointOp("getSiteWxRulesUsage", "mistapi.api.v1.sites.stats"),  # Issue #1229.
    _SimpleEndpointOp("listSiteAAMWProfilesDerived", "mistapi.api.v1.sites.aamwprofiles"),  # Issue #1307.
    _SimpleEndpointOp("listSiteAllGuestAuthorizations", "mistapi.api.v1.sites.guests"),  # Issue #1308.
    _SimpleEndpointOp("listSiteAllGuestAuthorizationsDerived", "mistapi.api.v1.sites.guests"),  # Issue #1309.
    _SimpleEndpointOp("listSiteAntivirusProfilesDerived", "mistapi.api.v1.sites.avprofiles"),  # Issue #1310.
    _SimpleEndpointOp("listSiteApps", "mistapi.api.v1.sites.apps"),  # Issue #1312.
    _SimpleEndpointOp("listSiteApTemplatesDerived", "mistapi.api.v1.sites.aptemplates"),  # Issue #1311.
    _SimpleEndpointOp("listSiteAssetFilters", "mistapi.api.v1.sites.assetfilters"),  # Issue #1313.
    _SimpleEndpointOp("listSiteAssets", "mistapi.api.v1.sites.assets"),  # Issue #1314.
    _SimpleEndpointOp("listSiteAssetsStats", "mistapi.api.v1.sites.stats"),  # Issue #1315.
    _SimpleEndpointOp("listSiteAvailableDeviceVersions", "mistapi.api.v1.sites.devices"),  # Issue #1316.
    _SimpleEndpointOp("listSiteBeaconsStats", "mistapi.api.v1.sites.stats"),  # Issue #1317.
    _SimpleEndpointOp("listSiteDeviceProfilesDerived", "mistapi.api.v1.sites.deviceprofiles"),  # Issue #1319.
    _SimpleEndpointOp("listSiteDeviceRadioChannels", "mistapi.api.v1.sites.devices"),  # Issue #1320.
    _SimpleEndpointOp("listSiteDiscoveredAssets", "mistapi.api.v1.sites.stats"),  # Issue #1321.
    _SimpleEndpointOp("listSiteDiscoveredSwitchesMetrics", "mistapi.api.v1.sites.stats"),  # Issue #1322.
    _SimpleEndpointOp("listSiteEvpnTopologies", "mistapi.api.v1.sites.evpn_topologies"),  # Issue #1323.
    _SimpleEndpointOp("listSiteIdpProfilesDerived", "mistapi.api.v1.sites.idpprofiles"),  # Issue #1324.
    _SimpleEndpointOp("listSiteMapStacks", "mistapi.api.v1.sites.mapstacks"),  # Issue #1326.
    _SimpleEndpointOp("listSiteMxEdges", "mistapi.api.v1.sites.mxedges"),  # Issue #1327.
    _SimpleEndpointOp("listSiteMxEdgesStats", "mistapi.api.v1.sites.stats"),  # Issue #1328.
    _SimpleEndpointOp("listSiteNetworkTemplatesDerived", "mistapi.api.v1.sites.networktemplates"),  # Issue #1329.
    _SimpleEndpointOp("listSiteOtherDevices", "mistapi.api.v1.sites.otherdevices"),  # Issue #1330.
    _SimpleEndpointOp("listSitePsks", "mistapi.api.v1.sites.psks"),  # Issue #1331.
    _SimpleEndpointOp("listSiteRfTemplatesDerived", "mistapi.api.v1.sites.rftemplates"),  # Issue #1332.
    _SimpleEndpointOp("listSiteRoamingEvents", "mistapi.api.v1.sites.events"),  # Issue #1333.
    _SimpleEndpointOp("listSiteRrmEvents", "mistapi.api.v1.sites.rrm"),  # Issue #1334.
    _SimpleEndpointOp("listSiteRssiZones", "mistapi.api.v1.sites.rssizones"),  # Issue #1335.
    _SimpleEndpointOp("listSiteRssiZonesStats", "mistapi.api.v1.sites.stats"),  # Issue #1336.
    _SimpleEndpointOp("listSiteSecIntelProfilesDerived", "mistapi.api.v1.sites.secintelprofiles"),  # Issue #1337.
    _SimpleEndpointOp("listSiteServicesDerived", "mistapi.api.v1.sites.services"),  # Issue #1338.
    _SimpleEndpointOp("listSiteSiteTemplatesDerived", "mistapi.api.v1.sites.sitetemplates"),  # Issue #1339.
    _SimpleEndpointOp("listSiteSpectrumAnalysis", "mistapi.api.v1.sites.stats"),  # Issue #1350.
    _SimpleEndpointOp("listSiteTroubleshootCalls", "mistapi.api.v1.sites.stats"),  # Issue #1351.
    _SimpleEndpointOp("listSiteUiSettingDerived", "mistapi.api.v1.sites.uisettings"),  # Issue #1352.
    _SimpleEndpointOp("listSiteUiSettings", "mistapi.api.v1.sites.uisettings"),  # Issue #1353.
    _SimpleEndpointOp("listSiteVpnsDerived", "mistapi.api.v1.sites.vpns"),  # Issue #1355.
    _SimpleEndpointOp("listSiteWebhooks", "mistapi.api.v1.sites.webhooks"),  # Issue #1356.
    _SimpleEndpointOp("listSiteWxRules", "mistapi.api.v1.sites.wxrules"),  # Issue #1357.
    _SimpleEndpointOp("ListSiteWxRulesDerived", "mistapi.api.v1.sites.wxrules"),  # Issue #1015.
    _SimpleEndpointOp("listSiteWxTags", "mistapi.api.v1.sites.wxtags"),  # Issue #1358.
    _SimpleEndpointOp("listSiteWxTunnels", "mistapi.api.v1.sites.wxtunnels"),  # Issue #1359.
    _SimpleEndpointOp("listSiteZonesStats", "mistapi.api.v1.sites.stats"),  # Issue #1360.
)

_MSP_OPS: tuple[_SimpleEndpointOp, ...] = (
    _SimpleEndpointOp("getMspDetails", "mistapi.api.v1.msps.msps"),  # Issue #1095.
    _SimpleEndpointOp("listMspAdmins", "mistapi.api.v1.msps.admins"),  # Issue #1258.
    _SimpleEndpointOp("listMspAuditLogs", "mistapi.api.v1.msps.logs"),  # Issue #1259.
    _SimpleEndpointOp("listMspOrgGroups", "mistapi.api.v1.msps.orggroups"),  # Issue #1261.
    _SimpleEndpointOp("listMspOrgLicenses", "mistapi.api.v1.msps.stats"),  # Issue #1262.
    _SimpleEndpointOp("listMspOrgs", "mistapi.api.v1.msps.orgs"),  # Issue #1264.
    _SimpleEndpointOp("listMspOrgStats", "mistapi.api.v1.msps.stats"),  # Issue #1263.
    _SimpleEndpointOp("listMspSsoRoles", "mistapi.api.v1.msps.ssoroles"),  # Issue #1266.
    _SimpleEndpointOp("listMspSsos", "mistapi.api.v1.msps.ssos"),  # Issue #1267.
    _SimpleEndpointOp("listMspTickets", "mistapi.api.v1.msps.tickets"),  # Issue #1268.
)


class SimpleEndpointExporter:
    """Exporter for get and list endpoints with at most one identifier."""

    @staticmethod
    def _resolve(operation: _SimpleEndpointOp) -> Any:
        """Return the SDK function for one operation."""
        try:
            module = importlib.import_module(operation.module)  # Load the SDK module only when selected.
        except ImportError:
            logging.error("SDK module %s is not importable", operation.module)  # Record the missing SDK module.
            return None
        callable_obj = getattr(module, operation.operation, None)  # Read the selected function from the module.
        if callable_obj is None:
            logging.error("SDK module %s does not define %s", operation.module, operation.operation)  # Record drift.
        return callable_obj

    @staticmethod
    def _choose(operations: tuple[_SimpleEndpointOp, ...], scope_label: str) -> _SimpleEndpointOp | None:
        """Prompt the operator to select one operation from a scope table."""
        mh = importlib.import_module("MistHelper")  # Load MistHelper lazily to avoid an import cycle.
        logging.info("Offering %d %s simple endpoint operations", len(operations), scope_label)  # Log the prompt.
        for index, operation in enumerate(operations, start=1):
            print(f"  [{index}] {operation.operation}")  # Show one operator choice per table row.
        answer = str(
            mh.InputUtils.safe_input(
                f"Select a {scope_label} endpoint operation (1-{len(operations)}): ",
                allow_empty=False,
                context=f"simple_endpoint_exporter.{scope_label}.selection",
            )
        ).strip()  # Normalize the prompt result for validation.
        logging.debug("Operator answered %r for the %s simple endpoint selection", answer, scope_label)  # Trace input.
        if not answer.isdigit():
            logging.info("! No operation selected. Returning to the menu.")  # Explain the safe cancel path.
            return None
        position = int(answer)  # Convert after the numeric guard to avoid ValueError.
        if not 1 <= position <= len(operations):
            logging.error("Selection %d is outside 1-%d", position, len(operations))  # Record the bad bound.
            logging.info("! That number is not on the list. Returning to the menu.")  # Explain the safe cancel path.
            return None
        return operations[position - 1]  # Map the one-based menu row to the tuple index.

    @staticmethod
    def _normalize(rawdata: Any) -> list[Any]:
        """Return response data as a list that the shared exporter can write."""
        if rawdata is None:
            return []
        if isinstance(rawdata, list):
            return rawdata
        if isinstance(rawdata, tuple):
            return list(rawdata)
        if isinstance(rawdata, dict):
            return [rawdata]
        return [{"value": rawdata}]

    @staticmethod
    def _persist(rawdata: Any, filename: str, operation: str) -> None:
        """Flatten and persist endpoint rows through the shared exporter."""
        mh = importlib.import_module("MistHelper")  # Load the shared DataExporter only when needed.
        rows = SimpleEndpointExporter._normalize(rawdata)  # Convert single-object responses to one row.
        logging.debug("%s returned %d normalized rows", operation, len(rows))  # Record the normalized size.
        if not rows:
            logging.info("! No %s data found", operation)  # Empty read results are valid.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rows)  # Flatten nested JSON for tabular output.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Keep line breaks safe in CSV cells.
        mh.DataExporter.write_with_format_selection(
            sanitized_data, filename, api_function_name=operation
        )  # Persist data.
        logging.debug("%s persisted %d rows to %s", operation, len(rows), filename)  # Record the write result.
        logging.info("! %d %s records exported to %s", len(rows), operation, filename)  # Tell the operator.

    @staticmethod
    def _run(operation: _SimpleEndpointOp, identifier: str | None, label: str) -> None:
        """Call one endpoint and persist all returned rows."""
        mh = importlib.import_module("MistHelper")  # Load apisession only during execution.
        callable_obj = SimpleEndpointExporter._resolve(operation)  # Resolve the SDK function before the API call.
        if callable_obj is None:
            logging.info("! %s is unavailable in this SDK version.", operation.operation)  # Explain SDK drift.
            return
        try:
            logging.info("Calling %s for %s", operation.operation, label)  # Log before the SDK call.
            if identifier is None:
                response = callable_obj(mh.apisession)  # No-scope endpoints take only the session.
            else:
                response = callable_obj(mh.apisession, identifier)  # Scoped endpoints take the session and one ID.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Collect every page.
            filename = f"{operation.operation}_{label.replace(' ', '_')}.csv"  # Build a readable export name.
            SimpleEndpointExporter._persist(rawdata, filename, operation.operation)  # Write the selected output format.
        except Exception as exc:
            logging.exception("Error running %s for %s", operation.operation, label)  # Keep traceback details.
            logging.info("! Error running %s: %s", operation.operation, exc)  # Show a short operator message.

    @staticmethod
    def global_endpoints() -> None:
        """Run any endpoint that needs no identifier."""
        logging.info("Global Simple Endpoints:")  # Show the menu header.
        operation = SimpleEndpointExporter._choose(_NONE_OPS, "global")  # Ask which endpoint to run.
        if operation is None:
            return
        SimpleEndpointExporter._run(operation, None, "global")  # Execute the no-identifier endpoint.

    @staticmethod
    def org_endpoints() -> None:
        """Run any org-scoped simple endpoint."""
        mh = importlib.import_module("MistHelper")  # Load the shared org selector lazily.
        logging.info("Org Simple Endpoints:")  # Show the menu header.
        operation = SimpleEndpointExporter._choose(_ORG_OPS, "org")  # Ask which endpoint to run.
        if operation is None:
            return
        org_id = str(mh.ConfigUtils.get_cached_or_prompted_org_id())  # Reuse the cached org prompt.
        if not org_id:
            logging.info("! No org selected. Returning to the menu.")  # Explain the safe cancel path.
            return
        SimpleEndpointExporter._run(operation, org_id, org_id)  # Execute the org endpoint.

    @staticmethod
    def site_endpoints() -> None:
        """Run any site-scoped simple endpoint."""
        mh = importlib.import_module("MistHelper")  # Load the shared site selector lazily.
        logging.info("Site Simple Endpoints:")  # Show the menu header.
        operation = SimpleEndpointExporter._choose(_SITE_OPS, "site")  # Ask which endpoint to run.
        if operation is None:
            return
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("site simple endpoints")  # Reuse the site prompt.
        if resolved is None:
            return
        site_id, site_name = resolved  # Keep the site name for a readable filename.
        SimpleEndpointExporter._run(operation, site_id, site_name)  # Execute the site endpoint.

    @staticmethod
    def msp_endpoints() -> None:
        """Run any MSP-scoped simple endpoint."""
        logging.info("MSP Simple Endpoints:")  # Show the menu header.
        operation = SimpleEndpointExporter._choose(_MSP_OPS, "msp")  # Ask which endpoint to run.
        if operation is None:
            return
        msp_id = InputUtils.prompt_msp_id()  # Use the shared EOF-safe MSP prompt.
        if msp_id is None:
            return
        SimpleEndpointExporter._run(operation, msp_id, msp_id)  # Execute the MSP endpoint.
