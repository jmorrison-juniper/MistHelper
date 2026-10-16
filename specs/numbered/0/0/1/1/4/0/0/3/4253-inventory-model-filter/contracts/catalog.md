# Catalog contract

`POST /api/firmware-policy/catalog` retains `organizations` and `kinds`.
Optional `show_all` defaults to `false` and accepts only a JSON boolean.
The response retains `catalogs`, including empty model maps when inventory has no compatible model.
Errors retain the protected route's checked error response.
No settings writes or backups occur during catalog requests.

The CLI displays Inventory models as its first scope choice.
Show all supported models is an explicit second choice.
Blank input still cancels. Empty filtered choices explain how to select all supported models.

Preparation continues validating every chosen version against all selected organizations.
This display preference does not weaken confirmation, backup, or freshness checks.
