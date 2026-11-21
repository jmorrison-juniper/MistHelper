# Cross-Org Subscription, Deployed Inventory, and Stock

Menu 308 reads the subscriptions and inventory of every organization that the active Mist session can access.
The operation is read-only.
It writes no organization setting, subscription, inventory, or device state.

## Run the report

Use an API token for the configured direct organization:

```text
python MistHelper.py --menu 308
```

Use interactive MSP authentication when the account has MSP organization access:

```text
python MistHelper.py --login --menu 308
```

Complete the email, password, and 2FA prompts.
The operation reads only organizations that the profile and MSP grants authorize.

## Read the files

The operation writes these files under `data/`:

| File | Purpose |
|---|---|
| `CrossOrgOrganizationStatus.csv` | Organization, source, access, and request status |
| `CrossOrgSubscriptionPurchase.csv` | One purchase or amendment row for each available subscription record |
| `CrossOrgSubscriptionBalance.csv` | Purchased, entitled, in-use, unused, and over-entitlement quantities |
| `CrossOrgDeployedInventory.csv` | One deployed device row for each inventory identity with a site |
| `CrossOrgDeployedInventorySummary.csv` | One deployed quantity row for each organization and device type |
| `CrossOrgInventorySummary.csv` | Deployed, stock, and combined quantity rows for each organization and device type |
| `CrossOrgStockInventory.csv` | Unassigned inventory that may require a subscription or support review |
| `CrossOrgContractEvidence.csv` | JSI contract evidence matched to inventory serial numbers |

The `deal_period` column separates records dated on or before 2023-12-31 from records dated after 2023-12-31.
The `band` and `days_remaining` fields show the subscription expiry risk.
Missing dates remain `Missing`.
Missing counts remain `Missing`.
They do not become zero or expired values.

## Read deployed inventory evidence

A deployed inventory row has a `site_id`.
The report keeps the site, serial, MAC, model, name, device type, and connection status when the source provides them.
The deployed summary groups these rows by organization and device type.
The summary does not combine deployed devices with unassigned stock.
`CrossOrgInventorySummary.csv` combines the deployed and stock quantities.
Use the `inventory_quantity` column to review all organization-assigned inventory identities.
The `serial` column uses the physical chassis serial when a source row has a synthetic 020003 or 020004 virtual identity.
The `vc_mac`, `chassis_serial`, `chassis_mac`, and `chassis_model` columns preserve the source VC evidence.
Menu 308 reads `getSiteDeviceVirtualChassis` for logical switch inventory.
Each `members[].serial` value becomes one deployed physical switch row.

The report reconciles every paginated inventory page.
One inventory set can contain 27,000 or more deployed devices.
The deployed count comes from the live organization inventory source.
The 2026-11-11 MSP inventory snapshot is a comparison baseline, not a live source.

## Read stock evidence

A stock row is an inventory record with no `site_id`.
A stock switch with a synthetic VC identity uses the physical chassis serial and MAC when the source provides them.
The report does not limit stock to AP and switch records.
It includes gateway, SSR, Mist Edge, router, and other inventory types.
The JSI match uses serial number.
A no-match status means JSI evidence did not match that serial.
It does not prove that the device has no license or support contract.

## Failure behavior

A failed organization leaves a visible organization status row.
The report does not convert that failure to zero purchased, entitlement, or stock quantities.
An HTTP 429 response waits 60 seconds and retries once.
Other HTTP failures stop retry and remain visible.
The operation continues to other organizations after a partial failure.
An absent JSI account makes contract evidence unavailable.
The `--standalone` flag disables ArangoDB, Redis, and shared API request admission.
Close a CSV report in Excel or another program before you rerun the operation.
If a stable CSV name remains locked, the report writes a UTC timestamped fallback file.

## Source attribution

This report uses the workflow and purchase-balance concepts of
`MistOrgLicensingComparison` by `jmorrison-juniper`.
The source project uses CC BY-NC-SA 4.0.
Each report row includes the source attribution.
