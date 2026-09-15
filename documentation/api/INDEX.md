# Mist API Endpoint Index

> 1013 spec operations, 61 library-only stubs (1074 total)

## Admins

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/invite/verify/{token} | verifyAdminInvite | verifyAdminInvite | [POST_invite_verify_token.md](admins/POST_invite_verify_token.md) |
| POST | /api/v1/register | registerNewAdmin | registerNewAdmin | [POST_register.md](admins/POST_register.md) |
| GET | /api/v1/register/recaptcha | getAdminRegistrationInfo | getAdminRegistrationInfo | [GET_register_recaptcha.md](admins/GET_register_recaptcha.md) |
| POST | /api/v1/register/verify/{token} | verifyRegistration | verifyRegistration | [POST_register_verify_token.md](admins/POST_register_verify_token.md) |

## Admins Login

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/login | login | login | [POST_login.md](admins/POST_login.md) |
| POST | /api/v1/login/two_factor | twoFactor | twoFactor | [POST_login_two_factor.md](admins/POST_login_two_factor.md) |

## Admins Login - OAuth2

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/login/oauth/{provider} | getOauth2AuthorizationUrlForLogin | getOauth2AuthorizationUrlForLogin | [GET_login_oauth_provider.md](admins/GET_login_oauth_provider.md) |
| POST | /api/v1/login/oauth/{provider} | loginOauth2 | loginOauth2 | [POST_login_oauth_provider.md](admins/POST_login_oauth_provider.md) |
| DELETE | /api/v1/login/oauth/{provider} | unlinkOauth2Provider | unlinkOauth2Provider | [DELETE_login_oauth_provider.md](admins/DELETE_login_oauth_provider.md) |

## Admins Logout

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/logout | logout | logout | [POST_logout.md](admins/POST_logout.md) |

## Admins Lookup

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/login/lookup | lookup | lookup | [POST_login_lookup.md](admins/POST_login_lookup.md) |

## Admins Recover Password

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/recover | recoverPassword | recoverPassword | [POST_recover.md](admins/POST_recover.md) |
| POST | /api/v1/recover/verify/{token} | verifyRecoverPassword | verifyRecoverPassword | [POST_recover_verify_token.md](admins/POST_recover_verify_token.md) |

## Constants Definitions

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/const/ap_channels | listApChannels | listApChannels | [GET_const_ap_channels.md](constants/GET_const_ap_channels.md) |
| GET | /api/v1/const/ap_esl_versions | listApLEslVersions | listApLEslVersions | [GET_const_ap_esl_versions.md](constants/GET_const_ap_esl_versions.md) |
| GET | /api/v1/const/ap_led_status | listApLedDefinition | listApLedDefinition | [GET_const_ap_led_status.md](constants/GET_const_ap_led_status.md) |
| GET | /api/v1/const/app_categories | listAppCategoryDefinitions | listAppCategoryDefinitions | [GET_const_app_categories.md](constants/GET_const_app_categories.md) |
| GET | /api/v1/const/app_subcategories | listAppSubCategoryDefinitions | listAppSubCategoryDefinitions | [GET_const_app_subcategories.md](constants/GET_const_app_subcategories.md) |
| GET | /api/v1/const/applications | listApplications | listApplications | [GET_const_applications.md](constants/GET_const_applications.md) |
| GET | /api/v1/const/countries | listCountryCodes | listCountryCodes | [GET_const_countries.md](constants/GET_const_countries.md) |
| GET | /api/v1/const/fingerprint_types | listFingerprintTypes | listFingerprintTypes | [GET_const_fingerprint_types.md](constants/GET_const_fingerprint_types.md) |
| GET | /api/v1/const/gateway_applications | listGatewayApplications | listGatewayApplications | [GET_const_gateway_applications.md](constants/GET_const_gateway_applications.md) |
| GET | /api/v1/const/insight_metrics | listInsightMetrics | listInsightMetrics | [GET_const_insight_metrics.md](constants/GET_const_insight_metrics.md) |
| GET | /api/v1/const/languages | listSiteLanguages | listSiteLanguages | [GET_const_languages.md](constants/GET_const_languages.md) |
| GET | /api/v1/const/license_types | listLicenseTypes | listLicenseTypes | [GET_const_license_types.md](constants/GET_const_license_types.md) |
| GET | /api/v1/const/marvisclient_versions | listMarvisClientVersions | listMarvisClientVersions | [GET_const_marvisclient_versions.md](constants/GET_const_marvisclient_versions.md) |
| GET | /api/v1/const/states | listStates | listStates | [GET_const_states.md](constants/GET_const_states.md) |
| GET | /api/v1/const/traffic_types | listTrafficTypes | listTrafficTypes | [GET_const_traffic_types.md](constants/GET_const_traffic_types.md) |
| GET | /api/v1/const/webhook_topics | listWebhookTopics | listWebhookTopics | [GET_const_webhook_topics.md](constants/GET_const_webhook_topics.md) |

## Constants Events

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/const/alarm_defs | listAlarmDefinitions | listAlarmDefinitions | [GET_const_alarm_defs.md](constants/GET_const_alarm_defs.md) |
| GET | /api/v1/const/client_events | listClientEventsDefinitions | listClientEventsDefinitions | [GET_const_client_events.md](constants/GET_const_client_events.md) |
| GET | /api/v1/const/device_events | listDeviceEventsDefinitions | listDeviceEventsDefinitions | [GET_const_device_events.md](constants/GET_const_device_events.md) |
| GET | /api/v1/const/mxedge_events | listMxEdgeEventsDefinitions | listMxEdgeEventsDefinitions | [GET_const_mxedge_events.md](constants/GET_const_mxedge_events.md) |
| GET | /api/v1/const/nac_events | listNacEventsDefinitions | listNacEventsDefinitions | [GET_const_nac_events.md](constants/GET_const_nac_events.md) |
| GET | /api/v1/const/otherdevice_events | listOtherDeviceEventsDefinitions | listOtherDeviceEventsDefinitions | [GET_const_otherdevice_events.md](constants/GET_const_otherdevice_events.md) |
| GET | /api/v1/const/system_events | listSystemEventsDefinitions | listSystemEventsDefinitions | [GET_const_system_events.md](constants/GET_const_system_events.md) |

## Constants Models

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/const/default_gateway_config | getGatewayDefaultConfig | getGatewayDefaultConfig | [GET_const_default_gateway_config.md](constants/GET_const_default_gateway_config.md) |
| GET | /api/v1/const/device_models | listDeviceModels | listDeviceModels | [GET_const_device_models.md](constants/GET_const_device_models.md) |
| GET | /api/v1/const/mxedge_models | listMxEdgeModels | listMxEdgeModels | [GET_const_mxedge_models.md](constants/GET_const_mxedge_models.md) |
| GET | /api/v1/const/otherdevice_models | listSupportedOtherDeviceModels | listSupportedOtherDeviceModels | [GET_const_otherdevice_models.md](constants/GET_const_otherdevice_models.md) |

## Installer

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/installer/orgs/{org_id}/alarmtemplates | listInstallerAlarmTemplates | listInstallerAlarmTemplates | [GET_installer_orgs_org_id_alarmtemplates.md](installer/GET_installer_orgs_org_id_alarmtemplates.md) |
| GET | /api/v1/installer/orgs/{org_id}/deviceprofiles | listInstallerDeviceProfiles | listInstallerDeviceProfiles | [GET_installer_orgs_org_id_deviceprofiles.md](installer/GET_installer_orgs_org_id_deviceprofiles.md) |
| GET | /api/v1/installer/orgs/{org_id}/devices | listInstallerListOfRecentlyClaimedDevices | listInstallerListOfRecentlyClaimedDevices | [GET_installer_orgs_org_id_devices.md](installer/GET_installer_orgs_org_id_devices.md) |
| POST | /api/v1/installer/orgs/{org_id}/devices | claimInstallerDevices | claimInstallerDevices | [POST_installer_orgs_org_id_devices.md](installer/POST_installer_orgs_org_id_devices.md) |
| PUT | /api/v1/installer/orgs/{org_id}/devices/{device_mac} | provisionInstallerDevices | provisionInstallerDevices | [PUT_installer_orgs_org_id_devices_device_mac.md](installer/PUT_installer_orgs_org_id_devices_device_mac.md) |
| DELETE | /api/v1/installer/orgs/{org_id}/devices/{device_mac} | unassignInstallerRecentlyClaimedDevice | unassignInstallerRecentlyClaimedDevice | [DELETE_installer_orgs_org_id_devices_device_mac.md](installer/DELETE_installer_orgs_org_id_devices_device_mac.md) |
| POST | /api/v1/installer/orgs/{org_id}/devices/{device_mac}/locate | startInstallerLocateDevice | startInstallerLocateDevice | [POST_installer_orgs_org_id_devices_device_mac_locate.md](installer/POST_installer_orgs_org_id_devices_device_mac_locate.md) |
| POST | /api/v1/installer/orgs/{org_id}/devices/{device_mac}/unlocate | stopInstallerLocateDevice | stopInstallerLocateDevice | [POST_installer_orgs_org_id_devices_device_mac_unlocate.md](installer/POST_installer_orgs_org_id_devices_device_mac_unlocate.md) |
| POST | /api/v1/installer/orgs/{org_id}/devices/{device_mac}/{image_name} | addInstallerDeviceImage | addInstallerDeviceImage | [POST_installer_orgs_org_id_devices_device_mac_image_name.md](installer/POST_installer_orgs_org_id_devices_device_mac_image_name.md) |
| DELETE | /api/v1/installer/orgs/{org_id}/devices/{device_mac}/{image_name} | deleteInstallerDeviceImage | deleteInstallerDeviceImage | [DELETE_installer_orgs_org_id_devices_device_mac_image_name.md](installer/DELETE_installer_orgs_org_id_devices_device_mac_image_name.md) |
| GET | /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc | getInstallerDeviceVirtualChassis | getInstallerDeviceVirtualChassis | [GET_installer_orgs_org_id_devices_fpc0_mac_vc.md](installer/GET_installer_orgs_org_id_devices_fpc0_mac_vc.md) |
| POST | /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc | createInstallerVirtualChassis | createInstallerVirtualChassis | [POST_installer_orgs_org_id_devices_fpc0_mac_vc.md](installer/POST_installer_orgs_org_id_devices_fpc0_mac_vc.md) |
| PUT | /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc | updateInstallerVirtualChassisMember | updateInstallerVirtualChassisMember | [PUT_installer_orgs_org_id_devices_fpc0_mac_vc.md](installer/PUT_installer_orgs_org_id_devices_fpc0_mac_vc.md) |
| GET | /api/v1/installer/orgs/{org_id}/rftemplates | listInstallerRfTemplatesNames | listInstallerRfTemplatesNames | [GET_installer_orgs_org_id_rftemplates.md](installer/GET_installer_orgs_org_id_rftemplates.md) |
| GET | /api/v1/installer/orgs/{org_id}/sitegroups | listInstallerSiteGroups | listInstallerSiteGroups | [GET_installer_orgs_org_id_sitegroups.md](installer/GET_installer_orgs_org_id_sitegroups.md) |
| GET | /api/v1/installer/orgs/{org_id}/sites | listInstallerSites | listInstallerSites | [GET_installer_orgs_org_id_sites.md](installer/GET_installer_orgs_org_id_sites.md) |
| PUT | /api/v1/installer/orgs/{org_id}/sites/{site_name} | createOrUpdateInstallerSites | createOrUpdateInstallerSites | [PUT_installer_orgs_org_id_sites_site_name.md](installer/PUT_installer_orgs_org_id_sites_site_name.md) |
| GET | /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps | listInstallerMaps | listInstallerMaps | [GET_installer_orgs_org_id_sites_site_name_maps.md](installer/GET_installer_orgs_org_id_sites_site_name_maps.md) |
| POST | /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps/import | importInstallerMap | importInstallerMap | [POST_installer_orgs_org_id_sites_site_name_maps_import.md](installer/POST_installer_orgs_org_id_sites_site_name_maps_import.md) |
| POST | /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps/{map_id} | createInstallerMap | createInstallerMap | [POST_installer_orgs_org_id_sites_site_name_maps_map_id.md](installer/POST_installer_orgs_org_id_sites_site_name_maps_map_id.md) |
| PUT | /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps/{map_id} | updateInstallerMap | updateInstallerMap | [PUT_installer_orgs_org_id_sites_site_name_maps_map_id.md](installer/PUT_installer_orgs_org_id_sites_site_name_maps_map_id.md) |
| DELETE | /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps/{map_id} | deleteInstallerMap | deleteInstallerMap | [DELETE_installer_orgs_org_id_sites_site_name_maps_map_id.md](installer/DELETE_installer_orgs_org_id_sites_site_name_maps_map_id.md) |
| GET | /api/v1/installer/sites/{site_name}/optimize | optimizeInstallerRrm | optimizeInstallerRrm | [GET_installer_sites_site_name_optimize.md](installer/GET_installer_sites_site_name_optimize.md) |

## MSPs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/msps | createMsp | createMsp | [POST_msps.md](msps/POST_msps.md) |
| GET | /api/v1/msps/{msp_id} | getMspDetails | getMspDetails | [GET_msps_msp_id.md](msps/GET_msps_msp_id.md) |
| PUT | /api/v1/msps/{msp_id} | updateMsp | updateMsp | [PUT_msps_msp_id.md](msps/PUT_msps_msp_id.md) |
| DELETE | /api/v1/msps/{msp_id} | deleteMsp | deleteMsp | [DELETE_msps_msp_id.md](msps/DELETE_msps_msp_id.md) |
| GET | /api/v1/msps/{msp_id}/search | searchMspOrgGroup | searchMspOrgGroup | [GET_msps_msp_id_search.md](msps/GET_msps_msp_id_search.md) |

## MSPs Admins

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/admins | listMspAdmins | listMspAdmins | [GET_msps_msp_id_admins.md](msps/GET_msps_msp_id_admins.md) |
| GET | /api/v1/msps/{msp_id}/admins/{admin_id} | getMspAdmin | getMspAdmin | [GET_msps_msp_id_admins_admin_id.md](msps/GET_msps_msp_id_admins_admin_id.md) |
| PUT | /api/v1/msps/{msp_id}/admins/{admin_id} | updateMspAdmin | updateMspAdmin | [PUT_msps_msp_id_admins_admin_id.md](msps/PUT_msps_msp_id_admins_admin_id.md) |
| DELETE | /api/v1/msps/{msp_id}/admins/{admin_id} | revokeMspAdmin | revokeMspAdmin | [DELETE_msps_msp_id_admins_admin_id.md](msps/DELETE_msps_msp_id_admins_admin_id.md) |
| POST | /api/v1/msps/{msp_id}/invites | inviteMspAdmin | inviteMspAdmin | [POST_msps_msp_id_invites.md](msps/POST_msps_msp_id_invites.md) |
| PUT | /api/v1/msps/{msp_id}/invites/{invite_id} | updateMspAdminInvite | updateMspAdminInvite | [PUT_msps_msp_id_invites_invite_id.md](msps/PUT_msps_msp_id_invites_invite_id.md) |
| DELETE | /api/v1/msps/{msp_id}/invites/{invite_id} | uninviteMspAdmin | uninviteMspAdmin | [DELETE_msps_msp_id_invites_invite_id.md](msps/DELETE_msps_msp_id_invites_invite_id.md) |

## MSPs Inventory

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/inventory/{device_mac} | getMspInventoryByMac | getMspInventoryByMac | [GET_msps_msp_id_inventory_device_mac.md](msps/GET_msps_msp_id_inventory_device_mac.md) |

## MSPs Licenses

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/msps/{msp_id}/claim | claimMspLicense | claimMspLicense | [POST_msps_msp_id_claim.md](msps/POST_msps_msp_id_claim.md) |
| GET | /api/v1/msps/{msp_id}/licenses | listMspLicenses | listMspLicenses | [GET_msps_msp_id_licenses.md](msps/GET_msps_msp_id_licenses.md) |
| PUT | /api/v1/msps/{msp_id}/licenses | moveOrDeleteMspLicenseToAnotherOrg | moveOrDeleteMspLicenseToAnotherOrg | [PUT_msps_msp_id_licenses.md](msps/PUT_msps_msp_id_licenses.md) |
| GET | /api/v1/msps/{msp_id}/stats/licenses | listMspOrgLicenses | listMspOrgLicenses | [GET_msps_msp_id_stats_licenses.md](msps/GET_msps_msp_id_stats_licenses.md) |

## MSPs Logo

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/msps/{msp_id}/logo | postMspLogo | postMspLogo | [POST_msps_msp_id_logo.md](msps/POST_msps_msp_id_logo.md) |
| DELETE | /api/v1/msps/{msp_id}/logo | deleteMspLogo | deleteMspLogo | [DELETE_msps_msp_id_logo.md](msps/DELETE_msps_msp_id_logo.md) |

## MSPs Logs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/logs | listMspAuditLogs | listMspAuditLogs | [GET_msps_msp_id_logs.md](msps/GET_msps_msp_id_logs.md) |
| GET | /api/v1/msps/{msp_id}/logs/count | countMspAuditLogs | countMspAuditLogs | [GET_msps_msp_id_logs_count.md](msps/GET_msps_msp_id_logs_count.md) |

## MSPs Marvis

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/suggestion/count | countMspsMarvisActions | countMspsMarvisActions | [GET_msps_msp_id_suggestion_count.md](msps/GET_msps_msp_id_suggestion_count.md) |

## MSPs Org Groups

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/orggroups | listMspOrgGroups | listMspOrgGroups | [GET_msps_msp_id_orggroups.md](msps/GET_msps_msp_id_orggroups.md) |
| POST | /api/v1/msps/{msp_id}/orggroups | createMspOrgGroup | createMspOrgGroup | [POST_msps_msp_id_orggroups.md](msps/POST_msps_msp_id_orggroups.md) |
| GET | /api/v1/msps/{msp_id}/orggroups/{orggroup_id} | getMspOrgGroup | getMspOrgGroup | [GET_msps_msp_id_orggroups_orggroup_id.md](msps/GET_msps_msp_id_orggroups_orggroup_id.md) |
| PUT | /api/v1/msps/{msp_id}/orggroups/{orggroup_id} | updateMspOrgGroup | updateMspOrgGroup | [PUT_msps_msp_id_orggroups_orggroup_id.md](msps/PUT_msps_msp_id_orggroups_orggroup_id.md) |
| DELETE | /api/v1/msps/{msp_id}/orggroups/{orggroup_id} | deleteMspOrgGroup | deleteMspOrgGroup | [DELETE_msps_msp_id_orggroups_orggroup_id.md](msps/DELETE_msps_msp_id_orggroups_orggroup_id.md) |

## MSPs Orgs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/orgs | listMspOrgs | listMspOrgs | [GET_msps_msp_id_orgs.md](msps/GET_msps_msp_id_orgs.md) |
| POST | /api/v1/msps/{msp_id}/orgs | createMspOrg | createMspOrg | [POST_msps_msp_id_orgs.md](msps/POST_msps_msp_id_orgs.md) |
| PUT | /api/v1/msps/{msp_id}/orgs | manageMspOrgs | manageMspOrgs | [PUT_msps_msp_id_orgs.md](msps/PUT_msps_msp_id_orgs.md) |
| GET | /api/v1/msps/{msp_id}/orgs/search | searchMspOrgs | searchMspOrgs | [GET_msps_msp_id_orgs_search.md](msps/GET_msps_msp_id_orgs_search.md) |
| GET | /api/v1/msps/{msp_id}/orgs/{org_id} | getMspOrg | getMspOrg | [GET_msps_msp_id_orgs_org_id.md](msps/GET_msps_msp_id_orgs_org_id.md) |
| PUT | /api/v1/msps/{msp_id}/orgs/{org_id} | updateMspOrg | updateMspOrg | [PUT_msps_msp_id_orgs_org_id.md](msps/PUT_msps_msp_id_orgs_org_id.md) |
| DELETE | /api/v1/msps/{msp_id}/orgs/{org_id} | deleteMspOrg | deleteMspOrg | [DELETE_msps_msp_id_orgs_org_id.md](msps/DELETE_msps_msp_id_orgs_org_id.md) |
| GET | /api/v1/msps/{msp_id}/stats/orgs | listMspOrgStats | listMspOrgStats | [GET_msps_msp_id_stats_orgs.md](msps/GET_msps_msp_id_stats_orgs.md) |

## MSPs SLEs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/insights/{metric} | getMspSle | getMspSle | [GET_msps_msp_id_insights_metric.md](msps/GET_msps_msp_id_insights_metric.md) |

## MSPs SSO

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/ssos | listMspSsos | listMspSsos | [GET_msps_msp_id_ssos.md](msps/GET_msps_msp_id_ssos.md) |
| POST | /api/v1/msps/{msp_id}/ssos | createMspSso | createMspSso | [POST_msps_msp_id_ssos.md](msps/POST_msps_msp_id_ssos.md) |
| GET | /api/v1/msps/{msp_id}/ssos/{sso_id} | getMspSso | getMspSso | [GET_msps_msp_id_ssos_sso_id.md](msps/GET_msps_msp_id_ssos_sso_id.md) |
| PUT | /api/v1/msps/{msp_id}/ssos/{sso_id} | updateMspSso | updateMspSso | [PUT_msps_msp_id_ssos_sso_id.md](msps/PUT_msps_msp_id_ssos_sso_id.md) |
| DELETE | /api/v1/msps/{msp_id}/ssos/{sso_id} | deleteMspSso | deleteMspSso | [DELETE_msps_msp_id_ssos_sso_id.md](msps/DELETE_msps_msp_id_ssos_sso_id.md) |
| GET | /api/v1/msps/{msp_id}/ssos/{sso_id}/failures | listMspSsoLatestFailures | listMspSsoLatestFailures | [GET_msps_msp_id_ssos_sso_id_failures.md](msps/GET_msps_msp_id_ssos_sso_id_failures.md) |
| GET | /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata | getMspSamlMetadata | getMspSamlMetadata | [GET_msps_msp_id_ssos_sso_id_metadata.md](msps/GET_msps_msp_id_ssos_sso_id_metadata.md) |
| GET | /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml | downloadMspSamlMetadata | downloadMspSamlMetadata | [GET_msps_msp_id_ssos_sso_id_metadata.xml.md](msps/GET_msps_msp_id_ssos_sso_id_metadata.xml.md) |

## MSPs SSO Roles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/ssoroles | listMspSsoRoles | listMspSsoRoles | [GET_msps_msp_id_ssoroles.md](msps/GET_msps_msp_id_ssoroles.md) |
| POST | /api/v1/msps/{msp_id}/ssoroles | createMspSsoRole | createMspSsoRole | [POST_msps_msp_id_ssoroles.md](msps/POST_msps_msp_id_ssoroles.md) |
| PUT | /api/v1/msps/{msp_id}/ssoroles/{ssorole_id} | updateMspSsoRole | updateMspSsoRole | [PUT_msps_msp_id_ssoroles_ssorole_id.md](msps/PUT_msps_msp_id_ssoroles_ssorole_id.md) |
| DELETE | /api/v1/msps/{msp_id}/ssoroles/{ssorole_id} | deleteMspSsoRole | deleteMspSsoRole | [DELETE_msps_msp_id_ssoroles_ssorole_id.md](msps/DELETE_msps_msp_id_ssoroles_ssorole_id.md) |

## MSPs Tickets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/msps/{msp_id}/tickets | listMspTickets | listMspTickets | [GET_msps_msp_id_tickets.md](msps/GET_msps_msp_id_tickets.md) |
| GET | /api/v1/msps/{msp_id}/tickets/count | countMspTickets | countMspTickets | [GET_msps_msp_id_tickets_count.md](msps/GET_msps_msp_id_tickets_count.md) |

## Orgs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs | createOrg | createOrg | [POST_orgs.md](orgs/POST_orgs.md) |
| GET | /api/v1/orgs/{org_id} | getOrg | getOrg | [GET_orgs_org_id.md](orgs/GET_orgs_org_id.md) |
| PUT | /api/v1/orgs/{org_id} | updateOrg | updateOrg | [PUT_orgs_org_id.md](orgs/PUT_orgs_org_id.md) |
| DELETE | /api/v1/orgs/{org_id} | deleteOrg | deleteOrg | [DELETE_orgs_org_id.md](orgs/DELETE_orgs_org_id.md) |
| POST | /api/v1/orgs/{org_id}/clone | cloneOrg | cloneOrg | [POST_orgs_org_id_clone.md](orgs/POST_orgs_org_id_clone.md) |

## Orgs AP Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/aptemplates | listOrgAptemplates | listOrgAptemplates | [GET_orgs_org_id_aptemplates.md](orgs/GET_orgs_org_id_aptemplates.md) |
| POST | /api/v1/orgs/{org_id}/aptemplates | createOrgAptemplate | createOrgAptemplate | [POST_orgs_org_id_aptemplates.md](orgs/POST_orgs_org_id_aptemplates.md) |
| GET | /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id} | getOrgAptemplate | getOrgAptemplate | [GET_orgs_org_id_aptemplates_aptemplate_id.md](orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id} | updateOrgAptemplate | updateOrgAptemplate | [PUT_orgs_org_id_aptemplates_aptemplate_id.md](orgs/PUT_orgs_org_id_aptemplates_aptemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id} | deleteOrgAptemplate | deleteOrgAptemplate | [DELETE_orgs_org_id_aptemplates_aptemplate_id.md](orgs/DELETE_orgs_org_id_aptemplates_aptemplate_id.md) |

## Orgs API Tokens

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/apitokens | listOrgApiTokens | listOrgApiTokens | [GET_orgs_org_id_apitokens.md](orgs/GET_orgs_org_id_apitokens.md) |
| POST | /api/v1/orgs/{org_id}/apitokens | createOrgApiToken | createOrgApiToken | [POST_orgs_org_id_apitokens.md](orgs/POST_orgs_org_id_apitokens.md) |
| GET | /api/v1/orgs/{org_id}/apitokens/{apitoken_id} | getOrgApiToken | getOrgApiToken | [GET_orgs_org_id_apitokens_apitoken_id.md](orgs/GET_orgs_org_id_apitokens_apitoken_id.md) |
| PUT | /api/v1/orgs/{org_id}/apitokens/{apitoken_id} | updateOrgApiToken | updateOrgApiToken | [PUT_orgs_org_id_apitokens_apitoken_id.md](orgs/PUT_orgs_org_id_apitokens_apitoken_id.md) |
| DELETE | /api/v1/orgs/{org_id}/apitokens/{apitoken_id} | deleteOrgApiToken | deleteOrgApiToken | [DELETE_orgs_org_id_apitokens_apitoken_id.md](orgs/DELETE_orgs_org_id_apitokens_apitoken_id.md) |

## Orgs Admins

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/admins | listOrgAdmins | listOrgAdmins | [GET_orgs_org_id_admins.md](orgs/GET_orgs_org_id_admins.md) |
| PUT | /api/v1/orgs/{org_id}/admins/{admin_id} | updateOrgAdmin | updateOrgAdmin | [PUT_orgs_org_id_admins_admin_id.md](orgs/PUT_orgs_org_id_admins_admin_id.md) |
| DELETE | /api/v1/orgs/{org_id}/admins/{admin_id} | revokeOrgAdmin | revokeOrgAdmin | [DELETE_orgs_org_id_admins_admin_id.md](orgs/DELETE_orgs_org_id_admins_admin_id.md) |
| POST | /api/v1/orgs/{org_id}/invites | inviteOrgAdmin | inviteOrgAdmin | [POST_orgs_org_id_invites.md](orgs/POST_orgs_org_id_invites.md) |
| PUT | /api/v1/orgs/{org_id}/invites/{invite_id} | updateOrgAdminInvite | updateOrgAdminInvite | [PUT_orgs_org_id_invites_invite_id.md](orgs/PUT_orgs_org_id_invites_invite_id.md) |
| DELETE | /api/v1/orgs/{org_id}/invites/{invite_id} | uninviteOrgAdmin | uninviteOrgAdmin | [DELETE_orgs_org_id_invites_invite_id.md](orgs/DELETE_orgs_org_id_invites_invite_id.md) |

## Orgs Advanced Anti Malware Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/aamwprofiles | listOrgAAMWProfiles | listOrgAAMWProfiles | [GET_orgs_org_id_aamwprofiles.md](orgs/GET_orgs_org_id_aamwprofiles.md) |
| POST | /api/v1/orgs/{org_id}/aamwprofiles | createOrgAAMWProfile | createOrgAAMWProfile | [POST_orgs_org_id_aamwprofiles.md](orgs/POST_orgs_org_id_aamwprofiles.md) |
| GET | /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id} | getOrgAAMWProfile | getOrgAAMWProfile | [GET_orgs_org_id_aamwprofiles_aamwprofile_id.md](orgs/GET_orgs_org_id_aamwprofiles_aamwprofile_id.md) |
| PUT | /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id} | updateOrgAAMWProfile | updateOrgAAMWProfile | [PUT_orgs_org_id_aamwprofiles_aamwprofile_id.md](orgs/PUT_orgs_org_id_aamwprofiles_aamwprofile_id.md) |
| DELETE | /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id} | deleteOrgAAMWProfile | deleteOrgAAMWProfile | [DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md](orgs/DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md) |

## Orgs Alarm Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/alarmtemplates | listOrgAlarmTemplates | listOrgAlarmTemplates | [GET_orgs_org_id_alarmtemplates.md](orgs/GET_orgs_org_id_alarmtemplates.md) |
| POST | /api/v1/orgs/{org_id}/alarmtemplates | createOrgAlarmTemplate | createOrgAlarmTemplate | [POST_orgs_org_id_alarmtemplates.md](orgs/POST_orgs_org_id_alarmtemplates.md) |
| GET | /api/v1/orgs/{org_id}/alarmtemplates/suppress | listOrgSuppressedAlarms | listOrgSuppressedAlarms | [GET_orgs_org_id_alarmtemplates_suppress.md](orgs/GET_orgs_org_id_alarmtemplates_suppress.md) |
| POST | /api/v1/orgs/{org_id}/alarmtemplates/suppress | suppressOrgAlarm | suppressOrgAlarm | [POST_orgs_org_id_alarmtemplates_suppress.md](orgs/POST_orgs_org_id_alarmtemplates_suppress.md) |
| DELETE | /api/v1/orgs/{org_id}/alarmtemplates/suppress | unsuppressOrgSuppressedAlarms | unsuppressOrgSuppressedAlarms | [DELETE_orgs_org_id_alarmtemplates_suppress.md](orgs/DELETE_orgs_org_id_alarmtemplates_suppress.md) |
| GET | /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id} | getOrgAlarmTemplate | getOrgAlarmTemplate | [GET_orgs_org_id_alarmtemplates_alarmtemplate_id.md](orgs/GET_orgs_org_id_alarmtemplates_alarmtemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id} | updateOrgAlarmTemplate | updateOrgAlarmTemplate | [PUT_orgs_org_id_alarmtemplates_alarmtemplate_id.md](orgs/PUT_orgs_org_id_alarmtemplates_alarmtemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id} | deleteOrgAlarmTemplate | deleteOrgAlarmTemplate | [DELETE_orgs_org_id_alarmtemplates_alarmtemplate_id.md](orgs/DELETE_orgs_org_id_alarmtemplates_alarmtemplate_id.md) |

## Orgs Alarms

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/alarms/ack | ackOrgMultipleAlarms | ackOrgMultipleAlarms | [POST_orgs_org_id_alarms_ack.md](orgs/POST_orgs_org_id_alarms_ack.md) |
| POST | /api/v1/orgs/{org_id}/alarms/ack_all | ackOrgAllAlarms | ackOrgAllAlarms | [POST_orgs_org_id_alarms_ack_all.md](orgs/POST_orgs_org_id_alarms_ack_all.md) |
| GET | /api/v1/orgs/{org_id}/alarms/count | countOrgAlarms | countOrgAlarms | [GET_orgs_org_id_alarms_count.md](orgs/GET_orgs_org_id_alarms_count.md) |
| GET | /api/v1/orgs/{org_id}/alarms/search | searchOrgAlarms | searchOrgAlarms | [GET_orgs_org_id_alarms_search.md](orgs/GET_orgs_org_id_alarms_search.md) |
| POST | /api/v1/orgs/{org_id}/alarms/unack | unackOrgMultipleAlarms | unackOrgMultipleAlarms | [POST_orgs_org_id_alarms_unack.md](orgs/POST_orgs_org_id_alarms_unack.md) |
| POST | /api/v1/orgs/{org_id}/alarms/unack_all | unackOrgAllAlarms | unackOrgAllAlarms | [POST_orgs_org_id_alarms_unack_all.md](orgs/POST_orgs_org_id_alarms_unack_all.md) |
| POST | /api/v1/orgs/{org_id}/alarms/{alarm_id}/ack | ackOrgAlarm | ackOrgAlarm | [POST_orgs_org_id_alarms_alarm_id_ack.md](orgs/POST_orgs_org_id_alarms_alarm_id_ack.md) |
| POST | /api/v1/orgs/{org_id}/subscriptions | subscribeOrgAlarmsReports | subscribeOrgAlarmsReports | [POST_orgs_org_id_subscriptions.md](orgs/POST_orgs_org_id_subscriptions.md) |
| DELETE | /api/v1/orgs/{org_id}/subscriptions | unsubscribeOrgAlarmsReports | unsubscribeOrgAlarmsReports | [DELETE_orgs_org_id_subscriptions.md](orgs/DELETE_orgs_org_id_subscriptions.md) |

## Orgs Antivirus Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/avprofiles | listOrgAntivirusProfiles | listOrgAntivirusProfiles | [GET_orgs_org_id_avprofiles.md](orgs/GET_orgs_org_id_avprofiles.md) |
| POST | /api/v1/orgs/{org_id}/avprofiles | createOrgAntivirusProfile | createOrgAntivirusProfile | [POST_orgs_org_id_avprofiles.md](orgs/POST_orgs_org_id_avprofiles.md) |
| GET | /api/v1/orgs/{org_id}/avprofiles/{avprofile_id} | getOrgAntivirusProfile | getOrgAntivirusProfile | [GET_orgs_org_id_avprofiles_avprofile_id.md](orgs/GET_orgs_org_id_avprofiles_avprofile_id.md) |
| PUT | /api/v1/orgs/{org_id}/avprofiles/{avprofile_id} | updateOrgAntivirusProfile | updateOrgAntivirusProfile | [PUT_orgs_org_id_avprofiles_avprofile_id.md](orgs/PUT_orgs_org_id_avprofiles_avprofile_id.md) |
| DELETE | /api/v1/orgs/{org_id}/avprofiles/{avprofile_id} | deleteOrgAntivirusProfile | deleteOrgAntivirusProfile | [DELETE_orgs_org_id_avprofiles_avprofile_id.md](orgs/DELETE_orgs_org_id_avprofiles_avprofile_id.md) |

## Orgs Asset Filters

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/assetfilters | listOrgAssetFilters | listOrgAssetFilters | [GET_orgs_org_id_assetfilters.md](orgs/GET_orgs_org_id_assetfilters.md) |
| POST | /api/v1/orgs/{org_id}/assetfilters | createOrgAssetFilter | createOrgAssetFilter | [POST_orgs_org_id_assetfilters.md](orgs/POST_orgs_org_id_assetfilters.md) |
| GET | /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id} | getOrgAssetFilter | getOrgAssetFilter | [GET_orgs_org_id_assetfilters_assetfilter_id.md](orgs/GET_orgs_org_id_assetfilters_assetfilter_id.md) |
| PUT | /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id} | updateOrgAssetFilter | updateOrgAssetFilter | [PUT_orgs_org_id_assetfilters_assetfilter_id.md](orgs/PUT_orgs_org_id_assetfilters_assetfilter_id.md) |
| DELETE | /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id} | deleteOrgAssetFilter | deleteOrgAssetFilter | [DELETE_orgs_org_id_assetfilters_assetfilter_id.md](orgs/DELETE_orgs_org_id_assetfilters_assetfilter_id.md) |

## Orgs Assets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/assets | listOrgAssets | listOrgAssets | [GET_orgs_org_id_assets.md](orgs/GET_orgs_org_id_assets.md) |
| POST | /api/v1/orgs/{org_id}/assets | createOrgAsset | createOrgAsset | [POST_orgs_org_id_assets.md](orgs/POST_orgs_org_id_assets.md) |
| POST | /api/v1/orgs/{org_id}/assets/import | importOrgAssets | importOrgAssets | [POST_orgs_org_id_assets_import.md](orgs/POST_orgs_org_id_assets_import.md) |
| GET | /api/v1/orgs/{org_id}/assets/{asset_id} | getOrgAsset | getOrgAsset | [GET_orgs_org_id_assets_asset_id.md](orgs/GET_orgs_org_id_assets_asset_id.md) |
| PUT | /api/v1/orgs/{org_id}/assets/{asset_id} | updateOrgAsset | updateOrgAsset | [PUT_orgs_org_id_assets_asset_id.md](orgs/PUT_orgs_org_id_assets_asset_id.md) |
| DELETE | /api/v1/orgs/{org_id}/assets/{asset_id} | deleteOrgAsset | deleteOrgAsset | [DELETE_orgs_org_id_assets_asset_id.md](orgs/DELETE_orgs_org_id_assets_asset_id.md) |

## Orgs CRL

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/crl | getOrgCrlFile | getOrgCrlFile | [GET_orgs_org_id_crl.md](orgs/GET_orgs_org_id_crl.md) |

## Orgs Cert

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/cert | listOrgCertificates | listOrgCertificates | [GET_orgs_org_id_cert.md](orgs/GET_orgs_org_id_cert.md) |
| POST | /api/v1/orgs/{org_id}/cert/apply_pending | rotateOrgCertificate | rotateOrgCertificate | [POST_orgs_org_id_cert_apply_pending.md](orgs/POST_orgs_org_id_cert_apply_pending.md) |
| POST | /api/v1/orgs/{org_id}/cert/regenerate | clearOrgCertificates | clearOrgCertificates | [POST_orgs_org_id_cert_regenerate.md](orgs/POST_orgs_org_id_cert_regenerate.md) |
| POST | /api/v1/orgs/{org_id}/crl/truncate | truncateOrgCrlFile | truncateOrgCrlFile | [POST_orgs_org_id_crl_truncate.md](orgs/POST_orgs_org_id_crl_truncate.md) |
| GET | /api/v1/orgs/{org_id}/ssl_proxy_cert | getOrgSslProxyCert | getOrgSslProxyCert | [GET_orgs_org_id_ssl_proxy_cert.md](orgs/GET_orgs_org_id_ssl_proxy_cert.md) |

## Orgs Clients - Marvis

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| DELETE | /api/v1/orgs/{org_id}/stats/marvisclients | deleteOrgMarvisClient | deleteOrgMarvisClient | [DELETE_orgs_org_id_stats_marvisclients.md](orgs/DELETE_orgs_org_id_stats_marvisclients.md) |

## Orgs Clients - NAC

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/nac_clients/count | countOrgNacClients | countOrgNacClients | [GET_orgs_org_id_nac_clients_count.md](orgs/GET_orgs_org_id_nac_clients_count.md) |
| GET | /api/v1/orgs/{org_id}/nac_clients/events/count | countOrgNacClientEvents | countOrgNacClientEvents | [GET_orgs_org_id_nac_clients_events_count.md](orgs/GET_orgs_org_id_nac_clients_events_count.md) |
| GET | /api/v1/orgs/{org_id}/nac_clients/events/search | searchOrgNacClientEvents | searchOrgNacClientEvents | [GET_orgs_org_id_nac_clients_events_search.md](orgs/GET_orgs_org_id_nac_clients_events_search.md) |
| GET | /api/v1/orgs/{org_id}/nac_clients/search | searchOrgNacClients | searchOrgNacClients | [GET_orgs_org_id_nac_clients_search.md](orgs/GET_orgs_org_id_nac_clients_search.md) |

## Orgs Clients - SDK

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| PUT | /api/v1/orgs/{org_id}/sdkclients/{sdkclient_id} | updateSdkClient | updateSdkClient | [PUT_orgs_org_id_sdkclients_sdkclient_id.md](orgs/PUT_orgs_org_id_sdkclients_sdkclient_id.md) |

## Orgs Clients - Wan

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wan_client/events/count | countOrgWanClientEvents | countOrgWanClientEvents | [GET_orgs_org_id_wan_client_events_count.md](orgs/GET_orgs_org_id_wan_client_events_count.md) |
| GET | /api/v1/orgs/{org_id}/wan_clients/count | countOrgWanClients | countOrgWanClients | [GET_orgs_org_id_wan_clients_count.md](orgs/GET_orgs_org_id_wan_clients_count.md) |
| GET | /api/v1/orgs/{org_id}/wan_clients/events/search | searchOrgWanClientEvents | searchOrgWanClientEvents | [GET_orgs_org_id_wan_clients_events_search.md](orgs/GET_orgs_org_id_wan_clients_events_search.md) |
| GET | /api/v1/orgs/{org_id}/wan_clients/search | searchOrgWanClients | searchOrgWanClients | [GET_orgs_org_id_wan_clients_search.md](orgs/GET_orgs_org_id_wan_clients_search.md) |

## Orgs Clients - Wired

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wired_clients/count | countOrgWiredClients | countOrgWiredClients | [GET_orgs_org_id_wired_clients_count.md](orgs/GET_orgs_org_id_wired_clients_count.md) |
| GET | /api/v1/orgs/{org_id}/wired_clients/search | searchOrgWiredClients | searchOrgWiredClients | [GET_orgs_org_id_wired_clients_search.md](orgs/GET_orgs_org_id_wired_clients_search.md) |

## Orgs Clients - Wireless

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/clients/count | countOrgWirelessClients | countOrgWirelessClients | [GET_orgs_org_id_clients_count.md](orgs/GET_orgs_org_id_clients_count.md) |
| GET | /api/v1/orgs/{org_id}/clients/events/count | countOrgWirelessClientEvents | countOrgWirelessClientEvents | [GET_orgs_org_id_clients_events_count.md](orgs/GET_orgs_org_id_clients_events_count.md) |
| GET | /api/v1/orgs/{org_id}/clients/events/search | searchOrgWirelessClientEvents | searchOrgWirelessClientEvents | [GET_orgs_org_id_clients_events_search.md](orgs/GET_orgs_org_id_clients_events_search.md) |
| GET | /api/v1/orgs/{org_id}/clients/search | searchOrgWirelessClients | searchOrgWirelessClients | [GET_orgs_org_id_clients_search.md](orgs/GET_orgs_org_id_clients_search.md) |
| GET | /api/v1/orgs/{org_id}/clients/sessions/count | countOrgWirelessClientsSessions | countOrgWirelessClientsSessions | [GET_orgs_org_id_clients_sessions_count.md](orgs/GET_orgs_org_id_clients_sessions_count.md) |
| GET | /api/v1/orgs/{org_id}/clients/sessions/search | searchOrgWirelessClientSessions | searchOrgWirelessClientSessions | [GET_orgs_org_id_clients_sessions_search.md](orgs/GET_orgs_org_id_clients_sessions_search.md) |

## Orgs Device Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/deviceprofiles | listOrgDeviceProfiles | listOrgDeviceProfiles | [GET_orgs_org_id_deviceprofiles.md](orgs/GET_orgs_org_id_deviceprofiles.md) |
| POST | /api/v1/orgs/{org_id}/deviceprofiles | createOrgDeviceProfile | createOrgDeviceProfile | [POST_orgs_org_id_deviceprofiles.md](orgs/POST_orgs_org_id_deviceprofiles.md) |
| GET | /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id} | getOrgDeviceProfile | getOrgDeviceProfile | [GET_orgs_org_id_deviceprofiles_deviceprofile_id.md](orgs/GET_orgs_org_id_deviceprofiles_deviceprofile_id.md) |
| PUT | /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id} | updateOrgDeviceProfile | updateOrgDeviceProfile | [PUT_orgs_org_id_deviceprofiles_deviceprofile_id.md](orgs/PUT_orgs_org_id_deviceprofiles_deviceprofile_id.md) |
| DELETE | /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id} | deleteOrgDeviceProfile | deleteOrgDeviceProfile | [DELETE_orgs_org_id_deviceprofiles_deviceprofile_id.md](orgs/DELETE_orgs_org_id_deviceprofiles_deviceprofile_id.md) |
| POST | /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign | assignOrgDeviceProfile | assignOrgDeviceProfile | [POST_orgs_org_id_deviceprofiles_deviceprofile_id_assign.md](orgs/POST_orgs_org_id_deviceprofiles_deviceprofile_id_assign.md) |
| POST | /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/unassign | unassignOrgDeviceProfile | unassignOrgDeviceProfile | [POST_orgs_org_id_deviceprofiles_deviceprofile_id_unassign.md](orgs/POST_orgs_org_id_deviceprofiles_deviceprofile_id_unassign.md) |

## Orgs Devices

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/devices | listOrgDevices | listOrgDevices | [GET_orgs_org_id_devices.md](orgs/GET_orgs_org_id_devices.md) |
| GET | /api/v1/orgs/{org_id}/devices/count | countOrgDevices | countOrgDevices | [GET_orgs_org_id_devices_count.md](orgs/GET_orgs_org_id_devices_count.md) |
| GET | /api/v1/orgs/{org_id}/devices/events/count | countOrgDeviceEvents | countOrgDeviceEvents | [GET_orgs_org_id_devices_events_count.md](orgs/GET_orgs_org_id_devices_events_count.md) |
| GET | /api/v1/orgs/{org_id}/devices/events/search | searchOrgDeviceEvents | searchOrgDeviceEvents | [GET_orgs_org_id_devices_events_search.md](orgs/GET_orgs_org_id_devices_events_search.md) |
| GET | /api/v1/orgs/{org_id}/devices/last_config/count | countOrgDeviceLastConfigs | countOrgDeviceLastConfigs | [GET_orgs_org_id_devices_last_config_count.md](orgs/GET_orgs_org_id_devices_last_config_count.md) |
| GET | /api/v1/orgs/{org_id}/devices/last_config/search | searchOrgDeviceLastConfigs | searchOrgDeviceLastConfigs | [GET_orgs_org_id_devices_last_config_search.md](orgs/GET_orgs_org_id_devices_last_config_search.md) |
| GET | /api/v1/orgs/{org_id}/devices/radio_macs | listOrgApsMacs | listOrgApsMacs | [GET_orgs_org_id_devices_radio_macs.md](orgs/GET_orgs_org_id_devices_radio_macs.md) |
| GET | /api/v1/orgs/{org_id}/devices/search | searchOrgDevices | searchOrgDevices | [GET_orgs_org_id_devices_search.md](orgs/GET_orgs_org_id_devices_search.md) |
| GET | /api/v1/orgs/{org_id}/devices/summary | listOrgDevicesSummary | listOrgDevicesSummary | [GET_orgs_org_id_devices_summary.md](orgs/GET_orgs_org_id_devices_summary.md) |
| GET | /api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd | getOrgJuniperDevicesCommand | getOrgJuniperDevicesCommand | [GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md](orgs/GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md) |

## Orgs Devices - AOS

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/aos/register_cmd | getOrgAosRegisterCmd | getOrgAosRegisterCmd | [GET_orgs_org_id_aos_register_cmd.md](orgs/GET_orgs_org_id_aos_register_cmd.md) |

## Orgs Devices - Others

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/otherdevices | listOrgOtherDevices | listOrgOtherDevices | [GET_orgs_org_id_otherdevices.md](orgs/GET_orgs_org_id_otherdevices.md) |
| PUT | /api/v1/orgs/{org_id}/otherdevices | updateOrgOtherDevices | updateOrgOtherDevices | [PUT_orgs_org_id_otherdevices.md](orgs/PUT_orgs_org_id_otherdevices.md) |
| GET | /api/v1/orgs/{org_id}/otherdevices/events/count | countOrgOtherDeviceEvents | countOrgOtherDeviceEvents | [GET_orgs_org_id_otherdevices_events_count.md](orgs/GET_orgs_org_id_otherdevices_events_count.md) |
| GET | /api/v1/orgs/{org_id}/otherdevices/events/search | searchOrgOtherDeviceEvents | searchOrgOtherDeviceEvents | [GET_orgs_org_id_otherdevices_events_search.md](orgs/GET_orgs_org_id_otherdevices_events_search.md) |
| GET | /api/v1/orgs/{org_id}/otherdevices/{device_mac} | getOrgOtherDevice | getOrgOtherDevice | [GET_orgs_org_id_otherdevices_device_mac.md](orgs/GET_orgs_org_id_otherdevices_device_mac.md) |
| PUT | /api/v1/orgs/{org_id}/otherdevices/{device_mac} | updateOrgOtherDevice | updateOrgOtherDevice | [PUT_orgs_org_id_otherdevices_device_mac.md](orgs/PUT_orgs_org_id_otherdevices_device_mac.md) |
| DELETE | /api/v1/orgs/{org_id}/otherdevices/{device_mac} | deleteOrgOtherDevice | deleteOrgOtherDevice | [DELETE_orgs_org_id_otherdevices_device_mac.md](orgs/DELETE_orgs_org_id_otherdevices_device_mac.md) |
| POST | /api/v1/orgs/{org_id}/otherdevices/{device_mac}/reboot | rebootOrgOtherDevice | rebootOrgOtherDevice | [POST_orgs_org_id_otherdevices_device_mac_reboot.md](orgs/POST_orgs_org_id_otherdevices_device_mac_reboot.md) |

## Orgs Devices - SSR

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/128routers/register_cmd | getOrg128TRegistrationCommands | getOrg128TRegistrationCommands | [GET_orgs_org_id_128routers_register_cmd.md](orgs/GET_orgs_org_id_128routers_register_cmd.md) |
| POST | /api/v1/orgs/{org_id}/ssr/export_idtokens | exportOrgSsrIdTokens | exportOrgSsrIdTokens | [POST_orgs_org_id_ssr_export_idtokens.md](orgs/POST_orgs_org_id_ssr_export_idtokens.md) |
| GET | /api/v1/orgs/{org_id}/ssr/register_cmd | getOrgSsrRegistrationCommands | getOrgSsrRegistrationCommands | [GET_orgs_org_id_ssr_register_cmd.md](orgs/GET_orgs_org_id_ssr_register_cmd.md) |

## Orgs EVPN Topologies

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/evpn_topologies | listOrgEvpnTopologies | listOrgEvpnTopologies | [GET_orgs_org_id_evpn_topologies.md](orgs/GET_orgs_org_id_evpn_topologies.md) |
| POST | /api/v1/orgs/{org_id}/evpn_topologies | createOrgEvpnTopology | createOrgEvpnTopology | [POST_orgs_org_id_evpn_topologies.md](orgs/POST_orgs_org_id_evpn_topologies.md) |
| GET | /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id} | getOrgEvpnTopology | getOrgEvpnTopology | [GET_orgs_org_id_evpn_topologies_evpn_topology_id.md](orgs/GET_orgs_org_id_evpn_topologies_evpn_topology_id.md) |
| PUT | /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id} | updateOrgEvpnTopology | updateOrgEvpnTopology | [PUT_orgs_org_id_evpn_topologies_evpn_topology_id.md](orgs/PUT_orgs_org_id_evpn_topologies_evpn_topology_id.md) |
| DELETE | /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id} | deleteOrgEvpnTopology | deleteOrgEvpnTopology | [DELETE_orgs_org_id_evpn_topologies_evpn_topology_id.md](orgs/DELETE_orgs_org_id_evpn_topologies_evpn_topology_id.md) |

## Orgs Events

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/events/search | searchOrgEvents | searchOrgEvents | [GET_orgs_org_id_events_search.md](orgs/GET_orgs_org_id_events_search.md) |
| GET | /api/v1/orgs/{org_id}/events/system/count | countOrgSystemEvents | countOrgSystemEvents | [GET_orgs_org_id_events_system_count.md](orgs/GET_orgs_org_id_events_system_count.md) |
| GET | /api/v1/orgs/{org_id}/events/system/search | searchOrgSystemEvents | searchOrgSystemEvents | [GET_orgs_org_id_events_system_search.md](orgs/GET_orgs_org_id_events_system_search.md) |

## Orgs Gateway Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/gatewaytemplates | listOrgGatewayTemplates | listOrgGatewayTemplates | [GET_orgs_org_id_gatewaytemplates.md](orgs/GET_orgs_org_id_gatewaytemplates.md) |
| POST | /api/v1/orgs/{org_id}/gatewaytemplates | createOrgGatewayTemplate | createOrgGatewayTemplate | [POST_orgs_org_id_gatewaytemplates.md](orgs/POST_orgs_org_id_gatewaytemplates.md) |
| GET | /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id} | getOrgGatewayTemplate | getOrgGatewayTemplate | [GET_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md](orgs/GET_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id} | updateOrgGatewayTemplate | updateOrgGatewayTemplate | [PUT_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md](orgs/PUT_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id} | deleteOrgGatewayTemplate | deleteOrgGatewayTemplate | [DELETE_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md](orgs/DELETE_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md) |

## Orgs Guests

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/guests | listOrgGuestAuthorizations | listOrgGuestAuthorizations | [GET_orgs_org_id_guests.md](orgs/GET_orgs_org_id_guests.md) |
| GET | /api/v1/orgs/{org_id}/guests/count | countOrgGuestAuthorizations | countOrgGuestAuthorizations | [GET_orgs_org_id_guests_count.md](orgs/GET_orgs_org_id_guests_count.md) |
| GET | /api/v1/orgs/{org_id}/guests/search | searchOrgGuestAuthorization | searchOrgGuestAuthorization | [GET_orgs_org_id_guests_search.md](orgs/GET_orgs_org_id_guests_search.md) |
| GET | /api/v1/orgs/{org_id}/guests/{guest_mac} | getOrgGuestAuthorization | getOrgGuestAuthorization | [GET_orgs_org_id_guests_guest_mac.md](orgs/GET_orgs_org_id_guests_guest_mac.md) |
| PUT | /api/v1/orgs/{org_id}/guests/{guest_mac} | updateOrgGuestAuthorization | updateOrgGuestAuthorization | [PUT_orgs_org_id_guests_guest_mac.md](orgs/PUT_orgs_org_id_guests_guest_mac.md) |
| DELETE | /api/v1/orgs/{org_id}/guests/{guest_mac} | deleteOrgGuestAuthorization | deleteOrgGuestAuthorization | [DELETE_orgs_org_id_guests_guest_mac.md](orgs/DELETE_orgs_org_id_guests_guest_mac.md) |

## Orgs IDP Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/idpprofiles | listOrgIdpProfiles | listOrgIdpProfiles | [GET_orgs_org_id_idpprofiles.md](orgs/GET_orgs_org_id_idpprofiles.md) |
| POST | /api/v1/orgs/{org_id}/idpprofiles | createOrgIdpProfile | createOrgIdpProfile | [POST_orgs_org_id_idpprofiles.md](orgs/POST_orgs_org_id_idpprofiles.md) |
| GET | /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id} | getOrgIdpProfile | getOrgIdpProfile | [GET_orgs_org_id_idpprofiles_idpprofile_id.md](orgs/GET_orgs_org_id_idpprofiles_idpprofile_id.md) |
| PUT | /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id} | updateOrgIdpProfile | updateOrgIdpProfile | [PUT_orgs_org_id_idpprofiles_idpprofile_id.md](orgs/PUT_orgs_org_id_idpprofiles_idpprofile_id.md) |
| DELETE | /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id} | deleteOrgIdpProfile | deleteOrgIdpProfile | [DELETE_orgs_org_id_idpprofiles_idpprofile_id.md](orgs/DELETE_orgs_org_id_idpprofiles_idpprofile_id.md) |

## Orgs Integration Cradlepoint

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/cradlepoint/setup | testOrgCradlepointConnection | testOrgCradlepointConnection | [GET_orgs_org_id_setting_cradlepoint_setup.md](orgs/GET_orgs_org_id_setting_cradlepoint_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/cradlepoint/setup | setupOrgCradlepointConnectionToMist | setupOrgCradlepointConnectionToMist | [POST_orgs_org_id_setting_cradlepoint_setup.md](orgs/POST_orgs_org_id_setting_cradlepoint_setup.md) |
| PUT | /api/v1/orgs/{org_id}/setting/cradlepoint/setup | updateOrgCradlepointConnectionToMist | updateOrgCradlepointConnectionToMist | [PUT_orgs_org_id_setting_cradlepoint_setup.md](orgs/PUT_orgs_org_id_setting_cradlepoint_setup.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/cradlepoint/setup | deleteOrgCradlepointConnection | deleteOrgCradlepointConnection | [DELETE_orgs_org_id_setting_cradlepoint_setup.md](orgs/DELETE_orgs_org_id_setting_cradlepoint_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/cradlepoint/sync | syncOrgCradlepointRouters | syncOrgCradlepointRouters | [POST_orgs_org_id_setting_cradlepoint_sync.md](orgs/POST_orgs_org_id_setting_cradlepoint_sync.md) |

## Orgs Integration JSE

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/jse/info | getOrgJseInfo | getOrgJseInfo | [GET_orgs_org_id_setting_jse_info.md](orgs/GET_orgs_org_id_setting_jse_info.md) |
| GET | /api/v1/orgs/{org_id}/setting/jse/setup | getOrgJseIntegration | getOrgJseIntegration | [GET_orgs_org_id_setting_jse_setup.md](orgs/GET_orgs_org_id_setting_jse_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/jse/setup | setupOrgJseIntegration | setupOrgJseIntegration | [POST_orgs_org_id_setting_jse_setup.md](orgs/POST_orgs_org_id_setting_jse_setup.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/jse/setup | deleteOrgJseIntegration | deleteOrgJseIntegration | [DELETE_orgs_org_id_setting_jse_setup.md](orgs/DELETE_orgs_org_id_setting_jse_setup.md) |

## Orgs Integration Juniper

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/setting/juniper/link_accounts | linkOrgToJuniperJuniperAccount | linkOrgToJuniperJuniperAccount | [POST_orgs_org_id_setting_juniper_link_accounts.md](orgs/POST_orgs_org_id_setting_juniper_link_accounts.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/juniper/unlink_account | unlinkOrgFromJuniperCustomerId | unlinkOrgFromJuniperCustomerId | [DELETE_orgs_org_id_setting_juniper_unlink_account.md](orgs/DELETE_orgs_org_id_setting_juniper_unlink_account.md) |

## Orgs Integration SkyATP

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| PUT | /api/v1/orgs/{org_id}/setting/skyatp/secintel_allowlist | udpateOrgAtpAllowedList | udpateOrgAtpAllowedList | [PUT_orgs_org_id_setting_skyatp_secintel_allowlist.md](orgs/PUT_orgs_org_id_setting_skyatp_secintel_allowlist.md) |
| PUT | /api/v1/orgs/{org_id}/setting/skyatp/secintel_blocklist | udpateOrgAtpBlockedList | udpateOrgAtpBlockedList | [PUT_orgs_org_id_setting_skyatp_secintel_blocklist.md](orgs/PUT_orgs_org_id_setting_skyatp_secintel_blocklist.md) |
| GET | /api/v1/orgs/{org_id}/setting/skyatp/setup | getOrgSkyAtpIntegration | getOrgSkyAtpIntegration | [GET_orgs_org_id_setting_skyatp_setup.md](orgs/GET_orgs_org_id_setting_skyatp_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/skyatp/setup | setupOrgAtpIntegration | setupOrgAtpIntegration | [POST_orgs_org_id_setting_skyatp_setup.md](orgs/POST_orgs_org_id_setting_skyatp_setup.md) |
| PUT | /api/v1/orgs/{org_id}/setting/skyatp/setup | udpateOrgAtpIntegration | udpateOrgAtpIntegration | [PUT_orgs_org_id_setting_skyatp_setup.md](orgs/PUT_orgs_org_id_setting_skyatp_setup.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/skyatp/setup | deleteOrgSkyAtpIntegration | deleteOrgSkyAtpIntegration | [DELETE_orgs_org_id_setting_skyatp_setup.md](orgs/DELETE_orgs_org_id_setting_skyatp_setup.md) |

## Orgs Integration Zscaler

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/zscaler/setup | getOrgZscalerIntegration | getOrgZscalerIntegration | [GET_orgs_org_id_setting_zscaler_setup.md](orgs/GET_orgs_org_id_setting_zscaler_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/zscaler/setup | setupOrgZscalerIntegration | setupOrgZscalerIntegration | [POST_orgs_org_id_setting_zscaler_setup.md](orgs/POST_orgs_org_id_setting_zscaler_setup.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/zscaler/setup | deleteOrgZscalerIntegration | deleteOrgZscalerIntegration | [DELETE_orgs_org_id_setting_zscaler_setup.md](orgs/DELETE_orgs_org_id_setting_zscaler_setup.md) |

## Orgs Inventory

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/inventory | getOrgInventory | getOrgInventory | [GET_orgs_org_id_inventory.md](orgs/GET_orgs_org_id_inventory.md) |
| POST | /api/v1/orgs/{org_id}/inventory | addOrgInventory | addOrgInventory | [POST_orgs_org_id_inventory.md](orgs/POST_orgs_org_id_inventory.md) |
| PUT | /api/v1/orgs/{org_id}/inventory | updateOrgInventoryAssignment | updateOrgInventoryAssignment | [PUT_orgs_org_id_inventory.md](orgs/PUT_orgs_org_id_inventory.md) |
| GET | /api/v1/orgs/{org_id}/inventory/count | countOrgInventory | countOrgInventory | [GET_orgs_org_id_inventory_count.md](orgs/GET_orgs_org_id_inventory_count.md) |
| POST | /api/v1/orgs/{org_id}/inventory/create_ha_cluster | createOrgGatewayHaCluster | createOrgGatewayHaCluster | [POST_orgs_org_id_inventory_create_ha_cluster.md](orgs/POST_orgs_org_id_inventory_create_ha_cluster.md) |
| POST | /api/v1/orgs/{org_id}/inventory/delete_ha_cluster | deleteOrgGatewayHaCluster | deleteOrgGatewayHaCluster | [POST_orgs_org_id_inventory_delete_ha_cluster.md](orgs/POST_orgs_org_id_inventory_delete_ha_cluster.md) |
| POST | /api/v1/orgs/{org_id}/inventory/reevaluate_auto_assignment | reevaluateOrgAutoAssignment | reevaluateOrgAutoAssignment | [POST_orgs_org_id_inventory_reevaluate_auto_assignment.md](orgs/POST_orgs_org_id_inventory_reevaluate_auto_assignment.md) |
| POST | /api/v1/orgs/{org_id}/inventory/replace | replaceOrgDevices | replaceOrgDevices | [POST_orgs_org_id_inventory_replace.md](orgs/POST_orgs_org_id_inventory_replace.md) |
| GET | /api/v1/orgs/{org_id}/inventory/search | searchOrgInventory | searchOrgInventory | [GET_orgs_org_id_inventory_search.md](orgs/GET_orgs_org_id_inventory_search.md) |

## Orgs JSI

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/jsi/devices | listOrgJsiDevices | listOrgJsiDevices | [GET_orgs_org_id_jsi_devices.md](orgs/GET_orgs_org_id_jsi_devices.md) |
| GET | /api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd | adoptOrgJsiDevice | adoptOrgJsiDevice | [GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md](orgs/GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md) |
| POST | /api/v1/orgs/{org_id}/jsi/devices/{device_mac}/shell | createOrgJsiDeviceShellSession | createOrgJsiDeviceShellSession | [POST_orgs_org_id_jsi_devices_device_mac_shell.md](orgs/POST_orgs_org_id_jsi_devices_device_mac_shell.md) |
| GET | /api/v1/orgs/{org_id}/jsi/inventory | listOrgJsiPastPurchases | listOrgJsiPastPurchases | [GET_orgs_org_id_jsi_inventory.md](orgs/GET_orgs_org_id_jsi_inventory.md) |
| GET | /api/v1/orgs/{org_id}/jsi/inventory/count | countOrgJsiAssetsAndContracts | countOrgJsiAssetsAndContracts | [GET_orgs_org_id_jsi_inventory_count.md](orgs/GET_orgs_org_id_jsi_inventory_count.md) |
| GET | /api/v1/orgs/{org_id}/jsi/inventory/search | searchOrgJsiAssetsAndContracts | searchOrgJsiAssetsAndContracts | [GET_orgs_org_id_jsi_inventory_search.md](orgs/GET_orgs_org_id_jsi_inventory_search.md) |
| GET | /api/v1/orgs/{org_id}/jsi/pbn/count | countOrgJsiPbn | countOrgJsiPbn | [GET_orgs_org_id_jsi_pbn_count.md](orgs/GET_orgs_org_id_jsi_pbn_count.md) |
| GET | /api/v1/orgs/{org_id}/jsi/pbn/search | searchOrgJsiPbn | searchOrgJsiPbn | [GET_orgs_org_id_jsi_pbn_search.md](orgs/GET_orgs_org_id_jsi_pbn_search.md) |
| GET | /api/v1/orgs/{org_id}/jsi/sirt/count | countOrgJsiSirt | countOrgJsiSirt | [GET_orgs_org_id_jsi_sirt_count.md](orgs/GET_orgs_org_id_jsi_sirt_count.md) |
| GET | /api/v1/orgs/{org_id}/jsi/sirt/search | searchOrgJsiSirt | searchOrgJsiSirt | [GET_orgs_org_id_jsi_sirt_search.md](orgs/GET_orgs_org_id_jsi_sirt_search.md) |

## Orgs Licenses

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/claim | claimOrgLicense | claimOrgLicense | [POST_orgs_org_id_claim.md](orgs/POST_orgs_org_id_claim.md) |
| GET | /api/v1/orgs/{org_id}/claim/status | GetOrgLicenseAsyncClaimStatus | GetOrgLicenseAsyncClaimStatus | [GET_orgs_org_id_claim_status.md](orgs/GET_orgs_org_id_claim_status.md) |
| GET | /api/v1/orgs/{org_id}/licenses | getOrgLicensesSummary | getOrgLicensesSummary | [GET_orgs_org_id_licenses.md](orgs/GET_orgs_org_id_licenses.md) |
| PUT | /api/v1/orgs/{org_id}/licenses | moveOrDeleteOrgLicenseToAnotherOrg | moveOrDeleteOrgLicenseToAnotherOrg | [PUT_orgs_org_id_licenses.md](orgs/PUT_orgs_org_id_licenses.md) |
| GET | /api/v1/orgs/{org_id}/licenses/usages | getOrgLicensesBySite | getOrgLicensesBySite | [GET_orgs_org_id_licenses_usages.md](orgs/GET_orgs_org_id_licenses_usages.md) |

## Orgs Linked Applications

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts | getOrgOauthAppLinkedStatus | getOrgOauthAppLinkedStatus | [GET_orgs_org_id_setting_app_name_link_accounts.md](orgs/GET_orgs_org_id_setting_app_name_link_accounts.md) |
| POST | /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts | addOrgOauthAppAccounts | addOrgOauthAppAccounts | [POST_orgs_org_id_setting_app_name_link_accounts.md](orgs/POST_orgs_org_id_setting_app_name_link_accounts.md) |
| PUT | /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts/{account_id} | updateOrgOauthAppAccount | updateOrgOauthAppAccount | [PUT_orgs_org_id_setting_app_name_link_accounts_account_id.md](orgs/PUT_orgs_org_id_setting_app_name_link_accounts_account_id.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts/{account_id} | deleteOrgOauthAppAuthorization | deleteOrgOauthAppAuthorization | [DELETE_orgs_org_id_setting_app_name_link_accounts_account_id.md](orgs/DELETE_orgs_org_id_setting_app_name_link_accounts_account_id.md) |

## Orgs Logs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/logs | listOrgAuditLogs | listOrgAuditLogs | [GET_orgs_org_id_logs.md](orgs/GET_orgs_org_id_logs.md) |
| GET | /api/v1/orgs/{org_id}/logs/count | countOrgAuditLogs | countOrgAuditLogs | [GET_orgs_org_id_logs_count.md](orgs/GET_orgs_org_id_logs_count.md) |

## Orgs Maps

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/maps/import | importOrgMaps | importOrgMaps | [POST_orgs_org_id_maps_import.md](orgs/POST_orgs_org_id_maps_import.md) |
| POST | /api/v1/orgs/{org_id}/sites/{site_name}/maps/import | importOrgMapToSite | importOrgMapToSite | [POST_orgs_org_id_sites_site_name_maps_import.md](orgs/POST_orgs_org_id_sites_site_name_maps_import.md) |

## Orgs Marvis

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/troubleshoot | troubleshootOrg | troubleshootOrg | [GET_orgs_org_id_troubleshoot.md](orgs/GET_orgs_org_id_troubleshoot.md) |

## Orgs Marvis Invites

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/marvisinvites | listOrgMarvisClientInvites | listOrgMarvisClientInvites | [GET_orgs_org_id_marvisinvites.md](orgs/GET_orgs_org_id_marvisinvites.md) |
| POST | /api/v1/orgs/{org_id}/marvisinvites | createOrgMarvisClientInvite | createOrgMarvisClientInvite | [POST_orgs_org_id_marvisinvites.md](orgs/POST_orgs_org_id_marvisinvites.md) |
| GET | /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id} | getOrgMarvisClientInvite | getOrgMarvisClientInvite | [GET_orgs_org_id_marvisinvites_marvisinvite_id.md](orgs/GET_orgs_org_id_marvisinvites_marvisinvite_id.md) |
| PUT | /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id} | updateOrgMarvisClientInvite | updateOrgMarvisClientInvite | [PUT_orgs_org_id_marvisinvites_marvisinvite_id.md](orgs/PUT_orgs_org_id_marvisinvites_marvisinvite_id.md) |
| DELETE | /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id} | deleteOrgMarvisClientInvite | deleteOrgMarvisClientInvite | [DELETE_orgs_org_id_marvisinvites_marvisinvite_id.md](orgs/DELETE_orgs_org_id_marvisinvites_marvisinvite_id.md) |

## Orgs MxClusters

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/mxclusters | listOrgMxEdgeClusters | listOrgMxEdgeClusters | [GET_orgs_org_id_mxclusters.md](orgs/GET_orgs_org_id_mxclusters.md) |
| POST | /api/v1/orgs/{org_id}/mxclusters | createOrgMxEdgeCluster | createOrgMxEdgeCluster | [POST_orgs_org_id_mxclusters.md](orgs/POST_orgs_org_id_mxclusters.md) |
| GET | /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id} | getOrgMxEdgeCluster | getOrgMxEdgeCluster | [GET_orgs_org_id_mxclusters_mxcluster_id.md](orgs/GET_orgs_org_id_mxclusters_mxcluster_id.md) |
| PUT | /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id} | updateOrgMxEdgeCluster | updateOrgMxEdgeCluster | [PUT_orgs_org_id_mxclusters_mxcluster_id.md](orgs/PUT_orgs_org_id_mxclusters_mxcluster_id.md) |
| DELETE | /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id} | deleteOrgMxEdgeCluster | deleteOrgMxEdgeCluster | [DELETE_orgs_org_id_mxclusters_mxcluster_id.md](orgs/DELETE_orgs_org_id_mxclusters_mxcluster_id.md) |

## Orgs MxEdges

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/mxedges | listOrgMxEdges | listOrgMxEdges | [GET_orgs_org_id_mxedges.md](orgs/GET_orgs_org_id_mxedges.md) |
| POST | /api/v1/orgs/{org_id}/mxedges | createOrgMxEdge | createOrgMxEdge | [POST_orgs_org_id_mxedges.md](orgs/POST_orgs_org_id_mxedges.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/assign | assignOrgMxEdgeToSite | assignOrgMxEdgeToSite | [POST_orgs_org_id_mxedges_assign.md](orgs/POST_orgs_org_id_mxedges_assign.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/claim | claimOrgMxEdge | claimOrgMxEdge | [POST_orgs_org_id_mxedges_claim.md](orgs/POST_orgs_org_id_mxedges_claim.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/count | countOrgMxEdges | countOrgMxEdges | [GET_orgs_org_id_mxedges_count.md](orgs/GET_orgs_org_id_mxedges_count.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/events/count | countOrgSiteMxEdgeEvents | countOrgSiteMxEdgeEvents | [GET_orgs_org_id_mxedges_events_count.md](orgs/GET_orgs_org_id_mxedges_events_count.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/events/search | searchOrgMistEdgeEvents | searchOrgMistEdgeEvents | [GET_orgs_org_id_mxedges_events_search.md](orgs/GET_orgs_org_id_mxedges_events_search.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/search | searchOrgMxEdges | searchOrgMxEdges | [GET_orgs_org_id_mxedges_search.md](orgs/GET_orgs_org_id_mxedges_search.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/unassign | unassignOrgMxEdgeFromSite | unassignOrgMxEdgeFromSite | [POST_orgs_org_id_mxedges_unassign.md](orgs/POST_orgs_org_id_mxedges_unassign.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/versions | getOrgMxEdgeUpgradeInfo | getOrgMxEdgeUpgradeInfo | [GET_orgs_org_id_mxedges_versions.md](orgs/GET_orgs_org_id_mxedges_versions.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/{mxedge_id} | getOrgMxEdge | getOrgMxEdge | [GET_orgs_org_id_mxedges_mxedge_id.md](orgs/GET_orgs_org_id_mxedges_mxedge_id.md) |
| PUT | /api/v1/orgs/{org_id}/mxedges/{mxedge_id} | updateOrgMxEdge | updateOrgMxEdge | [PUT_orgs_org_id_mxedges_mxedge_id.md](orgs/PUT_orgs_org_id_mxedges_mxedge_id.md) |
| DELETE | /api/v1/orgs/{org_id}/mxedges/{mxedge_id} | deleteOrgMxEdge | deleteOrgMxEdge | [DELETE_orgs_org_id_mxedges_mxedge_id.md](orgs/DELETE_orgs_org_id_mxedges_mxedge_id.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/image/{image_number} | addOrgMxEdgeImage | addOrgMxEdgeImage | [POST_orgs_org_id_mxedges_mxedge_id_image_image_number.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_image_image_number.md) |
| DELETE | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/image/{image_number} | deleteOrgMxEdgeImage | deleteOrgMxEdgeImage | [DELETE_orgs_org_id_mxedges_mxedge_id_image_image_number.md](orgs/DELETE_orgs_org_id_mxedges_mxedge_id_image_image_number.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/restart | restartOrgMxEdge | restartOrgMxEdge | [POST_orgs_org_id_mxedges_mxedge_id_restart.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_restart.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/tunterm/bounce_port | bounceOrgMxEdgeDataPorts | bounceOrgMxEdgeDataPorts | [POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_bounce_port.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_bounce_port.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/tunterm/disconnect_aps | disconnectOrgMxEdgeTuntermAps | disconnectOrgMxEdgeTuntermAps | [POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_disconnect_aps.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_disconnect_aps.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/{name}/{action} | controlOrgMxEdgeServices | controlOrgMxEdgeServices | [POST_orgs_org_id_mxedges_mxedge_id_services_name_action.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_services_name_action.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/support | uploadOrgMxEdgeSupportFiles | uploadOrgMxEdgeSupportFiles | [POST_orgs_org_id_mxedges_mxedge_id_support.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_support.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/unregister | unregisterOrgMxEdge | unregisterOrgMxEdge | [POST_orgs_org_id_mxedges_mxedge_id_unregister.md](orgs/POST_orgs_org_id_mxedges_mxedge_id_unregister.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params | getOrgMxEdgeVmParams | getOrgMxEdgeVmParams | [GET_orgs_org_id_mxedges_mxedge_id_vm_params.md](orgs/GET_orgs_org_id_mxedges_mxedge_id_vm_params.md) |

## Orgs MxTunnels

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/mxtunnels | listOrgMxTunnels | listOrgMxTunnels | [GET_orgs_org_id_mxtunnels.md](orgs/GET_orgs_org_id_mxtunnels.md) |
| POST | /api/v1/orgs/{org_id}/mxtunnels | createOrgMxTunnel | createOrgMxTunnel | [POST_orgs_org_id_mxtunnels.md](orgs/POST_orgs_org_id_mxtunnels.md) |
| GET | /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id} | getOrgMxTunnel | getOrgMxTunnel | [GET_orgs_org_id_mxtunnels_mxtunnel_id.md](orgs/GET_orgs_org_id_mxtunnels_mxtunnel_id.md) |
| PUT | /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id} | updateOrgMxTunnel | updateOrgMxTunnel | [PUT_orgs_org_id_mxtunnels_mxtunnel_id.md](orgs/PUT_orgs_org_id_mxtunnels_mxtunnel_id.md) |
| DELETE | /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id} | deleteOrgMxTunnel | deleteOrgMxTunnel | [DELETE_orgs_org_id_mxtunnels_mxtunnel_id.md](orgs/DELETE_orgs_org_id_mxtunnels_mxtunnel_id.md) |

## Orgs NAC CRL

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/mist_nac_crls | getOrgNacCrl | getOrgNacCrl | [GET_orgs_org_id_setting_mist_nac_crls.md](orgs/GET_orgs_org_id_setting_mist_nac_crls.md) |
| POST | /api/v1/orgs/{org_id}/setting/mist_nac_crls | importOrgNacCrl | importOrgNacCrl | [POST_orgs_org_id_setting_mist_nac_crls.md](orgs/POST_orgs_org_id_setting_mist_nac_crls.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/mist_nac_crls/{naccrl_id} | deleteOrgNacCrl | deleteOrgNacCrl | [DELETE_orgs_org_id_setting_mist_nac_crls_naccrl_id.md](orgs/DELETE_orgs_org_id_setting_mist_nac_crls_naccrl_id.md) |

## Orgs NAC Fingerprints

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/insights/fingerprints/count | countOrgClientFingerprints | countOrgClientFingerprints | [GET_sites_site_id_insights_fingerprints_count.md](orgs/GET_sites_site_id_insights_fingerprints_count.md) |
| GET | /api/v1/sites/{site_id}/insights/fingerprints/search | searchOrgClientFingerprints | searchOrgClientFingerprints | [GET_sites_site_id_insights_fingerprints_search.md](orgs/GET_sites_site_id_insights_fingerprints_search.md) |

## Orgs NAC IDP

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/mist_nac/test_idp | validateOrgIdpCredential | validateOrgIdpCredential | [POST_orgs_org_id_mist_nac_test_idp.md](orgs/POST_orgs_org_id_mist_nac_test_idp.md) |

## Orgs NAC Portals

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/nacportals | listOrgNacPortals | listOrgNacPortals | [GET_orgs_org_id_nacportals.md](orgs/GET_orgs_org_id_nacportals.md) |
| POST | /api/v1/orgs/{org_id}/nacportals | createOrgNacPortal | createOrgNacPortal | [POST_orgs_org_id_nacportals.md](orgs/POST_orgs_org_id_nacportals.md) |
| GET | /api/v1/orgs/{org_id}/nacportals/{nacportal_id} | getOrgNacPortal | getOrgNacPortal | [GET_orgs_org_id_nacportals_nacportal_id.md](orgs/GET_orgs_org_id_nacportals_nacportal_id.md) |
| PUT | /api/v1/orgs/{org_id}/nacportals/{nacportal_id} | updateOrgNacPortal | updateOrgNacPortal | [PUT_orgs_org_id_nacportals_nacportal_id.md](orgs/PUT_orgs_org_id_nacportals_nacportal_id.md) |
| DELETE | /api/v1/orgs/{org_id}/nacportals/{nacportal_id} | deleteOrgNacPortal | deleteOrgNacPortal | [DELETE_orgs_org_id_nacportals_nacportal_id.md](orgs/DELETE_orgs_org_id_nacportals_nacportal_id.md) |
| GET | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/failures | listOrgNacPortalSsoLatestFailures | listOrgNacPortalSsoLatestFailures | [GET_orgs_org_id_nacportals_nacportal_id_failures.md](orgs/GET_orgs_org_id_nacportals_nacportal_id_failures.md) |
| POST | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/portal_image | uploadOrgNacPortalImage | uploadOrgNacPortalImage | [POST_orgs_org_id_nacportals_nacportal_id_portal_image.md](orgs/POST_orgs_org_id_nacportals_nacportal_id_portal_image.md) |
| DELETE | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/portal_image | deleteOrgNacPortalImage | deleteOrgNacPortalImage | [DELETE_orgs_org_id_nacportals_nacportal_id_portal_image.md](orgs/DELETE_orgs_org_id_nacportals_nacportal_id_portal_image.md) |
| PUT | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/portal_template | updateOrgNacPortalTemplate | updateOrgNacPortalTemplate | [PUT_orgs_org_id_nacportals_nacportal_id_portal_template.md](orgs/PUT_orgs_org_id_nacportals_nacportal_id_portal_template.md) |
| GET | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata | getOrgNacPortalSamlMetadata | getOrgNacPortalSamlMetadata | [GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.md](orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.md) |
| GET | /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml | downloadOrgNacPortalSamlMetadata | downloadOrgNacPortalSamlMetadata | [GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.xml.md](orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.xml.md) |

## Orgs NAC Rules

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/nacrules | listOrgNacRules | listOrgNacRules | [GET_orgs_org_id_nacrules.md](orgs/GET_orgs_org_id_nacrules.md) |
| POST | /api/v1/orgs/{org_id}/nacrules | createOrgNacRule | createOrgNacRule | [POST_orgs_org_id_nacrules.md](orgs/POST_orgs_org_id_nacrules.md) |
| GET | /api/v1/orgs/{org_id}/nacrules/{nacrule_id} | getOrgNacRule | getOrgNacRule | [GET_orgs_org_id_nacrules_nacrule_id.md](orgs/GET_orgs_org_id_nacrules_nacrule_id.md) |
| PUT | /api/v1/orgs/{org_id}/nacrules/{nacrule_id} | updateOrgNacRule | updateOrgNacRule | [PUT_orgs_org_id_nacrules_nacrule_id.md](orgs/PUT_orgs_org_id_nacrules_nacrule_id.md) |
| DELETE | /api/v1/orgs/{org_id}/nacrules/{nacrule_id} | deleteOrgNacRule | deleteOrgNacRule | [DELETE_orgs_org_id_nacrules_nacrule_id.md](orgs/DELETE_orgs_org_id_nacrules_nacrule_id.md) |

## Orgs NAC Tags

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/nactags | listOrgNacTags | listOrgNacTags | [GET_orgs_org_id_nactags.md](orgs/GET_orgs_org_id_nactags.md) |
| POST | /api/v1/orgs/{org_id}/nactags | createOrgNacTag | createOrgNacTag | [POST_orgs_org_id_nactags.md](orgs/POST_orgs_org_id_nactags.md) |
| GET | /api/v1/orgs/{org_id}/nactags/{nactag_id} | getOrgNacTag | getOrgNacTag | [GET_orgs_org_id_nactags_nactag_id.md](orgs/GET_orgs_org_id_nactags_nactag_id.md) |
| PUT | /api/v1/orgs/{org_id}/nactags/{nactag_id} | updateOrgNacTag | updateOrgNacTag | [PUT_orgs_org_id_nactags_nactag_id.md](orgs/PUT_orgs_org_id_nactags_nactag_id.md) |
| DELETE | /api/v1/orgs/{org_id}/nactags/{nactag_id} | deleteOrgNacTag | deleteOrgNacTag | [DELETE_orgs_org_id_nactags_nactag_id.md](orgs/DELETE_orgs_org_id_nactags_nactag_id.md) |

## Orgs Network Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/networktemplates | listOrgNetworkTemplates | listOrgNetworkTemplates | [GET_orgs_org_id_networktemplates.md](orgs/GET_orgs_org_id_networktemplates.md) |
| POST | /api/v1/orgs/{org_id}/networktemplates | createOrgNetworkTemplate | createOrgNetworkTemplate | [POST_orgs_org_id_networktemplates.md](orgs/POST_orgs_org_id_networktemplates.md) |
| GET | /api/v1/orgs/{org_id}/networktemplates/{networktemplate_id} | getOrgNetworkTemplate | getOrgNetworkTemplate | [GET_orgs_org_id_networktemplates_networktemplate_id.md](orgs/GET_orgs_org_id_networktemplates_networktemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/networktemplates/{networktemplate_id} | updateOrgNetworkTemplate | updateOrgNetworkTemplate | [PUT_orgs_org_id_networktemplates_networktemplate_id.md](orgs/PUT_orgs_org_id_networktemplates_networktemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/networktemplates/{networktemplate_id} | deleteOrgNetworkTemplate | deleteOrgNetworkTemplate | [DELETE_orgs_org_id_networktemplates_networktemplate_id.md](orgs/DELETE_orgs_org_id_networktemplates_networktemplate_id.md) |

## Orgs Networks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/networks | listOrgNetworks | listOrgNetworks | [GET_orgs_org_id_networks.md](orgs/GET_orgs_org_id_networks.md) |
| POST | /api/v1/orgs/{org_id}/networks | createOrgNetwork | createOrgNetwork | [POST_orgs_org_id_networks.md](orgs/POST_orgs_org_id_networks.md) |
| GET | /api/v1/orgs/{org_id}/networks/{network_id} | getOrgNetwork | getOrgNetwork | [GET_orgs_org_id_networks_network_id.md](orgs/GET_orgs_org_id_networks_network_id.md) |
| PUT | /api/v1/orgs/{org_id}/networks/{network_id} | updateOrgNetwork | updateOrgNetwork | [PUT_orgs_org_id_networks_network_id.md](orgs/PUT_orgs_org_id_networks_network_id.md) |
| DELETE | /api/v1/orgs/{org_id}/networks/{network_id} | deleteOrgNetwork | deleteOrgNetwork | [DELETE_orgs_org_id_networks_network_id.md](orgs/DELETE_orgs_org_id_networks_network_id.md) |

## Orgs Premium Analytics

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/pma/dashboards | listOrgPmaDashboards | listOrgPmaDashboards | [GET_orgs_org_id_pma_dashboards.md](orgs/GET_orgs_org_id_pma_dashboards.md) |

## Orgs Psk Portals

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/pskportals | listOrgPskPortals | listOrgPskPortals | [GET_orgs_org_id_pskportals.md](orgs/GET_orgs_org_id_pskportals.md) |
| POST | /api/v1/orgs/{org_id}/pskportals | createOrgPskPortal | createOrgPskPortal | [POST_orgs_org_id_pskportals.md](orgs/POST_orgs_org_id_pskportals.md) |
| GET | /api/v1/orgs/{org_id}/pskportals/logs | listOrgPskPortalLogs | listOrgPskPortalLogs | [GET_orgs_org_id_pskportals_logs.md](orgs/GET_orgs_org_id_pskportals_logs.md) |
| GET | /api/v1/orgs/{org_id}/pskportals/logs/count | countOrgPskPortalLogs | countOrgPskPortalLogs | [GET_orgs_org_id_pskportals_logs_count.md](orgs/GET_orgs_org_id_pskportals_logs_count.md) |
| GET | /api/v1/orgs/{org_id}/pskportals/logs/search | searchOrgPskPortalLogs | searchOrgPskPortalLogs | [GET_orgs_org_id_pskportals_logs_search.md](orgs/GET_orgs_org_id_pskportals_logs_search.md) |
| GET | /api/v1/orgs/{org_id}/pskportals/{pskportal_id} | getOrgPskPortal | getOrgPskPortal | [GET_orgs_org_id_pskportals_pskportal_id.md](orgs/GET_orgs_org_id_pskportals_pskportal_id.md) |
| PUT | /api/v1/orgs/{org_id}/pskportals/{pskportal_id} | updateOrgPskPortal | updateOrgPskPortal | [PUT_orgs_org_id_pskportals_pskportal_id.md](orgs/PUT_orgs_org_id_pskportals_pskportal_id.md) |
| DELETE | /api/v1/orgs/{org_id}/pskportals/{pskportal_id} | deleteOrgPskPortal | deleteOrgPskPortal | [DELETE_orgs_org_id_pskportals_pskportal_id.md](orgs/DELETE_orgs_org_id_pskportals_pskportal_id.md) |
| POST | /api/v1/orgs/{org_id}/pskportals/{pskportal_id}/portal_image | uploadOrgPskPortalImage | uploadOrgPskPortalImage | [POST_orgs_org_id_pskportals_pskportal_id_portal_image.md](orgs/POST_orgs_org_id_pskportals_pskportal_id_portal_image.md) |
| DELETE | /api/v1/orgs/{org_id}/pskportals/{pskportal_id}/portal_image | deleteOrgPskPortalImage | deleteOrgPskPortalImage | [DELETE_orgs_org_id_pskportals_pskportal_id_portal_image.md](orgs/DELETE_orgs_org_id_pskportals_pskportal_id_portal_image.md) |
| PUT | /api/v1/orgs/{org_id}/pskportals/{pskportal_id}/portal_template | updateOrgPskPortalTemplate | updateOrgPskPortalTemplate | [PUT_orgs_org_id_pskportals_pskportal_id_portal_template.md](orgs/PUT_orgs_org_id_pskportals_pskportal_id_portal_template.md) |

## Orgs Psks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/psks | listOrgPsks | listOrgPsks | [GET_orgs_org_id_psks.md](orgs/GET_orgs_org_id_psks.md) |
| POST | /api/v1/orgs/{org_id}/psks | createOrgPsk | createOrgPsk | [POST_orgs_org_id_psks.md](orgs/POST_orgs_org_id_psks.md) |
| PUT | /api/v1/orgs/{org_id}/psks | updateOrgMultiplePsks | updateOrgMultiplePsks | [PUT_orgs_org_id_psks.md](orgs/PUT_orgs_org_id_psks.md) |
| POST | /api/v1/orgs/{org_id}/psks/delete | deleteOrgPskList | deleteOrgPskList | [POST_orgs_org_id_psks_delete.md](orgs/POST_orgs_org_id_psks_delete.md) |
| POST | /api/v1/orgs/{org_id}/psks/import | importOrgPsks | importOrgPsks | [POST_orgs_org_id_psks_import.md](orgs/POST_orgs_org_id_psks_import.md) |
| GET | /api/v1/orgs/{org_id}/psks/{psk_id} | getOrgPsk | getOrgPsk | [GET_orgs_org_id_psks_psk_id.md](orgs/GET_orgs_org_id_psks_psk_id.md) |
| PUT | /api/v1/orgs/{org_id}/psks/{psk_id} | updateOrgPsk | updateOrgPsk | [PUT_orgs_org_id_psks_psk_id.md](orgs/PUT_orgs_org_id_psks_psk_id.md) |
| DELETE | /api/v1/orgs/{org_id}/psks/{psk_id} | deleteOrgPsk | deleteOrgPsk | [DELETE_orgs_org_id_psks_psk_id.md](orgs/DELETE_orgs_org_id_psks_psk_id.md) |
| POST | /api/v1/orgs/{org_id}/psks/{psk_id}/delete_old_passphrase | deleteOrgPskOldPassphrase | deleteOrgPskOldPassphrase | [POST_orgs_org_id_psks_psk_id_delete_old_passphrase.md](orgs/POST_orgs_org_id_psks_psk_id_delete_old_passphrase.md) |

## Orgs RF Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/rftemplates | listOrgRfTemplates | listOrgRfTemplates | [GET_orgs_org_id_rftemplates.md](orgs/GET_orgs_org_id_rftemplates.md) |
| POST | /api/v1/orgs/{org_id}/rftemplates | createOrgRfTemplate | createOrgRfTemplate | [POST_orgs_org_id_rftemplates.md](orgs/POST_orgs_org_id_rftemplates.md) |
| GET | /api/v1/orgs/{org_id}/rftemplates/{rftemplate_id} | getOrgRfTemplate | getOrgRfTemplate | [GET_orgs_org_id_rftemplates_rftemplate_id.md](orgs/GET_orgs_org_id_rftemplates_rftemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/rftemplates/{rftemplate_id} | updateOrgRfTemplate | updateOrgRfTemplate | [PUT_orgs_org_id_rftemplates_rftemplate_id.md](orgs/PUT_orgs_org_id_rftemplates_rftemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/rftemplates/{rftemplate_id} | deleteOrgRfTemplate | deleteOrgRfTemplate | [DELETE_orgs_org_id_rftemplates_rftemplate_id.md](orgs/DELETE_orgs_org_id_rftemplates_rftemplate_id.md) |

## Orgs SCEP

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting/mist_scep | getOrgMistScep | getOrgMistScep | [GET_orgs_org_id_setting_mist_scep.md](orgs/GET_orgs_org_id_setting_mist_scep.md) |
| PUT | /api/v1/orgs/{org_id}/setting/mist_scep | updateOrgMistScep | updateOrgMistScep | [PUT_orgs_org_id_setting_mist_scep.md](orgs/PUT_orgs_org_id_setting_mist_scep.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/mist_scep | disableOrgMistScep | disableOrgMistScep | [DELETE_orgs_org_id_setting_mist_scep.md](orgs/DELETE_orgs_org_id_setting_mist_scep.md) |
| GET | /api/v1/orgs/{org_id}/setting/mist_scep/client_certs | listOrgIssuedClientCertificates | listOrgIssuedClientCertificates | [GET_orgs_org_id_setting_mist_scep_client_certs.md](orgs/GET_orgs_org_id_setting_mist_scep_client_certs.md) |
| POST | /api/v1/orgs/{org_id}/setting/mist_scep/client_certs/revoke | revokeOrgIssuedClientCertificates | revokeOrgIssuedClientCertificates | [POST_orgs_org_id_setting_mist_scep_client_certs_revoke.md](orgs/POST_orgs_org_id_setting_mist_scep_client_certs_revoke.md) |

## Orgs SDK Invites

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/mobile/verify/{secret} | activateSdkInvite | activateSdkInvite | [POST_mobile_verify_secret.md](orgs/POST_mobile_verify_secret.md) |
| GET | /api/v1/orgs/{org_id}/sdkinvites | listSdkInvites | listSdkInvites | [GET_orgs_org_id_sdkinvites.md](orgs/GET_orgs_org_id_sdkinvites.md) |
| POST | /api/v1/orgs/{org_id}/sdkinvites | createSdkInvite | createSdkInvite | [POST_orgs_org_id_sdkinvites.md](orgs/POST_orgs_org_id_sdkinvites.md) |
| GET | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id} | getSdkInvite | getSdkInvite | [GET_orgs_org_id_sdkinvites_sdkinvite_id.md](orgs/GET_orgs_org_id_sdkinvites_sdkinvite_id.md) |
| PUT | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id} | updateSdkInvite | updateSdkInvite | [PUT_orgs_org_id_sdkinvites_sdkinvite_id.md](orgs/PUT_orgs_org_id_sdkinvites_sdkinvite_id.md) |
| DELETE | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id} | revokeSdkInvite | revokeSdkInvite | [DELETE_orgs_org_id_sdkinvites_sdkinvite_id.md](orgs/DELETE_orgs_org_id_sdkinvites_sdkinvite_id.md) |
| POST | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/email | sendSdkInviteEmail | sendSdkInviteEmail | [POST_orgs_org_id_sdkinvites_sdkinvite_id_email.md](orgs/POST_orgs_org_id_sdkinvites_sdkinvite_id_email.md) |
| GET | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/qrcode | getSdkInviteQrCode | getSdkInviteQrCode | [GET_orgs_org_id_sdkinvites_sdkinvite_id_qrcode.md](orgs/GET_orgs_org_id_sdkinvites_sdkinvite_id_qrcode.md) |
| POST | /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/sms | sendSdkInviteSms | sendSdkInviteSms | [POST_orgs_org_id_sdkinvites_sdkinvite_id_sms.md](orgs/POST_orgs_org_id_sdkinvites_sdkinvite_id_sms.md) |

## Orgs SDK Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/sdktemplates | listSdkTemplates | listSdkTemplates | [GET_orgs_org_id_sdktemplates.md](orgs/GET_orgs_org_id_sdktemplates.md) |
| POST | /api/v1/orgs/{org_id}/sdktemplates | createSdkTemplate | createSdkTemplate | [POST_orgs_org_id_sdktemplates.md](orgs/POST_orgs_org_id_sdktemplates.md) |
| GET | /api/v1/orgs/{org_id}/sdktemplates/{sdktemplate_id} | getSdkTemplate | getSdkTemplate | [GET_orgs_org_id_sdktemplates_sdktemplate_id.md](orgs/GET_orgs_org_id_sdktemplates_sdktemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/sdktemplates/{sdktemplate_id} | updateSdkTemplate | updateSdkTemplate | [PUT_orgs_org_id_sdktemplates_sdktemplate_id.md](orgs/PUT_orgs_org_id_sdktemplates_sdktemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/sdktemplates/{sdktemplate_id} | deleteSdkTemplate | deleteSdkTemplate | [DELETE_orgs_org_id_sdktemplates_sdktemplate_id.md](orgs/DELETE_orgs_org_id_sdktemplates_sdktemplate_id.md) |

## Orgs SLEs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/insights/sites-sle | getOrgSitesSle | getOrgSitesSle | [GET_orgs_org_id_insights_sites-sle.md](orgs/GET_orgs_org_id_insights_sites-sle.md) |
| GET | /api/v1/orgs/{org_id}/insights/{metric} | getOrgSle | getOrgSle | [GET_orgs_org_id_insights_metric.md](orgs/GET_orgs_org_id_insights_metric.md) |

## Orgs SSO

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/ssos | listOrgSsos | listOrgSsos | [GET_orgs_org_id_ssos.md](orgs/GET_orgs_org_id_ssos.md) |
| POST | /api/v1/orgs/{org_id}/ssos | createOrgSso | createOrgSso | [POST_orgs_org_id_ssos.md](orgs/POST_orgs_org_id_ssos.md) |
| GET | /api/v1/orgs/{org_id}/ssos/{sso_id} | getOrgSso | getOrgSso | [GET_orgs_org_id_ssos_sso_id.md](orgs/GET_orgs_org_id_ssos_sso_id.md) |
| PUT | /api/v1/orgs/{org_id}/ssos/{sso_id} | updateOrgSso | updateOrgSso | [PUT_orgs_org_id_ssos_sso_id.md](orgs/PUT_orgs_org_id_ssos_sso_id.md) |
| DELETE | /api/v1/orgs/{org_id}/ssos/{sso_id} | deleteOrgSso | deleteOrgSso | [DELETE_orgs_org_id_ssos_sso_id.md](orgs/DELETE_orgs_org_id_ssos_sso_id.md) |
| GET | /api/v1/orgs/{org_id}/ssos/{sso_id}/failures | listOrgSsoLatestFailures | listOrgSsoLatestFailures | [GET_orgs_org_id_ssos_sso_id_failures.md](orgs/GET_orgs_org_id_ssos_sso_id_failures.md) |
| GET | /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata | getOrgSamlMetadata | getOrgSamlMetadata | [GET_orgs_org_id_ssos_sso_id_metadata.md](orgs/GET_orgs_org_id_ssos_sso_id_metadata.md) |
| GET | /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml | downloadOrgSamlMetadata | downloadOrgSamlMetadata | [GET_orgs_org_id_ssos_sso_id_metadata.xml.md](orgs/GET_orgs_org_id_ssos_sso_id_metadata.xml.md) |

## Orgs SSO Roles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/ssoroles | listOrgSsoRoles | listOrgSsoRoles | [GET_orgs_org_id_ssoroles.md](orgs/GET_orgs_org_id_ssoroles.md) |
| POST | /api/v1/orgs/{org_id}/ssoroles | createOrgSsoRole | createOrgSsoRole | [POST_orgs_org_id_ssoroles.md](orgs/POST_orgs_org_id_ssoroles.md) |
| GET | /api/v1/orgs/{org_id}/ssoroles/{ssorole_id} | getOrgSsoRole | getOrgSsoRole | [GET_orgs_org_id_ssoroles_ssorole_id.md](orgs/GET_orgs_org_id_ssoroles_ssorole_id.md) |
| PUT | /api/v1/orgs/{org_id}/ssoroles/{ssorole_id} | updateOrgSsoRole | updateOrgSsoRole | [PUT_orgs_org_id_ssoroles_ssorole_id.md](orgs/PUT_orgs_org_id_ssoroles_ssorole_id.md) |
| DELETE | /api/v1/orgs/{org_id}/ssoroles/{ssorole_id} | deleteOrgSsoRole | deleteOrgSsoRole | [DELETE_orgs_org_id_ssoroles_ssorole_id.md](orgs/DELETE_orgs_org_id_ssoroles_ssorole_id.md) |

## Orgs SecIntel Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/secintelprofiles | listOrgSecIntelProfiles | listOrgSecIntelProfiles | [GET_orgs_org_id_secintelprofiles.md](orgs/GET_orgs_org_id_secintelprofiles.md) |
| POST | /api/v1/orgs/{org_id}/secintelprofiles | createOrgSecIntelProfile | createOrgSecIntelProfile | [POST_orgs_org_id_secintelprofiles.md](orgs/POST_orgs_org_id_secintelprofiles.md) |
| GET | /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id} | getOrgSecIntelProfile | getOrgSecIntelProfile | [GET_orgs_org_id_secintelprofiles_secintelprofile_id.md](orgs/GET_orgs_org_id_secintelprofiles_secintelprofile_id.md) |
| PUT | /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id} | updateOrgSecIntelProfile | updateOrgSecIntelProfile | [PUT_orgs_org_id_secintelprofiles_secintelprofile_id.md](orgs/PUT_orgs_org_id_secintelprofiles_secintelprofile_id.md) |
| DELETE | /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id} | deleteOrgSecIntelProfile | deleteOrgSecIntelProfile | [DELETE_orgs_org_id_secintelprofiles_secintelprofile_id.md](orgs/DELETE_orgs_org_id_secintelprofiles_secintelprofile_id.md) |

## Orgs Security Policies

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/secpolicies | listOrgSecPolicies | listOrgSecPolicies | [GET_orgs_org_id_secpolicies.md](orgs/GET_orgs_org_id_secpolicies.md) |
| POST | /api/v1/orgs/{org_id}/secpolicies | createOrgSecPolicy | createOrgSecPolicy | [POST_orgs_org_id_secpolicies.md](orgs/POST_orgs_org_id_secpolicies.md) |
| GET | /api/v1/orgs/{org_id}/secpolicies/{secpolicy_id} | getOrgSecPolicy | getOrgSecPolicy | [GET_orgs_org_id_secpolicies_secpolicy_id.md](orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md) |
| PUT | /api/v1/orgs/{org_id}/secpolicies/{secpolicy_id} | updateOrgSecPolicy | updateOrgSecPolicy | [PUT_orgs_org_id_secpolicies_secpolicy_id.md](orgs/PUT_orgs_org_id_secpolicies_secpolicy_id.md) |
| DELETE | /api/v1/orgs/{org_id}/secpolicies/{secpolicy_id} | deleteOrgSecPolicy | deleteOrgSecPolicy | [DELETE_orgs_org_id_secpolicies_secpolicy_id.md](orgs/DELETE_orgs_org_id_secpolicies_secpolicy_id.md) |

## Orgs Service Policies

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/servicepolicies | listOrgServicePolicies | listOrgServicePolicies | [GET_orgs_org_id_servicepolicies.md](orgs/GET_orgs_org_id_servicepolicies.md) |
| POST | /api/v1/orgs/{org_id}/servicepolicies | createOrgServicePolicy | createOrgServicePolicy | [POST_orgs_org_id_servicepolicies.md](orgs/POST_orgs_org_id_servicepolicies.md) |
| GET | /api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id} | getOrgServicePolicy | getOrgServicePolicy | [GET_orgs_org_id_servicepolicies_servicepolicy_id.md](orgs/GET_orgs_org_id_servicepolicies_servicepolicy_id.md) |
| PUT | /api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id} | updateOrgServicePolicy | updateOrgServicePolicy | [PUT_orgs_org_id_servicepolicies_servicepolicy_id.md](orgs/PUT_orgs_org_id_servicepolicies_servicepolicy_id.md) |
| DELETE | /api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id} | deleteOrgServicePolicy | deleteOrgServicePolicy | [DELETE_orgs_org_id_servicepolicies_servicepolicy_id.md](orgs/DELETE_orgs_org_id_servicepolicies_servicepolicy_id.md) |

## Orgs Services

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/services | listOrgServices | listOrgServices | [GET_orgs_org_id_services.md](orgs/GET_orgs_org_id_services.md) |
| POST | /api/v1/orgs/{org_id}/services | createOrgService | createOrgService | [POST_orgs_org_id_services.md](orgs/POST_orgs_org_id_services.md) |
| GET | /api/v1/orgs/{org_id}/services/{service_id} | getOrgService | getOrgService | [GET_orgs_org_id_services_service_id.md](orgs/GET_orgs_org_id_services_service_id.md) |
| PUT | /api/v1/orgs/{org_id}/services/{service_id} | updateOrgService | updateOrgService | [PUT_orgs_org_id_services_service_id.md](orgs/PUT_orgs_org_id_services_service_id.md) |
| DELETE | /api/v1/orgs/{org_id}/services/{service_id} | deleteOrgService | deleteOrgService | [DELETE_orgs_org_id_services_service_id.md](orgs/DELETE_orgs_org_id_services_service_id.md) |

## Orgs Setting

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/setting | getOrgSettings | getOrgSettings | [GET_orgs_org_id_setting.md](orgs/GET_orgs_org_id_setting.md) |
| PUT | /api/v1/orgs/{org_id}/setting | updateOrgSettings | updateOrgSettings | [PUT_orgs_org_id_setting.md](orgs/PUT_orgs_org_id_setting.md) |
| POST | /api/v1/orgs/{org_id}/setting/blacklist | createOrgWirelessClientsBlocklist | createOrgWirelessClientsBlocklist | [POST_orgs_org_id_setting_blacklist.md](orgs/POST_orgs_org_id_setting_blacklist.md) |
| DELETE | /api/v1/orgs/{org_id}/setting/blacklist | deleteOrgWirelessClientsBlocklist | deleteOrgWirelessClientsBlocklist | [DELETE_orgs_org_id_setting_blacklist.md](orgs/DELETE_orgs_org_id_setting_blacklist.md) |
| POST | /api/v1/orgs/{org_id}/setting/pcap_bucket/setup | setOrgCustomBucket | setOrgCustomBucket | [POST_orgs_org_id_setting_pcap_bucket_setup.md](orgs/POST_orgs_org_id_setting_pcap_bucket_setup.md) |
| POST | /api/v1/orgs/{org_id}/setting/pcap_bucket/verify | verifyOrgCustomBucket | verifyOrgCustomBucket | [POST_orgs_org_id_setting_pcap_bucket_verify.md](orgs/POST_orgs_org_id_setting_pcap_bucket_verify.md) |

## Orgs Site Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/sitetemplates | listOrgSiteTemplates | listOrgSiteTemplates | [GET_orgs_org_id_sitetemplates.md](orgs/GET_orgs_org_id_sitetemplates.md) |
| POST | /api/v1/orgs/{org_id}/sitetemplates | createOrgSiteTemplate | createOrgSiteTemplate | [POST_orgs_org_id_sitetemplates.md](orgs/POST_orgs_org_id_sitetemplates.md) |
| GET | /api/v1/orgs/{org_id}/sitetemplates/{sitetemplate_id} | getOrgSiteTemplate | getOrgSiteTemplate | [GET_orgs_org_id_sitetemplates_sitetemplate_id.md](orgs/GET_orgs_org_id_sitetemplates_sitetemplate_id.md) |
| PUT | /api/v1/orgs/{org_id}/sitetemplates/{sitetemplate_id} | updateOrgSiteTemplate | updateOrgSiteTemplate | [PUT_orgs_org_id_sitetemplates_sitetemplate_id.md](orgs/PUT_orgs_org_id_sitetemplates_sitetemplate_id.md) |
| DELETE | /api/v1/orgs/{org_id}/sitetemplates/{sitetemplate_id} | deleteOrgSiteTemplate | deleteOrgSiteTemplate | [DELETE_orgs_org_id_sitetemplates_sitetemplate_id.md](orgs/DELETE_orgs_org_id_sitetemplates_sitetemplate_id.md) |

## Orgs Sitegroups

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/sitegroups | listOrgSiteGroups | listOrgSiteGroups | [GET_orgs_org_id_sitegroups.md](orgs/GET_orgs_org_id_sitegroups.md) |
| POST | /api/v1/orgs/{org_id}/sitegroups | createOrgSiteGroup | createOrgSiteGroup | [POST_orgs_org_id_sitegroups.md](orgs/POST_orgs_org_id_sitegroups.md) |
| GET | /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id} | getOrgSiteGroup | getOrgSiteGroup | [GET_orgs_org_id_sitegroups_sitegroup_id.md](orgs/GET_orgs_org_id_sitegroups_sitegroup_id.md) |
| PUT | /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id} | updateOrgSiteGroup | updateOrgSiteGroup | [PUT_orgs_org_id_sitegroups_sitegroup_id.md](orgs/PUT_orgs_org_id_sitegroups_sitegroup_id.md) |
| DELETE | /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id} | deleteOrgSiteGroup | deleteOrgSiteGroup | [DELETE_orgs_org_id_sitegroups_sitegroup_id.md](orgs/DELETE_orgs_org_id_sitegroups_sitegroup_id.md) |

## Orgs Sites

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/sites | listOrgSites | listOrgSites | [GET_orgs_org_id_sites.md](orgs/GET_orgs_org_id_sites.md) |
| POST | /api/v1/orgs/{org_id}/sites | createOrgSite | createOrgSite | [POST_orgs_org_id_sites.md](orgs/POST_orgs_org_id_sites.md) |
| GET | /api/v1/orgs/{org_id}/sites/count | countOrgSites | countOrgSites | [GET_orgs_org_id_sites_count.md](orgs/GET_orgs_org_id_sites_count.md) |
| GET | /api/v1/orgs/{org_id}/sites/search | searchOrgSites | searchOrgSites | [GET_orgs_org_id_sites_search.md](orgs/GET_orgs_org_id_sites_search.md) |

## Orgs Stats

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats | getOrgStats | getOrgStats | [GET_orgs_org_id_stats.md](orgs/GET_orgs_org_id_stats.md) |

## Orgs Stats - Assets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/assets | listOrgAssetsStats | listOrgAssetsStats | [GET_orgs_org_id_stats_assets.md](orgs/GET_orgs_org_id_stats_assets.md) |
| GET | /api/v1/orgs/{org_id}/stats/assets/count | countOrgAssetsByDistanceField | countOrgAssetsByDistanceField | [GET_orgs_org_id_stats_assets_count.md](orgs/GET_orgs_org_id_stats_assets_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/assets/search | searchOrgAssets | searchOrgAssets | [GET_orgs_org_id_stats_assets_search.md](orgs/GET_orgs_org_id_stats_assets_search.md) |

## Orgs Stats - BGP Peers

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/bgp_peers/count | countOrgBgpStats | countOrgBgpStats | [GET_orgs_org_id_stats_bgp_peers_count.md](orgs/GET_orgs_org_id_stats_bgp_peers_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/bgp_peers/search | searchOrgBgpStats | searchOrgBgpStats | [GET_orgs_org_id_stats_bgp_peers_search.md](orgs/GET_orgs_org_id_stats_bgp_peers_search.md) |

## Orgs Stats - Devices

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/devices | listOrgDevicesStats | listOrgDevicesStats | [GET_orgs_org_id_stats_devices.md](orgs/GET_orgs_org_id_stats_devices.md) |

## Orgs Stats - MxEdges

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/mxedges | listOrgMxEdgesStats | listOrgMxEdgesStats | [GET_orgs_org_id_stats_mxedges.md](orgs/GET_orgs_org_id_stats_mxedges.md) |
| GET | /api/v1/orgs/{org_id}/stats/mxedges/{mxedge_id} | getOrgMxEdgeStats | getOrgMxEdgeStats | [GET_orgs_org_id_stats_mxedges_mxedge_id.md](orgs/GET_orgs_org_id_stats_mxedges_mxedge_id.md) |

## Orgs Stats - Ospf

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/ospf_peers/count | countOrgOspfStats | countOrgOspfStats | [GET_orgs_org_id_stats_ospf_peers_count.md](orgs/GET_orgs_org_id_stats_ospf_peers_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/ospf_peers/search | searchOrgOspfStats | searchOrgOspfStats | [GET_orgs_org_id_stats_ospf_peers_search.md](orgs/GET_orgs_org_id_stats_ospf_peers_search.md) |

## Orgs Stats - Other Devices

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/otherdevices/{device_mac} | getOrgOtherDeviceStats | getOrgOtherDeviceStats | [GET_orgs_org_id_stats_otherdevices_device_mac.md](orgs/GET_orgs_org_id_stats_otherdevices_device_mac.md) |

## Orgs Stats - Ports

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/ports/count | countOrgSwOrGwPorts | countOrgSwOrGwPorts | [GET_orgs_org_id_stats_ports_count.md](orgs/GET_orgs_org_id_stats_ports_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/ports/search | searchOrgSwOrGwPorts | searchOrgSwOrGwPorts | [GET_orgs_org_id_stats_ports_search.md](orgs/GET_orgs_org_id_stats_ports_search.md) |

## Orgs Stats - Sites

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/sites | listOrgSiteStats | listOrgSiteStats | [GET_orgs_org_id_stats_sites.md](orgs/GET_orgs_org_id_stats_sites.md) |

## Orgs Stats - Tunnels

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/tunnels/count | countOrgTunnelsStats | countOrgTunnelsStats | [GET_orgs_org_id_stats_tunnels_count.md](orgs/GET_orgs_org_id_stats_tunnels_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/tunnels/search | searchOrgTunnelsStats | searchOrgTunnelsStats | [GET_orgs_org_id_stats_tunnels_search.md](orgs/GET_orgs_org_id_stats_tunnels_search.md) |

## Orgs Stats - VPN Peers

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/stats/vpn_peers/count | countOrgPeerPathStats | countOrgPeerPathStats | [GET_orgs_org_id_stats_vpn_peers_count.md](orgs/GET_orgs_org_id_stats_vpn_peers_count.md) |
| GET | /api/v1/orgs/{org_id}/stats/vpn_peers/search | searchOrgPeerPathStats | searchOrgPeerPathStats | [GET_orgs_org_id_stats_vpn_peers_search.md](orgs/GET_orgs_org_id_stats_vpn_peers_search.md) |

## Orgs Tickets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/tickets | listOrgTickets | listOrgTickets | [GET_orgs_org_id_tickets.md](orgs/GET_orgs_org_id_tickets.md) |
| POST | /api/v1/orgs/{org_id}/tickets | createOrgTicket | createOrgTicket | [POST_orgs_org_id_tickets.md](orgs/POST_orgs_org_id_tickets.md) |
| GET | /api/v1/orgs/{org_id}/tickets/count | countOrgTickets | countOrgTickets | [GET_orgs_org_id_tickets_count.md](orgs/GET_orgs_org_id_tickets_count.md) |
| GET | /api/v1/orgs/{org_id}/tickets/{ticket_id} | getOrgTicket | getOrgTicket | [GET_orgs_org_id_tickets_ticket_id.md](orgs/GET_orgs_org_id_tickets_ticket_id.md) |
| PUT | /api/v1/orgs/{org_id}/tickets/{ticket_id} | updateOrgTicket | updateOrgTicket | [PUT_orgs_org_id_tickets_ticket_id.md](orgs/PUT_orgs_org_id_tickets_ticket_id.md) |
| POST | /api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments | UploadOrgTicketAttachment | UploadOrgTicketAttachment | [POST_orgs_org_id_tickets_ticket_id_attachments.md](orgs/POST_orgs_org_id_tickets_ticket_id_attachments.md) |
| GET | /api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments/{attachment_id} | GetOrgTicketAttachment | GetOrgTicketAttachment | [GET_orgs_org_id_tickets_ticket_id_attachments_attachment_id.md](orgs/GET_orgs_org_id_tickets_ticket_id_attachments_attachment_id.md) |
| POST | /api/v1/orgs/{org_id}/tickets/{ticket_id}/comments | addOrgTicketComment | addOrgTicketComment | [POST_orgs_org_id_tickets_ticket_id_comments.md](orgs/POST_orgs_org_id_tickets_ticket_id_comments.md) |

## Orgs UI Settings

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/uisettings | listOrgUiSettings | listOrgUiSettings | [GET_orgs_org_id_uisettings.md](orgs/GET_orgs_org_id_uisettings.md) |
| POST | /api/v1/orgs/{org_id}/uisettings | createOrgUiSettings | createOrgUiSettings | [POST_orgs_org_id_uisettings.md](orgs/POST_orgs_org_id_uisettings.md) |
| GET | /api/v1/orgs/{org_id}/uisettings/{uisetting_id} | getOrgUiSetting | getOrgUiSetting | [GET_orgs_org_id_uisettings_uisetting_id.md](orgs/GET_orgs_org_id_uisettings_uisetting_id.md) |
| POST | /api/v1/orgs/{org_id}/uisettings/{uisetting_id} | updateOrgUiSetting | updateOrgUiSetting | [POST_orgs_org_id_uisettings_uisetting_id.md](orgs/POST_orgs_org_id_uisettings_uisetting_id.md) |
| DELETE | /api/v1/orgs/{org_id}/uisettings/{uisetting_id} | deleteOrgUiSetting | deleteOrgUiSetting | [DELETE_orgs_org_id_uisettings_uisetting_id.md](orgs/DELETE_orgs_org_id_uisettings_uisetting_id.md) |

## Orgs User MACs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/usermacs | createOrgUserMac | createOrgUserMac | [POST_orgs_org_id_usermacs.md](orgs/POST_orgs_org_id_usermacs.md) |
| PUT | /api/v1/orgs/{org_id}/usermacs | updateOrgMultipleUserMacs | updateOrgMultipleUserMacs | [PUT_orgs_org_id_usermacs.md](orgs/PUT_orgs_org_id_usermacs.md) |
| GET | /api/v1/orgs/{org_id}/usermacs/count | countOrgUserMacs | countOrgUserMacs | [GET_orgs_org_id_usermacs_count.md](orgs/GET_orgs_org_id_usermacs_count.md) |
| POST | /api/v1/orgs/{org_id}/usermacs/delete | deleteOrgMultipleUserMacs | deleteOrgMultipleUserMacs | [POST_orgs_org_id_usermacs_delete.md](orgs/POST_orgs_org_id_usermacs_delete.md) |
| POST | /api/v1/orgs/{org_id}/usermacs/import | importOrgUserMacs | importOrgUserMacs | [POST_orgs_org_id_usermacs_import.md](orgs/POST_orgs_org_id_usermacs_import.md) |
| GET | /api/v1/orgs/{org_id}/usermacs/search | searchOrgUserMacs | searchOrgUserMacs | [GET_orgs_org_id_usermacs_search.md](orgs/GET_orgs_org_id_usermacs_search.md) |
| GET | /api/v1/orgs/{org_id}/usermacs/{usermac_id} | getOrgUserMac | getOrgUserMac | [GET_orgs_org_id_usermacs_usermac_id.md](orgs/GET_orgs_org_id_usermacs_usermac_id.md) |
| PUT | /api/v1/orgs/{org_id}/usermacs/{usermac_id} | updateOrgUserMac | updateOrgUserMac | [PUT_orgs_org_id_usermacs_usermac_id.md](orgs/PUT_orgs_org_id_usermacs_usermac_id.md) |
| DELETE | /api/v1/orgs/{org_id}/usermacs/{usermac_id} | deleteOrgUserMac | deleteOrgUserMac | [DELETE_orgs_org_id_usermacs_usermac_id.md](orgs/DELETE_orgs_org_id_usermacs_usermac_id.md) |

## Orgs VPNs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/vpns | listOrgVpns | listOrgVpns | [GET_orgs_org_id_vpns.md](orgs/GET_orgs_org_id_vpns.md) |
| POST | /api/v1/orgs/{org_id}/vpns | createOrgVpn | createOrgVpn | [POST_orgs_org_id_vpns.md](orgs/POST_orgs_org_id_vpns.md) |
| GET | /api/v1/orgs/{org_id}/vpns/{vpn_id} | getOrgVpn | getOrgVpn | [GET_orgs_org_id_vpns_vpn_id.md](orgs/GET_orgs_org_id_vpns_vpn_id.md) |
| PUT | /api/v1/orgs/{org_id}/vpns/{vpn_id} | updateOrgVpn | updateOrgVpn | [PUT_orgs_org_id_vpns_vpn_id.md](orgs/PUT_orgs_org_id_vpns_vpn_id.md) |
| DELETE | /api/v1/orgs/{org_id}/vpns/{vpn_id} | deleteOrgVpn | deleteOrgVpn | [DELETE_orgs_org_id_vpns_vpn_id.md](orgs/DELETE_orgs_org_id_vpns_vpn_id.md) |

## Orgs Vars

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/vars/search | searchOrgVars | searchOrgVars | [GET_orgs_org_id_vars_search.md](orgs/GET_orgs_org_id_vars_search.md) |

## Orgs WLAN Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/templates | listOrgTemplates | listOrgTemplates | [GET_orgs_org_id_templates.md](orgs/GET_orgs_org_id_templates.md) |
| POST | /api/v1/orgs/{org_id}/templates | createOrgTemplate | createOrgTemplate | [POST_orgs_org_id_templates.md](orgs/POST_orgs_org_id_templates.md) |
| GET | /api/v1/orgs/{org_id}/templates/{template_id} | getOrgTemplate | getOrgTemplate | [GET_orgs_org_id_templates_template_id.md](orgs/GET_orgs_org_id_templates_template_id.md) |
| PUT | /api/v1/orgs/{org_id}/templates/{template_id} | updateOrgTemplate | updateOrgTemplate | [PUT_orgs_org_id_templates_template_id.md](orgs/PUT_orgs_org_id_templates_template_id.md) |
| DELETE | /api/v1/orgs/{org_id}/templates/{template_id} | deleteOrgTemplate | deleteOrgTemplate | [DELETE_orgs_org_id_templates_template_id.md](orgs/DELETE_orgs_org_id_templates_template_id.md) |
| POST | /api/v1/orgs/{org_id}/templates/{template_id}/clone | cloneOrgTemplate | cloneOrgTemplate | [POST_orgs_org_id_templates_template_id_clone.md](orgs/POST_orgs_org_id_templates_template_id_clone.md) |

## Orgs Webhooks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/webhooks | listOrgWebhooks | listOrgWebhooks | [GET_orgs_org_id_webhooks.md](orgs/GET_orgs_org_id_webhooks.md) |
| POST | /api/v1/orgs/{org_id}/webhooks | createOrgWebhook | createOrgWebhook | [POST_orgs_org_id_webhooks.md](orgs/POST_orgs_org_id_webhooks.md) |
| GET | /api/v1/orgs/{org_id}/webhooks/{webhook_id} | getOrgWebhook | getOrgWebhook | [GET_orgs_org_id_webhooks_webhook_id.md](orgs/GET_orgs_org_id_webhooks_webhook_id.md) |
| PUT | /api/v1/orgs/{org_id}/webhooks/{webhook_id} | updateOrgWebhook | updateOrgWebhook | [PUT_orgs_org_id_webhooks_webhook_id.md](orgs/PUT_orgs_org_id_webhooks_webhook_id.md) |
| DELETE | /api/v1/orgs/{org_id}/webhooks/{webhook_id} | deleteOrgWebhook | deleteOrgWebhook | [DELETE_orgs_org_id_webhooks_webhook_id.md](orgs/DELETE_orgs_org_id_webhooks_webhook_id.md) |
| GET | /api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count | countOrgWebhooksDeliveries | countOrgWebhooksDeliveries | [GET_orgs_org_id_webhooks_webhook_id_events_count.md](orgs/GET_orgs_org_id_webhooks_webhook_id_events_count.md) |
| GET | /api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/search | searchOrgWebhooksDeliveries | searchOrgWebhooksDeliveries | [GET_orgs_org_id_webhooks_webhook_id_events_search.md](orgs/GET_orgs_org_id_webhooks_webhook_id_events_search.md) |
| POST | /api/v1/orgs/{org_id}/webhooks/{webhook_id}/ping | pingOrgWebhook | pingOrgWebhook | [POST_orgs_org_id_webhooks_webhook_id_ping.md](orgs/POST_orgs_org_id_webhooks_webhook_id_ping.md) |

## Orgs Wlans

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wlans | listOrgWlans | listOrgWlans | [GET_orgs_org_id_wlans.md](orgs/GET_orgs_org_id_wlans.md) |
| POST | /api/v1/orgs/{org_id}/wlans | createOrgWlan | createOrgWlan | [POST_orgs_org_id_wlans.md](orgs/POST_orgs_org_id_wlans.md) |
| GET | /api/v1/orgs/{org_id}/wlans/{wlan_id} | getOrgWLAN | getOrgWLAN | [GET_orgs_org_id_wlans_wlan_id.md](orgs/GET_orgs_org_id_wlans_wlan_id.md) |
| PUT | /api/v1/orgs/{org_id}/wlans/{wlan_id} | updateOrgWlan | updateOrgWlan | [PUT_orgs_org_id_wlans_wlan_id.md](orgs/PUT_orgs_org_id_wlans_wlan_id.md) |
| DELETE | /api/v1/orgs/{org_id}/wlans/{wlan_id} | deleteOrgWlan | deleteOrgWlan | [DELETE_orgs_org_id_wlans_wlan_id.md](orgs/DELETE_orgs_org_id_wlans_wlan_id.md) |
| POST | /api/v1/orgs/{org_id}/wlans/{wlan_id}/portal_image | uploadOrgWlanPortalImage | uploadOrgWlanPortalImage | [POST_orgs_org_id_wlans_wlan_id_portal_image.md](orgs/POST_orgs_org_id_wlans_wlan_id_portal_image.md) |
| DELETE | /api/v1/orgs/{org_id}/wlans/{wlan_id}/portal_image | deleteOrgWlanPortalImage | deleteOrgWlanPortalImage | [DELETE_orgs_org_id_wlans_wlan_id_portal_image.md](orgs/DELETE_orgs_org_id_wlans_wlan_id_portal_image.md) |
| PUT | /api/v1/orgs/{org_id}/wlans/{wlan_id}/portal_template | updateOrgWlanPortalTemplate | updateOrgWlanPortalTemplate | [PUT_orgs_org_id_wlans_wlan_id_portal_template.md](orgs/PUT_orgs_org_id_wlans_wlan_id_portal_template.md) |

## Orgs WxRules

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wxrules | listOrgWxRules | listOrgWxRules | [GET_orgs_org_id_wxrules.md](orgs/GET_orgs_org_id_wxrules.md) |
| POST | /api/v1/orgs/{org_id}/wxrules | createOrgWxRule | createOrgWxRule | [POST_orgs_org_id_wxrules.md](orgs/POST_orgs_org_id_wxrules.md) |
| GET | /api/v1/orgs/{org_id}/wxrules/{wxrule_id} | getOrgWxRule | getOrgWxRule | [GET_orgs_org_id_wxrules_wxrule_id.md](orgs/GET_orgs_org_id_wxrules_wxrule_id.md) |
| PUT | /api/v1/orgs/{org_id}/wxrules/{wxrule_id} | updateOrgWxRule | updateOrgWxRule | [PUT_orgs_org_id_wxrules_wxrule_id.md](orgs/PUT_orgs_org_id_wxrules_wxrule_id.md) |
| DELETE | /api/v1/orgs/{org_id}/wxrules/{wxrule_id} | deleteOrgWxRule | deleteOrgWxRule | [DELETE_orgs_org_id_wxrules_wxrule_id.md](orgs/DELETE_orgs_org_id_wxrules_wxrule_id.md) |

## Orgs WxTags

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wxtags | listOrgWxTags | listOrgWxTags | [GET_orgs_org_id_wxtags.md](orgs/GET_orgs_org_id_wxtags.md) |
| POST | /api/v1/orgs/{org_id}/wxtags | createOrgWxTag | createOrgWxTag | [POST_orgs_org_id_wxtags.md](orgs/POST_orgs_org_id_wxtags.md) |
| GET | /api/v1/orgs/{org_id}/wxtags/apps | getOrgApplicationList | getOrgApplicationList | [GET_orgs_org_id_wxtags_apps.md](orgs/GET_orgs_org_id_wxtags_apps.md) |
| GET | /api/v1/orgs/{org_id}/wxtags/{wxtag_id} | getOrgWxTag | getOrgWxTag | [GET_orgs_org_id_wxtags_wxtag_id.md](orgs/GET_orgs_org_id_wxtags_wxtag_id.md) |
| PUT | /api/v1/orgs/{org_id}/wxtags/{wxtag_id} | updateOrgWxTag | updateOrgWxTag | [PUT_orgs_org_id_wxtags_wxtag_id.md](orgs/PUT_orgs_org_id_wxtags_wxtag_id.md) |
| DELETE | /api/v1/orgs/{org_id}/wxtags/{wxtag_id} | deleteOrgWxTag | deleteOrgWxTag | [DELETE_orgs_org_id_wxtags_wxtag_id.md](orgs/DELETE_orgs_org_id_wxtags_wxtag_id.md) |
| GET | /api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients | getOrgCurrentMatchingClientsOfAWxTag | getOrgCurrentMatchingClientsOfAWxTag | [GET_orgs_org_id_wxtags_wxtag_id_clients.md](orgs/GET_orgs_org_id_wxtags_wxtag_id_clients.md) |

## Orgs WxTunnels

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/wxtunnels | listOrgWxTunnels | listOrgWxTunnels | [GET_orgs_org_id_wxtunnels.md](orgs/GET_orgs_org_id_wxtunnels.md) |
| POST | /api/v1/orgs/{org_id}/wxtunnels | createOrgWxTunnel | createOrgWxTunnel | [POST_orgs_org_id_wxtunnels.md](orgs/POST_orgs_org_id_wxtunnels.md) |
| GET | /api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id} | getOrgWxTunnel | getOrgWxTunnel | [GET_orgs_org_id_wxtunnels_wxtunnel_id.md](orgs/GET_orgs_org_id_wxtunnels_wxtunnel_id.md) |
| PUT | /api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id} | updateOrgWxTunnel | updateOrgWxTunnel | [PUT_orgs_org_id_wxtunnels_wxtunnel_id.md](orgs/PUT_orgs_org_id_wxtunnels_wxtunnel_id.md) |
| DELETE | /api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id} | deleteOrgWxTunnel | deleteOrgWxTunnel | [DELETE_orgs_org_id_wxtunnels_wxtunnel_id.md](orgs/DELETE_orgs_org_id_wxtunnels_wxtunnel_id.md) |

## Self API Token

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self/apitokens | listApiTokens | listApiTokens | [GET_self_apitokens.md](self/GET_self_apitokens.md) |
| POST | /api/v1/self/apitokens | createApiToken | createApiToken | [POST_self_apitokens.md](self/POST_self_apitokens.md) |
| GET | /api/v1/self/apitokens/{apitoken_id} | getApiToken | getApiToken | [GET_self_apitokens_apitoken_id.md](self/GET_self_apitokens_apitoken_id.md) |
| PUT | /api/v1/self/apitokens/{apitoken_id} | updateApiToken | updateApiToken | [PUT_self_apitokens_apitoken_id.md](self/PUT_self_apitokens_apitoken_id.md) |
| DELETE | /api/v1/self/apitokens/{apitoken_id} | deleteApiToken | deleteApiToken | [DELETE_self_apitokens_apitoken_id.md](self/DELETE_self_apitokens_apitoken_id.md) |

## Self Account

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self | getSelf | getSelf | [GET_self.md](self/GET_self.md) |
| PUT | /api/v1/self | updateSelf | updateSelf | [PUT_self.md](self/PUT_self.md) |
| DELETE | /api/v1/self | deleteSelf | deleteSelf | [DELETE_self.md](self/DELETE_self.md) |
| GET | /api/v1/self/login_failures | getSelfLoginFailures | getSelfLoginFailures | [GET_self_login_failures.md](self/GET_self_login_failures.md) |
| POST | /api/v1/self/update | updateSelfEmail | updateSelfEmail | [POST_self_update.md](self/POST_self_update.md) |
| GET | /api/v1/self/update/verify/{token} | verifySelfEmail | verifySelfEmail | [GET_self_update_verify_token.md](self/GET_self_update_verify_token.md) |
| GET | /api/v1/self/usage | getSelfApiUsage | getSelfApiUsage | [GET_self_usage.md](self/GET_self_usage.md) |

## Self Alarms

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self/subscriptions | listAlarmSubscriptions | listAlarmSubscriptions | [GET_self_subscriptions.md](self/GET_self_subscriptions.md) |

## Self Audit Logs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self/logs | listSelfAuditLogs | listSelfAuditLogs | [GET_self_logs.md](self/GET_self_logs.md) |

## Self MFA

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self/two_factor/token | generateSecretFor2faVerification | generateSecretFor2faVerification | [GET_self_two_factor_token.md](self/GET_self_two_factor_token.md) |
| POST | /api/v1/self/two_factor/verify | verifyTwoFactor | verifyTwoFactor | [POST_self_two_factor_verify.md](self/POST_self_two_factor_verify.md) |

## Self OAuth2

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/self/oauth/{provider} | getOauth2UrlForLinking | getOauth2UrlForLinking | [GET_self_oauth_provider.md](self/GET_self_oauth_provider.md) |
| POST | /api/v1/self/oauth/{provider} | linkOauth2MistAccount | linkOauth2MistAccount | [POST_self_oauth_provider.md](self/POST_self_oauth_provider.md) |

## Sites

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id} | getSiteInfo | getSiteInfo | [GET_sites_site_id.md](sites/GET_sites_site_id.md) |
| PUT | /api/v1/sites/{site_id} | updateSiteInfo | updateSiteInfo | [PUT_sites_site_id.md](sites/PUT_sites_site_id.md) |
| DELETE | /api/v1/sites/{site_id} | deleteSite | deleteSite | [DELETE_sites_site_id.md](sites/DELETE_sites_site_id.md) |

## Sites AP Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/aptemplates/derived | listSiteApTemplatesDerived | listSiteApTemplatesDerived | [GET_sites_site_id_aptemplates_derived.md](sites/GET_sites_site_id_aptemplates_derived.md) |

## Sites Advanced Anti Malware Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/aamwprofiles/derived | listSiteAAMWProfilesDerived | listSiteAAMWProfilesDerived | [GET_sites_site_id_aamwprofiles_derived.md](sites/GET_sites_site_id_aamwprofiles_derived.md) |

## Sites Alarms

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/alarms/ack | AckSiteMultipleAlarms | AckSiteMultipleAlarms | [POST_sites_site_id_alarms_ack.md](sites/POST_sites_site_id_alarms_ack.md) |
| POST | /api/v1/sites/{site_id}/alarms/ack_all | ackSiteAllAlarms | ackSiteAllAlarms | [POST_sites_site_id_alarms_ack_all.md](sites/POST_sites_site_id_alarms_ack_all.md) |
| GET | /api/v1/sites/{site_id}/alarms/count | countSiteAlarms | countSiteAlarms | [GET_sites_site_id_alarms_count.md](sites/GET_sites_site_id_alarms_count.md) |
| GET | /api/v1/sites/{site_id}/alarms/search | searchSiteAlarms | searchSiteAlarms | [GET_sites_site_id_alarms_search.md](sites/GET_sites_site_id_alarms_search.md) |
| POST | /api/v1/sites/{site_id}/alarms/unack | unackSiteMultipleAlarms | unackSiteMultipleAlarms | [POST_sites_site_id_alarms_unack.md](sites/POST_sites_site_id_alarms_unack.md) |
| POST | /api/v1/sites/{site_id}/alarms/unack_all | unackSiteAllAlarms | unackSiteAllAlarms | [POST_sites_site_id_alarms_unack_all.md](sites/POST_sites_site_id_alarms_unack_all.md) |
| POST | /api/v1/sites/{site_id}/alarms/{alarm_id}/ack | ackSiteAlarm | ackSiteAlarm | [POST_sites_site_id_alarms_alarm_id_ack.md](sites/POST_sites_site_id_alarms_alarm_id_ack.md) |
| POST | /api/v1/sites/{site_id}/alarms/{alarm_id}/unack | unackSiteAlarm | unackSiteAlarm | [POST_sites_site_id_alarms_alarm_id_unack.md](sites/POST_sites_site_id_alarms_alarm_id_unack.md) |
| POST | /api/v1/sites/{site_id}/subscriptions | SubscribeSiteAlarms | SubscribeSiteAlarms | [POST_sites_site_id_subscriptions.md](sites/POST_sites_site_id_subscriptions.md) |
| DELETE | /api/v1/sites/{site_id}/subscriptions | UnsubscribeSiteAlarms | UnsubscribeSiteAlarms | [DELETE_sites_site_id_subscriptions.md](sites/DELETE_sites_site_id_subscriptions.md) |

## Sites Anomaly

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/anomaly/client/{client_mac}/{metric} | getSiteAnomalyEventsForClient | getSiteAnomalyEventsForClient | [GET_sites_site_id_anomaly_client_client_mac_metric.md](sites/GET_sites_site_id_anomaly_client_client_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/anomaly/device/{device_mac}/{metric} | getSiteAnomalyEventsForDevice | getSiteAnomalyEventsForDevice | [GET_sites_site_id_anomaly_device_device_mac_metric.md](sites/GET_sites_site_id_anomaly_device_device_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/anomaly/{metric} | listSiteAnomalyEvents | listSiteAnomalyEvents | [GET_sites_site_id_anomaly_metric.md](sites/GET_sites_site_id_anomaly_metric.md) |

## Sites Antivirus Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/avprofiles/derived | listSiteAntivirusProfilesDerived | listSiteAntivirusProfilesDerived | [GET_sites_site_id_avprofiles_derived.md](sites/GET_sites_site_id_avprofiles_derived.md) |

## Sites Applications

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/apps | listSiteApps | listSiteApps | [GET_sites_site_id_apps.md](sites/GET_sites_site_id_apps.md) |

## Sites Asset Filters

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/assetfilters | listSiteAssetFilters | listSiteAssetFilters | [GET_sites_site_id_assetfilters.md](sites/GET_sites_site_id_assetfilters.md) |
| POST | /api/v1/sites/{site_id}/assetfilters | createSiteAssetFilter | createSiteAssetFilter | [POST_sites_site_id_assetfilters.md](sites/POST_sites_site_id_assetfilters.md) |
| GET | /api/v1/sites/{site_id}/assetfilters/{assetfilter_id} | getSiteAssetFilter | getSiteAssetFilter | [GET_sites_site_id_assetfilters_assetfilter_id.md](sites/GET_sites_site_id_assetfilters_assetfilter_id.md) |
| PUT | /api/v1/sites/{site_id}/assetfilters/{assetfilter_id} | updateSiteAssetFilter | updateSiteAssetFilter | [PUT_sites_site_id_assetfilters_assetfilter_id.md](sites/PUT_sites_site_id_assetfilters_assetfilter_id.md) |
| DELETE | /api/v1/sites/{site_id}/assetfilters/{assetfilter_id} | deleteSiteAssetFilter | deleteSiteAssetFilter | [DELETE_sites_site_id_assetfilters_assetfilter_id.md](sites/DELETE_sites_site_id_assetfilters_assetfilter_id.md) |

## Sites Assets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/assets | listSiteAssets | listSiteAssets | [GET_sites_site_id_assets.md](sites/GET_sites_site_id_assets.md) |
| POST | /api/v1/sites/{site_id}/assets | createSiteAsset | createSiteAsset | [POST_sites_site_id_assets.md](sites/POST_sites_site_id_assets.md) |
| POST | /api/v1/sites/{site_id}/assets/import | importSiteAssets | importSiteAssets | [POST_sites_site_id_assets_import.md](sites/POST_sites_site_id_assets_import.md) |
| GET | /api/v1/sites/{site_id}/assets/{asset_id} | getSiteAsset | getSiteAsset | [GET_sites_site_id_assets_asset_id.md](sites/GET_sites_site_id_assets_asset_id.md) |
| PUT | /api/v1/sites/{site_id}/assets/{asset_id} | updateSiteAsset | updateSiteAsset | [PUT_sites_site_id_assets_asset_id.md](sites/PUT_sites_site_id_assets_asset_id.md) |
| DELETE | /api/v1/sites/{site_id}/assets/{asset_id} | deleteSiteAsset | deleteSiteAsset | [DELETE_sites_site_id_assets_asset_id.md](sites/DELETE_sites_site_id_assets_asset_id.md) |
| POST | /api/v1/sites/{site_id}/assets/{asset_id}/image | attachSiteAssetImage | attachSiteAssetImage | [POST_sites_site_id_assets_asset_id_image.md](sites/POST_sites_site_id_assets_asset_id_image.md) |
| DELETE | /api/v1/sites/{site_id}/assets/{asset_id}/image | deleteSiteAssetImage | deleteSiteAssetImage | [DELETE_sites_site_id_assets_asset_id_image.md](sites/DELETE_sites_site_id_assets_asset_id_image.md) |

## Sites Beacons

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/beacons | listSiteBeacons | listSiteBeacons | [GET_sites_site_id_beacons.md](sites/GET_sites_site_id_beacons.md) |
| POST | /api/v1/sites/{site_id}/beacons | createSiteBeacon | createSiteBeacon | [POST_sites_site_id_beacons.md](sites/POST_sites_site_id_beacons.md) |
| GET | /api/v1/sites/{site_id}/beacons/{beacon_id} | getSiteBeacon | getSiteBeacon | [GET_sites_site_id_beacons_beacon_id.md](sites/GET_sites_site_id_beacons_beacon_id.md) |
| PUT | /api/v1/sites/{site_id}/beacons/{beacon_id} | updateSiteBeacon | updateSiteBeacon | [PUT_sites_site_id_beacons_beacon_id.md](sites/PUT_sites_site_id_beacons_beacon_id.md) |
| DELETE | /api/v1/sites/{site_id}/beacons/{beacon_id} | deleteSiteBeacon | deleteSiteBeacon | [DELETE_sites_site_id_beacons_beacon_id.md](sites/DELETE_sites_site_id_beacons_beacon_id.md) |

## Sites Clients - NAC

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/nac_clients/count | countSiteNacClients | countSiteNacClients | [GET_sites_site_id_nac_clients_count.md](sites/GET_sites_site_id_nac_clients_count.md) |
| GET | /api/v1/sites/{site_id}/nac_clients/events/count | countSiteNacClientEvents | countSiteNacClientEvents | [GET_sites_site_id_nac_clients_events_count.md](sites/GET_sites_site_id_nac_clients_events_count.md) |
| GET | /api/v1/sites/{site_id}/nac_clients/events/search | searchSiteNacClientEvents | searchSiteNacClientEvents | [GET_sites_site_id_nac_clients_events_search.md](sites/GET_sites_site_id_nac_clients_events_search.md) |
| GET | /api/v1/sites/{site_id}/nac_clients/search | searchSiteNacClients | searchSiteNacClients | [GET_sites_site_id_nac_clients_search.md](sites/GET_sites_site_id_nac_clients_search.md) |

## Sites Clients - Wan

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wan_client/events/count | countSiteWanClientEvents | countSiteWanClientEvents | [GET_sites_site_id_wan_client_events_count.md](sites/GET_sites_site_id_wan_client_events_count.md) |
| GET | /api/v1/sites/{site_id}/wan_clients/count | countSiteWanClients | countSiteWanClients | [GET_sites_site_id_wan_clients_count.md](sites/GET_sites_site_id_wan_clients_count.md) |
| GET | /api/v1/sites/{site_id}/wan_clients/events/search | searchSiteWanClientEvents | searchSiteWanClientEvents | [GET_sites_site_id_wan_clients_events_search.md](sites/GET_sites_site_id_wan_clients_events_search.md) |
| GET | /api/v1/sites/{site_id}/wan_clients/search | searchSiteWanClients | searchSiteWanClients | [GET_sites_site_id_wan_clients_search.md](sites/GET_sites_site_id_wan_clients_search.md) |

## Sites Clients - Wired

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wired_clients/count | countSiteWiredClients | countSiteWiredClients | [GET_sites_site_id_wired_clients_count.md](sites/GET_sites_site_id_wired_clients_count.md) |
| GET | /api/v1/sites/{site_id}/wired_clients/search | searchSiteWiredClients | searchSiteWiredClients | [GET_sites_site_id_wired_clients_search.md](sites/GET_sites_site_id_wired_clients_search.md) |

## Sites Clients - Wireless

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/clients/count | countSiteWirelessClients | countSiteWirelessClients | [GET_sites_site_id_clients_count.md](sites/GET_sites_site_id_clients_count.md) |
| GET | /api/v1/sites/{site_id}/clients/events/count | countSiteWirelessClientEvents | countSiteWirelessClientEvents | [GET_sites_site_id_clients_events_count.md](sites/GET_sites_site_id_clients_events_count.md) |
| GET | /api/v1/sites/{site_id}/clients/events/search | searchSiteWirelessClientEvents | searchSiteWirelessClientEvents | [GET_sites_site_id_clients_events_search.md](sites/GET_sites_site_id_clients_events_search.md) |
| GET | /api/v1/sites/{site_id}/clients/search | searchSiteWirelessClients | searchSiteWirelessClients | [GET_sites_site_id_clients_search.md](sites/GET_sites_site_id_clients_search.md) |
| GET | /api/v1/sites/{site_id}/clients/sessions/count | countSiteWirelessClientSessions | countSiteWirelessClientSessions | [GET_sites_site_id_clients_sessions_count.md](sites/GET_sites_site_id_clients_sessions_count.md) |
| GET | /api/v1/sites/{site_id}/clients/sessions/search | searchSiteWirelessClientSessions | searchSiteWirelessClientSessions | [GET_sites_site_id_clients_sessions_search.md](sites/GET_sites_site_id_clients_sessions_search.md) |
| GET | /api/v1/sites/{site_id}/clients/{client_mac}/events | getSiteEventsForClient | getSiteEventsForClient | [GET_sites_site_id_clients_client_mac_events.md](sites/GET_sites_site_id_clients_client_mac_events.md) |

## Sites Device Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/deviceprofiles/derived | listSiteDeviceProfilesDerived | listSiteDeviceProfilesDerived | [GET_sites_site_id_deviceprofiles_derived.md](sites/GET_sites_site_id_deviceprofiles_derived.md) |

## Sites Devices

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/devices | listSiteDevices | listSiteDevices | [GET_sites_site_id_devices.md](sites/GET_sites_site_id_devices.md) |
| GET | /api/v1/sites/{site_id}/devices/config_history/count | countSiteDeviceConfigHistory | countSiteDeviceConfigHistory | [GET_sites_site_id_devices_config_history_count.md](sites/GET_sites_site_id_devices_config_history_count.md) |
| GET | /api/v1/sites/{site_id}/devices/config_history/search | searchSiteDeviceConfigHistory | searchSiteDeviceConfigHistory | [GET_sites_site_id_devices_config_history_search.md](sites/GET_sites_site_id_devices_config_history_search.md) |
| GET | /api/v1/sites/{site_id}/devices/count | countSiteDevices | countSiteDevices | [GET_sites_site_id_devices_count.md](sites/GET_sites_site_id_devices_count.md) |
| GET | /api/v1/sites/{site_id}/devices/events/count | countSiteDeviceEvents | countSiteDeviceEvents | [GET_sites_site_id_devices_events_count.md](sites/GET_sites_site_id_devices_events_count.md) |
| GET | /api/v1/sites/{site_id}/devices/events/search | searchSiteDeviceEvents | searchSiteDeviceEvents | [GET_sites_site_id_devices_events_search.md](sites/GET_sites_site_id_devices_events_search.md) |
| GET | /api/v1/sites/{site_id}/devices/export | exportSiteDevices | exportSiteDevices | [GET_sites_site_id_devices_export.md](sites/GET_sites_site_id_devices_export.md) |
| POST | /api/v1/sites/{site_id}/devices/gbp_tag | setSiteDevicesGbpTag | setSiteDevicesGbpTag | [POST_sites_site_id_devices_gbp_tag.md](sites/POST_sites_site_id_devices_gbp_tag.md) |
| POST | /api/v1/sites/{site_id}/devices/import | importSiteDevices | importSiteDevices | [POST_sites_site_id_devices_import.md](sites/POST_sites_site_id_devices_import.md) |
| GET | /api/v1/sites/{site_id}/devices/last_config/count | countSiteDeviceLastConfig | countSiteDeviceLastConfig | [GET_sites_site_id_devices_last_config_count.md](sites/GET_sites_site_id_devices_last_config_count.md) |
| GET | /api/v1/sites/{site_id}/devices/last_config/search | searchSiteDeviceLastConfigs | searchSiteDeviceLastConfigs | [GET_sites_site_id_devices_last_config_search.md](sites/GET_sites_site_id_devices_last_config_search.md) |
| GET | /api/v1/sites/{site_id}/devices/search | searchSiteDevices | searchSiteDevices | [GET_sites_site_id_devices_search.md](sites/GET_sites_site_id_devices_search.md) |
| GET | /api/v1/sites/{site_id}/devices/{device_id} | getSiteDevice | getSiteDevice | [GET_sites_site_id_devices_device_id.md](sites/GET_sites_site_id_devices_device_id.md) |
| PUT | /api/v1/sites/{site_id}/devices/{device_id} | updateSiteDevice | updateSiteDevice | [PUT_sites_site_id_devices_device_id.md](sites/PUT_sites_site_id_devices_device_id.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number} | addSiteDeviceImage | addSiteDeviceImage | [POST_sites_site_id_devices_device_id_image_image_number.md](sites/POST_sites_site_id_devices_device_id_image_image_number.md) |
| DELETE | /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number} | deleteSiteDeviceImage | deleteSiteDeviceImage | [DELETE_sites_site_id_devices_device_id_image_image_number.md](sites/DELETE_sites_site_id_devices_device_id_image_image_number.md) |

## Sites Devices - Others

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/otherdevices | listSiteOtherDevices | listSiteOtherDevices | [GET_sites_site_id_otherdevices.md](sites/GET_sites_site_id_otherdevices.md) |
| GET | /api/v1/sites/{site_id}/otherdevices/events/count | countSiteOtherDeviceEvents | countSiteOtherDeviceEvents | [GET_sites_site_id_otherdevices_events_count.md](sites/GET_sites_site_id_otherdevices_events_count.md) |
| GET | /api/v1/sites/{site_id}/otherdevices/events/search | searchSiteOtherDeviceEvents | searchSiteOtherDeviceEvents | [GET_sites_site_id_otherdevices_events_search.md](sites/GET_sites_site_id_otherdevices_events_search.md) |

## Sites Devices - WAN Cluster

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/devices/{device_id}/ha | GetSiteDeviceHaClusterNode | GetSiteDeviceHaClusterNode | [GET_sites_site_id_devices_device_id_ha.md](sites/GET_sites_site_id_devices_device_id_ha.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/ha | createSiteDeviceHaCluster | createSiteDeviceHaCluster | [POST_sites_site_id_devices_device_id_ha.md](sites/POST_sites_site_id_devices_device_id_ha.md) |
| DELETE | /api/v1/sites/{site_id}/devices/{device_id}/ha | deleteSiteDeviceHaCluster | deleteSiteDeviceHaCluster | [DELETE_sites_site_id_devices_device_id_ha.md](sites/DELETE_sites_site_id_devices_device_id_ha.md) |

## Sites Devices - Wired

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| PUT | /api/v1/sites/{site_id}/devices/{device_id}/local_port_config | updateSiteLocalSwitchPortConfig | updateSiteLocalSwitchPortConfig | [PUT_sites_site_id_devices_device_id_local_port_config.md](sites/PUT_sites_site_id_devices_device_id_local_port_config.md) |
| DELETE | /api/v1/sites/{site_id}/devices/{device_id}/local_port_config | deleteSiteLocalSwitchPortConfig | deleteSiteLocalSwitchPortConfig | [DELETE_sites_site_id_devices_device_id_local_port_config.md](sites/DELETE_sites_site_id_devices_device_id_local_port_config.md) |

## Sites Devices - Wired - Virtual Chassis

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/devices/{device_id}/set_vc_port_mode | changeSiteSwitchVcPortMode | changeSiteSwitchVcPortMode | [POST_sites_site_id_devices_device_id_set_vc_port_mode.md](sites/POST_sites_site_id_devices_device_id_set_vc_port_mode.md) |
| GET | /api/v1/sites/{site_id}/devices/{device_id}/vc | getSiteDeviceVirtualChassis | getSiteDeviceVirtualChassis | [GET_sites_site_id_devices_device_id_vc.md](sites/GET_sites_site_id_devices_device_id_vc.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/vc | createSiteVirtualChassis | createSiteVirtualChassis | [POST_sites_site_id_devices_device_id_vc.md](sites/POST_sites_site_id_devices_device_id_vc.md) |
| PUT | /api/v1/sites/{site_id}/devices/{device_id}/vc | updateSiteVirtualChassisMember | updateSiteVirtualChassisMember | [PUT_sites_site_id_devices_device_id_vc.md](sites/PUT_sites_site_id_devices_device_id_vc.md) |
| DELETE | /api/v1/sites/{site_id}/devices/{device_id}/vc | deleteSiteVirtualChassis | deleteSiteVirtualChassis | [DELETE_sites_site_id_devices_device_id_vc.md](sites/DELETE_sites_site_id_devices_device_id_vc.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/vc/convert_to_virtualmac | convertSiteVirtualChassisToVirtualMac | convertSiteVirtualChassisToVirtualMac | [POST_sites_site_id_devices_device_id_vc_convert_to_virtualmac.md](sites/POST_sites_site_id_devices_device_id_vc_convert_to_virtualmac.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/vc/vc_port | setSiteVcPort | setSiteVcPort | [POST_sites_site_id_devices_device_id_vc_vc_port.md](sites/POST_sites_site_id_devices_device_id_vc_vc_port.md) |

## Sites Devices - Wireless

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/devices/ap_channels | listSiteDeviceRadioChannels | listSiteDeviceRadioChannels | [GET_sites_site_id_devices_ap_channels.md](sites/GET_sites_site_id_devices_ap_channels.md) |
| GET | /api/v1/sites/{site_id}/devices/{device_id}/iot | getSiteDeviceIotPort | getSiteDeviceIotPort | [GET_sites_site_id_devices_device_id_iot.md](sites/GET_sites_site_id_devices_device_id_iot.md) |
| PUT | /api/v1/sites/{site_id}/devices/{device_id}/iot | setSiteDeviceIotPort | setSiteDeviceIotPort | [PUT_sites_site_id_devices_device_id_iot.md](sites/PUT_sites_site_id_devices_device_id_iot.md) |

## Sites EVPN Topologies

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/evpn_topologies | listSiteEvpnTopologies | listSiteEvpnTopologies | [GET_sites_site_id_evpn_topologies.md](sites/GET_sites_site_id_evpn_topologies.md) |
| POST | /api/v1/sites/{site_id}/evpn_topologies | createSiteEvpnTopology | createSiteEvpnTopology | [POST_sites_site_id_evpn_topologies.md](sites/POST_sites_site_id_evpn_topologies.md) |
| GET | /api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id} | getSiteEvpnTopology | getSiteEvpnTopology | [GET_sites_site_id_evpn_topologies_evpn_topology_id.md](sites/GET_sites_site_id_evpn_topologies_evpn_topology_id.md) |
| PUT | /api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id} | updateSiteEvpnTopology | updateSiteEvpnTopology | [PUT_sites_site_id_evpn_topologies_evpn_topology_id.md](sites/PUT_sites_site_id_evpn_topologies_evpn_topology_id.md) |
| DELETE | /api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id} | deleteSiteEvpnTopology | deleteSiteEvpnTopology | [DELETE_sites_site_id_evpn_topologies_evpn_topology_id.md](sites/DELETE_sites_site_id_evpn_topologies_evpn_topology_id.md) |

## Sites Events

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/events/fast_roam | listSiteRoamingEvents | listSiteRoamingEvents | [GET_sites_site_id_events_fast_roam.md](sites/GET_sites_site_id_events_fast_roam.md) |
| GET | /api/v1/sites/{site_id}/events/system/count | countSiteSystemEvents | countSiteSystemEvents | [GET_sites_site_id_events_system_count.md](sites/GET_sites_site_id_events_system_count.md) |
| GET | /api/v1/sites/{site_id}/events/system/search | searchSiteSystemEvents | searchSiteSystemEvents | [GET_sites_site_id_events_system_search.md](sites/GET_sites_site_id_events_system_search.md) |

## Sites Gateway Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/gatewaytemplates/derived | listSiteGatewayTemplatesDerived | listSiteGatewayTemplatesDerived | [GET_sites_site_id_gatewaytemplates_derived.md](sites/GET_sites_site_id_gatewaytemplates_derived.md) |

## Sites Guests

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/guests | listSiteAllGuestAuthorizations | listSiteAllGuestAuthorizations | [GET_sites_site_id_guests.md](sites/GET_sites_site_id_guests.md) |
| GET | /api/v1/sites/{site_id}/guests/count | countSiteGuestAuthorizations | countSiteGuestAuthorizations | [GET_sites_site_id_guests_count.md](sites/GET_sites_site_id_guests_count.md) |
| GET | /api/v1/sites/{site_id}/guests/derived | listSiteAllGuestAuthorizationsDerived | listSiteAllGuestAuthorizationsDerived | [GET_sites_site_id_guests_derived.md](sites/GET_sites_site_id_guests_derived.md) |
| GET | /api/v1/sites/{site_id}/guests/search | searchSiteGuestAuthorization | searchSiteGuestAuthorization | [GET_sites_site_id_guests_search.md](sites/GET_sites_site_id_guests_search.md) |
| GET | /api/v1/sites/{site_id}/guests/{guest_mac} | getSiteGuestAuthorization | getSiteGuestAuthorization | [GET_sites_site_id_guests_guest_mac.md](sites/GET_sites_site_id_guests_guest_mac.md) |
| PUT | /api/v1/sites/{site_id}/guests/{guest_mac} | updateSiteGuestAuthorization | updateSiteGuestAuthorization | [PUT_sites_site_id_guests_guest_mac.md](sites/PUT_sites_site_id_guests_guest_mac.md) |
| DELETE | /api/v1/sites/{site_id}/guests/{guest_mac} | deleteSiteGuestAuthorization | deleteSiteGuestAuthorization | [DELETE_sites_site_id_guests_guest_mac.md](sites/DELETE_sites_site_id_guests_guest_mac.md) |

## Sites IDP Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/idpprofiles/derived | listSiteIdpProfilesDerived | listSiteIdpProfilesDerived | [GET_sites_site_id_idpprofiles_derived.md](sites/GET_sites_site_id_idpprofiles_derived.md) |

## Sites Insights

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/insights/client/{client_mac}/{metric} | getSiteInsightMetricsForClient | getSiteInsightMetricsForClient | [GET_sites_site_id_insights_client_client_mac_metric.md](sites/GET_sites_site_id_insights_client_client_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/insights/device/{device_mac}/{metric} | getSiteInsightMetricsForDevice | getSiteInsightMetricsForDevice | [GET_sites_site_id_insights_device_device_mac_metric.md](sites/GET_sites_site_id_insights_device_device_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/insights/gateway/{device_id}/stats/{metric} | getSiteInsightMetricsForGateway | getSiteInsightMetricsForGateway | [GET_sites_site_id_insights_gateway_device_id_stats_metric.md](sites/GET_sites_site_id_insights_gateway_device_id_stats_metric.md) |
| GET | /api/v1/sites/{site_id}/insights/mxedge/{device_mac}/{metric} | getSiteInsightMetricsForMxEdge | getSiteInsightMetricsForMxEdge | [GET_sites_site_id_insights_mxedge_device_mac_metric.md](sites/GET_sites_site_id_insights_mxedge_device_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/insights/switch/{device_mac}/{metric} | getSiteInsightMetricsForSwitch | getSiteInsightMetricsForSwitch | [GET_sites_site_id_insights_switch_device_mac_metric.md](sites/GET_sites_site_id_insights_switch_device_mac_metric.md) |
| GET | /api/v1/sites/{site_id}/insights/{metric} | getSiteInsightMetrics | getSiteInsightMetrics | [GET_sites_site_id_insights_metric.md](sites/GET_sites_site_id_insights_metric.md) |

## Sites JSE

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/setting/jse/info | getSiteJseInfo | getSiteJseInfo | [GET_sites_site_id_setting_jse_info.md](sites/GET_sites_site_id_setting_jse_info.md) |

## Sites Licenses

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/licenses/usages | getSiteLicenseUsage | getSiteLicenseUsage | [GET_sites_site_id_licenses_usages.md](sites/GET_sites_site_id_licenses_usages.md) |

## Sites Location

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/location/coverage | getSiteBeamCoverageOverview | getSiteBeamCoverageOverview | [GET_sites_site_id_location_coverage.md](sites/GET_sites_site_id_location_coverage.md) |
| GET | /api/v1/sites/{site_id}/location/ml/current | getSiteMachineLearningCurrentStat | getSiteMachineLearningCurrentStat | [GET_sites_site_id_location_ml_current.md](sites/GET_sites_site_id_location_ml_current.md) |
| GET | /api/v1/sites/{site_id}/location/ml/defaults | getSiteDefaultPlfForModels | getSiteDefaultPlfForModels | [GET_sites_site_id_location_ml_defaults.md](sites/GET_sites_site_id_location_ml_defaults.md) |
| PUT | /api/v1/sites/{site_id}/location/ml/device/{device_id} | overwriteSiteMlForDevice | overwriteSiteMlForDevice | [PUT_sites_site_id_location_ml_device_device_id.md](sites/PUT_sites_site_id_location_ml_device_device_id.md) |
| DELETE | /api/v1/sites/{site_id}/location/ml/device/{device_id} | clearSiteMlOverwriteForDevice | clearSiteMlOverwriteForDevice | [DELETE_sites_site_id_location_ml_device_device_id.md](sites/DELETE_sites_site_id_location_ml_device_device_id.md) |
| PUT | /api/v1/sites/{site_id}/location/ml/map/{map_id} | overwriteSiteMlForMap | overwriteSiteMlForMap | [PUT_sites_site_id_location_ml_map_map_id.md](sites/PUT_sites_site_id_location_ml_map_map_id.md) |
| DELETE | /api/v1/sites/{site_id}/location/ml/map/{map_id} | clearSiteMlOverwriteForMap | clearSiteMlOverwriteForMap | [DELETE_sites_site_id_location_ml_map_map_id.md](sites/DELETE_sites_site_id_location_ml_map_map_id.md) |
| POST | /api/v1/sites/{site_id}/location/ml/reset/map/{map_id} | resetSiteMlStatsByMap | resetSiteMlStatsByMap | [POST_sites_site_id_location_ml_reset_map_map_id.md](sites/POST_sites_site_id_location_ml_reset_map_map_id.md) |

## Sites Map Stacks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/mapstacks | listSiteMapStacks | listSiteMapStacks | [GET_sites_site_id_mapstacks.md](sites/GET_sites_site_id_mapstacks.md) |
| POST | /api/v1/sites/{site_id}/mapstacks | createSiteMapStack | createSiteMapStack | [POST_sites_site_id_mapstacks.md](sites/POST_sites_site_id_mapstacks.md) |

## Sites Maps

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/maps | listSiteMaps | listSiteMaps | [GET_sites_site_id_maps.md](sites/GET_sites_site_id_maps.md) |
| POST | /api/v1/sites/{site_id}/maps | createSiteMap | createSiteMap | [POST_sites_site_id_maps.md](sites/POST_sites_site_id_maps.md) |
| POST | /api/v1/sites/{site_id}/maps/auto_geofences | startSiteMapsAutoGeofence | startSiteMapsAutoGeofence | [POST_sites_site_id_maps_auto_geofences.md](sites/POST_sites_site_id_maps_auto_geofences.md) |
| POST | /api/v1/sites/{site_id}/maps/import | importSiteMaps | importSiteMaps | [POST_sites_site_id_maps_import.md](sites/POST_sites_site_id_maps_import.md) |
| GET | /api/v1/sites/{site_id}/maps/{map_id} | getSiteMap | getSiteMap | [GET_sites_site_id_maps_map_id.md](sites/GET_sites_site_id_maps_map_id.md) |
| PUT | /api/v1/sites/{site_id}/maps/{map_id} | updateSiteMap | updateSiteMap | [PUT_sites_site_id_maps_map_id.md](sites/PUT_sites_site_id_maps_map_id.md) |
| DELETE | /api/v1/sites/{site_id}/maps/{map_id} | deleteSiteMap | deleteSiteMap | [DELETE_sites_site_id_maps_map_id.md](sites/DELETE_sites_site_id_maps_map_id.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/auto_geofences | startSiteMapAutoGeofence | startSiteMapAutoGeofence | [POST_sites_site_id_maps_map_id_auto_geofences.md](sites/POST_sites_site_id_maps_map_id_auto_geofences.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/image | addSiteMapImage | addSiteMapImage | [POST_sites_site_id_maps_map_id_image.md](sites/POST_sites_site_id_maps_map_id_image.md) |
| DELETE | /api/v1/sites/{site_id}/maps/{map_id}/image | deleteSiteMapImage | deleteSiteMapImage | [DELETE_sites_site_id_maps_map_id_image.md](sites/DELETE_sites_site_id_maps_map_id_image.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/replace | replaceSiteMapImage | replaceSiteMapImage | [POST_sites_site_id_maps_map_id_replace.md](sites/POST_sites_site_id_maps_map_id_replace.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/set_map | bulkAssignSiteApsToMap | bulkAssignSiteApsToMap | [POST_sites_site_id_maps_map_id_set_map.md](sites/POST_sites_site_id_maps_map_id_set_map.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/wayfinding/import | importSiteWayfindings | importSiteWayfindings | [POST_sites_site_id_maps_map_id_wayfinding_import.md](sites/POST_sites_site_id_maps_map_id_wayfinding_import.md) |

## Sites Maps - Auto-Zone

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/maps/{map_id}/auto_zones | getSiteMapAutoZoneStatus | getSiteMapAutoZoneStatus | [GET_sites_site_id_maps_map_id_auto_zones.md](sites/GET_sites_site_id_maps_map_id_auto_zones.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/auto_zones | startSiteMapAutoZone | startSiteMapAutoZone | [POST_sites_site_id_maps_map_id_auto_zones.md](sites/POST_sites_site_id_maps_map_id_auto_zones.md) |
| DELETE | /api/v1/sites/{site_id}/maps/{map_id}/auto_zones | deleteSiteMapAutoZone | deleteSiteMapAutoZone | [DELETE_sites_site_id_maps_map_id_auto_zones.md](sites/DELETE_sites_site_id_maps_map_id_auto_zones.md) |

## Sites Maps - Auto-placement

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/maps/{map_id}/auto_orient | getSiteApAutoOrientation | getSiteApAutoOrientation | [GET_sites_site_id_maps_map_id_auto_orient.md](sites/GET_sites_site_id_maps_map_id_auto_orient.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/auto_orient | startSiteApAutoOrientation | startSiteApAutoOrientation | [POST_sites_site_id_maps_map_id_auto_orient.md](sites/POST_sites_site_id_maps_map_id_auto_orient.md) |
| DELETE | /api/v1/sites/{site_id}/maps/{map_id}/auto_orient | deleteSiteApAutoOrientation | deleteSiteApAutoOrientation | [DELETE_sites_site_id_maps_map_id_auto_orient.md](sites/DELETE_sites_site_id_maps_map_id_auto_orient.md) |
| GET | /api/v1/sites/{site_id}/maps/{map_id}/auto_placement | getSiteApAutoPlacement | getSiteApAutoPlacement | [GET_sites_site_id_maps_map_id_auto_placement.md](sites/GET_sites_site_id_maps_map_id_auto_placement.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/auto_placement | runSiteApAutoplacement | runSiteApAutoplacement | [POST_sites_site_id_maps_map_id_auto_placement.md](sites/POST_sites_site_id_maps_map_id_auto_placement.md) |
| DELETE | /api/v1/sites/{site_id}/maps/{map_id}/auto_placement | deleteSiteApAutoplacement | deleteSiteApAutoplacement | [DELETE_sites_site_id_maps_map_id_auto_placement.md](sites/DELETE_sites_site_id_maps_map_id_auto_placement.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/clear_auto_orient | clearSiteApAutoOrient | clearSiteApAutoOrient | [POST_sites_site_id_maps_map_id_clear_auto_orient.md](sites/POST_sites_site_id_maps_map_id_clear_auto_orient.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/clear_autoplacement | clearSiteApAutoplacement | clearSiteApAutoplacement | [POST_sites_site_id_maps_map_id_clear_autoplacement.md](sites/POST_sites_site_id_maps_map_id_clear_autoplacement.md) |
| POST | /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values | confirmSiteApLocalizationData | confirmSiteApLocalizationData | [POST_sites_site_id_maps_map_id_use_auto_ap_values.md](sites/POST_sites_site_id_maps_map_id_use_auto_ap_values.md) |

## Sites MxEdges

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/mxedges | listSiteMxEdges | listSiteMxEdges | [GET_sites_site_id_mxedges.md](sites/GET_sites_site_id_mxedges.md) |
| GET | /api/v1/sites/{site_id}/mxedges/events/count | countSiteMxEdgeEvents | countSiteMxEdgeEvents | [GET_sites_site_id_mxedges_events_count.md](sites/GET_sites_site_id_mxedges_events_count.md) |
| GET | /api/v1/sites/{site_id}/mxedges/events/search | searchSiteMistEdgeEvents | searchSiteMistEdgeEvents | [GET_sites_site_id_mxedges_events_search.md](sites/GET_sites_site_id_mxedges_events_search.md) |
| GET | /api/v1/sites/{site_id}/mxedges/{mxedge_id} | getSiteMxEdge | getSiteMxEdge | [GET_sites_site_id_mxedges_mxedge_id.md](sites/GET_sites_site_id_mxedges_mxedge_id.md) |
| PUT | /api/v1/sites/{site_id}/mxedges/{mxedge_id} | updateSiteMxEdge | updateSiteMxEdge | [PUT_sites_site_id_mxedges_mxedge_id.md](sites/PUT_sites_site_id_mxedges_mxedge_id.md) |
| DELETE | /api/v1/sites/{site_id}/mxedges/{mxedge_id} | deleteSiteMxEdge | deleteSiteMxEdge | [DELETE_sites_site_id_mxedges_mxedge_id.md](sites/DELETE_sites_site_id_mxedges_mxedge_id.md) |
| POST | /api/v1/sites/{site_id}/mxedges/{mxedge_id}/support | uploadSiteMxEdgeSupportFiles | uploadSiteMxEdgeSupportFiles | [POST_sites_site_id_mxedges_mxedge_id_support.md](sites/POST_sites_site_id_mxedges_mxedge_id_support.md) |

## Sites Network Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/networktemplates/derived | listSiteNetworkTemplatesDerived | listSiteNetworkTemplatesDerived | [GET_sites_site_id_networktemplates_derived.md](sites/GET_sites_site_id_networktemplates_derived.md) |

## Sites Networks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/networks/derived | listSiteNetworksDerived | listSiteNetworksDerived | [GET_sites_site_id_networks_derived.md](sites/GET_sites_site_id_networks_derived.md) |

## Sites Psks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/psks | listSitePsks | listSitePsks | [GET_sites_site_id_psks.md](sites/GET_sites_site_id_psks.md) |
| POST | /api/v1/sites/{site_id}/psks | createSitePsk | createSitePsk | [POST_sites_site_id_psks.md](sites/POST_sites_site_id_psks.md) |
| PUT | /api/v1/sites/{site_id}/psks | updateSiteMultiplePsks | updateSiteMultiplePsks | [PUT_sites_site_id_psks.md](sites/PUT_sites_site_id_psks.md) |
| POST | /api/v1/sites/{site_id}/psks/import | importSitePsks | importSitePsks | [POST_sites_site_id_psks_import.md](sites/POST_sites_site_id_psks_import.md) |
| GET | /api/v1/sites/{site_id}/psks/{psk_id} | getSitePsk | getSitePsk | [GET_sites_site_id_psks_psk_id.md](sites/GET_sites_site_id_psks_psk_id.md) |
| PUT | /api/v1/sites/{site_id}/psks/{psk_id} | updateSitePsk | updateSitePsk | [PUT_sites_site_id_psks_psk_id.md](sites/PUT_sites_site_id_psks_psk_id.md) |
| DELETE | /api/v1/sites/{site_id}/psks/{psk_id} | deleteSitePsk | deleteSitePsk | [DELETE_sites_site_id_psks_psk_id.md](sites/DELETE_sites_site_id_psks_psk_id.md) |

## Sites RF Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/rftemplates/derived | listSiteRfTemplatesDerived | listSiteRfTemplatesDerived | [GET_sites_site_id_rftemplates_derived.md](sites/GET_sites_site_id_rftemplates_derived.md) |

## Sites RRM

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/rrm/current | getSiteCurrentChannelPlanning | getSiteCurrentChannelPlanning | [GET_sites_site_id_rrm_current.md](sites/GET_sites_site_id_rrm_current.md) |
| GET | /api/v1/sites/{site_id}/rrm/current/devices/{device_id}/band/{band} | getSiteCurrentRrmConsiderations | getSiteCurrentRrmConsiderations | [GET_sites_site_id_rrm_current_devices_device_id_band_band.md](sites/GET_sites_site_id_rrm_current_devices_device_id_band_band.md) |
| GET | /api/v1/sites/{site_id}/rrm/events | listSiteRrmEvents | listSiteRrmEvents | [GET_sites_site_id_rrm_events.md](sites/GET_sites_site_id_rrm_events.md) |
| GET | /api/v1/sites/{site_id}/rrm/neighbors/band/{band} | listSiteCurrentRrmNeighbors | listSiteCurrentRrmNeighbors | [GET_sites_site_id_rrm_neighbors_band_band.md](sites/GET_sites_site_id_rrm_neighbors_band_band.md) |

## Sites RSSI Zones

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/rssizones | listSiteRssiZones | listSiteRssiZones | [GET_sites_site_id_rssizones.md](sites/GET_sites_site_id_rssizones.md) |
| POST | /api/v1/sites/{site_id}/rssizones | createSiteRssiZone | createSiteRssiZone | [POST_sites_site_id_rssizones.md](sites/POST_sites_site_id_rssizones.md) |
| GET | /api/v1/sites/{site_id}/rssizones/{rssizone_id} | getSiteRssiZone | getSiteRssiZone | [GET_sites_site_id_rssizones_rssizone_id.md](sites/GET_sites_site_id_rssizones_rssizone_id.md) |
| PUT | /api/v1/sites/{site_id}/rssizones/{rssizone_id} | updateSiteRssiZone | updateSiteRssiZone | [PUT_sites_site_id_rssizones_rssizone_id.md](sites/PUT_sites_site_id_rssizones_rssizone_id.md) |
| DELETE | /api/v1/sites/{site_id}/rssizones/{rssizone_id} | deleteSiteRssiZone | deleteSiteRssiZone | [DELETE_sites_site_id_rssizones_rssizone_id.md](sites/DELETE_sites_site_id_rssizones_rssizone_id.md) |

## Sites Rfdiags

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/rfdiags | getSiteSiteRfdiagRecording | getSiteSiteRfdiagRecording | [GET_sites_site_id_rfdiags.md](sites/GET_sites_site_id_rfdiags.md) |
| POST | /api/v1/sites/{site_id}/rfdiags | startSiteRecording | startSiteRecording | [POST_sites_site_id_rfdiags.md](sites/POST_sites_site_id_rfdiags.md) |
| GET | /api/v1/sites/{site_id}/rfdiags/{rfdiag_id} | getSiteRfdiagRecording | getSiteRfdiagRecording | [GET_sites_site_id_rfdiags_rfdiag_id.md](sites/GET_sites_site_id_rfdiags_rfdiag_id.md) |
| PUT | /api/v1/sites/{site_id}/rfdiags/{rfdiag_id} | updateSiteRfdiagRecording | updateSiteRfdiagRecording | [PUT_sites_site_id_rfdiags_rfdiag_id.md](sites/PUT_sites_site_id_rfdiags_rfdiag_id.md) |
| DELETE | /api/v1/sites/{site_id}/rfdiags/{rfdiag_id} | deleteSiteRfdiagRecording | deleteSiteRfdiagRecording | [DELETE_sites_site_id_rfdiags_rfdiag_id.md](sites/DELETE_sites_site_id_rfdiags_rfdiag_id.md) |
| GET | /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download | downloadSiteRfdiagRecording | downloadSiteRfdiagRecording | [GET_sites_site_id_rfdiags_rfdiag_id_download.md](sites/GET_sites_site_id_rfdiags_rfdiag_id_download.md) |
| POST | /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/stop | stopSiteRfdiagRecording | stopSiteRfdiagRecording | [POST_sites_site_id_rfdiags_rfdiag_id_stop.md](sites/POST_sites_site_id_rfdiags_rfdiag_id_stop.md) |

## Sites Rogues

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/insights/rogues | listSiteRogueAPs | listSiteRogueAPs | [GET_sites_site_id_insights_rogues.md](sites/GET_sites_site_id_insights_rogues.md) |
| GET | /api/v1/sites/{site_id}/insights/rogues/clients | listSiteRogueClients | listSiteRogueClients | [GET_sites_site_id_insights_rogues_clients.md](sites/GET_sites_site_id_insights_rogues_clients.md) |
| GET | /api/v1/sites/{site_id}/rogues/events/count | countSiteRogueEvents | countSiteRogueEvents | [GET_sites_site_id_rogues_events_count.md](sites/GET_sites_site_id_rogues_events_count.md) |
| GET | /api/v1/sites/{site_id}/rogues/events/search | searchSiteRogueEvents | searchSiteRogueEvents | [GET_sites_site_id_rogues_events_search.md](sites/GET_sites_site_id_rogues_events_search.md) |
| GET | /api/v1/sites/{site_id}/rogues/{rogue_bssid} | getSiteRogueAP | getSiteRogueAP | [GET_sites_site_id_rogues_rogue_bssid.md](sites/GET_sites_site_id_rogues_rogue_bssid.md) |

## Sites SLEs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary | getSiteSleClassifierDetails | getSiteSleClassifierDetails | [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend | getSiteSleClassifierSummaryTrend | getSiteSleClassifierSummaryTrend | [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary-trend.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary-trend.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifiers | listSiteSleMetricClassifiers | listSiteSleMetricClassifiers | [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/histogram | getSiteSleHistogram | getSiteSleHistogram | [GET_sites_site_id_sle_scope_scope_id_metric_metric_histogram.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_histogram.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impact-summary | getSiteSleImpactSummary | getSiteSleImpactSummary | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-applications | listSiteSleImpactedApplications | listSiteSleImpactedApplications | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-applications.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-applications.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-aps | listSiteSleImpactedAps | listSiteSleImpactedAps | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-aps.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-aps.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-chassis | listSiteSleImpactedChassis | listSiteSleImpactedChassis | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-chassis.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-chassis.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-clients | listSiteSleImpactedWiredClients | listSiteSleImpactedWiredClients | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-gateways | listSiteSleImpactedGateways | listSiteSleImpactedGateways | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-gateways.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-gateways.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-interfaces | listSiteSleImpactedInterfaces | listSiteSleImpactedInterfaces | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-interfaces.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-interfaces.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-switches | listSiteSleImpactedSwitches | listSiteSleImpactedSwitches | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-switches.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-switches.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-users | listSiteSleImpactedWirelessClients | listSiteSleImpactedWirelessClients | [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-users.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-users.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary | getSiteSleSummary | getSiteSleSummary | [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend | getSiteSleSummaryTrend | getSiteSleSummaryTrend | [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold | getSiteSleThreshold | getSiteSleThreshold | [GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) |
| POST | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold | replaceSiteSleThreshold | replaceSiteSleThreshold | [POST_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](sites/POST_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) |
| PUT | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold | updateSiteSleThreshold | updateSiteSleThreshold | [PUT_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](sites/PUT_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) |
| GET | /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metrics | listSiteSlesMetrics | listSiteSlesMetrics | [GET_sites_site_id_sle_scope_scope_id_metrics.md](sites/GET_sites_site_id_sle_scope_scope_id_metrics.md) |

## Sites SecIntel Profiles

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/secintelprofiles/derived | listSiteSecIntelProfilesDerived | listSiteSecIntelProfilesDerived | [GET_sites_site_id_secintelprofiles_derived.md](sites/GET_sites_site_id_secintelprofiles_derived.md) |

## Sites Service Policies

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/servicepolicies/derived | listSiteServicePoliciesDerived | listSiteServicePoliciesDerived | [GET_sites_site_id_servicepolicies_derived.md](sites/GET_sites_site_id_servicepolicies_derived.md) |

## Sites Services

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/services/derived | listSiteServicesDerived | listSiteServicesDerived | [GET_sites_site_id_services_derived.md](sites/GET_sites_site_id_services_derived.md) |
| GET | /api/v1/sites/{site_id}/services/events/count | countSiteServicePathEvents | countSiteServicePathEvents | [GET_sites_site_id_services_events_count.md](sites/GET_sites_site_id_services_events_count.md) |
| GET | /api/v1/sites/{site_id}/services/events/search | searchSiteServicePathEvents | searchSiteServicePathEvents | [GET_sites_site_id_services_events_search.md](sites/GET_sites_site_id_services_events_search.md) |

## Sites Setting

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/setting | getSiteSetting | getSiteSetting | [GET_sites_site_id_setting.md](sites/GET_sites_site_id_setting.md) |
| PUT | /api/v1/sites/{site_id}/setting | updateSiteSettings | updateSiteSettings | [PUT_sites_site_id_setting.md](sites/PUT_sites_site_id_setting.md) |
| POST | /api/v1/sites/{site_id}/setting/blacklist | createSiteWirelessClientsBlocklist | createSiteWirelessClientsBlocklist | [POST_sites_site_id_setting_blacklist.md](sites/POST_sites_site_id_setting_blacklist.md) |
| DELETE | /api/v1/sites/{site_id}/setting/blacklist | deleteSiteWirelessClientsBlocklist | deleteSiteWirelessClientsBlocklist | [DELETE_sites_site_id_setting_blacklist.md](sites/DELETE_sites_site_id_setting_blacklist.md) |
| GET | /api/v1/sites/{site_id}/setting/derived | getSiteSettingDerived | getSiteSettingDerived | [GET_sites_site_id_setting_derived.md](sites/GET_sites_site_id_setting_derived.md) |
| POST | /api/v1/sites/{site_id}/setting/watched_station | createSiteWatchedStations | createSiteWatchedStations | [POST_sites_site_id_setting_watched_station.md](sites/POST_sites_site_id_setting_watched_station.md) |
| DELETE | /api/v1/sites/{site_id}/setting/watched_station | deleteSiteWatchedStations | deleteSiteWatchedStations | [DELETE_sites_site_id_setting_watched_station.md](sites/DELETE_sites_site_id_setting_watched_station.md) |
| POST | /api/v1/sites/{site_id}/setting/whitelist | createSiteWirelessClientsAllowlist | createSiteWirelessClientsAllowlist | [POST_sites_site_id_setting_whitelist.md](sites/POST_sites_site_id_setting_whitelist.md) |
| DELETE | /api/v1/sites/{site_id}/setting/whitelist | deleteSiteWirelessClientsAllowlist | deleteSiteWirelessClientsAllowlist | [DELETE_sites_site_id_setting_whitelist.md](sites/DELETE_sites_site_id_setting_whitelist.md) |

## Sites Site Templates

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/sitetemplates/derived | listSiteSiteTemplatesDerived | listSiteSiteTemplatesDerived | [GET_sites_site_id_sitetemplates_derived.md](sites/GET_sites_site_id_sitetemplates_derived.md) |

## Sites Skyatp

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/skyatp/events/count | countSiteSkyatpEvents | countSiteSkyatpEvents | [GET_sites_site_id_skyatp_events_count.md](sites/GET_sites_site_id_skyatp_events_count.md) |
| GET | /api/v1/sites/{site_id}/skyatp/events/search | searchSiteSkyatpEvents | searchSiteSkyatpEvents | [GET_sites_site_id_skyatp_events_search.md](sites/GET_sites_site_id_skyatp_events_search.md) |

## Sites Spectrum Analysis

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/analyze_spectrum | getSiteRunningSpectrumAnalysis | getSiteRunningSpectrumAnalysis | [GET_sites_site_id_analyze_spectrum.md](sites/GET_sites_site_id_analyze_spectrum.md) |
| POST | /api/v1/sites/{site_id}/analyze_spectrum | initiateSiteAnalyzeSpectrum | initiateSiteAnalyzeSpectrum | [POST_sites_site_id_analyze_spectrum.md](sites/POST_sites_site_id_analyze_spectrum.md) |
| GET | /api/v1/sites/{site_id}/stats/analyze_spectrum | listSiteSpectrumAnalysis | listSiteSpectrumAnalysis | [GET_sites_site_id_stats_analyze_spectrum.md](sites/GET_sites_site_id_stats_analyze_spectrum.md) |

## Sites Stats

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats | getSiteStats | getSiteStats | [GET_sites_site_id_stats.md](sites/GET_sites_site_id_stats.md) |

## Sites Stats - Apps

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/apps/count | countSiteApps | countSiteApps | [GET_sites_site_id_stats_apps_count.md](sites/GET_sites_site_id_stats_apps_count.md) |

## Sites Stats - Assets

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/assets | listSiteAssetsStats | listSiteAssetsStats | [GET_sites_site_id_stats_assets.md](sites/GET_sites_site_id_stats_assets.md) |
| GET | /api/v1/sites/{site_id}/stats/assets/count | countSiteAssets | countSiteAssets | [GET_sites_site_id_stats_assets_count.md](sites/GET_sites_site_id_stats_assets_count.md) |
| GET | /api/v1/sites/{site_id}/stats/assets/search | searchSiteAssets | searchSiteAssets | [GET_sites_site_id_stats_assets_search.md](sites/GET_sites_site_id_stats_assets_search.md) |
| GET | /api/v1/sites/{site_id}/stats/assets/{asset_id} | getSiteAssetStats | getSiteAssetStats | [GET_sites_site_id_stats_assets_asset_id.md](sites/GET_sites_site_id_stats_assets_asset_id.md) |
| GET | /api/v1/sites/{site_id}/stats/discovered_assets | listSiteDiscoveredAssets | listSiteDiscoveredAssets | [GET_sites_site_id_stats_discovered_assets.md](sites/GET_sites_site_id_stats_discovered_assets.md) |
| GET | /api/v1/sites/{site_id}/stats/filtered_assets | getSiteAssetsOfInterest | getSiteAssetsOfInterest | [GET_sites_site_id_stats_filtered_assets.md](sites/GET_sites_site_id_stats_filtered_assets.md) |
| GET | /api/v1/sites/{site_id}/stats/maps/{map_id}/discovered_assets | getSiteDiscoveredAssetByMap | getSiteDiscoveredAssetByMap | [GET_sites_site_id_stats_maps_map_id_discovered_assets.md](sites/GET_sites_site_id_stats_maps_map_id_discovered_assets.md) |

## Sites Stats - BGP Peers

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/bgp_peers/count | countSiteBgpStats | countSiteBgpStats | [GET_sites_site_id_stats_bgp_peers_count.md](sites/GET_sites_site_id_stats_bgp_peers_count.md) |
| GET | /api/v1/sites/{site_id}/stats/bgp_peers/search | searchSiteBgpStats | searchSiteBgpStats | [GET_sites_site_id_stats_bgp_peers_search.md](sites/GET_sites_site_id_stats_bgp_peers_search.md) |

## Sites Stats - Beacons

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/beacons | listSiteBeaconsStats | listSiteBeaconsStats | [GET_sites_site_id_stats_beacons.md](sites/GET_sites_site_id_stats_beacons.md) |

## Sites Stats - Calls

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/calls/client/{client_mac}/troubleshoot | troubleshootSiteCall | troubleshootSiteCall | [GET_sites_site_id_stats_calls_client_client_mac_troubleshoot.md](sites/GET_sites_site_id_stats_calls_client_client_mac_troubleshoot.md) |
| GET | /api/v1/sites/{site_id}/stats/calls/count | countSiteCalls | countSiteCalls | [GET_sites_site_id_stats_calls_count.md](sites/GET_sites_site_id_stats_calls_count.md) |
| GET | /api/v1/sites/{site_id}/stats/calls/search | searchSiteCalls | searchSiteCalls | [GET_sites_site_id_stats_calls_search.md](sites/GET_sites_site_id_stats_calls_search.md) |
| GET | /api/v1/sites/{site_id}/stats/calls/summary | getSiteCallsSummary | getSiteCallsSummary | [GET_sites_site_id_stats_calls_summary.md](sites/GET_sites_site_id_stats_calls_summary.md) |
| GET | /api/v1/sites/{site_id}/stats/calls/troubleshoot | listSiteTroubleshootCalls | listSiteTroubleshootCalls | [GET_sites_site_id_stats_calls_troubleshoot.md](sites/GET_sites_site_id_stats_calls_troubleshoot.md) |

## Sites Stats - Clients SDK

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/maps/{map_id}/sdkclients | getSiteSdkStatsByMap | getSiteSdkStatsByMap | [GET_sites_site_id_stats_maps_map_id_sdkclients.md](sites/GET_sites_site_id_stats_maps_map_id_sdkclients.md) |
| GET | /api/v1/sites/{site_id}/stats/sdkclients/{sdkclient_id} | getSiteSdkStats | getSiteSdkStats | [GET_sites_site_id_stats_sdkclients_sdkclient_id.md](sites/GET_sites_site_id_stats_sdkclients_sdkclient_id.md) |

## Sites Stats - Clients Wireless

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/clients | listSiteWirelessClientsStats | listSiteWirelessClientsStats | [GET_sites_site_id_stats_clients.md](sites/GET_sites_site_id_stats_clients.md) |
| GET | /api/v1/sites/{site_id}/stats/clients/{client_mac} | getSiteWirelessClientStats | getSiteWirelessClientStats | [GET_sites_site_id_stats_clients_client_mac.md](sites/GET_sites_site_id_stats_clients_client_mac.md) |
| GET | /api/v1/sites/{site_id}/stats/maps/{map_id}/clients | getSiteWirelessClientsStatsByMap | getSiteWirelessClientsStatsByMap | [GET_sites_site_id_stats_maps_map_id_clients.md](sites/GET_sites_site_id_stats_maps_map_id_clients.md) |
| GET | /api/v1/sites/{site_id}/stats/maps/{map_id}/unconnected_clients | listSiteUnconnectedClientStats | listSiteUnconnectedClientStats | [GET_sites_site_id_stats_maps_map_id_unconnected_clients.md](sites/GET_sites_site_id_stats_maps_map_id_unconnected_clients.md) |

## Sites Stats - Devices

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/devices | listSiteDevicesStats | listSiteDevicesStats | [GET_sites_site_id_stats_devices.md](sites/GET_sites_site_id_stats_devices.md) |
| GET | /api/v1/sites/{site_id}/stats/devices/{device_id} | getSiteDeviceStats | getSiteDeviceStats | [GET_sites_site_id_stats_devices_device_id.md](sites/GET_sites_site_id_stats_devices_device_id.md) |
| GET | /api/v1/sites/{site_id}/stats/devices/{device_id}/clients | getSiteAllClientsStatsByDevice | getSiteAllClientsStatsByDevice | [GET_sites_site_id_stats_devices_device_id_clients.md](sites/GET_sites_site_id_stats_devices_device_id_clients.md) |
| GET | /api/v1/sites/{site_id}/stats/gateways/metrics | getSiteGatewayMetrics | getSiteGatewayMetrics | [GET_sites_site_id_stats_gateways_metrics.md](sites/GET_sites_site_id_stats_gateways_metrics.md) |
| GET | /api/v1/sites/{site_id}/stats/switches/metrics | getSiteSwitchesMetrics | getSiteSwitchesMetrics | [GET_sites_site_id_stats_switches_metrics.md](sites/GET_sites_site_id_stats_switches_metrics.md) |

## Sites Stats - Discovered Switches

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/discovered_switch_metrics/search | searchSiteDiscoveredSwitchesMetrics | searchSiteDiscoveredSwitchesMetrics | [GET_sites_site_id_stats_discovered_switch_metrics_search.md](sites/GET_sites_site_id_stats_discovered_switch_metrics_search.md) |
| GET | /api/v1/sites/{site_id}/stats/discovered_switches/count | countSiteDiscoveredSwitches | countSiteDiscoveredSwitches | [GET_sites_site_id_stats_discovered_switches_count.md](sites/GET_sites_site_id_stats_discovered_switches_count.md) |
| GET | /api/v1/sites/{site_id}/stats/discovered_switches/metrics | listSiteDiscoveredSwitchesMetrics | listSiteDiscoveredSwitchesMetrics | [GET_sites_site_id_stats_discovered_switches_metrics.md](sites/GET_sites_site_id_stats_discovered_switches_metrics.md) |
| GET | /api/v1/sites/{site_id}/stats/discovered_switches/search | searchSiteDiscoveredSwitches | searchSiteDiscoveredSwitches | [GET_sites_site_id_stats_discovered_switches_search.md](sites/GET_sites_site_id_stats_discovered_switches_search.md) |

## Sites Stats - MxEdges

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/mxedges | listSiteMxEdgesStats | listSiteMxEdgesStats | [GET_sites_site_id_stats_mxedges.md](sites/GET_sites_site_id_stats_mxedges.md) |
| GET | /api/v1/sites/{site_id}/stats/mxedges/{mxedge_id} | getSiteMxEdgeStats | getSiteMxEdgeStats | [GET_sites_site_id_stats_mxedges_mxedge_id.md](sites/GET_sites_site_id_stats_mxedges_mxedge_id.md) |

## Sites Stats - Ospf

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/ospf_peers/count | countSiteOspfStats | countSiteOspfStats | [GET_sites_site_id_stats_ospf_peers_count.md](sites/GET_sites_site_id_stats_ospf_peers_count.md) |
| GET | /api/v1/sites/{site_id}/stats/ospf_peers/search | searchSiteOspfStats | searchSiteOspfStats | [GET_sites_site_id_stats_ospf_peers_search.md](sites/GET_sites_site_id_stats_ospf_peers_search.md) |

## Sites Stats - Ports

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/ports/count | countSiteSwOrGwPorts | countSiteSwOrGwPorts | [GET_sites_site_id_stats_ports_count.md](sites/GET_sites_site_id_stats_ports_count.md) |
| GET | /api/v1/sites/{site_id}/stats/ports/search | searchSiteSwOrGwPorts | searchSiteSwOrGwPorts | [GET_sites_site_id_stats_ports_search.md](sites/GET_sites_site_id_stats_ports_search.md) |

## Sites Stats - WxRules

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/wxrules | getSiteWxRulesUsage | getSiteWxRulesUsage | [GET_sites_site_id_stats_wxrules.md](sites/GET_sites_site_id_stats_wxrules.md) |

## Sites Stats - Zones

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/stats/rssizones | listSiteRssiZonesStats | listSiteRssiZonesStats | [GET_sites_site_id_stats_rssizones.md](sites/GET_sites_site_id_stats_rssizones.md) |
| GET | /api/v1/sites/{site_id}/stats/rssizones/{zone_id} | getSiteRssiZoneStats | getSiteRssiZoneStats | [GET_sites_site_id_stats_rssizones_zone_id.md](sites/GET_sites_site_id_stats_rssizones_zone_id.md) |
| GET | /api/v1/sites/{site_id}/stats/zones | listSiteZonesStats | listSiteZonesStats | [GET_sites_site_id_stats_zones.md](sites/GET_sites_site_id_stats_zones.md) |
| GET | /api/v1/sites/{site_id}/stats/zones/{zone_id} | getSiteZoneStats | getSiteZoneStats | [GET_sites_site_id_stats_zones_zone_id.md](sites/GET_sites_site_id_stats_zones_zone_id.md) |

## Sites Synthetic Tests

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/devices/{device_id}/check_radius_server | startSiteSwitchRadiusSyntheticTest | startSiteSwitchRadiusSyntheticTest | [POST_sites_site_id_devices_device_id_check_radius_server.md](sites/POST_sites_site_id_devices_device_id_check_radius_server.md) |
| GET | /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test | getSiteDeviceSyntheticTest | getSiteDeviceSyntheticTest | [GET_sites_site_id_devices_device_id_synthetic_test.md](sites/GET_sites_site_id_devices_device_id_synthetic_test.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test | triggerSiteDeviceSyntheticTest | triggerSiteDeviceSyntheticTest | [POST_sites_site_id_devices_device_id_synthetic_test.md](sites/POST_sites_site_id_devices_device_id_synthetic_test.md) |
| POST | /api/v1/sites/{site_id}/synthetic_test | triggerSiteSyntheticTest | triggerSiteSyntheticTest | [POST_sites_site_id_synthetic_test.md](sites/POST_sites_site_id_synthetic_test.md) |
| GET | /api/v1/sites/{site_id}/synthetic_test/search | searchSiteSyntheticTest | searchSiteSyntheticTest | [GET_sites_site_id_synthetic_test_search.md](sites/GET_sites_site_id_synthetic_test_search.md) |

## Sites UI Settings

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/uisettings | listSiteUiSettings | listSiteUiSettings | [GET_sites_site_id_uisettings.md](sites/GET_sites_site_id_uisettings.md) |
| POST | /api/v1/sites/{site_id}/uisettings | createSiteUiSettings | createSiteUiSettings | [POST_sites_site_id_uisettings.md](sites/POST_sites_site_id_uisettings.md) |
| GET | /api/v1/sites/{site_id}/uisettings/derived | listSiteUiSettingDerived | listSiteUiSettingDerived | [GET_sites_site_id_uisettings_derived.md](sites/GET_sites_site_id_uisettings_derived.md) |
| GET | /api/v1/sites/{site_id}/uisettings/{uisetting_id} | getSiteUiSetting | getSiteUiSetting | [GET_sites_site_id_uisettings_uisetting_id.md](sites/GET_sites_site_id_uisettings_uisetting_id.md) |
| POST | /api/v1/sites/{site_id}/uisettings/{uisetting_id} | updateSiteUiSetting | updateSiteUiSetting | [POST_sites_site_id_uisettings_uisetting_id.md](sites/POST_sites_site_id_uisettings_uisetting_id.md) |
| DELETE | /api/v1/sites/{site_id}/uisettings/{uisetting_id} | deleteSiteUiSetting | deleteSiteUiSetting | [DELETE_sites_site_id_uisettings_uisetting_id.md](sites/DELETE_sites_site_id_uisettings_uisetting_id.md) |

## Sites VPNs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/vpns/derived | listSiteVpnsDerived | listSiteVpnsDerived | [GET_sites_site_id_vpns_derived.md](sites/GET_sites_site_id_vpns_derived.md) |

## Sites WAN Usages

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wan_usages/count | countSiteWanUsage | countSiteWanUsage | [GET_sites_site_id_wan_usages_count.md](sites/GET_sites_site_id_wan_usages_count.md) |
| GET | /api/v1/sites/{site_id}/wan_usages/search | searchSiteWanUsage | searchSiteWanUsage | [GET_sites_site_id_wan_usages_search.md](sites/GET_sites_site_id_wan_usages_search.md) |

## Sites Webhooks

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/webhooks | listSiteWebhooks | listSiteWebhooks | [GET_sites_site_id_webhooks.md](sites/GET_sites_site_id_webhooks.md) |
| POST | /api/v1/sites/{site_id}/webhooks | createSiteWebhook | createSiteWebhook | [POST_sites_site_id_webhooks.md](sites/POST_sites_site_id_webhooks.md) |
| GET | /api/v1/sites/{site_id}/webhooks/{webhook_id} | getSiteWebhook | getSiteWebhook | [GET_sites_site_id_webhooks_webhook_id.md](sites/GET_sites_site_id_webhooks_webhook_id.md) |
| PUT | /api/v1/sites/{site_id}/webhooks/{webhook_id} | updateSiteWebhook | updateSiteWebhook | [PUT_sites_site_id_webhooks_webhook_id.md](sites/PUT_sites_site_id_webhooks_webhook_id.md) |
| DELETE | /api/v1/sites/{site_id}/webhooks/{webhook_id} | deleteSiteWebhook | deleteSiteWebhook | [DELETE_sites_site_id_webhooks_webhook_id.md](sites/DELETE_sites_site_id_webhooks_webhook_id.md) |
| GET | /api/v1/sites/{site_id}/webhooks/{webhook_id}/events/count | countSiteWebhooksDeliveries | countSiteWebhooksDeliveries | [GET_sites_site_id_webhooks_webhook_id_events_count.md](sites/GET_sites_site_id_webhooks_webhook_id_events_count.md) |
| GET | /api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search | searchSiteWebhooksDeliveries | searchSiteWebhooksDeliveries | [GET_sites_site_id_webhooks_webhook_id_events_search.md](sites/GET_sites_site_id_webhooks_webhook_id_events_search.md) |
| POST | /api/v1/sites/{site_id}/webhooks/{webhook_id}/ping | pingSiteWebhook | pingSiteWebhook | [POST_sites_site_id_webhooks_webhook_id_ping.md](sites/POST_sites_site_id_webhooks_webhook_id_ping.md) |

## Sites Wlans

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wlans | listSiteWlans | listSiteWlans | [GET_sites_site_id_wlans.md](sites/GET_sites_site_id_wlans.md) |
| POST | /api/v1/sites/{site_id}/wlans | createSiteWlan | createSiteWlan | [POST_sites_site_id_wlans.md](sites/POST_sites_site_id_wlans.md) |
| GET | /api/v1/sites/{site_id}/wlans/derived | listSiteWlansDerived | listSiteWlansDerived | [GET_sites_site_id_wlans_derived.md](sites/GET_sites_site_id_wlans_derived.md) |
| GET | /api/v1/sites/{site_id}/wlans/{wlan_id} | getSiteWlan | getSiteWlan | [GET_sites_site_id_wlans_wlan_id.md](sites/GET_sites_site_id_wlans_wlan_id.md) |
| PUT | /api/v1/sites/{site_id}/wlans/{wlan_id} | updateSiteWlan | updateSiteWlan | [PUT_sites_site_id_wlans_wlan_id.md](sites/PUT_sites_site_id_wlans_wlan_id.md) |
| DELETE | /api/v1/sites/{site_id}/wlans/{wlan_id} | deleteSiteWlan | deleteSiteWlan | [DELETE_sites_site_id_wlans_wlan_id.md](sites/DELETE_sites_site_id_wlans_wlan_id.md) |
| POST | /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_image | uploadSiteWlanPortalImage | uploadSiteWlanPortalImage | [POST_sites_site_id_wlans_wlan_id_portal_image.md](sites/POST_sites_site_id_wlans_wlan_id_portal_image.md) |
| DELETE | /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_image | deleteSiteWlanPortalImage | deleteSiteWlanPortalImage | [DELETE_sites_site_id_wlans_wlan_id_portal_image.md](sites/DELETE_sites_site_id_wlans_wlan_id_portal_image.md) |
| PUT | /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_template | updateSiteWlanPortalTemplate | updateSiteWlanPortalTemplate | [PUT_sites_site_id_wlans_wlan_id_portal_template.md](sites/PUT_sites_site_id_wlans_wlan_id_portal_template.md) |

## Sites WxRules

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wxrules | listSiteWxRules | listSiteWxRules | [GET_sites_site_id_wxrules.md](sites/GET_sites_site_id_wxrules.md) |
| POST | /api/v1/sites/{site_id}/wxrules | createSiteWxRule | createSiteWxRule | [POST_sites_site_id_wxrules.md](sites/POST_sites_site_id_wxrules.md) |
| GET | /api/v1/sites/{site_id}/wxrules/derived | ListSiteWxRulesDerived | ListSiteWxRulesDerived | [GET_sites_site_id_wxrules_derived.md](sites/GET_sites_site_id_wxrules_derived.md) |
| GET | /api/v1/sites/{site_id}/wxrules/{wxrule_id} | getSiteWxRule | getSiteWxRule | [GET_sites_site_id_wxrules_wxrule_id.md](sites/GET_sites_site_id_wxrules_wxrule_id.md) |
| PUT | /api/v1/sites/{site_id}/wxrules/{wxrule_id} | updateSiteWxRule | updateSiteWxRule | [PUT_sites_site_id_wxrules_wxrule_id.md](sites/PUT_sites_site_id_wxrules_wxrule_id.md) |
| DELETE | /api/v1/sites/{site_id}/wxrules/{wxrule_id} | deleteSiteWxRule | deleteSiteWxRule | [DELETE_sites_site_id_wxrules_wxrule_id.md](sites/DELETE_sites_site_id_wxrules_wxrule_id.md) |

## Sites WxTags

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wxtags | listSiteWxTags | listSiteWxTags | [GET_sites_site_id_wxtags.md](sites/GET_sites_site_id_wxtags.md) |
| POST | /api/v1/sites/{site_id}/wxtags | createSiteWxTag | createSiteWxTag | [POST_sites_site_id_wxtags.md](sites/POST_sites_site_id_wxtags.md) |
| GET | /api/v1/sites/{site_id}/wxtags/apps | getSiteApplicationList | getSiteApplicationList | [GET_sites_site_id_wxtags_apps.md](sites/GET_sites_site_id_wxtags_apps.md) |
| GET | /api/v1/sites/{site_id}/wxtags/{wxtag_id} | getSiteWxTag | getSiteWxTag | [GET_sites_site_id_wxtags_wxtag_id.md](sites/GET_sites_site_id_wxtags_wxtag_id.md) |
| PUT | /api/v1/sites/{site_id}/wxtags/{wxtag_id} | updateSiteWxTag | updateSiteWxTag | [PUT_sites_site_id_wxtags_wxtag_id.md](sites/PUT_sites_site_id_wxtags_wxtag_id.md) |
| DELETE | /api/v1/sites/{site_id}/wxtags/{wxtag_id} | deleteSiteWxTag | deleteSiteWxTag | [DELETE_sites_site_id_wxtags_wxtag_id.md](sites/DELETE_sites_site_id_wxtags_wxtag_id.md) |

## Sites WxTunnels

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/wxtunnels | listSiteWxTunnels | listSiteWxTunnels | [GET_sites_site_id_wxtunnels.md](sites/GET_sites_site_id_wxtunnels.md) |
| POST | /api/v1/sites/{site_id}/wxtunnels | createSiteWxTunnel | createSiteWxTunnel | [POST_sites_site_id_wxtunnels.md](sites/POST_sites_site_id_wxtunnels.md) |
| GET | /api/v1/sites/{site_id}/wxtunnels/{wxtunnel_id} | getSiteWxTunnel | getSiteWxTunnel | [GET_sites_site_id_wxtunnels_wxtunnel_id.md](sites/GET_sites_site_id_wxtunnels_wxtunnel_id.md) |
| PUT | /api/v1/sites/{site_id}/wxtunnels/{wxtunnel_id} | updateSiteWxTunnel | updateSiteWxTunnel | [PUT_sites_site_id_wxtunnels_wxtunnel_id.md](sites/PUT_sites_site_id_wxtunnels_wxtunnel_id.md) |
| DELETE | /api/v1/sites/{site_id}/wxtunnels/{wxtunnel_id} | deleteSiteWxTunnel | deleteSiteWxTunnel | [DELETE_sites_site_id_wxtunnels_wxtunnel_id.md](sites/DELETE_sites_site_id_wxtunnels_wxtunnel_id.md) |

## Sites Zones

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/zones | listSiteZones | listSiteZones | [GET_sites_site_id_zones.md](sites/GET_sites_site_id_zones.md) |
| POST | /api/v1/sites/{site_id}/zones | createSiteZone | createSiteZone | [POST_sites_site_id_zones.md](sites/POST_sites_site_id_zones.md) |
| GET | /api/v1/sites/{site_id}/zones/{zone_id} | getSiteZone | getSiteZone | [GET_sites_site_id_zones_zone_id.md](sites/GET_sites_site_id_zones_zone_id.md) |
| PUT | /api/v1/sites/{site_id}/zones/{zone_id} | updateSiteZone | updateSiteZone | [PUT_sites_site_id_zones_zone_id.md](sites/PUT_sites_site_id_zones_zone_id.md) |
| DELETE | /api/v1/sites/{site_id}/zones/{zone_id} | deleteSiteZone | deleteSiteZone | [DELETE_sites_site_id_zones_zone_id.md](sites/DELETE_sites_site_id_zones_zone_id.md) |
| GET | /api/v1/sites/{site_id}/{zone_type}/count | countSiteZoneSessions | countSiteZoneSessions | [GET_sites_site_id_zone_type_count.md](sites/GET_sites_site_id_zone_type_count.md) |
| GET | /api/v1/sites/{site_id}/{zone_type}/visits/search | searchSiteZoneSessions | searchSiteZoneSessions | [GET_sites_site_id_zone_type_visits_search.md](sites/GET_sites_site_id_zone_type_visits_search.md) |

## Sites vBeacons

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/sites/{site_id}/vbeacons | listSiteVBeacons | listSiteVBeacons | [GET_sites_site_id_vbeacons.md](sites/GET_sites_site_id_vbeacons.md) |
| POST | /api/v1/sites/{site_id}/vbeacons | createSiteVBeacon | createSiteVBeacon | [POST_sites_site_id_vbeacons.md](sites/POST_sites_site_id_vbeacons.md) |
| GET | /api/v1/sites/{site_id}/vbeacons/{vbeacon_id} | getSiteVBeacon | getSiteVBeacon | [GET_sites_site_id_vbeacons_vbeacon_id.md](sites/GET_sites_site_id_vbeacons_vbeacon_id.md) |
| PUT | /api/v1/sites/{site_id}/vbeacons/{vbeacon_id} | updateSiteVBeacon | updateSiteVBeacon | [PUT_sites_site_id_vbeacons_vbeacon_id.md](sites/PUT_sites_site_id_vbeacons_vbeacon_id.md) |
| DELETE | /api/v1/sites/{site_id}/vbeacons/{vbeacon_id} | deleteSiteVBeacon | deleteSiteVBeacon | [DELETE_sites_site_id_vbeacons_vbeacon_id.md](sites/DELETE_sites_site_id_vbeacons_vbeacon_id.md) |

## Utilities Common

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/devices/restart | restartSiteMultipleDevices | restartSiteMultipleDevices | [POST_sites_site_id_devices_restart.md](utilities/POST_sites_site_id_devices_restart.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/arp | arpFromDevice | arpFromDevice | [POST_sites_site_id_devices_device_id_arp.md](utilities/POST_sites_site_id_devices_device_id_arp.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/bounce_port | bounceDevicePort | bounceDevicePort | [POST_sites_site_id_devices_device_id_bounce_port.md](utilities/POST_sites_site_id_devices_device_id_bounce_port.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_mac_table | clearSiteDeviceMacTable | clearSiteDeviceMacTable | [POST_sites_site_id_devices_device_id_clear_mac_table.md](utilities/POST_sites_site_id_devices_device_id_clear_mac_table.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_policy_hit_count | clearSiteDevicePolicyHitCount | clearSiteDevicePolicyHitCount | [POST_sites_site_id_devices_device_id_clear_policy_hit_count.md](utilities/POST_sites_site_id_devices_device_id_clear_policy_hit_count.md) |
| GET | /api/v1/sites/{site_id}/devices/{device_id}/config_cmd | getSiteDeviceConfigCmd | getSiteDeviceConfigCmd | [GET_sites_site_id_devices_device_id_config_cmd.md](utilities/GET_sites_site_id_devices_device_id_config_cmd.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/locate | startSiteLocateDevice | startSiteLocateDevice | [POST_sites_site_id_devices_device_id_locate.md](utilities/POST_sites_site_id_devices_device_id_locate.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/monitor_traffic | monitorSiteDeviceTraffic | monitorSiteDeviceTraffic | [POST_sites_site_id_devices_device_id_monitor_traffic.md](utilities/POST_sites_site_id_devices_device_id_monitor_traffic.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/ping | pingFromDevice | pingFromDevice | [POST_sites_site_id_devices_device_id_ping.md](utilities/POST_sites_site_id_devices_device_id_ping.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/readopt | readoptSiteOctermDevice | readoptSiteOctermDevice | [POST_sites_site_id_devices_device_id_readopt.md](utilities/POST_sites_site_id_devices_device_id_readopt.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/release_dhcp_leases | releaseSiteDeviceDhcpLease | releaseSiteDeviceDhcpLease | [POST_sites_site_id_devices_device_id_release_dhcp_leases.md](utilities/POST_sites_site_id_devices_device_id_release_dhcp_leases.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/reprovision | reprovisionSiteOctermDevice | reprovisionSiteOctermDevice | [POST_sites_site_id_devices_device_id_reprovision.md](utilities/POST_sites_site_id_devices_device_id_reprovision.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/request_ztp_password | getSiteDeviceZtpPassword | getSiteDeviceZtpPassword | [POST_sites_site_id_devices_device_id_request_ztp_password.md](utilities/POST_sites_site_id_devices_device_id_request_ztp_password.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/restart | restartSiteDevice | restartSiteDevice | [POST_sites_site_id_devices_device_id_restart.md](utilities/POST_sites_site_id_devices_device_id_restart.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/shell | createSiteDeviceShellSession | createSiteDeviceShellSession | [POST_sites_site_id_devices_device_id_shell.md](utilities/POST_sites_site_id_devices_device_id_shell.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_arp | showSiteDeviceArpTable | showSiteDeviceArpTable | [POST_sites_site_id_devices_device_id_show_arp.md](utilities/POST_sites_site_id_devices_device_id_show_arp.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_bgp_summary | showSiteDeviceBgpSummary | showSiteDeviceBgpSummary | [POST_sites_site_id_devices_device_id_show_bgp_summary.md](utilities/POST_sites_site_id_devices_device_id_show_bgp_summary.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_dhcp_leases | showSiteDeviceDhcpLeases | showSiteDeviceDhcpLeases | [POST_sites_site_id_devices_device_id_show_dhcp_leases.md](utilities/POST_sites_site_id_devices_device_id_show_dhcp_leases.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_dot1x | showSiteDeviceDot1xTable | showSiteDeviceDot1xTable | [POST_sites_site_id_devices_device_id_show_dot1x.md](utilities/POST_sites_site_id_devices_device_id_show_dot1x.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_evpn_database | showSiteDeviceEvpnDatabase | showSiteDeviceEvpnDatabase | [POST_sites_site_id_devices_device_id_show_evpn_database.md](utilities/POST_sites_site_id_devices_device_id_show_evpn_database.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_forwarding_table | showSiteDeviceForwardingTable | showSiteDeviceForwardingTable | [POST_sites_site_id_devices_device_id_show_forwarding_table.md](utilities/POST_sites_site_id_devices_device_id_show_forwarding_table.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_mac_table | showSiteDeviceMacTable | showSiteDeviceMacTable | [POST_sites_site_id_devices_device_id_show_mac_table.md](utilities/POST_sites_site_id_devices_device_id_show_mac_table.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/support | uploadSiteDeviceSupportFile | uploadSiteDeviceSupportFile | [POST_sites_site_id_devices_device_id_support.md](utilities/POST_sites_site_id_devices_device_id_support.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/traceroute | tracerouteFromDevice | tracerouteFromDevice | [POST_sites_site_id_devices_device_id_traceroute.md](utilities/POST_sites_site_id_devices_device_id_traceroute.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/unlocate | stopSiteLocateDevice | stopSiteLocateDevice | [POST_sites_site_id_devices_device_id_unlocate.md](utilities/POST_sites_site_id_devices_device_id_unlocate.md) |

## Utilities LAN

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/wired_clients/{client_mac}/coa | reauthOrgDot1xWiredClient | reauthOrgDot1xWiredClient | [POST_orgs_org_id_wired_clients_client_mac_coa.md](utilities/POST_orgs_org_id_wired_clients_client_mac_coa.md) |
| POST | /api/v1/sites/{site_id}/devices/clear_pending_version | clearSiteMultipleDevicePendingVersion | clearSiteMultipleDevicePendingVersion | [POST_sites_site_id_devices_clear_pending_version.md](utilities/POST_sites_site_id_devices_clear_pending_version.md) |
| POST | /api/v1/sites/{site_id}/devices/restore_backup_version | restoreSiteMultipleDeviceBackupVersion | restoreSiteMultipleDeviceBackupVersion | [POST_sites_site_id_devices_restore_backup_version.md](utilities/POST_sites_site_id_devices_restore_backup_version.md) |
| POST | /api/v1/sites/{site_id}/devices/upgrade_bios | upgradeSiteDevicesBios | upgradeSiteDevicesBios | [POST_sites_site_id_devices_upgrade_bios.md](utilities/POST_sites_site_id_devices_upgrade_bios.md) |
| POST | /api/v1/sites/{site_id}/devices/upgrade_fpga | upgradeSiteDevicesFpga | upgradeSiteDevicesFpga | [POST_sites_site_id_devices_upgrade_fpga.md](utilities/POST_sites_site_id_devices_upgrade_fpga.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/cable_test | cableTestFromSwitch | cableTestFromSwitch | [POST_sites_site_id_devices_device_id_cable_test.md](utilities/POST_sites_site_id_devices_device_id_cable_test.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_bpdu_error | clearBpduErrorsFromPortsOnSwitch | clearBpduErrorsFromPortsOnSwitch | [POST_sites_site_id_devices_device_id_clear_bpdu_error.md](utilities/POST_sites_site_id_devices_device_id_clear_bpdu_error.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_dot1x | clearSiteDeviceDot1xSession | clearSiteDeviceDot1xSession | [POST_sites_site_id_devices_device_id_clear_dot1x.md](utilities/POST_sites_site_id_devices_device_id_clear_dot1x.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_macs | clearAllLearnedMacsFromPortOnSwitch | clearAllLearnedMacsFromPortOnSwitch | [POST_sites_site_id_devices_device_id_clear_macs.md](utilities/POST_sites_site_id_devices_device_id_clear_macs.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_pending_version | clearSiteDevicePendingVersion | clearSiteDevicePendingVersion | [POST_sites_site_id_devices_device_id_clear_pending_version.md](utilities/POST_sites_site_id_devices_device_id_clear_pending_version.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/poll_stats | pollSiteSwitchStats | pollSiteSwitchStats | [POST_sites_site_id_devices_device_id_poll_stats.md](utilities/POST_sites_site_id_devices_device_id_poll_stats.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/restore_backup_version | restoreSiteDeviceBackupVersion | restoreSiteDeviceBackupVersion | [POST_sites_site_id_devices_device_id_restore_backup_version.md](utilities/POST_sites_site_id_devices_device_id_restore_backup_version.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/snapshot | createSiteDeviceSnapshot | createSiteDeviceSnapshot | [POST_sites_site_id_devices_device_id_snapshot.md](utilities/POST_sites_site_id_devices_device_id_snapshot.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/upgrade_bios | upgradeDeviceBios | upgradeDeviceBios | [POST_sites_site_id_devices_device_id_upgrade_bios.md](utilities/POST_sites_site_id_devices_device_id_upgrade_bios.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/upgrade_fpga | upgradeDeviceFPGA | upgradeDeviceFPGA | [POST_sites_site_id_devices_device_id_upgrade_fpga.md](utilities/POST_sites_site_id_devices_device_id_upgrade_fpga.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/vc/switch_master | toogleSiteDeviceVcRoutingEnginesRole | toogleSiteDeviceVcRoutingEnginesRole | [POST_sites_site_id_devices_device_id_vc_switch_master.md](utilities/POST_sites_site_id_devices_device_id_vc_switch_master.md) |
| POST | /api/v1/sites/{site_id}/wired_clients/{client_mac}/coa | reauthSiteDot1xWiredClient | reauthSiteDot1xWiredClient | [POST_sites_site_id_wired_clients_client_mac_coa.md](utilities/POST_sites_site_id_wired_clients_client_mac_coa.md) |

## Utilities Location

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/devices/send_ble_beacon | sendSiteDevicesArbitraryBleBeacon | sendSiteDevicesArbitraryBleBeacon | [POST_sites_site_id_devices_send_ble_beacon.md](utilities/POST_sites_site_id_devices_send_ble_beacon.md) |

## Utilities MxEdge

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/mxtunnels/{mxtunnel_id}/preempt_aps | preemptSitesMxTunnel | preemptSitesMxTunnel | [POST_sites_site_id_mxtunnels_mxtunnel_id_preempt_aps.md](utilities/POST_sites_site_id_mxtunnels_mxtunnel_id_preempt_aps.md) |

## Utilities PCAPs

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/pcaps | listOrgPacketCaptures | listOrgPacketCaptures | [GET_orgs_org_id_pcaps.md](utilities/GET_orgs_org_id_pcaps.md) |
| GET | /api/v1/orgs/{org_id}/pcaps/capture | getOrgCapturingStatus | getOrgCapturingStatus | [GET_orgs_org_id_pcaps_capture.md](utilities/GET_orgs_org_id_pcaps_capture.md) |
| POST | /api/v1/orgs/{org_id}/pcaps/capture | startOrgPacketCapture | startOrgPacketCapture | [POST_orgs_org_id_pcaps_capture.md](utilities/POST_orgs_org_id_pcaps_capture.md) |
| DELETE | /api/v1/orgs/{org_id}/pcaps/capture | stopOrgPacketCapture | stopOrgPacketCapture | [DELETE_orgs_org_id_pcaps_capture.md](utilities/DELETE_orgs_org_id_pcaps_capture.md) |
| GET | /api/v1/sites/{site_id}/pcaps | listSitePacketCaptures | listSitePacketCaptures | [GET_sites_site_id_pcaps.md](utilities/GET_sites_site_id_pcaps.md) |
| GET | /api/v1/sites/{site_id}/pcaps/capture | getSiteCapturingStatus | getSiteCapturingStatus | [GET_sites_site_id_pcaps_capture.md](utilities/GET_sites_site_id_pcaps_capture.md) |
| POST | /api/v1/sites/{site_id}/pcaps/capture | startSitePacketCapture | startSitePacketCapture | [POST_sites_site_id_pcaps_capture.md](utilities/POST_sites_site_id_pcaps_capture.md) |
| DELETE | /api/v1/sites/{site_id}/pcaps/capture | stopSitePacketCapture | stopSitePacketCapture | [DELETE_sites_site_id_pcaps_capture.md](utilities/DELETE_sites_site_id_pcaps_capture.md) |
| PUT | /api/v1/sites/{site_id}/pcaps/{pcap_id} | updateSitePacketCapture | updateSitePacketCapture | [PUT_sites_site_id_pcaps_pcap_id.md](utilities/PUT_sites_site_id_pcaps_pcap_id.md) |

## Utilities Upgrade

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| GET | /api/v1/orgs/{org_id}/devices/upgrade | listOrgDeviceUpgrades | listOrgDeviceUpgrades | [GET_orgs_org_id_devices_upgrade.md](utilities/GET_orgs_org_id_devices_upgrade.md) |
| POST | /api/v1/orgs/{org_id}/devices/upgrade | upgradeOrgDevices | upgradeOrgDevices | [POST_orgs_org_id_devices_upgrade.md](utilities/POST_orgs_org_id_devices_upgrade.md) |
| GET | /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id} | getOrgDeviceUpgrade | getOrgDeviceUpgrade | [GET_orgs_org_id_devices_upgrade_upgrade_id.md](utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md) |
| POST | /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel | cancelOrgDeviceUpgrade | cancelOrgDeviceUpgrade | [POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md](utilities/POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md) |
| GET | /api/v1/orgs/{org_id}/devices/versions | listOrgAvailableDeviceVersions | listOrgAvailableDeviceVersions | [GET_orgs_org_id_devices_versions.md](utilities/GET_orgs_org_id_devices_versions.md) |
| POST | /api/v1/orgs/{org_id}/jsi/devices/{device_mac}/upgrade | upgradeOrgJsiDevice | upgradeOrgJsiDevice | [POST_orgs_org_id_jsi_devices_device_mac_upgrade.md](utilities/POST_orgs_org_id_jsi_devices_device_mac_upgrade.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/upgrade | listOrgMxEdgeUpgrades | listOrgMxEdgeUpgrades | [GET_orgs_org_id_mxedges_upgrade.md](utilities/GET_orgs_org_id_mxedges_upgrade.md) |
| POST | /api/v1/orgs/{org_id}/mxedges/upgrade | upgradeOrgMxEdges | upgradeOrgMxEdges | [POST_orgs_org_id_mxedges_upgrade.md](utilities/POST_orgs_org_id_mxedges_upgrade.md) |
| GET | /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id} | getOrgMxEdgeUpgrade | getOrgMxEdgeUpgrade | [GET_orgs_org_id_mxedges_upgrade_upgrade_id.md](utilities/GET_orgs_org_id_mxedges_upgrade_upgrade_id.md) |
| GET | /api/v1/orgs/{org_id}/ssr/upgrade | listOrgSsrUpgrades | listOrgSsrUpgrades | [GET_orgs_org_id_ssr_upgrade.md](utilities/GET_orgs_org_id_ssr_upgrade.md) |
| POST | /api/v1/orgs/{org_id}/ssr/upgrade | upgradeOrgSsrs | upgradeOrgSsrs | [POST_orgs_org_id_ssr_upgrade.md](utilities/POST_orgs_org_id_ssr_upgrade.md) |
| GET | /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel | getOrgSsrUpgrade | getOrgSsrUpgrade | [GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](utilities/GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) |
| POST | /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel | cancelOrgSsrUpgrade | cancelOrgSsrUpgrade | [POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](utilities/POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) |
| GET | /api/v1/orgs/{org_id}/ssr/versions | listOrgAvailableSsrVersions | listOrgAvailableSsrVersions | [GET_orgs_org_id_ssr_versions.md](utilities/GET_orgs_org_id_ssr_versions.md) |
| GET | /api/v1/sites/{site_id}/devices/upgrade | listSiteDeviceUpgrades | listSiteDeviceUpgrades | [GET_sites_site_id_devices_upgrade.md](utilities/GET_sites_site_id_devices_upgrade.md) |
| POST | /api/v1/sites/{site_id}/devices/upgrade | upgradeSiteDevices | upgradeSiteDevices | [POST_sites_site_id_devices_upgrade.md](utilities/POST_sites_site_id_devices_upgrade.md) |
| GET | /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id} | getSiteDeviceUpgrade | getSiteDeviceUpgrade | [GET_sites_site_id_devices_upgrade_upgrade_id.md](utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md) |
| POST | /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}/cancel | cancelSiteDeviceUpgrade | cancelSiteDeviceUpgrade | [POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md](utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md) |
| GET | /api/v1/sites/{site_id}/devices/versions | listSiteAvailableDeviceVersions | listSiteAvailableDeviceVersions | [GET_sites_site_id_devices_versions.md](utilities/GET_sites_site_id_devices_versions.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/upgrade | upgradeDevice | upgradeDevice | [POST_sites_site_id_devices_device_id_upgrade.md](utilities/POST_sites_site_id_devices_device_id_upgrade.md) |
| GET | /api/v1/sites/{site_id}/ssr/upgrade/{upgrade_id} | getSiteSsrUpgrade | getSiteSsrUpgrade | [GET_sites_site_id_ssr_upgrade_upgrade_id.md](utilities/GET_sites_site_id_ssr_upgrade_upgrade_id.md) |
| POST | /api/v1/sites/{site_id}/ssr/{device_id}/upgrade | upgradeSsr | upgradeSsr | [POST_sites_site_id_ssr_device_id_upgrade.md](utilities/POST_sites_site_id_ssr_device_id_upgrade.md) |

## Utilities WAN

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_arp | clearSiteSsrArpCache | clearSiteSsrArpCache | [POST_sites_site_id_devices_device_id_clear_arp.md](utilities/POST_sites_site_id_devices_device_id_clear_arp.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_bgp | clearSiteSsrBgpRoutes | clearSiteSsrBgpRoutes | [POST_sites_site_id_devices_device_id_clear_bgp.md](utilities/POST_sites_site_id_devices_device_id_clear_bgp.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/clear_session | clearSiteDeviceSession | clearSiteDeviceSession | [POST_sites_site_id_devices_device_id_clear_session.md](utilities/POST_sites_site_id_devices_device_id_clear_session.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/release_dhcp | releaseSiteSsrDhcpLease | releaseSiteSsrDhcpLease | [POST_sites_site_id_devices_device_id_release_dhcp.md](utilities/POST_sites_site_id_devices_device_id_release_dhcp.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/resolve_dns | testSiteSsrDnsResolution | testSiteSsrDnsResolution | [POST_sites_site_id_devices_device_id_resolve_dns.md](utilities/POST_sites_site_id_devices_device_id_resolve_dns.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/run_top | runSiteSrxTopCommand | runSiteSrxTopCommand | [POST_sites_site_id_devices_device_id_run_top.md](utilities/POST_sites_site_id_devices_device_id_run_top.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/service_ping | servicePingFromSsr | servicePingFromSsr | [POST_sites_site_id_devices_device_id_service_ping.md](utilities/POST_sites_site_id_devices_device_id_service_ping.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_ospf_database | showSiteGatewayOspfDatabase | showSiteGatewayOspfDatabase | [POST_sites_site_id_devices_device_id_show_ospf_database.md](utilities/POST_sites_site_id_devices_device_id_show_ospf_database.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_ospf_interfaces | showSiteGatewayOspfInterfaces | showSiteGatewayOspfInterfaces | [POST_sites_site_id_devices_device_id_show_ospf_interfaces.md](utilities/POST_sites_site_id_devices_device_id_show_ospf_interfaces.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_ospf_neighbors | showSiteGatewayOspfNeighbors | showSiteGatewayOspfNeighbors | [POST_sites_site_id_devices_device_id_show_ospf_neighbors.md](utilities/POST_sites_site_id_devices_device_id_show_ospf_neighbors.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_ospf_summary | showSiteGatewayOspfSummary | showSiteGatewayOspfSummary | [POST_sites_site_id_devices_device_id_show_ospf_summary.md](utilities/POST_sites_site_id_devices_device_id_show_ospf_summary.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_route | showSiteSsrAndSrxRoutes | showSiteSsrAndSrxRoutes | [POST_sites_site_id_devices_device_id_show_route.md](utilities/POST_sites_site_id_devices_device_id_show_route.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_service_path | showSiteSsrServicePath | showSiteSsrServicePath | [POST_sites_site_id_devices_device_id_show_service_path.md](utilities/POST_sites_site_id_devices_device_id_show_service_path.md) |
| POST | /api/v1/sites/{site_id}/devices/{device_id}/show_session | showSiteSsrAndSrxSessions | showSiteSsrAndSrxSessions | [POST_sites_site_id_devices_device_id_show_session.md](utilities/POST_sites_site_id_devices_device_id_show_session.md) |

## Utilities Wi-Fi

| Method | Path | operationId | Summary | File |
|--------|------|-------------|---------|------|
| POST | /api/v1/orgs/{org_id}/clients/{client_mac}/coa | reauthOrgDot1xWirelessClient | reauthOrgDot1xWirelessClient | [POST_orgs_org_id_clients_client_mac_coa.md](utilities/POST_orgs_org_id_clients_client_mac_coa.md) |
| POST | /api/v1/sites/{site_id}/clients/disconnect | disconnectSiteMultipleClients | disconnectSiteMultipleClients | [POST_sites_site_id_clients_disconnect.md](utilities/POST_sites_site_id_clients_disconnect.md) |
| POST | /api/v1/sites/{site_id}/clients/unauthorize | unauthorizeSiteMultipleClients | unauthorizeSiteMultipleClients | [POST_sites_site_id_clients_unauthorize.md](utilities/POST_sites_site_id_clients_unauthorize.md) |
| POST | /api/v1/sites/{site_id}/clients/{client_mac}/coa | reauthSiteDot1xWirelessClient | reauthSiteDot1xWirelessClient | [POST_sites_site_id_clients_client_mac_coa.md](utilities/POST_sites_site_id_clients_client_mac_coa.md) |
| POST | /api/v1/sites/{site_id}/clients/{client_mac}/disconnect | disconnectSiteWirelessClient | disconnectSiteWirelessClient | [POST_sites_site_id_clients_client_mac_disconnect.md](utilities/POST_sites_site_id_clients_client_mac_disconnect.md) |
| POST | /api/v1/sites/{site_id}/clients/{client_mac}/unauthorize | unauthorizeSiteWirelessClient | unauthorizeSiteWirelessClient | [POST_sites_site_id_clients_client_mac_unauthorize.md](utilities/POST_sites_site_id_clients_client_mac_unauthorize.md) |
| POST | /api/v1/sites/{site_id}/devices/reprovision | reprovisionSiteAllDevices | reprovisionSiteAllDevices | [POST_sites_site_id_devices_reprovision.md](utilities/POST_sites_site_id_devices_reprovision.md) |
| POST | /api/v1/sites/{site_id}/devices/reset_radio_config | resetSiteAllApsToUseRrm | resetSiteAllApsToUseRrm | [POST_sites_site_id_devices_reset_radio_config.md](utilities/POST_sites_site_id_devices_reset_radio_config.md) |
| POST | /api/v1/sites/{site_id}/devices/zeroize | zeroizeSiteFipsAllAps | zeroizeSiteFipsAllAps | [POST_sites_site_id_devices_zeroize.md](utilities/POST_sites_site_id_devices_zeroize.md) |
| POST | /api/v1/sites/{site_id}/rogues/{rogue_bssid}/deauth_clients | deauthSiteWirelessClientsConnectedToARogue | deauthSiteWirelessClientsConnectedToARogue | [POST_sites_site_id_rogues_rogue_bssid_deauth_clients.md](utilities/POST_sites_site_id_rogues_rogue_bssid_deauth_clients.md) |
| POST | /api/v1/sites/{site_id}/rrm/optimize | optimizeSiteRrm | optimizeSiteRrm | [POST_sites_site_id_rrm_optimize.md](utilities/POST_sites_site_id_rrm_optimize.md) |
| POST | /api/v1/utils/test_smsglobal | testSiteWlanSmsGlobal | testSiteWlanSmsGlobal | [POST_utils_test_smsglobal.md](utilities/POST_utils_test_smsglobal.md) |
| POST | /api/v1/utils/test_telstra | testSiteWlanTelstraSetup | testSiteWlanTelstraSetup | [POST_utils_test_telstra.md](utilities/POST_utils_test_telstra.md) |
| POST | /api/v1/utils/test_twilio | testSiteWlanTwilioSetup | testSiteWlanTwilioSetup | [POST_utils_test_twilio.md](utilities/POST_utils_test_twilio.md) |

## Library-Only (mistapi SDK, not in OpenAPI spec)

> The following endpoints exist in the installed `mistapi` Python library but are absent from the OpenAPI specification. Stub documentation was auto-generated from the library source.

| Function | Module | Category | File |
|----------|--------|----------|------|
| UploadOrgTicketAttachmentFile | `mistapi.api.v1.orgs.tickets` | orgs | [SDK_UploadOrgTicketAttachmentFile.md](orgs/SDK_UploadOrgTicketAttachmentFile.md) |
| acceptSiteApLocalizationData | `mistapi.api.v1.sites.maps` | sites | [SDK_acceptSiteApLocalizationData.md](sites/SDK_acceptSiteApLocalizationData.md) |
| addInstallerDeviceImageFile | `mistapi.api.v1.installer.orgs.devices` | installer | [SDK_addInstallerDeviceImageFile.md](installer/SDK_addInstallerDeviceImageFile.md) |
| addOrgMxEdgeImageFile | `mistapi.api.v1.orgs.mxedges` | orgs | [SDK_addOrgMxEdgeImageFile.md](orgs/SDK_addOrgMxEdgeImageFile.md) |
| addOrgTicketCommentFile | `mistapi.api.v1.orgs.tickets` | orgs | [SDK_addOrgTicketCommentFile.md](orgs/SDK_addOrgTicketCommentFile.md) |
| addSiteDeviceImageFile | `mistapi.api.v1.sites.devices` | sites | [SDK_addSiteDeviceImageFile.md](sites/SDK_addSiteDeviceImageFile.md) |
| addSiteMapImageFile | `mistapi.api.v1.sites.maps` | sites | [SDK_addSiteMapImageFile.md](sites/SDK_addSiteMapImageFile.md) |
| applySiteAutoMapAssignment | `mistapi.api.v1.sites.apply_auto_map_assignment` | sites | [SDK_applySiteAutoMapAssignment.md](sites/SDK_applySiteAutoMapAssignment.md) |
| attachSiteAssetImageFile | `mistapi.api.v1.sites.assets` | sites | [SDK_attachSiteAssetImageFile.md](sites/SDK_attachSiteAssetImageFile.md) |
| cancelOrgMxEdgeUpgrade | `mistapi.api.v1.orgs.mxedges` | orgs | [SDK_cancelOrgMxEdgeUpgrade.md](orgs/SDK_cancelOrgMxEdgeUpgrade.md) |
| cancelSiteAutoMapAssignment | `mistapi.api.v1.sites.auto_map_assignment` | sites | [SDK_cancelSiteAutoMapAssignment.md](sites/SDK_cancelSiteAutoMapAssignment.md) |
| cancelSiteMxEdgeUpgrade | `mistapi.api.v1.sites.mxedges` | sites | [SDK_cancelSiteMxEdgeUpgrade.md](sites/SDK_cancelSiteMxEdgeUpgrade.md) |
| clearSiteAutoMapAssignment | `mistapi.api.v1.sites.clear_auto_map_assignment` | sites | [SDK_clearSiteAutoMapAssignment.md](sites/SDK_clearSiteAutoMapAssignment.md) |
| countOrgMarvisClientEvents | `mistapi.api.v1.orgs.marvisclients` | orgs | [SDK_countOrgMarvisClientEvents.md](orgs/SDK_countOrgMarvisClientEvents.md) |
| countOrgMarvisClientsStats | `mistapi.api.v1.orgs.stats` | orgs | [SDK_countOrgMarvisClientsStats.md](orgs/SDK_countOrgMarvisClientsStats.md) |
| countSiteClientFingerprints | `mistapi.api.v1.sites.insights` | sites | [SDK_countSiteClientFingerprints.md](sites/SDK_countSiteClientFingerprints.md) |
| countSiteMarvisConfigActions | `mistapi.api.v1.sites.marvis_configs` | sites | [SDK_countSiteMarvisConfigActions.md](sites/SDK_countSiteMarvisConfigActions.md) |
| createOrgAsyncClaim | `mistapi.api.v1.orgs.claims` | orgs | [SDK_createOrgAsyncClaim.md](orgs/SDK_createOrgAsyncClaim.md) |
| deleteMspSsoAdmins | `mistapi.api.v1.msps.ssos` | msps | [SDK_deleteMspSsoAdmins.md](msps/SDK_deleteMspSsoAdmins.md) |
| deleteOrgSsoAdmins | `mistapi.api.v1.orgs.ssos` | orgs | [SDK_deleteOrgSsoAdmins.md](orgs/SDK_deleteOrgSsoAdmins.md) |
| deleteSiteMarvisConfigAction | `mistapi.api.v1.sites.marvis_configs` | sites | [SDK_deleteSiteMarvisConfigAction.md](sites/SDK_deleteSiteMarvisConfigAction.md) |
| disableOrgE911Report | `mistapi.api.v1.orgs.exports` | orgs | [SDK_disableOrgE911Report.md](orgs/SDK_disableOrgE911Report.md) |
| enableOrgE911Report | `mistapi.api.v1.orgs.exports` | orgs | [SDK_enableOrgE911Report.md](orgs/SDK_enableOrgE911Report.md) |
| enableSiteDeviceZigbeeJoin | `mistapi.api.v1.sites.devices` | sites | [SDK_enableSiteDeviceZigbeeJoin.md](sites/SDK_enableSiteDeviceZigbeeJoin.md) |
| getOrgAsyncClaimStatus | `mistapi.api.v1.orgs.claims` | orgs | [SDK_getOrgAsyncClaimStatus.md](orgs/SDK_getOrgAsyncClaimStatus.md) |
| getOrgE911Report | `mistapi.api.v1.orgs.exports` | orgs | [SDK_getOrgE911Report.md](orgs/SDK_getOrgE911Report.md) |
| getOrgMarvisClientInsights | `mistapi.api.v1.orgs.insights` | orgs | [SDK_getOrgMarvisClientInsights.md](orgs/SDK_getOrgMarvisClientInsights.md) |
| getSiteAutoMapAssignmentStatus | `mistapi.api.v1.sites.auto_map_assignment` | sites | [SDK_getSiteAutoMapAssignmentStatus.md](sites/SDK_getSiteAutoMapAssignmentStatus.md) |
| getSiteChannelScores | `mistapi.api.v1.sites.rrm` | sites | [SDK_getSiteChannelScores.md](sites/SDK_getSiteChannelScores.md) |
| getSiteInsightMetricsForAP | `mistapi.api.v1.sites.insights` | sites | [SDK_getSiteInsightMetricsForAP.md](sites/SDK_getSiteInsightMetricsForAP.md) |
| getSiteMxEdgeUpgrade | `mistapi.api.v1.sites.mxedges` | sites | [SDK_getSiteMxEdgeUpgrade.md](sites/SDK_getSiteMxEdgeUpgrade.md) |
| importInstallerMapFile | `mistapi.api.v1.installer.orgs.sites` | installer | [SDK_importInstallerMapFile.md](installer/SDK_importInstallerMapFile.md) |
| importOrgAssetsFile | `mistapi.api.v1.orgs.assets` | orgs | [SDK_importOrgAssetsFile.md](orgs/SDK_importOrgAssetsFile.md) |
| importOrgMapToSiteFile | `mistapi.api.v1.orgs.sites` | orgs | [SDK_importOrgMapToSiteFile.md](orgs/SDK_importOrgMapToSiteFile.md) |
| importOrgMapsFile | `mistapi.api.v1.orgs.maps` | orgs | [SDK_importOrgMapsFile.md](orgs/SDK_importOrgMapsFile.md) |
| importOrgNacCrlFile | `mistapi.api.v1.orgs.setting` | orgs | [SDK_importOrgNacCrlFile.md](orgs/SDK_importOrgNacCrlFile.md) |
| importOrgPsksFile | `mistapi.api.v1.orgs.psks` | orgs | [SDK_importOrgPsksFile.md](orgs/SDK_importOrgPsksFile.md) |
| importOrgUserMacsFile | `mistapi.api.v1.orgs.usermacs` | orgs | [SDK_importOrgUserMacsFile.md](orgs/SDK_importOrgUserMacsFile.md) |
| importSiteAssetsFile | `mistapi.api.v1.sites.assets` | sites | [SDK_importSiteAssetsFile.md](sites/SDK_importSiteAssetsFile.md) |
| importSiteDevicesFile | `mistapi.api.v1.sites.devices` | sites | [SDK_importSiteDevicesFile.md](sites/SDK_importSiteDevicesFile.md) |
| importSiteMapsFile | `mistapi.api.v1.sites.maps` | sites | [SDK_importSiteMapsFile.md](sites/SDK_importSiteMapsFile.md) |
| importSitePsksFile | `mistapi.api.v1.sites.psks` | sites | [SDK_importSitePsksFile.md](sites/SDK_importSitePsksFile.md) |
| listOrgAsyncClaims | `mistapi.api.v1.orgs.claims` | orgs | [SDK_listOrgAsyncClaims.md](orgs/SDK_listOrgAsyncClaims.md) |
| listSiteMxEdgeUpgrades | `mistapi.api.v1.sites.mxedges` | sites | [SDK_listSiteMxEdgeUpgrades.md](sites/SDK_listSiteMxEdgeUpgrades.md) |
| replaceSiteMapImageFile | `mistapi.api.v1.sites.maps` | sites | [SDK_replaceSiteMapImageFile.md](sites/SDK_replaceSiteMapImageFile.md) |
| searchOrgMarvisClientEvents | `mistapi.api.v1.orgs.marvisclients` | orgs | [SDK_searchOrgMarvisClientEvents.md](orgs/SDK_searchOrgMarvisClientEvents.md) |
| searchOrgMarvisClientsStats | `mistapi.api.v1.orgs.stats` | orgs | [SDK_searchOrgMarvisClientsStats.md](orgs/SDK_searchOrgMarvisClientsStats.md) |
| searchSiteClientFingerprints | `mistapi.api.v1.sites.insights` | sites | [SDK_searchSiteClientFingerprints.md](sites/SDK_searchSiteClientFingerprints.md) |
| searchSiteIotEndpoints | `mistapi.api.v1.sites.iotendpoints` | sites | [SDK_searchSiteIotEndpoints.md](sites/SDK_searchSiteIotEndpoints.md) |
| searchSiteMarvisConfigActions | `mistapi.api.v1.sites.marvis_configs` | sites | [SDK_searchSiteMarvisConfigActions.md](sites/SDK_searchSiteMarvisConfigActions.md) |
| sendOrgNacClientCoA | `mistapi.api.v1.orgs.nac_clients` | orgs | [SDK_sendOrgNacClientCoA.md](orgs/SDK_sendOrgNacClientCoA.md) |
| sendSiteNacClientCoA | `mistapi.api.v1.sites.nac_clients` | sites | [SDK_sendSiteNacClientCoA.md](sites/SDK_sendSiteNacClientCoA.md) |
| startSiteAutoMapAssignment | `mistapi.api.v1.sites.auto_map_assignment` | sites | [SDK_startSiteAutoMapAssignment.md](sites/SDK_startSiteAutoMapAssignment.md) |
| submitSiteMarvisConfigFeedback | `mistapi.api.v1.sites.marvis_configs` | sites | [SDK_submitSiteMarvisConfigFeedback.md](sites/SDK_submitSiteMarvisConfigFeedback.md) |
| updateOrgMxEdgeUpgrade | `mistapi.api.v1.orgs.mxedges` | orgs | [SDK_updateOrgMxEdgeUpgrade.md](orgs/SDK_updateOrgMxEdgeUpgrade.md) |
| updateSiteMxEdgeUpgrade | `mistapi.api.v1.sites.mxedges` | sites | [SDK_updateSiteMxEdgeUpgrade.md](sites/SDK_updateSiteMxEdgeUpgrade.md) |
| upgradeSiteMxEdges | `mistapi.api.v1.sites.mxedges` | sites | [SDK_upgradeSiteMxEdges.md](sites/SDK_upgradeSiteMxEdges.md) |
| uploadOrgNacPortalImageFile | `mistapi.api.v1.orgs.nacportals` | orgs | [SDK_uploadOrgNacPortalImageFile.md](orgs/SDK_uploadOrgNacPortalImageFile.md) |
| uploadOrgPskPortalImageFile | `mistapi.api.v1.orgs.pskportals` | orgs | [SDK_uploadOrgPskPortalImageFile.md](orgs/SDK_uploadOrgPskPortalImageFile.md) |
| uploadOrgWlanPortalImageFile | `mistapi.api.v1.orgs.wlans` | orgs | [SDK_uploadOrgWlanPortalImageFile.md](orgs/SDK_uploadOrgWlanPortalImageFile.md) |
| uploadSiteWlanPortalImageFile | `mistapi.api.v1.sites.wlans` | sites | [SDK_uploadSiteWlanPortalImageFile.md](sites/SDK_uploadSiteWlanPortalImageFile.md) |

