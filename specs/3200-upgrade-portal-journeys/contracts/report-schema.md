# Contract: The report schema

**Feature**: #3200 | **Package**: `tests/support/upgrade_portal_e2e/harness/run/`

This contract states the fields of `report.json`, `journey.json`,
`inspection.json`, the index page, and the parity matrix. The entities are in
[data-model.md](../data-model.md).

## report.json

The report is one JSON file for each harness run (FR-064, FR-065).

| Field | Type | Rule |
| - | - | - |
| `schema_version` | integer | `1`. A change that removes or renames a field adds one. |
| `run` | object | The fields of `HarnessRun` |
| `journeys` | array | One summary for each case: `case`, `outcome`, `seconds`, `steps`, `writes`, `gaps`, `issue`, `artifact` |
| `writes` | object | For each case, each write key and its count. Each count must be 1 (SR-005). |
| `traps` | object | Each trap counter at the end of each case. Each value must be 0 (SC-003). |
| `gaps` | array | Each `HarnessGap` of the run |
| `credentials` | object | `scanned_files`, `scanned_pages`, `matches`. `matches` must be 0 (SC-012). |
| `parity` | object | `rows`, `parity_rows`, `percentage`, `out_of_date`, `unmapped_controls` |
| `performance` | object | For each fleet: `pages` and `api_calls`, each ranked by the 95th percentile, 10 entries each (PR-006) |
| `budgets` | array | Each `Budget` with its `result`, `issue`, and `delta` |
| `result` | string | `pass` or `fail`, by the exit code rules of [harness-command.md](harness-command.md) |

Each ranked performance entry holds `method`, `path_template`, `p50_ms`,
`p95_ms`, `max_ms`, `count`, and `cloud_calls_p95` (PR-007).

## journey.json

The branch recorder writes `journey`, `outcome`, `steps`, and `events`. The
harness keeps those fields and adds fields.

| Field | Rule |
| - | - |
| `journey` | The catalog identifier |
| `outcome` | The `JourneyRecord` outcome |
| `steps` | Each `StepRecord`. The branch fields `number`, `name`, `url`, `seconds`, `screenshot`, and `ttfb_ms` stay. |
| `events` | Each console error, page error, failed request, and response of 400 or more |
| `expected_errors` | The expected errors of the case |
| `writes`, `traps`, `gaps` | The fields of `JourneyRecord` |
| `excerpts` | The paths of the server log excerpt and the runner log excerpt |
| `trace` | The path of the browser trace, or `null` |

## inspection.json

The harness writes one entry for each screenshot with an empty verdict. The
engineer completes each verdict (FR-067). The feature keeps the completed
record as `inspection-record.md` in the feature directory.

| Field | Rule |
| - | - |
| `screenshot`, `journey`, `step` | The screenshot to examine |
| `automatic` | The result of each automatic screenshot check (FR-066) |
| `verdict`, `note`, `issue` | The fields of `InspectionEntry` |

## The index page

`index.html` holds one section for each case. Each section shows each step in
sequence. Each step shows its screenshot, URL, times, and check results. A
failed step also shows its errors, its server log lines, its runner log
lines, and a link to the trace. The page reads only files of its run directory.

## The parity matrix

The harness writes `parity-matrix.md` into the run directory and into
`specs/3200-upgrade-portal-journeys/` (FR-077).

| Column | Rule |
| - | - |
| `Identifier` | C01 to C54 |
| `Capability` | The name from the inventory of the spec |
| `Single-site` | `proven`, `partial`, `missing`, or `defect` |
| `Multi-site` | The same words |
| `Families` | The family combinations that apply, and the result of each |
| `Journeys` | The cases that prove the status |
| `Verdict` | `parity` or `gap` |
| `Issue` | The issue number of a gap |

A shared group comes first. It holds the sign-in, the sign-out, and the theme
control, with one status for each row (FR-079). The summary shows the parity
percentage (FR-076). A row that is out of date shows `out of date` in the
verdict, and the run fails.
