# Research: Firmware policy comparisons

## Preparation phases

**Decision**: Preserve both full read passes and label them separately.
**Rationale**: `PolicyWorkflow.prepare` captures complete settings.
`back_up` invokes `_verify_current` before one private save.
Save verification and boundary verification read the local file, not Mist settings.
The parent confirmed 290 settings reads for 145 targets and one new backup.
Public evidence is in
[issue #4229](https://github.com/jmorrison-juniper/MistHelper/issues/4229#issuecomment-6185186592).
**Alternative rejected**: Removing freshness reads would weaken recovery safety.

## SDK and schema contracts

**Decision**: Pass `limit=1000` to `listOrgSites` and gateway `getOrgInventory`.
Continue checked `mistapi.get_next` pagination and admission for every page.
**Rationale**: The pinned SDK accepts limit/page on these endpoints.
`listMspOrgs`, model constants, and firmware catalogs have no limit parameter.
The local schema's shared limit has a default of 100 and no declared maximum.
The requested maximum of 1000 matches the repository's established page ceiling.
No smaller endpoint-specific ceiling appears in the inspected contracts.
**Alternative rejected**: Inventing limit arguments on unsupported SDK methods.

`listOrgSites` returns `SitesArray`, whose items reference `site`, not `site_setting`.
The SDK org-sites module exposes list, search, count, create, and map import.
It exposes no bulk complete-settings read. `getSiteSetting` reads one complete
local settings object and has no page or limit parameter.
`get_all` collects list pages. It does not change the endpoint payload.

For 4,000 sites, each capture or freshness pass reads 4,001 complete settings.
Two passes already exceed a 5,000-request rolling-hour allowance before catalogs,
membership pages, identity checks, and usage probes. Existing admission must wait.
Lazy comparison adds bounded reads only for rows requested by the operator.

## Public projection

**Decision**: Validate the supported firmware schema before projecting known fields.
**Rationale**: Private siblings and unknown policy shapes must not escape.
Keep raw saved field presence. Report normalization separately.
**Alternative rejected**: Returning complete dictionaries or normalized saved values.

## Inspection and ownership

**Decision**: Route prepared comparisons through existing worker ownership.
Validate historical files and scope access without constructing restoration.
**Rationale**: Private plans remain local and proofs remain single-use.
**Alternative rejected**: Eager public job snapshots and implicit restoration previews.
