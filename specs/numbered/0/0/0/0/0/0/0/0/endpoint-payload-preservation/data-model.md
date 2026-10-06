# Data Model: Endpoint Payload Preservation

## Response payload

A decoded response from an existing `mistapi` endpoint method.

| Field | Type | Rule |
| --- | --- | --- |
| `status_code` | integer | Successful object evidence requires HTTP 200 behavior. |
| `data` | list, dictionary, tuple, or null | The SDK decoder supplies this value. |
| `next` | string or null | A non-null value indicates pagination. |
| `operation` | string | Must identify the selected endpoint method. |

## Proven response shape

One of the documented shapes accepted by this feature.

| Shape | Required fields | Record count |
| --- | --- | ---: |
| Summary trend object | `start`, `end`, `sle`, `classifiers` | 1 when non-empty |
| Classifier trend object | `start`, `end`, `metric`, `classifier` | 1 when non-empty |
| Top-level list | list elements | Number of elements |
| `results` envelope | `results` list and valid page metadata | Number across pages |

Unknown dictionaries are not proven response shapes.

## Received record

A response record available after shape handling and before output persistence.
The two documented non-empty objects each produce one received record.

## Written record

A normalized record accepted by the existing output boundary after flattening
and multiline escaping. The writer keeps the selected filename and operation
metadata.

## Validation evidence

| Field | Type | Rule |
| --- | --- | --- |
| `received_count` | integer | Count after response-shape handling. |
| `written_count` | integer | Count accepted by the output boundary. |
| `operation` | string | Identifies the export. |
| `shape` | string | Identifies list, results, proven object, empty, or discarded. |
| `status_code` | integer or null | Supports failure evidence without exposing secrets. |
| `complete` | boolean | True only when counts match and the response is valid. |

A mismatch makes `complete` false and produces visible validation evidence.

## State transitions

```text
decoded response
  -> proven object or paginated records
  -> received records
  -> normalized records
  -> written records
  -> complete only when received_count == written_count
```

Empty valid responses stop with zero received and zero written records.
Unknown or malformed payloads stop with a visible discard or error reason.
