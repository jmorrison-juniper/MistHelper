# Data model: AP warning report

Each row represents one inventory AP in one organization.
The natural key is `org_id` plus normalized `mac`.

## Identity and assignment

Retain `org_id`, `device_id`, `mac`, `name`, `serial`, `model`, `site_id`, and `site_name`.
Retain a `site_lookup_status` value of `found`, `unassigned`, or `missing`.
Do not invent a missing site name.

## Trouble evidence

Retain `code`, `definition_status`, `code_key`, `code_name`, and `code_description`.
`definition_status` is `known` or `unknown`.
Retain `trouble_source`, `trouble_timestamp`, and `reported_at`.
Available times use UTC ISO 8601.
An absent observation time remains empty.

## Connection state

Retain `connection_status` as `connected`, `disconnected`, or `unknown`.
Prefer statistics when they provide a valid connection state.
Otherwise use the inventory `connected` Boolean.

## Validation

Reject malformed collection rows, missing AP MAC addresses, duplicate identity records, and conflicting definition codes.
Accept colon-separated, dash-separated, or plain twelve-digit MAC addresses.
Normalize numeric trouble codes to at least two digits.
Reject Boolean, negative, fractional, and structured code values.
Absent, empty, or zero codes are not reportable.
Reject malformed observation timestamps rather than substituting the report time.
