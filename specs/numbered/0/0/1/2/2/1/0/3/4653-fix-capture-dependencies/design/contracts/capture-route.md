# Capture Route Contract

**Feature**: [spec.md](../../spec.md)

The existing endpoint is `POST /api/runs/<run_id>/capture/start`.

| Condition | Result |
|---|---|
| The request has a valid operator session and storage, and capture returns an ID. | Return HTTP 202 and the existing pending-capture response. |
| The request has no valid operator session. | Return HTTP 401 before storage construction or capture work. |
| Request storage or capture service construction fails. | Return HTTP 503 before a Mist request or success response. |
| A capture service override is configured. | Use the override without constructing production request resources. |

The route must not start a firmware upgrade. Existing authorization and site-lock checks remain in force.
