# Report Contract: Deployed Inventory

## CrossOrgDeployedInventory.csv

One row per deployed inventory identity.

Required fields:
- msp_id
- org_id
- org_name
- site_id
- site_name
- serial
- mac
- model
- name
- device_type
- deployment_status
- connected
- source_attribution

Deployment status is `deployed`.

## CrossOrgDeployedInventorySummary.csv

One row per organization and device type.

Required fields:
- msp_id
- org_id
- org_name
- device_type
- deployed_quantity
- request_status
- source_attribution

A successful inventory read with no deployed rows uses quantity zero.
A failed inventory read uses `Missing`.

## CrossOrgInventorySummary.csv

One row per organization and device type.

Required fields:
- msp_id
- org_id
- org_name
- device_type
- deployed_quantity
- stock_quantity
- inventory_quantity
- request_status
- source_attribution

`inventory_quantity` is the sum of the deployed and stock quantities.
A failed inventory read uses `Missing` for all three quantities.

## CrossOrgStockInventory.csv

One row per unassigned inventory identity.

The existing stock contract remains unchanged.

## Console Contract

The console summary adds:
- Deployed inventory rows
- Deployed inventory organizations
- Deployed inventory summary rows

The existing organization, purchase, balance, stock, and contract counts remain visible.
