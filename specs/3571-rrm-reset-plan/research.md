# Research: RRM optimize or reset plan capture

## Skill evidence

### RRM operation

**Decision**: Treat menu `291` as a destructive site-level RRM operation.  
**Rationale**: The Juniper Mist wireless skill states that RRM can adjust channel assignments, Dynamic Frequency Selection treatment, AP broadcast power, and band control. It also states that RRM uses up to `30 days` of site radio data and sends optimization updates to APs. Source: `juniper-mist-wireless/08-radio-management-and-rrm/01-rrm-operation-channel-power-and-band-control.md`.  
**Alternatives considered**: Treat the operation as safe. Rejected because channels or power can change.

### RRM hierarchy and monitoring

**Decision**: Record that the operation reads site configuration and site RRM state, while RF templates, device profiles, and AP overrides can influence results.  
**Rationale**: The RRM hierarchy page states that RF templates are broadest, device profiles override RF templates, and direct AP configuration has highest precedence. It also names the `Site > Radio Management` dashboard and fields such as `CHANNEL DIST. SCORE`, `AP DENSITY`, and `Triggered site RRM`. Source: `juniper-mist-wireless/08-radio-management-and-rrm/02-rrm-configuration-hierarchy-monitoring-and-maintenance.md`.  
**Alternatives considered**: Model the feature as AP-level only. Rejected because the site RRM read and site optimize request cover the site.

### Bulk optimize evidence

**Decision**: Warn that radio optimization can change client RF behavior, and require a maintenance window.  
**Rationale**: The Access Points bulk actions page states that `Optimize Radios for Selected APs` can change channels or power and should avoid a client-sensitive window. Source: `juniper-mist-wireless/04-device-profiles-and-ap-operations/02-access-points-page-and-bulk-actions.md`.  
**Alternatives considered**: Omit the warning. Rejected because the user needs a clear destructive-operation risk.

## OpenAPI evidence

### `getSiteCurrentChannelPlanning`

**Decision**: Use the existing menu `86` read path for current channel planning.  
**Rationale**: OpenAPI lists `GET /api/v1/sites/{site_id}/rrm/current` with required path parameter `site_id`. The `200` response references schema `rrm`. The `rrm` schema includes `band_24`, `band_5`, `band_6`, `rftemplate`, `rftemplate_id`, `rftemplate_name`, `status`, and `timestamp`. Each `rrm_band` can include `channel`, `bandwidth`, `power`, `curr_channel`, `curr_bandwidth`, and `curr_power`.  
**Alternatives considered**: Build a separate RRM read. Rejected because the assignment requires the menu `86` read.

### `optimizeSiteRrm`

**Decision**: Use the SDK function for RRM optimization.  
**Rationale**: OpenAPI lists `POST /api/v1/sites/{site_id}/rrm/optimize` with required path parameter `site_id`. The request body references `utils_rrm_optimize`, which requires `bands`. Optional fields are `macs` and `txpower_only`. The installed SDK exposes `mistapi.api.v1.sites.rrm.optimizeSiteRrm`.  
**Alternatives considered**: Use `apisession.mist_post`. Rejected because the SDK function exists.

### `resetSiteAllApsToUseRrm`

**Decision**: Use `apisession.mist_post` for reset until the SDK exposes the function.  
**Rationale**: OpenAPI lists `POST /api/v1/sites/{site_id}/devices/reset_radio_config` with required path parameter `site_id`. The request body references `utils_reset_radio_config`, which requires `bands` and has optional `force`. The installed SDK does not expose `mistapi.api.v1.sites.rrm.resetSiteAllApsToUseRrm`.  
**Alternatives considered**: Skip reset. Rejected because reset is an acceptance criterion.

## Runtime decisions

### Request body

**Decision**: Send `{"bands": ["24", "5", "6"]}` by default for both destructive requests.  
**Rationale**: Both documented request schemas require `bands`, and the OpenAPI examples use `["24", "5", "6"]`.  
**Alternatives considered**: Send an empty body. Rejected because the schemas require `bands`.

### Settle time

**Decision**: Default to `300` seconds and allow a positive integer override through `RRM_SETTLE_SECONDS`.  
**Rationale**: The assignment requires this behavior. A positive integer avoids accidental negative or nonnumeric waits.  
**Alternatives considered**: Prompt for the wait. Rejected because the acceptance criterion names an environment variable.

### Diff comparison

**Decision**: Compare stable radio keys by `site_id`, AP identifier, and band, then compare channel, width, and power values.  
**Rationale**: The operator needs only radios whose service-relevant RF values changed.  
**Alternatives considered**: Write all radios with a changed flag. Rejected because the acceptance criterion requires changed radios only.
