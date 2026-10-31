# Retry scope data model

## Operator selection

The server-side operator session keeps the selected site tuple.
Save, confirmation, and submission do not replace this tuple.

## Durable parent

For retry saves, `site_ids` holds selected sites with validated planned targets, in selected order.
`site_names` holds names for exactly those site IDs.
`retry_of_operation_id` remains the link to the settled source.
The nonce, ownership, record version, and audit fields retain their current meaning.

## Children

Each child keeps its existing body and explicit targets.
The union of planned target sites equals the effective retry scope.
No child can add a site outside the validated selected rows.

## Submission context

For an owned retry, effective IDs are the active selected IDs that occur in durable `site_ids`.
The exact-context check still compares the ordered effective IDs with durable `site_ids`.
A missing or reordered effective site refuses submission.
Plain and legacy requests keep their full selected scope.
