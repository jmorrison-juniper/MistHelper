### Explain why no documented endpoint can replace the Marvis Actions labs endpoints (menu 270)

- **Changed**: The Marvis Actions API report now holds the section "Why no
  documented endpoint can replace the labs endpoints". The section states the
  three conditions that a replacement must meet, and it compares each similar
  documented endpoint with the `labs` list, schema, and resolve. It covers the
  alarm search, count, acknowledge, and suppress requests, and the alarm
  definitions. It also covers the MSP count, the troubleshoot endpoint, the device
  events, the SLE and Marvis Client endpoints, the Marvis settings, and the
  webhooks. Issue #3368.

- **Changed**: The report records the live evidence of 2026-09-25. Only 33 of 114
  actions had a Marvis alarm, and no alarm holds the `row_key` that the resolve
  needs. The alarm search has no status filter, and the alarm acknowledge records
  a note, not a resolution code. Issue #3368.

- **Changed**: A table in the report compares the 35 topics with the alarm types.
  It shows where the names, the examples, and the live join do not agree. The
  report also names the errors in the examples of the alarm definitions. It tells
  the operator to join the alarm `id` to the action `uuid` instead. Issue #3368.
