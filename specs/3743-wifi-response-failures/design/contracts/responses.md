# Response Contract

## Accepted Page

Each page has an integer HTTP 200 status and a readable record list.
Boolean and string statuses do not qualify.
The record list contains objects only.
Both list bodies and search-result bodies retain their order.

An empty accepted list means no records on that page.
A next-page link still requires another validated page.

## Failed Page

A missing response, invalid status, refusal, parse failure, or invalid shape stops the export.
No final CSV writer, final exporter, router, or SQLite constructor runs.
The existing error notice identifies the endpoint, site, page, and status.
Parse context contains no raw body or credential.

## Output

Complete successful reads retain the existing merge and output selection.
Complete empty reads retain the existing placeholder.
The requested output name remains `SiteWiFiClients.CSV`.
This feature does not define or repair case-insensitive CSV suffix handling.
