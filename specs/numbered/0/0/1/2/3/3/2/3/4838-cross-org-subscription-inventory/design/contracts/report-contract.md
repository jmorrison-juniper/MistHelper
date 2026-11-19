# Report Contract: Menu 308

## CLI Entry

The public operation is `CrossOrgSubscriptionInventoryReport.run()`.

The menu row is:

```text
308 - Export cross-org subscription, entitlement, and stock inventory report
```

The operation is read-only and belongs in the `safe` category.

The command is:

```text
python MistHelper.py --menu 308
```

Interactive MSP authentication can use:

```text
python MistHelper.py --login --menu 308
```

The operation accepts no destructive confirmation and sends no Mist write request.

## SDK Inputs

The operation uses the active Mist session and these explicit mistapi calls:

| Method | Purpose |
|---|---|
| `getSelf` | Read profile grants |
| `listMspOrgs` | Discover organizations under an MSP grant |
| `getOrgLicensesSummary` | Read entitlement and purchase records |
| `getOrgLicensesBySite` | Read in-use quantities |
| `getOrgInventory` | Read inventory and stock |
| `searchOrgJsiAssetsAndContracts` | Read contract evidence |
| `listMspLicenses` | Read optional MSP purchase and amendment data |

The operation validates organization IDs before organization-specific calls.
The operation does not call MSP endpoints after the profile denies an MSP grant.

## Output Files

The operation writes five CSV-compatible reports:

| File | One row for |
|---|---|
| `CrossOrgOrganizationStatus.csv` | One organization or discovery status |
| `CrossOrgSubscriptionPurchase.csv` | One available subscription purchase or amendment |
| `CrossOrgSubscriptionBalance.csv` | One organization and subscription type |
| `CrossOrgStockInventory.csv` | One unassigned inventory device |
| `CrossOrgContractEvidence.csv` | One JSI contract evidence row |

Each report includes an organization or organization-status field as required.
The purchase report includes quantity, remaining quantity, start date, end date, created date, and deal period.
The balance report includes purchased, entitled, in-use, unused, over-entitlement, status, and band.
The stock report includes serial, MAC, model, device type, organization, JSI match status, and license review state.
The contract report includes serial, status, support evidence, claim state, and available contract date.

## Failure Contract

An HTTP 4xx or 5xx response remains visible for the affected organization.
The report must not convert that failure to an empty zero.
A 429 response waits 60 seconds and retries once.
No other HTTP response is retried.
An absent JSI account creates an unavailable contract state.
The report continues when one organization succeeds and another organization fails.

## Source Attribution

Each report row includes source attribution.
The text names `MistOrgLicensingComparison` by `jmorrison-juniper`.
The text names the CC BY-NC-SA 4.0 source license.

## Summary Contract

The console prints counts for:
- Organizations discovered
- Organizations with success or partial status
- Organizations with failed status
- Subscription purchase rows
- Subscription balance rows
- Stock rows
- Contract evidence rows

The console counts match the exported result categories.
