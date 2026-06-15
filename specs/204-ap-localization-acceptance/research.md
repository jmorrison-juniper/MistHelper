# Research: AP Localization Acceptance (Menu 204)

## API Discovery

### Decision: Use `confirmSiteApLocalizationData` from `mistapi.api.v1.sites.maps`

**Rationale**: This is the only endpoint in mistapi 0.63.0 that handles
AP localization acceptance. It was located by inspecting all submodules of
`mistapi.api.v1.sites` for functions containing "localization" or "accept",
and confirmed against the OpenAPI spec.

**Alternatives considered**: None — single purpose endpoint.

---

## Endpoint Contract

**SDK function**: `mistapi.api.v1.sites.maps.confirmSiteApLocalizationData`  
**HTTP**: `POST /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values`  
**mistapi version required**: 0.63.0+  

### Path parameters
| Param | Type | Notes |
|-------|------|-------|
| `site_id` | UUID string | Required |
| `map_id` | UUID string | Required |

### Body schema (`use_auto_ap_values`)
| Field | Type | Required | Values | Meaning |
|-------|------|----------|--------|---------|
| `accept` | bool | Yes | `true`/`false` | Accept or reject localization data |
| `for` | enum string | Yes | `"placement"`, `"orientation"` | Which localization type |
| `macs` | list[str] | No | AP MAC addresses | Scope to specific APs; omit for full-map scope |

### Responses
| Status | Body | Meaning |
|--------|------|---------|
| 200 | *(empty)* | Success |
| 400 | error | Invalid request |
| 401 | error | Unauthorized |
| 403 | error | Forbidden |
| 404 | error | Site or map not found |
| 429 | error | Rate limited |

---

## Safety Model

### Decision: Typed confirmation with action-specific phrases

**Rationale**: The endpoint is state-changing (it alters AP placement/orientation
data in the Mist cloud). Existing destructive operations in MistHelper use typed
confirmation (e.g., `"CONVERT"`, `"CONFIRM"` patterns at lines 20062 and 24949).
This feature uses accept/reject-specific phrases to prevent operator confusion:
- Accept flow requires: `ACCEPT-LOCALIZATION`
- Reject flow requires: `REJECT-LOCALIZATION`

**Alternatives considered**: Single `CONFIRM` phrase — rejected because it does not
distinguish accept from reject and increases the risk of an operator accidentally
reversing intent under time pressure.

---

## Audit Record Design

### Decision: Construct audit record locally; use `auto_increment_with_unique` PK strategy

**Rationale**: The API returns HTTP 200 with an empty body (confirmed from OpenAPI
spec). There is no stable UUID or entity ID returned. The audit record must
therefore be constructed from request context and response metadata. The
`auto_increment_with_unique` strategy (used by `getOrgLicensesSummary` and similar
action-result endpoints) is the correct match for this pattern.

**Alternatives considered**:
- `composite_pk` with timestamp + site_id — would fail if the same operator submits
  twice in the same second. `auto_increment_with_unique` is safer.
- No export — rejected by FR-009/FR-010; every attempt must produce an audit artifact.

---

## Menu Numbering

### Decision: Menu 204

**Rationale**: Current highest menu operation is 203 (`send_site_nac_client_coa`,
line 28129). The feature spec folder is named `204-ap-localization-acceptance`,
confirming the intended number. Destructive/config-changing operations occupy the
154–194 range by convention, but newer operations have been appended sequentially
at the top (195+). Menu 204 is the next sequential slot.

**Alternatives considered**: Inserting inside 154–194 block — rejected; resequencing
existing operations breaks existing `--menu N` automation scripts used by operators.

---

## Test Strategy

### Decision: Unit tests using `unittest.mock.patch`; no live API calls

**Rationale**: The operation is destructive and cannot safely run in CI without live
credentials and a test site. Unit tests mock `confirmSiteApLocalizationData` and
`DataExporter.write_with_format_selection` and verify:
1. Validation blocks empty site_id, empty map_id, invalid `for_type`
2. Confirmation failure cancels execution (no API call made)
3. Confirmation success invokes API with correct body parameters
4. Audit record is written for both executed and cancelled outcomes
5. Test-mode guard skips the API call when `TEST_MODE` is truthy

**Alternatives considered**: Integration test against live site — out of scope for
this spec slice; would require separate test environment setup spec.

---

## Cross-Cutting Concerns Resolved

| Unknown | Resolution |
|---------|------------|
| Does `macs` field in body use `macs` or `device_macs`? | OpenAPI schema says `macs`; the example in the request body (which was generated from an older doc version) used `device_macs` — the component schema (`use_auto_ap_values`) is authoritative: field is `macs` |
| Is `for` field required or optional? | OpenAPI schema has no `required` array on the object, but the example always includes it and the enum is the only discriminator. Treat as required to be safe. |
| Can the body be sent without `macs` for full-map scope? | Yes — schema says "If a list is not provided the API will accept/reject for the full map." |
| What does a 200 response look like? | Empty body (`"content": {}`). No data to parse. Status code is the only signal. |
