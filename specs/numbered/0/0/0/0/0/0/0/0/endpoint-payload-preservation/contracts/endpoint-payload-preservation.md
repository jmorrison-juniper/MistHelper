# Contract: Endpoint Payload Preservation

## Input contract

Use the existing `mistapi` methods for:

- `getSiteSleSummaryTrend`
- `getSiteSleClassifierSummaryTrend`

Use the existing SDK session and response decoder. Do not send direct HTTP
requests when the SDK method exists. Tests use local transport fixtures and no
production credentials.

## Response contract

| Input response | Required handling |
| --- | --- |
| Non-empty documented summary trend object | Preserve as one received record. |
| Non-empty documented classifier trend object | Preserve as one received record. |
| Top-level list | Preserve every record and its order. |
| `results` envelope | Preserve every record and valid following-page order. |
| Empty list | Write zero records. |
| Empty `results` envelope | Write zero records. |
| Empty object | Write zero records. |
| Unknown non-empty object | Do not claim support without evidence. |
| Unsuccessful or malformed response | Keep current non-raising safe handling. |

## Output contract

Preserved records use the existing normalization, flattening, multiline
escaping, filename, output selection, and `api_function_name` behavior.
Existing primary-key strategies and output backends remain unchanged.

## Observability contract

When a non-empty payload is discarded, emit loud ASCII logging with:

- operation name
- response status when available
- response shape classification
- discarded record count
- a safe reason

Do not log API tokens, passwords, request authorization headers, or other
secret values.

## Validation contract

The export is complete only when:

```text
received_count == written_count
```

A mismatch must be visible and must not produce a successful complete-export
result. Tests must prove both matching counts and mismatch handling.

## Compatibility contract

Retain existing endpoint arguments, labels, filenames, menu availability,
pagination behavior, SDK dependency constraints, and deprecated-attribute
absence behavior.
