# Research: Cross-Org Subscription and Stock Inventory

## MSP Organization Discovery

**Decision**: Read `getSelf` for direct and MSP access grants.
Use `listMspOrgs` for each MSP grant.
Add the configured direct organization as a fallback.
Deduplicate organizations by organization ID.

**Rationale**: The active session defines the authorization boundary.
A submitted organization list must not broaden that boundary.
This pattern already exists in the MistHelper licensing-comparison migration.

**Alternatives considered**:
- Read only the configured organization.
- Read every organization from a single global endpoint.
- Accept browser or operator organization IDs without access validation.

The alternatives cannot show all authorized MSP organizations or can expose out-of-scope data.

## Purchased and Entitlement Source

**Decision**: Read `getOrgLicensesSummary` for entitled quantities and dated license records.
Use `getOrgLicensesBySite` for in-use quantities.
Use `listMspLicenses` for an MSP-level purchase and amendment view when the session is authorized.

**Rationale**: The organization summary exposes 41 live T-Mobile license records with quantity and dates.
The organization usage endpoint exposes 48 live usage rows.
The MSP endpoint adds purchase context, but it can return HTTP 403 for a direct read-only token.

**Alternatives considered**:
- Use only the entitlement summary.
- Use only the MSP license endpoint.
- Infer purchased quantity from inventory.

Only the entitlement and usage endpoints provide the requested purchase and in-use evidence together.

## Start and End Dates

**Decision**: Normalize `start_time`, `created_time`, `end_time`, ISO strings, Unix seconds, and Unix milliseconds.
Use `start_time` or `created_time` to mark purchases after 2023-12-31.
Use `end_time` to calculate days remaining and the expiry band.

**Rationale**: Live T-Mobile records contain `start_time`, `created_time`, `end_time`, `quantity`, and `remaining_quantity`.
The date parser must reject invalid values instead of inventing dates.

**Alternatives considered**:
- Use only `end_time`.
- Use only `created_time`.
- Treat missing dates as expired or future.

Each alternative hides or invents an evidence condition.

## Stock Inventory

**Decision**: Read paginated `getOrgInventory` data.
Mark a record as stock when `site_id` is absent.
Include AP, switch, gateway, SSR, Mist Edge, and other types.

**Rationale**: The live inventory response shows 79 devices and one unassigned SSR130.
The same inventory source identifies assigned and unassigned devices.

**Alternatives considered**:
- Read only assigned devices.
- Count only AP and switch types.
- Use JSI records as the stock source.

The alternatives omit gateway and SSR stock or depend on contract evidence that is not inventory evidence.

## JSI Contract Join

**Decision**: Read `searchOrgJsiAssetsAndContracts` once for each accessible organization.
Join available evidence to stock by serial number.
Keep `has_support`, `status`, `model`, and available date fields visible.

**Rationale**: JSI is the support and contract evidence source.
A serial join avoids a model-only match.
The live JSI response can return no stock match.

**Alternatives considered**:
- Join by model.
- Mark every stock device unsupported.
- Mark every stock device supported.

Those alternatives can give false contract conclusions.

## Output Format

**Decision**: Write one organization status report and four linked CSV reports.
Use CSV format override for this operation.

**Rationale**: CSV is portable and supports the renewal packet.
One menu operation can call the existing DataExporter five times.
The existing licensing comparison export forces formula-safe CSV.

**Alternatives considered**:
- Write one wide CSV.
- Use only SQLite.
- Open separate interactive prompts for each report.

One wide CSV creates unstable columns.
The existing output format can vary between operators.
Separate prompts slow a complete renewal review.

## Source Repository Inspiration

**Decision**: Use `MistOrgLicensingComparison` as design and migration reference.
Do not copy source code or template code.
Preserve the existing license and source attribution in the integrated experience.

**Rationale**: The source repository already provides organization selection, purchased counts, inventory comparison, bundle concepts, manual rows, and CSV export.
The migration has a public specification and an attribution file.

**Alternatives considered**:
- Copy the source repository without review.
- Ignore the source repository.
- Migrate every source feature before this request.

Copying lacks this feature's audit and hierarchy requirements.
Ignoring it loses established purchase and inventory behavior.
Full migration is outside one renewal report.

## Live Evidence

The repository token can authenticate to T-Mobile USA Validation Lab.
It read 41 dated license records, 48 usage rows, 79 inventory devices, and one unassigned SSR130.
The active direct token read JSI and received two JSI rows.
The stock serial did not match the JSI rows.
The direct token received HTTP 403 for MSP organizations and MSP licenses.
MSP-wide evidence requires interactive MSP authentication or a role with MSP read access.
