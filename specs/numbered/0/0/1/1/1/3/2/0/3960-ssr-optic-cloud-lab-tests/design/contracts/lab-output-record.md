# Contract: Lab output record

This contract sets the record for each owner-only lab step. The owner fills each field. The implementer copies the sanitized text to the target in the runbook.

## Record fields

| Field | Rule |
|-------|------|
| Step identifier | One of H-1 to H-7. Use the identifier from tasks.md. |
| Release string | The software release that the router reports. Copy it exactly as the router prints it. |
| Command | The command text from tasks.md. Copy it without change. |
| Sanitized text | The output after sanitization. Keep each word of the error text as printed. |
| Removed items | A count of each removed type: address, serial number, customer name. Never record a removed value. |
| Run date | The run date in UTC, in ISO 8601 form. |

## Targets

| Step | Target in documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | Table change |
|------|-----------------------------------------------------------------|--------------|
| H-1 | Section 11 table, the row for `show device-interface <name> optics-statistics` (line 245). The error text goes in the What happens cell. | Row 360 names the release string. |
| H-2 | Section 11 table. Add one row for `show device-interface name <name> optics-statistics`, and record the error text in it. | Row 361 names the release string and points to the new section 11 row. |
| H-3 | Step 1 of section Check an optic without optics-statistics (line 117). Record the port names that the output lists. | Row 362 names the release string. |
| H-4 | Step C2 (line 104). Add the names of the power level fields and the threshold fields. | Row 363 names the release string. |
| H-5 | Step D7 (line 141). Change a value only when the output differs. | Row 364 names the release string. |
| H-6 | Last sentence of section Test the path to the Mist cloud (line 166). Change the sentence only when the Testing Tools operate. | Row 365 names the release string. |
| H-7 | Line 149. Add a source link, or remove the sentence. | None. |

## Sanitization checklist

Each item must pass before the commit.

- The text holds no IPv4 address. The only allowed addresses are 8.8.8.8 and 1.1.1.1, which step D1 uses.
- The text holds no MAC address.
- The text holds no serial number.
- The text holds no customer name, site name, or tenant name.
- The text holds no credential, token, or password.
- The command text is unchanged.
- The release string is present.

Warning: a committed address or customer name stays in the public repository history after a revert.
