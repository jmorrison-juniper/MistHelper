# Contract: Juniper Service Case API (read operations)

**Source**: `Export_JuniperServiceCaseAPI.json` (OpenAPI 3.0.1, version 1.0). Only read operations are in scope.

## Base Address and Transport

- Setting: `JUNIPER_CASE_BASE_URL`. Default: `https://apigw.juniper.net/css-caseapi/1.0` (O-9).
- Method: POST with a JSON body for every operation in scope.
- Response: JSON.

## Operations in Scope

| Operation | Path | Request wrapper key | Purpose |
| - | - | - | - |
| List | `/querysrlist` | `querySRListRequest` | Requests from the last 90 days |
| Details | `/querysrdetails` | `querySRRequest` | One request, with its RMA list |
| RMA details | `/queryrmadetails` | `queryRMARequest` (O-5, live check on 2026-10-08) | One RMA, with shipping and items |
| Note details | `/querysrnotedetails` | `querySRNoteRequest` with `noteId` | Notes of one request (menu 297) |
| List of values | `/getlov` (GET, query `appid`) | None | Lists of values (menu 298) |
| Software releases | `/getSoftwareEosLov` (GET, query `appid`) | None | Software release list (menu 299) |

Out of scope: `/createsr`, `/updatesr`, `/escalatesr`, `/closesr`, `/attachfile`, `/getfileuploadtoken`. The two list-of-values reads take the query name `appid` in lowercase. The name `appId` returns an empty object. Warning: A call to a write operation changes a customer's service request. The client must not call or reference any write operation.

## Request Envelope

| Key | Rule |
| - | - |
| `appId` | From `JUNIPER_APP_ID`. Secret. |
| `userId` | From `JUNIPER_USER_ID`. Must be a registered portal user. |
| `requestDateTime` | UTC, `YYYY-MM-DDTHH:mm:ss.SSSZ` (R-04). |
| `customerSourceID` | From `JUNIPER_CUSTOMER_SOURCE_ID`. Placement differs by operation (O-10). |
| `customerUniqueTransactionID` | 32 hex characters. A new value for each attempt (R-03). Placement differs by operation (O-10). |

Placement (O-10): The export shows where each operation takes these two values.

| Operation | Placement | Basis |
| - | - | - |
| `querysrlist` | Inside `caseInformation` | Live check on 2026-10-08: the top level returned faults 906 and 908. The `caseInformation` placement returned body status 200. |
| `querysrdetails` | Inside `caseInformation` | Live check on 2026-10-08: body status 200 for a request-number lookup. |
| `queryrmadetails` | Inside `caseInformation` | Live check on 2026-10-08: body status 200 with an empty `customerCaseNumber`. |

The list, detail, and RMA placements have live evidence from 2026-10-08. Onboarding confirms the remaining operations.

### List Request

```json
{
  "querySRListRequest": {
    "requestDateTime": "2026-10-08T14:03:22.123Z",
    "appId": "<JUNIPER_APP_ID>",
    "userId": "<JUNIPER_USER_ID>",
    "caseInformation": {
      "fromDate": "2026-07-10",
      "toDate": "2026-10-08",
      "customerSourceID": "<JUNIPER_CUSTOMER_SOURCE_ID>",
      "customerUniqueTransactionID": "<32 hex characters>"
    }
  }
}
```

The window runs from `toDate` minus 90 days to `toDate`. Both dates use the `YYYY-MM-DD` format in UTC.

Live evidence (2026-10-08): the top-level placement, which the export schema and example show, returned HTTP 400 with faults 906 and 908. The `caseInformation` placement returned HTTP 200 with body status 200 and no fault for the window 2026-09-01 to 2026-09-30. Use the `caseInformation` placement for `querysrlist`.

### Detail Request

```json
{
  "querySRRequest": {
    "appId": "<JUNIPER_APP_ID>",
    "userId": "<JUNIPER_USER_ID>",
    "requestDateTime": "2026-10-08T14:03:22.123Z",
    "caseInformation": {
      "customerCaseNumber": "<join value from JUNIPER_TICKET_KEY_FIELD>",
      "serviceRequestNumber": "<optional request number>",
      "customerSourceID": "<JUNIPER_CUSTOMER_SOURCE_ID>",
      "customerUniqueTransactionID": "<32 hex characters>"
    },
    "contact": {
      "accountID": "<JUNIPER_ACCOUNT_ID>",
      "contactEmail": "<JUNIPER_CONTACT_EMAIL>"
    }
  }
}
```

Live evidence (2026-10-08, read only): a lookup by request number returned body status 200 with no fault. The reply sets `customerCaseNumber` to null. The list returned the same value as `serviceRequestNumber` for each of the 15 cases of September 2026. The customer case number therefore cannot come from the detail reply in this account.

Fault 956 requires one of `customerCaseNumber` or `serviceRequestNumber`. Fault 763 means the case number matches more than one request. The export says to call the detail operation with `serviceRequestNumber`. The client takes candidate request numbers from the 90-day list. The engine marks the ticket as ambiguous and does not choose a request (R-05).

### RMA Request

The RMA request uses the same `caseInformation` and `contact` blocks as the detail request. It also adds `rmaNumber` beside them, inside the wrapper. The export has no request example for this operation. The other eleven request examples each wrap their body under `<operation>Request`. The client therefore uses `queryRMARequest` (O-5). The export example for the response uses `queryRMAResponse`. Live check on 2026-10-08: `queryRMARequest` with an empty `customerCaseNumber` returned body status 200 for one RMA with two items.

## Response Envelope

| Field | Meaning |
| - | - |
| `statusCode` | String. `200` success. `300` warning, with a result and faults. `400` error, with faults and no result. |
| `status` | `Success`, `Warning`, or `Error` |
| `message` | Plain text |
| `responseDateTime` | UTC text |
| `fault` | List of objects: `errorClass` (`Error` or `Warning`), `errorType` (`Validation` or `Processing`), `errorCode` (string), `errorMessage` |

Rules:

- The body `statusCode` decides the outcome (R-07). The HTTP status decides only the transport outcome.
- HTTP `3xx` is never followed. It is reported as an unexpected result.
- The detail and RMA responses may arrive with or without their wrapper keys (`querySRResponse`, `queryRMAResponse`). The parser accepts both.

## Result Fields Used

| Operation | Fields |
| - | - |
| List `cases[]` | `customerCaseNumber`, `serviceRequestNumber`, `caseTypeCode`, `priority`, `synopsis`, `srStatus`, `serialNumber`, `productID`, `productSeries`, `platform`, `routerName`, `software`, `version`, `release`, `specialRelease`, `accountID`, `accountName`, `lastModifiedDate`, `linkToCase`, `customerSourceID` |
| Detail | `serviceRequestNumber`, `customerCaseNumber`, `customerSourceID`, `caseType` (`caseTypeCode`, `caseTypeDescription`), `priority`, `srStatus`, `synopsis`, `contact` (`accountID`, `accountName`), `rma[]` (`rmaNumber`, `items[]` with `itemNumber`, `itemType`, `itemStatus`), `product` (`serialNumber`, `productID`, `productSeries`, `platform`, `version`, `release`, `software`, `specialRelease`, `routerName`) |
| RMA | `rmaNumber`, `rmaContact` (`companyName`, `contactName`, `contactEmail`, `telephoneCountryCode`, `telephoneNumber`, and address fields either flat or inside `address`), `defectiveItems[]`, `replacementItems[]`, `ceItems[]` |

Item fields:

- `defectiveItems[]`: `itemNumber`, `dateTime`, `productID`, `serialNumber`, `trackingNumber`, `carrierDescription`, `receivedDate`, `defectiveItemStatus`.
- `replacementItems[]`: `itemNumber`, `defectiveItemNumber`, `productID`, `serialNumber`, `carrierDescription`, `shipDate`, `shipmentServiceLevel`, `trackingNumber`, `replacementStatus`, `deliveredDate`, `receivedBy`.
- `ceItems[]`: `defectiveItemNumber`, `productID`, `engineerStatus`, `vendorName`, `vendorPhone`, `serviceRequestedDate`, `actualServicedDate`, `contactedDate`, `estimatedArrivalDate`.

Warning: A strict date parser stops on these values and fails the run. The export contains `deliveredDate` = `2017-09-05-T12:57:00.000Z`. It also contains `receivedDate` = `2017:09:12T17:37:30.000Z`. Both values are malformed. Keep the raw text when parsing fails (R-09).

Fields that the client ignores: `notes`, `recentNotes`, `attachments`, `linkedReferences`, `escalate`, `problemDescription`.

## Fault Codes

Codes that a read operation can return:

| Code | Meaning | Operator action |
| - | - | - |
| 707 | appId and customerSourceID combination is not valid | Check `JUNIPER_APP_ID` and `JUNIPER_CUSTOMER_SOURCE_ID` |
| 735 | appId is not valid | Check `JUNIPER_APP_ID` |
| 750 | More than one contact record for contactEmail | Contact Juniper |
| 751 | accountID is not valid | Check `JUNIPER_ACCOUNT_ID` |
| 752 | customerSourceID and accountID combination is not valid | Check both values |
| 753 | contactEmail is not a registered user | Check `JUNIPER_CONTACT_EMAIL` |
| 754 | contactEmail is not linked to accountID | Check `JUNIPER_CONTACT_EMAIL` |
| 755 | userId is not linked to accountID | Check `JUNIPER_USER_ID` |
| 756 | customerCaseNumber is not linked to the account | Record the ticket as unmatched |
| 757 | serviceRequestNumber is not valid | Check the input |
| 763 | customerCaseNumber has more than one request with the same value | Call the detail operation with `serviceRequestNumber` |
| 765 | rmaNumber is not valid | Check the input |
| 768 | Serial number or SSRN is not valid | Check the input |
| 769 | More than one contact record for userId | Contact Juniper |
| 771 | userId is not a registered user | Check `JUNIPER_USER_ID` |
| 775 | rmaNumber does not belong to serviceRequestNumber | Check the input |
| 778 | serviceRequestNumber is not linked to the account | Check the input |
| 900 | appId is missing | Set `JUNIPER_APP_ID` |
| 901 | userId is missing | Set `JUNIPER_USER_ID` |
| 902 | requestDateTime is missing | Report as an internal error |
| 903 | requestDateTime format is wrong | Report as an internal error |
| 906 | customerSourceID is missing | Set `JUNIPER_CUSTOMER_SOURCE_ID` |
| 907 | appId and customerSourceID combination is not valid | Check both values |
| 908 | customerUniqueTransactionID is missing | Report as an internal error |
| 931 | serviceRequestNumber is missing | Check the input |
| 932 | appId and userId combination is not valid | Check both values |
| 935 | appId is invalid | Check `JUNIPER_APP_ID` |
| 937 | Invalid authentication method | Confirm the credential type (O-2, O-8) |
| 938 | User not authenticated with a valid certificate | Confirm the credential type (O-8) |
| 944 | rmaNumber is missing | Check the input |
| 955 | Duplicate customerUniqueTransactionID | Retry with a new identifier (R-03) |
| 956 | Neither serviceRequestNumber nor customerCaseNumber is given | Check the input |
| 973 | System error while preparing the response | Retry later. Report if it repeats. |
| 999 | A key exceeds its maximum length | Report as an internal error |

The client shows any code outside this table with its raw message.
