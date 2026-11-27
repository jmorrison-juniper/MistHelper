# Data Model: VPN Inventory Read

Each entity lists its fields and constraints. A task cites a field as `Entity.field`. The source of the field shapes is the OpenAPI `vpn` schema in `documentation/mist-api-openapi31yaml.yaml`, lines 117776 to 117809 (RC-65, RC-66).

## VpnRecord

One object in the `data` list of a page.

| Field | Type | Constraint |
|-------|------|------------|
| `VpnRecord.name` | text | Required by the schema (RC-65). The reader requires a nonblank string (FR-004). The schema sets `minLength` to 1 (RC-66). The duplicate key is the name after trimming and lowering the case (FR-014). |
| `VpnRecord.id` | text | A Mist identifier. The schema does not require it. The reader does not require it. The builder does not use it for duplicates. |
| `VpnRecord.paths` | object | Required by the schema. The reader does not validate it. The builder reads it only for display. |

The natural key for the duplicate check is `VpnRecord.name`, compared without case and without surrounding spaces. The Mist identifier `VpnRecord.id` is not used for that check.

## Page

One response object from `listOrgVpns` or from `mistapi.get_next`. Mistapi returns the same object type in both cases (RC-59).

| Field | Type | Constraint |
|-------|------|------------|
| `Page.status_code` | integer or none | Must be 200 through 299 (FR-002). None means that no HTTP response reached mistapi. |
| `Page.data` | list | Must be a list (FR-003). Each item must be a `VpnRecord` (FR-004). |
| `Page.next` | text or none | None means no next link (FR-006). A value must be a nonblank link that the reader has not followed (FR-007). |
| `Page.headers` | mapping or none | Must hold the three pagination headers (FR-005). None means that the headers are absent. |

## PaginationHeaders

Three integer headers on each page. The OpenAPI file does not document these headers (RC-67). Mistapi reads them in `_check_next` (RC-57, RC-58).

| Field | Header | Type | Constraint |
|-------|--------|------|------------|
| `PaginationHeaders.total` | `X-Page-Total` | integer | 0 or more. Must equal the first page value (FR-008). |
| `PaginationHeaders.limit` | `X-Page-Limit` | integer | 1 or more. Must equal the first page value (FR-008). |
| `PaginationHeaders.page` | `X-Page-Page` | integer | 1 or more. Must not exceed the declared page count (FR-008). |

The declared page count is the total divided by the limit, rounded up, with a minimum of 1. The first page sets it.

## PageChain

The sequence of pages from one read.

| Field | Type | Constraint |
|-------|------|------------|
| `PageChain.first_numbers` | tuple of three integers | Set from the first page. Used for the position checks of later pages. |
| `PageChain.seen_links` | set of text | Holds each next link that the reader followed. A repeated link makes the inventory unavailable (FR-007). |
| `PageChain.records` | list of `VpnRecord` | Holds the records of each validated page. The reader returns this list only after the last page passes. |

## InventoryResult

The result of one read. The reader returns one of three states.

| State | Meaning | Return value | Builder behavior |
|-------|---------|--------------|------------------|
| Verified with records | Every page passes. At least one record exists. | The list of records | Strip each name. Display the list. Ask for a name. |
| Verified empty | The first page passes. It has zero records and total 0. | An empty list | Display the placeholder. Ask for a name. |
| Unavailable | Any rule fails, or the list request raises an exception. | None | Write the existing error line and the stop line. Return before any prompt (FR-012, FR-013). |

## State Transitions

1. The reader writes the info line and calls `listOrgVpns`.
2. An exception moves the read to Unavailable.
3. A first page that fails a page rule moves the read to Unavailable.
4. A first page with no next link and a valid last-page position moves the read to Verified empty or Verified with records.
5. A first page with a next link moves the read to the next-page step.
6. The next-page step writes the info line and calls `mistapi.get_next`. A missing response moves the read to Unavailable.
7. A later page repeats steps 3 to 6. A repeated link, a page beyond the declared count, or a changed total moves the read to Unavailable.
8. A later page with no next link and a valid last-page position moves the read to the final state.

## Relationships

- A read holds one `PageChain`.
- A `PageChain` holds one or more `Page` objects.
- Each `Page` holds zero or more `VpnRecord` objects.
- One `InventoryResult` comes from one `PageChain`.
