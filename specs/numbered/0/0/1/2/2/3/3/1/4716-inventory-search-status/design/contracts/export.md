# Export Contract

`OrgInventorySearchExporter.inventory()` returns `None`.
It retains organization selection, filter prompts, and exception logging.
A canceled organization selection makes no request and writes no output.
The SDK operation identifier remains `searchOrgInventory`.
The filename remains `OrgInventorySearch_<org_id>.csv`.

An invalid initial response produces an error without pagination, transformation, or output.
A valid empty response retains its empty-result message.
A false writer result produces an error without persistence or export-success messages.
Successful rows retain the existing transforms and output arguments.
