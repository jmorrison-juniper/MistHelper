# Contract: Menus and Exports

## Menus

| Menu | Title | Category | Inputs | Outputs |
| - | - | - | - | - |
| 301 | Check Juniper service API access | `interactive_safe` | None | Pass or fail message. No file. |
| 302 | Correlate Mist support tickets with Juniper RMAs | `interactive_safe` | Organization (cached or prompted) | Exports listed below |
| 303 | Look up a Juniper service request or RMA | `interactive_safe` | Request number or case number, and an optional RMA number | On-screen result and `JuniperLookup.csv` |
| 304 | Look up Juniper asset and warranty data | `interactive_safe` | Serial numbers, one per line or comma separated | `JuniperAssets.csv` and `JuniperAssetCoverage.csv` |
| 294 | List Juniper service requests for a date window | `interactive_safe` | Start and end dates (Enter keeps the last 90 days) | `JuniperRequestList.csv` |
| 295 | Read one Juniper service request with every field | `interactive_safe` | Request number or case number | `JuniperRequestDetail.csv` and `JuniperRequestDetailRecords.csv` |
| 296 | Read one Juniper RMA with its items | `interactive_safe` | RMA number, request number, and an optional case number | `JuniperRmaDetail.csv` and `JuniperRmaDetailItems.csv` |
| 297 | Read the notes of one Juniper service request | `interactive_safe` | Request number or case number | `JuniperRequestNotes.csv` |
| 298 | Read the Juniper list of values | `interactive_safe` | None | `JuniperLovs.csv` |
| 299 | Read the Juniper software release list | `interactive_safe` | None | `JuniperSoftwareVersions.csv` |
| 300 | Read asset bulk links for a date window | `interactive_safe` | Start and end dates, one to seven days old | `JuniperAssetBulkLinks.csv` and `JuniperAssetBulkNoData.csv`. Blocked until Juniper enables the asset API. |

Each menu uses the skip reason "Requires Juniper settings" in `OperationRegistry`.

Test-mode rule: Under `--test` and `--testinteractive`, a menu makes no live call unless the operator sets `JUNIPER_LIVE_TESTS=1`. The refusal names that setting. This rule applies even when the registry category allows the menu.

## Input Validation

Each input uses `safe_input()`. A blank input cancels the action before any call.

| Input | Rule |
| - | - |
| Request number | 1 to 40 characters. Letters, digits, and hyphens. |
| Customer case number | 1 to 40 characters. Letters, digits, and hyphens. |
| RMA number | 1 to 40 characters. Letters, digits, and hyphens. |
| Serial number or SSRN | 1 to 40 characters. Letters, digits, and hyphens. Any number per run. The client sends batches of 300. |
| Organization | Resolved by `ConfigUtils.get_cached_or_prompted_org_id()` |

Rejected input shows the rule that failed. It never reaches a Juniper call.

## Exports

Every export uses `DataExporter.write_with_format_selection()`. The file goes under `data/`. The database mirror uses the strategy named in the table.

| Menu | `api_function_name` | File | Key | Log-masked fields |
| - | - | - | - | - |
| 302 | `juniperCorrelationLinks` | `JuniperCorrelation.csv` | `mistTicketId` and `serviceRequestNumber` (one row per ticket when unmatched) | Yes |
| 302 | `juniperQuerySrDetails` | `JuniperServiceRequests.csv` | `serviceRequestNumber` | None |
| 302 | `juniperQueryRmaDetails` | `JuniperRmaItems.csv` | `rmaNumber`, `itemType`, `itemNumber` | Yes |
| 302 | `juniperRunRecords` | `JuniperRunRecords.csv` | `runId` | None |
| 303 | `juniperQuerySrDetails` | `JuniperLookup.csv` | `serviceRequestNumber` | None |
| 303 | `juniperQueryRmaDetails` | `JuniperLookupRmaItems.csv` | `rmaNumber`, `itemType`, `itemNumber` | Yes |
| 304 | `juniperQueryAssetsDetails` | `JuniperAssets.csv` | `serialNumber` | None |
| 304 | `juniperQueryAssetCoverage` | `JuniperAssetCoverage.csv` | `serialNumber`, `coverageKind`, `index`, `contractLineItemNumber` | None |
| 294 | `juniperQuerySrList` | `JuniperRequestList.csv` | `serviceRequestNumber` | Yes |
| 295 | `juniperQuerySrDetails` | `JuniperRequestDetail.csv` | `serviceRequestNumber` | Yes |
| 295 | `juniperQuerySrDetailRecords` | `JuniperRequestDetailRecords.csv` | One row for each nested note, attachment, and RMA item | Yes |
| 296 | `juniperQueryRmaHeaders` | `JuniperRmaDetail.csv` | `rmaNumber` | Yes |
| 296 | `juniperQueryRmaDetails` | `JuniperRmaDetailItems.csv` | `rmaNumber`, `itemType`, `itemNumber` | Yes |
| 297 | `juniperQuerySrNoteDetails` | `JuniperRequestNotes.csv` | `noteId` | Yes |
| 298 | `juniperGetLov` | `JuniperLovs.csv` | `lovGroup`, `lovPath`, `lovValue` | None |
| 299 | `juniperGetSoftwareEosLov` | `JuniperSoftwareVersions.csv` | `productSeries`, `platform`, `versionRelease` | None |
| 300 | `juniperQueryAssetsBulkData` | `JuniperAssetBulkLinks.csv` | One row for each file link, without its signature | Yes (signature) |
| 300 | `juniperQueryAssetsBulkNoData` | `JuniperAssetBulkNoData.csv` | One row for each snapshot date with no data | None |

### Correlation Columns (`JuniperCorrelation.csv`)

| Column | Meaning |
| - | - |
| `mistTicketId` | Mist ticket identifier (`id`) |
| `mistCaseNumber` | Mist display name (`case_number`) |
| `joinValue` | Value compared with the customer case number. It is the field that `JUNIPER_TICKET_KEY_FIELD` names. |
| `mistSubject` | Mist subject (free text, not masked) |
| `mistStatus` | Mist status |
| `matchStatus` | `matched`, `ambiguous`, or `unmatched` |
| `candidateCount` | Number of requests that match the case number |
| `unmatchedReason` | Plain text when the status is `unmatched` |
| `serviceRequestNumber` | Matched request (blank when ambiguous or unmatched) |
| `candidateRequests` | Comma-separated request numbers when the status is `ambiguous` |
| `srStatus` | Request status |
| `rmaNumber` | RMA number |
| `itemType` | `defective`, `replacement`, or `ce` |
| `itemNumber` | Item number |
| `serialNumber` | Item serial number |
| `productID` | Item product |
| `carrierDescription` | Carrier |
| `trackingNumber` | Tracking number |
| `shipDate` | Ship date |
| `deliveredDate` | Delivery date (raw text if malformed) |
| `rmaStatus` | Item status |
| `shipToCompany` | Company name |
| `shipToContact` | Contact name, kept in full |
| `shipToCityState` | City and state |
| `shipToCountry` | Country |
| `runId` | Run that produced the row |

The CSV writer quotes each value that contains a comma.

## Run Completion Message

Each menu ends with a summary line. The line shows the counts and the status. It shows no key and no personal value.

```text
Juniper correlation complete: status=complete tickets=120 matched=44 ambiguous=2 unmatched=74 failed=0 requests=231
```

When the status is `incomplete`, the message adds the reason and the number of items not finished.
