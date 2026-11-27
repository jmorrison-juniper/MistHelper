# Contract: Redis document key and write result

This contract defines the Redis key and the write result for device events after the fix. It applies to `RedisJSONWriter.write` (RC-04, RC-05).

## Key

- Format: the endpoint name, then the value of each primary key field, in strategy order.
- Device events: `searchOrgDeviceEvents:<record_id>:<org_id>:<timestamp>`.
- Each value converts with `str`.
- A missing field or a null value rejects the row. The key builder uses no sentinel value.

## Rejection

- Log event: `json_key_missing`, at error level. The log holds the endpoint and the field name. It holds no row value.
- The rejected row adds one to `records_failed`.
- The rejected row is not sent to Redis.

Caution: The ArangoDB write for the same row still runs. The archive keeps the row under its `record_id` key.

## Write

- Each accepted row sends a JSON set with the root path `$`, then an expire command, in one pipeline (RC-05).
- A set reply that is an exception adds one to `records_failed` and logs `json_set_failed` (RC-06).
- A set that succeeds adds one to `records_written`, even when the document replaces an identical document.

## Result

- `success` is true only when `records_failed` is zero.
- The dual write result reports success only when the Redis write and the ArangoDB write both succeed (RC-12).
- A failed Redis write marks the dual write as failed. Operators see the failure in the export log.
