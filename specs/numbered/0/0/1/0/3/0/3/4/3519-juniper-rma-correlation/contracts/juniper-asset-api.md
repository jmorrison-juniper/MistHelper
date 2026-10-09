# Contract: Juniper Service Asset API (read operation)

**Source**: `Export_JuniperServiceAssetAPI.json` (OpenAPI 3.0.1, version 1.0).

## Base Address

- Setting: `JUNIPER_ASSET_BASE_URL`. Default: `https://apigw.juniper.net/css-asset/1.0` (O-9).
- Method: POST with a JSON body.

## Operation in Scope

| Operation | Path | Request wrapper key | Limit |
| - | - | - | - |
| Asset details | `/queryAssetsDetails` | `queryAssetsDetailsRequest` (in the export example) | 1 to 300 serial numbers per request (fault 991) |

Out of scope: `/queryAssetsBulkData`. It returns links to AWS S3 files. Those hosts are not on the approved host list (FR-004).

## Request

| Key | Rule |
| - | - |
| `appId` | From `JUNIPER_APP_ID` |
| `requestDateTime` | UTC, `YYYY-MM-DDTHH:mm:ss.SSSZ` (R-04) |
| `customerUniqueTransactionID` | Alphanumeric characters only (fault 986). Use 32 hex characters (R-03). |
| `customerSourceID` | From `JUNIPER_CUSTOMER_SOURCE_ID` |
| `serialNumbersOrSSRNs` | Array of 1 to 300 strings |

```json
{
  "queryAssetsDetailsRequest": {
    "appId": "<JUNIPER_APP_ID>",
    "requestDateTime": "2026-10-08T14:03:22.123Z",
    "customerUniqueTransactionID": "<32 hex characters>",
    "customerSourceID": "<JUNIPER_CUSTOMER_SOURCE_ID>",
    "serialNumbersOrSSRNs": ["JN1234ABC", "JN5678DEF"]
  }
}
```

## Response

Two response shapes are in the export (O-6):

- The example wraps the response in `queryAssetsDetailsResponse`. It nests the result keys under a `data` object.
- The schema puts the same keys at the top level.

The parser can read either shape. The result keys are:

- `invalidSerialNumbersOrSSRNs[]`: objects with `serialNumberOrSSRN` and `message`. These numbers are not found.
- `notProcessedSerialNumbersOrSSRNs[]`: objects with the same keys. These numbers need another request.
- `assets[]`: asset records.

Top-level keys that always appear: `responseDateTime`, `customerSourceID`, `status`, `statusCode`, `message`. A fault adds `fault[]`.

## Asset Record Fields

| Group | Fields |
| - | - |
| Identity | `assetRecordId`, `assetStatus`, `serialNumber`, `softwareSupportReferenceNumber` |
| Dates | `registrationDate`, `shipDate`, `productSKUEolDate`, `productSKUEosDate` |
| Product | `productSKU`, `productSKUDescription`, `productLine`, `serviceEligible`, `assetIsFRUNoParent`, `isServiceDeclinedOnAsset`, `serviceDeclineReason` |
| Parent | `parentSerialNumber`, `parentProductSKU` |
| Site | `installedAtId`, `installedAtName`, `installedAtAddressLine1`, `installedAtCity`, `installedAtStateRegionProvince`, `installedAtPostalCode`, `installedAtCountry` |
| RMA | `rmaInfo`: the example shows one object. The schema enum lists `index`, which suggests a list. The parser accepts both (O-7). Fields: `rmaNumber`, `rmaLineItemNumber`, `rmaLineItemStatus`, `rmaDeliveredDate`, `rmaDefectiveSerialNumber`. |
| Warranty | `warranty[]`: `index`, `warrantyDescription`, `warrantyStartDate`, `warrantyEndDate` |
| Contracts | `serviceContract[]`: `index`, `contractNumber`, `endCustomer*`, `reseller*`, `salesOrderNumber`, `purchaseOrderNumber`, `contractDetails[]` |

`contractDetails[]` fields: `index`, `contractLineItemNumber`, `contractStartDate`, `contractEndDate`, `contractStatus`, `serviceSKU`, `serviceSKUDescription`, `serviceType`, `serviceSKUShipmentServiceLevel`, `serviceSKUEosDate`, `serviceSKUIsPlaceHolder`, `serviceSKUProvidesJTACsupport`.

The client stores the `endCustomer*` and `reseller*` business names and skips their address fields. It does not store the contact fields.

## Batching and Retry Rules

1. Split the serial numbers into batches of 300 or fewer. Keep the input order.

2. Send one request for each batch.

3. Collect the assets. Collect the invalid numbers as not found. Queue the not-processed numbers.

4. Send the queued numbers again. Stop after three passes. List the numbers that remain as not processed.

5. Keep the partial results when a later pass fails. Mark the run as incomplete.

Documented size limits: about 4 MB for the processed part of a response, about 6 MB for the full payload, and about 8 MB for one serial number. The response cap in R-12 covers these sizes.

## Live Evidence (2026-10-08)

The gateway rejected every call to `/queryAssetsDetails` with HTTP 401. It rejected the first call, and it rejected the call again after one token refresh. The reply body names the service `JuniperServiceAssetAPI` and the text `Unauthorized application request`. The same token works for the Case API. The rejection therefore means that the application is not enabled for the Asset API. The gateway stops the call before it checks the envelope, so the top-level placement above is not yet confirmed.

Action for Juniper: enable `JuniperServiceAssetAPI` for the application, then repeat the read-only check. The client reports the rejection as `Juniper gateway rejected the request with HTTP 401`. It does not resend the batch.

The latest live run of menu 304 and menu 300 returned the same HTTP 401 for the asset operations. Both operations need the same entitlement.

## Bulk Snapshot Operation (menu 300)

| Item | Value |
| - | - |
| Path | `/queryAssetsBulkData` |
| Wrapper key | `assetsBulkDataRequest` with `snapshotFromDate` and `snapshotToDate` |
| Window | Each date is one to seven days old, and the start date is not after the end date |
| Exports | `JuniperAssetBulkLinks.csv` (the signature is removed from each link) and `JuniperAssetBulkNoData.csv` (each snapshot date with no data) |
| Status | Blocked. Juniper returns HTTP 401 until the asset API is enabled for the application. |

## Fault Codes

| Code | Meaning |
| - | - |
| 900 | appId is missing |
| 902 | requestDateTime is missing |
| 903 | requestDateTime format is wrong |
| 906 | customerSourceID is missing |
| 907 | appId and customerSourceID do not match |
| 908 | customerUniqueTransactionID is missing |
| 935 | appId is invalid |
| 937 | Invalid authentication method |
| 955 | Duplicate customerUniqueTransactionID (retry with a new identifier, R-03) |
| 985 | Account identifier validation failed |
| 986 | customerUniqueTransactionID is invalid. Use only alphanumeric characters. |
| 991 | More than 300 serial numbers in one request (split the batch) |
| 992 | serialNumbersOrSSRNs is invalid |

Fault codes 980 and 981 concern snapshot dates. The bulk operation (menu 300) uses them. The asset details operation does not.
