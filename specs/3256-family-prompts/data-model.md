# Data Model: Endpoint family per-choice prompts

## Endpoint family registry row

- `category`: `interactive`.
- `parameters`: one chooser parameter named `endpoint_operation`.

## Endpoint option

- `value`: The one-based position the CLI chooser expects.
- `label`: The operation name shown to the operator.
- `required`: The full required tuple from the exporter row.

## Dynamic parameter

- `name`: The identifier that the handler prompt reads.
- `label`: A readable label for the identifier.
- `param_type`: `site`, `text`, or an existing supported portal control type.
- `required`: Always true for prompted identifiers.

## Organization identifier

The portal resolves the organization identifier through application context. The metadata can show that the selected operation needs `org_id`, but the answer list must not include a queued `org_id` value unless the handler asks for it.
