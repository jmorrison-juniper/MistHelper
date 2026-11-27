# Contract: Synthetic Fixtures

All fixtures live in `tests/integration/web_portal/labs/harness.py`. Every value is invented. No fixture holds a real device name, a real address, a token, or a private framework file (FR-018).

## Server Example

The server example in `src/interfaces/labs/planner.py` uses these values:

- Example name: `two-edge-example`.
- Default run name: `lab-example-01`.
- Logical devices: `edge-a` and `edge-b`.
- Links: one link from `edge-a` to `edge-b`.

## Harness Constants

| Constant | Content | Used by |
| - | - | - |
| `SYNTHETIC_VALID_RESULT` | Devices `edge-a` and `edge-b`, one link `edge-a` to `edge-b`, and a fingerprint from the projector | TR-07, TU-03, TU-07 |
| `SYNTHETIC_EXTRA_KEY_RESULT` | The valid result plus the key `note` | TU-04 |
| `SYNTHETIC_AUTHORITY_RESULT` | The valid result plus the key `execution_authority` with the value `true` | TU-05, TR-11 |
| `SYNTHETIC_UNKNOWN_END_RESULT` | One link that names `edge-z`, which no device holds | TU-06 |
| `SYNTHETIC_DUPLICATE_ID_RESULT` | Two devices with the id `edge-a` | TU-06 |

## Stub Planners

- A planner stub with a `plan` method. The method returns one of the constants above and records its keyword arguments.
- A planner stub whose `plan` method raises `RuntimeError` with the text "synthetic failure".
- A missing planner. The test sets `app.config["LABS_PLANNER_GATEWAY"]` to a gateway whose module lookup reports `absent`.

## Rules

- Use `tmp_path` for any file that a test writes.
- Do not read a private framework path, archive, or fixture.
- Do not set `WTF_CSRF_ENABLED` to false. Each POST test takes its token from the rendered page.
- Set `PORTAL_TITLE` and `PORTAL_THEME` only when the environment lacks them, as the e2e fixture does.
