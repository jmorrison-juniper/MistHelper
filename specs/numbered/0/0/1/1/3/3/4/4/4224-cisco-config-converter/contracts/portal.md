# Portal Contract: Cisco Config Converter

## Navigation and Page

- The converter appears as one navigation entry in the shared MistHelper portal.
- The page contains input selection, template name and type fields, conversion proposal,
  unsupported items, known gaps, review, and export controls.
- Preview and export remain available without Mist credentials.
- Cloud apply is not part of the first release.
- Every new interactive control has a stable `data-testid`.

## Input

- Accept `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log` files up to 16 MiB.
- Limit the multipart request body to the file limit plus 16 KiB of form overhead.
- Reject empty or whitespace-only files, invalid UTF-8, null characters, unsupported suffixes,
  path-like names, and files above the limit.
- Treat the uploaded file name as display text and process bytes in memory.
- Do not place file content or credentials in logs or browser storage.
- MistHelper has no shared portal upload-size setting. The 16 MiB limit is a feature policy based
  on the independently observed source behavior.

## Preview and Export

- Convert only global IPv4 `ip name-server` directives to `dns_servers`.
- Accept the verified template types `standalone` and `spoke`.
- Require a template name with 1 to 120 non-whitespace characters.
- Preserve IPv6, malformed, unknown, and other commands as unsupported items.
- Do not add gateway-role or hardware-model mappings.
- Unsupported items and known gaps remain visible in review and export.
- Identify unsupported items by source line and command category. Omit their values because unknown commands can contain credentials.
- Preview and export do not make Mist API requests.
- Export contains the operator-provided `name` and selected `type`. It contains `dns_servers`
  only when supported input provides values. It also contains unsupported items and known gaps,
  but no credentials.
- Store only proposal digests in the signed Flask session. Require the same digest for review
  and export. Reject edited proposals.
- Extend the shared portal base template. Use its `csrf-token` meta value.
- Include the CSRF token in the multipart preview form and send `X-CSRFToken` on every JSON
  POST request.
- Keep CSRF protection enabled. Test preview, review, and export with `CSRFProtect` active.
- Before registration, configure the host with `ConverterRequest` to prevent upload spooling before CSRF reads multipart data.
- Blueprint registration rejects hosts without this request class or active `CSRFProtect`.

## Errors

- Invalid input returns a clear operator-facing error and makes no Mist API request.
- A malformed command remains visible as unsupported and does not invalidate the whole file.
- A file with no supported command does not include an empty `dns_servers` field.

## Integration Status

The feature blueprint passes isolated route and browser tests. Shared portal registration and
navigation remain blocked because PR #4208 owns `web_portal/app.py` and
`web_portal/templates/base.html`. This branch does not edit either file.
