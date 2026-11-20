# Data Model: Deployed Inventory Report

## Organization Status

Fields:
- MSP ID
- Organization ID
- Organization name
- Source
- Request status
- Error

This entity records organization discovery and inventory read status.

## Deployed Inventory Row

Fields:
- MSP ID
- Organization ID
- Organization name
- Site ID
- Site name
- Serial
- MAC
- Model
- Name
- Device type
- Deployment status
- Connection status
- Source attribution

Rules:
- A record with a site ID is deployed.
- A record with no site ID is stock.
- Missing identity fields remain `Missing`.
- The row grain is one source inventory identity.
- Formula text is neutralized before export.

## Deployed Inventory Summary

Fields:
- MSP ID
- Organization ID
- Organization name
- Device type
- Deployed quantity
- Source inventory status
- Source attribution

Rules:
- Count each deployed detail row once.
- Group by organization and normalized device type.
- A failed organization inventory read returns Missing quantity.
- A successful organization with no deployed records returns zero deployed quantity.

## Inventory Summary

Fields:
- MSP ID
- Organization ID
- Organization name
- Device type
- Deployed quantity
- Stock quantity
- Inventory quantity
- Source inventory status
- Source attribution

Rules:
- Count each deployed detail row once.
- Count each stock detail row once.
- `inventory_quantity` is the sum of deployed and stock quantities.
- Failed inventory reads use `Missing` for every quantity.

## Stock Inventory Row

Fields:
- Organization identity
- Serial
- MAC
- Model
- Name
- Device type
- JSI match status
- Contract status
- Contract end date

Rules:
- A record with no site ID is stock.
- Stock does not enter deployed detail or summary rows.

## Relationships

- One organization status row describes one organization inventory read.
- One deployed inventory row belongs to one organization and one site.
- One deployed inventory summary row contains one organization and one device type.
- One stock row belongs to one organization but has no deployed site.

## Logging Record

Fields:
- Timestamp
- Logger name
- Severity level
- Event name
- Optional key-value context

Rules:
- The backend applies the configured console or file threshold.
- INFO and DEBUG remain below WARNING and CRITICAL thresholds.
- WARNING and ERROR remain visible at those thresholds.
- Credential-shaped keys become the redaction placeholder.
- Terminal output may enable ANSI color.
- File output contains no required ANSI color sequence.
