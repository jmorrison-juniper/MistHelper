# Portal contract

Menus 305 and 306 appear in the firmware category on `/operations`.
Selection reveals controls in the right workspace with the left category list unchanged.
Legacy dedicated URLs select the same integrated workflow.

`POST /api/firmware-policy/preview` accepts organizations and policies.
`POST /api/settings-restore/preview` accepts bundle, records, and cloud.
Both return HTTP 202 with job_id. They create no cloud writes.

`GET /api/firmware-policy/jobs/<job_id>` returns session-owned sanitized status.
Ready status includes the single-use token and verified backup rows.
Every saved record must also pass firmware-policy restoration projection before ready status.
Unsupported restoration shapes cause failed status without confirmation or settings writes.
Active status includes phase, counts, and request-wait estimates when available.
Foreign owners cannot read status or consume a token.

The existing apply endpoints accept token and the exact confirmation word.
They return HTTP 202 with job_id. A second consumption fails.
Application retains the preparation job identifier, including after a lost browser response.
Same-host workers route polling and consumption to the live owner without replay.
Conflicting cloud and organization writers fail explicitly before cloud requests.
Cancellation consumes readiness without cloud writes.

Every mutation requires existing CSRF and access controls.
Errors contain checked messages without settings or exception bodies.

Restoration previews and controls explicitly state firmware-policy-only scope.
Complete private source and recovery backups do not imply complete settings replacement.
The preview reports schedule defaults and policy removal effects without unrelated settings values.
