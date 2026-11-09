# Verification control contract

`GET /api/operations/parameters/247` keeps the interactive category and one required text parameter.
That parameter adds `input_type: password`. Its stable control identifier is `param-email_change_token`.

The renderer accepts `password` as a display override. Absent or unsupported overrides retain `text`.
The visible label remains `Email Change Token` with the required marker.

`POST /api/operations/run` keeps this request shape:

```json
{"menu_number":"247","parameters":{"input_answers":["synthetic verification value"]}}
```

The browser must not trim, encode again, mask, or replace the answer.
Empty input keeps Run disabled. No named-answer conversion applies.

The password control masks display only. SDK logs, request data, browser memory, and server handling remain outside this mitigation.
