# Data Model: Webhook response status

## Entities

### Initial response

- Source: the object that `listOrgWebhooks` or `searchOrgWebhooksDeliveries` returns (R76, R77).
- Attributes that the exporter reads: `status_code` (R79) and `data` (R78). The `data` value passes to `mistapi.get_all` (R80).
- Natural key: none. Each call produces one initial response.

### HTTP status

- Type: integer that is not a Boolean.
- Accepted values: 200 through 299 (R03).
- Rejected values: None, Booleans, floats, numeric strings, and each integer outside 200 to 299.
- Natural key: none. The status is a value, not an entity.

### Webhook row

- Source: one item that `mistapi.get_all` returns for the list call.
- Natural key: `id`, read as text and trimmed (R85).
- Display label: `name`, or `id` when `name` is empty.

### Delivery row

- Source: one item that `mistapi.get_all` returns for the delivery call.
- Natural key: `id`, `webhook_id`, and `timestamp` (R27).
- Persistence: the existing flatten and write steps store each row. The repair changes no step.

## State transitions

Initial response:

1. RECEIVED. The SDK call returns an object.
2. ACCEPTED. The HTTP status is an integer from 200 through 299.
3. REJECTED. The HTTP status is missing, invalid, or outside 200 through 299. The exporter logs one error. It stops before pagination.
4. PAGINATED. The exporter calls `mistapi.get_all` once for an accepted response.
5. EMPTY or PERSISTED. An empty result keeps its empty-result notice. A non-empty result goes to the writer.

Delivery call:

1. The delivery call runs only after one webhook selection.
2. The initial response follows the same transitions as the list call.
3. A rejected delivery response makes zero writer calls.
