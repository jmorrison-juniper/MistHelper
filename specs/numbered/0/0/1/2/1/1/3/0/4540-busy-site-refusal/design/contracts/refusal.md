# Busy-site response contract

The browser intercepts `POST /api/org-upgrades` and returns status 409.
The envelope uses code `site_lock_wrong_run` and a synthetic operator message.

| Case | `details.next` | Expected link count |
| - | - | - |
| Owning operation | `/upgrade/org/jobs/org-run-busy-4540` | 1 |
| No address | Absent | 0 |
| Unsafe address | `https://example.invalid/upgrade/org/jobs/org-run-busy-4540` | 0 |

Every case must show the exact message without page errors.
The confirmation field must remain empty and disabled.
The start control must remain disabled.

The owning-operation case must show the complete refusal in the viewport after the scroll.
