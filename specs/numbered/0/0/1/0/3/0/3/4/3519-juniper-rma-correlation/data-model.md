# Data Model: Juniper RMA Correlation

**Feature**: `3519-juniper-rma-correlation` | **Date**: 2026-10-08

Each entity has a natural key. That key is a business key from the source systems. Key strategies go in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (R-15). R-14 governs the personal fields. The exports keep them in full. The log lines mask them.

## Entities

### MistSupportTicket (input, not stored in full)

| Field | Source | Use |
| - | - | - |
| `id` | Mist `listOrgTickets` | Join value when `JUNIPER_TICKET_KEY_FIELD` is `id`. |
| `case_number` | Mist `listOrgTickets` | Display name. Join value by default (`JUNIPER_TICKET_KEY_FIELD` = `case_number`). |
| `status` | Mist | Export column |
| `subject` | Mist | Export column. Free text, not masked (see plan Risks). |
| `created_at` | Mist | Sort key and age check for the 90-day window |

Comments are never read into exports (R-16).

### JuniperServiceRequest

Natural key: `serviceRequestNumber`. Upserted by `juniperQuerySrList` and `juniperQuerySrDetails`.

| Field | Source | Log mask | Notes |
| - | - | - | - |
| `serviceRequestNumber` | list and details | No | Natural key |
| `customerCaseNumber` | list and details | No | Join value |
| `customerSourceID` | list and details | No | Configured source identifier |
| `accountID`, `accountName` | details | No | Account context |
| `caseTypeCode` | list and details | No | Tech or admin |
| `priority` | list and details | No | |
| `srStatus` | list and details | No | |
| `synopsis` | list | No | Short title |
| `productID`, `productSeries`, `platform` | list and details | No | |
| `serialNumber` | list and details | No | Links to RMA items and assets |
| `version`, `release`, `software`, `specialRelease` | details | No | |
| `routerName` | details | No | |
| `lastModifiedDate` | list | No | |
| `linkToCase` | list | No | Portal link |
| `retrievedAt` | MistHelper | No | Run time (UTC) |

Excluded: `problemDescription`, notes, attachments, and linked references. Also excluded: contact fields, except the account name.

Validation rules:

- `serviceRequestNumber`: 1 to 40 characters. Letters, digits, and hyphens only. A production example has 16 characters.
- `customerCaseNumber`: 1 to 40 characters.

### RmaRecord

Natural key: `rmaNumber`. One record for each RMA of a request.

| Field | Source | Log mask |
| - | - | - |
| `rmaNumber` | details and RMA detail | No |
| `serviceRequestNumber` | parent request | No |
| `companyName` | RMA detail `rmaContact` | No |
| `contactName` | RMA detail `rmaContact` | Yes |
| `contactEmail` | RMA detail `rmaContact` | Yes |
| `telephoneCountryCode` | RMA detail `rmaContact` | No |
| `telephoneNumber` | RMA detail `rmaContact` | Yes |
| `address1`, `address2` | RMA detail `rmaContact` (nested or flat) | Yes |
| `city`, `stateCode`, `state`, `countryCode`, `country` | RMA detail `rmaContact` | No |
| `postalCode` | RMA detail `rmaContact` | No |
| `retrievedAt` | MistHelper | No |

Validation rules:

- `rmaNumber`: 1 to 40 characters. Letters, digits, and hyphens only.

### RmaItem

Composite key: `rmaNumber`, `itemType`, `itemNumber`. One record for each item in `defectiveItems`, `replacementItems`, and `ceItems`.

| Field | Source | Log mask | Notes |
| - | - | - | - |
| `rmaNumber` | parent RMA | No | Part of the key |
| `itemType` | parser | No | `defective`, `replacement`, or `ce`. Part of the key. |
| `itemNumber` | item | No | Part of the key |
| `defectiveItemNumber` | replacement and CE items | No | Parent defective item |
| `productID` | item | No | |
| `serialNumber` | item | No | Used to join assets |
| `carrierDescription` | item | No | Carrier |
| `trackingNumber` | item | No | Tracking |
| `dateTime` | defective item | No | Created date |
| `receivedDate` | defective item | No | Received by Juniper |
| `shipDate` | replacement item | No | Shipped |
| `deliveredDate` | replacement item | No | Delivered. May hold a malformed timestamp (kept as text). |
| `shipmentServiceLevel` | replacement item | No | |
| `status` | item (`defectiveItemStatus`, `replacementStatus`, or `engineerStatus`) | No | Normalized to one column |
| `receivedBy` | replacement item | Yes | Person name |
| `vendorName` | CE item | No | Field service vendor |
| `vendorPhone` | CE item | Yes | Telephone |
| `serviceRequestedDate`, `actualServicedDate`, `contactedDate`, `estimatedArrivalDate` | CE item | No | |

### AssetRecord

Natural key: `serialNumber`. Fed by menu 304 and by menu 302 for matched serials.

| Field | Source | Notes |
| - | - | - |
| `serialNumber` | asset | Natural key |
| `assetRecordId` | asset | Juniper identifier, kept for reference |
| `assetStatus` | asset | |
| `softwareSupportReferenceNumber` | asset | SSRN |
| `registrationDate`, `shipDate` | asset | |
| `productSKU`, `productSKUDescription` | asset | |
| `productSKUEolDate`, `productSKUEosDate` | asset | |
| `serviceEligible`, `productLine` | asset | |
| `parentSerialNumber`, `parentProductSKU` | asset | |
| `installedAt*` | asset | Customer site. Business address, not masked. |
| `rmaInfo` summary | asset (object or list) | Latest RMA number and status |

### AssetCoverage (warranty and contract rows)

Composite key: `serialNumber`, `coverageKind`, `index`, `contractLineItemNumber`.

| Field | Source |
| - | - |
| `coverageKind` | `warranty` or `contract` |
| `index` | source index |
| `warrantyDescription`, `warrantyStartDate`, `warrantyEndDate` | warranty |
| `contractNumber`, `contractLineItemNumber`, `contractStartDate`, `contractEndDate`, `contractStatus` | contract |
| `serviceSKU`, `serviceSKUDescription`, `serviceType`, `serviceSKUShipmentServiceLevel`, `serviceSKUEosDate`, `serviceSKUIsPlaceHolder`, `serviceSKUProvidesJTACsupport` | contract details |
| `endCustomerName`, `resellerName` | contract. Business names, not masked. |

Address and contact fields of the contract are not stored.

### CorrelationLink

Composite key: `mistTicketId`, `serviceRequestNumber`.

| Field | Notes |
| - | - |
| `matchRule` | `customer_case_number` (R-05) |
| `matchStatus` | `matched` or `ambiguous`. Unmatched tickets have no link row. |
| `candidateCount` | Number of requests that matched the case number |
| `linkedAt` | First time the link appeared |
| `lastVerifiedAt` | Last run that confirmed the case number on the request |
| `runId` | Run that last verified the link |

### RunRecord

Auto key with unique `runId`.

| Field | Notes |
| - | - |
| `runId` | Unique run identifier |
| `operation` | Menu name |
| `startedAt`, `endedAt` | UTC timestamps |
| `ticketCount` | Mist tickets read |
| `matchedCount`, `unmatchedCount`, `ambiguousCount`, `failedCount` | Outcome counts |
| `requestCount` | Juniper requests sent |
| `status` | `running`, `complete`, `incomplete`, or `failed` |
| `reason` | Plain-text reason for `incomplete` or `failed` |

## Relationships

```text
MistSupportTicket 1 ---- 0..* CorrelationLink *---- 1 JuniperServiceRequest
JuniperServiceRequest 1 ---- 0..* RmaRecord 1 ---- 0..* RmaItem
RmaItem *---- 0..1 AssetRecord (by serialNumber)
AssetRecord 1 ---- 0..* AssetCoverage
RunRecord (one per menu run; referenced by CorrelationLink.runId)
```

## State Transitions

### RunRecord.status

```text
running --> complete     every ticket finished
running --> incomplete   stopped early, or retries ran out for some items
running --> failed       access check failed before any data was read
```

### CorrelationLink.matchStatus

```text
(none) --> matched       one request carries the case number
(none) --> ambiguous     two or more requests carry the case number
matched --> ambiguous    a later run finds a second request
ambiguous --> matched    a later run finds one request
any --> stale            the case number is no longer on the request (kept, not deleted)
```

## Retention

- In full, MistHelper keeps the personal fields. The purge deletes each export file that holds them (`JuniperCorrelation.csv` and `JuniperRmaItems.csv`) when its age passes `JUNIPER_PII_RETENTION_DAYS` (default 180).
- The purge runs once at the start of each run. It writes its count to the `purgedCount` column of the run record.
- The log lines mask every personal field. The exports keep the full values, by operator decision (2026-10-08).
