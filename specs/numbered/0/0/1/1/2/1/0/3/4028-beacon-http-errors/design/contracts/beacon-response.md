# Beacon response contract

The operation calls `mistapi.api.v1.sites.beacons.getSiteBeacon(session, site_id=site_id, beacon_id=beacon_id)`.

| Response | Required result |
| - | - |
| HTTP 404 or 503 with an error mapping | Failure message, one request, no export |
| HTTP 302 with a mapping | Failure message, no export |
| HTTP 200 or 299 with beacon data | Existing export rows and metadata |
| HTTP 429 followed by HTTP 200 | Existing adaptive delay, two requests, one export |
| Repeated HTTP 429 | Bounded retries, failure message, no export |
| Existing raw mapping | Existing successful export |

Error messages contain the HTTP status, not the response body.
