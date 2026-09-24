# Implementation Plan: Marvis Actions export and bulk resolve

**Branch**: `feat/3299-marvis-actions-bulk-resolve` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Issue**: #3299 | **Research**: [research.md](./research.md)

## Summary

Add menu operation 270. It reads every Marvis Action of one organization from
the Mist `labs` API. It shows a numbered category table and a numbered
subcategory table, so the engineer can filter the list by topic. Mode 1 writes
every selected action to `OrgMarvisActions.csv` and to the configured database
backend. Mode 2 writes only the open actions. Mode 3 marks the open actions of
the selected topics as resolved, with one of the four Mist resolution codes and
an optional comment. Mode 3 needs the typed answer `RESOLVE <count>`. It sends
one request for each action, reads the list again to verify the result, and
writes `OrgMarvisActionsResolveResults.csv`. The operations portal on port 8055
runs all three modes with six controls.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: `mistapi` 0.64 (installed). No new dependency.

**Storage**: CSV under `data/`, SQLite at `data/mist_data.db`, and the polyglot
ArangoDB and Redis backend. All three go through
`DataExporter.write_with_format_selection`.

**Testing**: `pytest`, `pytest-cov`, and `hypothesis`.

**Target platform**: Windows 11 for local work, and the Linux container for the
deployment.

**Project type**: A single Python project with a Flask operations portal.

**Performance goal**: A mode 1 run on 112 actions costs 3 API requests: one
schema read, one list page, and one site list page. A mode 3 run on N targets
costs N resolve requests plus one verification list read.

**Constraints**: The 5-Item Rule caps each function at 5 parameters, 5 blocks,
and 25 lines. `ruff` and `mypy` skip `web_portal/`, so the logic lives under
`src/`. The portal feeds its answers in position order, so the prompt order is a
contract.

**Scale**: The org list endpoint returns up to 1,000 rows on one page. A page
guard stops the paging at 100 pages, so the operation holds at most 100,000
rows in memory.

## Constitution Check

| Principle | Verdict | How this plan complies |
| - | - | - |
| I. Five-Item Rule | Pass | The new package holds 5 files. Each module holds 5 or fewer classes. Each class holds 5 or fewer public methods. Each function stays at 25 lines or fewer, with 5 or fewer parameters and 5 or fewer blocks. |
| II. Class-Based Architecture | Pass | Named classes only. No wrapper function. The menu row points at `MarvisActionsOperation.run`. |
| III. Safety-First | Pass | Modes 1 and 2 only read. Mode 3 writes a recoverable status only. It shows a preview, and it needs the typed answer `RESOLVE <count>`. A cap limits one run to 500 actions. The stop signal halts the loop. |
| IV. Full Deployment Pipeline | Pass | The plan runs every gate locally, then opens one pull request. |
| V. Observability | Pass | Each request logs an action line before it and a result line after it. Each resolve writes one result row. |
| VI. Inline Comments | Pass | Every executable line carries an inline comment that states the intent. |
| VII. Action Logging | Pass | `logging.info` before each action and `logging.debug` after, with `%s` formatting. |
| Database Keys | Pass | The plan adds two primary key strategies before the code writes a row. |
| Data Directory | Pass | Both CSV files land under `data/`. |
| mistapi only | Pass with a note | The site list uses the `mistapi` method `listOrgSites`. The `labs` endpoints have no `mistapi` method, so the code calls them through the `mistapi` session methods `mist_get` and `mist_put`. No code opens its own HTTP connection. |

## Complexity Tracking

| Deviation | Why it is necessary | Simpler option that was rejected |
| - | - | - |
| Menu 270 is `interactive_safe`, but mode 3 writes to Mist. | The portal runs only `safe` and `interactive_safe` rows (`PORTAL_RUNNABLE_CATEGORIES`), and the user requires the portal. The write sets a status that the Mist UI can set back to Open. The typed count answer blocks every unattended pass, because no provider can guess the count. | A `destructive` row. The portal refuses to run a destructive row, so the user requirement fails. |
| Two endpoints are not in the Mist API documentation. | The Mist UI uses them, and no documented endpoint lists or resolves Marvis Actions for an organization. Research R1 to R4 holds the evidence. | The documented MSP count endpoint. It returns counts only. |
| The CSV file holds a curated column set, not `flatten_dict` output. | `flatten_dict` makes a different header for each run, because the nested `details` and `evidence` fields differ for each topic. FR-015 needs one fixed header. The database receives the full nested row. | Flatten every field. The header then changes with the data, and a spreadsheet macro breaks. |
| The code parses a comma-separated token list. | The command line user can select several topics in one answer. | One choice for each prompt. It forces one run for each topic. |

## API Contract

All paths start at `/api/v1/`. Research R1 to R6 holds the evidence.

| Purpose | Call | Notes |
| - | - | - |
| Topic names | `GET labs/suggestions_schema` | The response is `{"data": [...]}`. Each entry holds `category`, `symptom`, `display_name`, and `recommended_action`. |
| Action list | `GET labs/orgs/{org_id}/suggestion?query=get_suggestion&resolve_wcid=true&limit=1000&page=P` | The response is `{"results": [...], "page", "limit", "total"}`. The first page is 1. |
| Site names | `mistapi.api.v1.orgs.sites.listOrgSites(session, org_id, limit=1000)` and `mistapi.get_all` | The documented site list. |
| Resolve | `PUT labs/orgs/{org_id}/suggestions` | One request for each action. The body is `{"row_key", "status": "resolved", "label", "comment", "resolve_time"}`. |
| Undo (documented only) | `PUT labs/orgs/{org_id}/suggestions` | The body is `{"row_key", "status": "open"}`. The feature does not send it. The endpoint report states it. |

The resolve body never holds `suggestion_id`. The Mist UI sends
`suggestion_id: a.id`, and `a.id` is undefined on every live row, so the key
never reaches the server. One `resolve_time` in epoch milliseconds serves the
whole run, as the Mist UI does for one bulk resolve.

### Paging rules

The client reads page 1, then page 2, and so on. It stops when one of these
conditions is true.

1. The page holds no row.
2. The count of rows read reaches `total`, when `total` is an integer.
3. The page holds fewer rows than the `limit` in the response, when `total` is
   absent. If the response holds no `limit`, the client uses its own page size.
4. The client read 100 pages. The client then logs a warning that the list can be
   incomplete, and the operation continues with the rows read.

If any page returns a status other than 200, the client discards every row and
reports the HTTP status. If a page holds no `results` list, the client discards
every row and reports the shape problem. The operation then writes no file and
changes nothing.

## Project Structure

### New source files

```text
src/marvis/actions/
├── __init__.py    # Public names: MarvisActionsOperation, MarvisCatalog
├── model.py       # ResolutionCode, MarvisCatalog, MarvisFieldReader,
│                  # MarvisActionRecord, MarvisActionRecordBuilder
├── client.py      # MarvisListResult, MarvisActionsClient
├── selection.py   # MarvisTopicCount, MarvisTopicSelector, MarvisFilterPrompts,
│                  # MarvisResolveRequest, MarvisResolvePrompts
└── operation.py   # MarvisResolveResult, MarvisBulkResolver, MarvisLoadedActions,
                   # MarvisResolveWorkflow, MarvisActionsOperation
```

`src/marvis/` holds `__init__.py` and `marvis_utils.py` today. After the change,
it holds three children, which respects the 5-Item Rule.

### New test files

```text
tests/unit/marvis/__init__.py
tests/unit/marvis/actions/
├── __init__.py
├── test_model.py        # catalog names, field reader, record builder, key derivation
├── test_client.py       # paging, page guard, error discard, shape guard, schema, sites, resolve
├── test_selection.py    # token grammar, tables, prompts, code parser, confirmation
├── test_operation.py    # modes 1 to 3, refusals, cap, stop, errors, verification
└── test_properties.py   # Hypothesis invariants
tests/guardrails/test_marvis_actions_portal_exposure.py
```

### Changed files

| File | Change |
| - | - |
| `MistHelper.py` | One import and one `MenuEntry` row for menu 270. |
| `src/utils/operation_registry.py` | Row `"270"` as `interactive_safe`, with a WHY comment. |
| `src/refactors/endpoint_primary_key_strategies.py` | Strategies `listOrgMarvisActions` and `resolveOrgMarvisActions`. |
| `web_portal/services/operation.py` | `CATEGORY_RANGES` row `(270, 270, "Marvis Actions")` and `registry["270"]`. |
| `web_portal/menu_registry.py` | Regenerated with `scripts/generate_portal_menu_registry.py`. |
| `documentation/wiki/Menu-Reference.md`, `documentation/menu_reference.md` | Regenerated with `scripts/generate_menu_wiki.py`. |
| `tests/unit/test_menu_entry_metadata.py` | The expected menu count goes from 269 to 270. |
| `README.md` | The operation count and the menu table row. |
| `.github/copilot-instructions.md` | The `interactive_safe` count goes from 92 to 93, and the list adds 270. |
| `deploy/.env.example` | `MARVIS_RESOLVE_MAX_ACTIONS=500`. |
| `documentation/marvis-actions-api-endpoints.md` | The tracked endpoint report. |
| `changelog.d/issue-3299-marvis-actions.md` | The release note fragment. |

The standalone report `data/Marvis_Actions_API_Endpoints_Report.md` lives in the
data directory of the served checkout. Git does not track `data/`, so the tracked
copy in `documentation/` is the source.

## Module Design

### `model.py`

Module constants:

- The constant `OPEN_STATUSES` holds `open`, `inprogress`, and `reoccured`.
- The constant `STATUS_NAMES` holds the seven status names of the Mist UI. It
  includes the key `expired action`, which holds a space.
- The constant `CATEGORY_NAMES` holds the eight category names.
- The constant `TOPIC_NAMES` holds 36 names, keyed by the pair `(category, symptom)`.
- The constant `RESOLUTION_CODES` holds the four codes in the Mist UI order. The
  alias `other` names the code `nonsuggested`.
- The constants `NAME_KEYS`, `MAC_KEYS`, `PORT_KEYS`, and `REASON_KEYS` hold the
  key orders of the entity columns.

Classes:

| Class | Public members | Purpose |
| - | - | - |
| `ResolutionCode` | `key`, `name`, `needs_comment` | A frozen dataclass for one Mist `label` value. |
| `MarvisCatalog` | `category_name`, `topic_name`, `recommended_action`, `status_name`, `known_pairs` | Name lookups. The built-in names win over the schema names. The schema swaps the names of `bad_wan_link` and `intermittent_wan_connectivity`. |
| `MarvisFieldReader` | `text`, `integer`, `flag`, `iso`, `first_text` | Static readers. Each one returns a safe value for a missing key or a wrong type. |
| `MarvisActionRecord` | `column_names`, `as_row`, `key` | A frozen dataclass with the 43 CSV columns. |
| `MarvisActionRecordBuilder` | `action_key`, `build`, `document` | Turns one raw row into one record and one database document. |

The entity columns read `details.impacted_tuple`. The builder takes the first
value that is not empty from each tuple item, in the key order below. It then
joins the unique values with `; `.

| Column | Key order |
| - | - |
| `entity_names` | `entity_name`, `ap_name`, `switch_hostname`, `switch_name`, `hostname` |
| `entity_macs` | `entity_mac`, `ap_id`, `switch_mac`, `gateway_id`, `mac` |
| `entity_ports` | `port_id` |
| `detail_reason` | `disconnect_reason`, `failure_reason`, `reason`, `sub_symptom`, `event_name`, `details_msg_in_ui` (read from `details`) |

`ap_id` comes before `switch_mac`, because an AP Offline tuple also names the
upstream switch MAC.

The action key is the value of the Mist field `uuid`. If a row holds no `uuid`,
the builder derives the key with `uuid3(NAMESPACE_X500, row_key)`. Mist uses the
same rule (research R7). If a row also holds no `row_key`, the builder derives the
key from the sorted JSON text of the row. The key therefore stays stable between
runs.

### `client.py`

| Class | Public members | Purpose |
| - | - | - |
| `MarvisListResult` | `rows`, `status_code`, `complete`, `problem` | A dataclass for one full list read. A problem text that is not empty means that the read failed. |
| `MarvisActionsClient` | `list_actions`, `read_schema`, `read_site_names`, `resolve_action` | The only class that calls the API. |

The method `resolve_action(body)` returns `(status_code, error_text)`. The error
text is empty for a 2xx answer. The methods `read_schema` and `read_site_names`
return an empty value and log a warning when the read fails. The report can
continue without names.

### `selection.py`

| Class | Public members | Purpose |
| - | - | - |
| `MarvisTopicCount` | `key`, `name`, `category`, `total`, `open_count` | One row of a numbered table. |
| `MarvisTopicSelector` | `category_counts`, `topic_counts`, `match_categories`, `match_topics`, `select` | The token grammar and the open filter. |
| `MarvisFilterPrompts` | `ask_mode`, `ask_categories`, `ask_subcategories` | Log a numbered table, then ask. |
| `MarvisResolveRequest` | `code`, `comment`, `resolve_time` | A frozen dataclass for the answers of one resolve run. |
| `MarvisResolvePrompts` | `ask_code`, `ask_comment`, `ask_confirmation`, `parse_code`, `confirmation_matches` | The resolve prompts and their parsers. |

### `operation.py`

| Class | Public members | Purpose |
| - | - | - |
| `MarvisResolveResult` | `column_names`, `as_row` | A dataclass for one result row. |
| `MarvisBulkResolver` | `resolve`, `verify` | The write loop, the stop check, the pacing, and the verification. |
| `MarvisLoadedActions` | fields only | The org, the client, the catalog, the records, and the documents of one run. |
| `MarvisResolveWorkflow` | `resolve_open_actions` | The mode 3 flow after the filter. |
| `MarvisActionsOperation` | `run` | The menu handler for all three modes. |

## Run Flow

1. Ask the mode. Accept `1`, `2`, or `3`. The default is `1`.
2. Resolve the organization with `ConfigUtils.get_cached_or_prompted_org_id`.
3. Read the list. If the read fails, log the reason and return.
4. If the list is empty, log the no-action message and return.
5. Read the schema and the site names, then build the records.
6. In modes 2 and 3, keep the open actions only. If none remains, log the
   no-open message and return.
7. Log the category table, then ask the category filter.
8. Log the subcategory table for the selected categories, then ask the
   subcategory filter.
9. In modes 1 and 2, write the export and log the completion line.
10. In mode 3, run the resolve workflow.

### Prompt contract

The portal feeds one answer for each control, in this order. The code must ask
the prompts in this order and must never skip a prompt that a later prompt
follows.

| Position | Prompt | Default | Asked when |
| - | - | - | - |
| 1 | Mode | `1` | Always |
| 2 | Category filter | `all` | The list holds a matching action |
| 3 | Subcategory filter | `all` | The category filter selected a topic |
| 4 | Resolution code | `suggested` | Mode 3 with at least one target |
| 5 | Comment | empty | Mode 3 with at least one target, for every code |
| 6 | Confirmation | empty | Mode 3 with at least one target |

The comment prompt appears for every code, because the portal always sends the
comment answer in position 5. If the code skipped the prompt, the confirmation
prompt would read the comment answer.

The static audit in `tools/prompt_audit.py` must count all six prompts, because
`tests/unit/web_portal/test_portal_required_controls.py` refuses a row that
declares more controls than the audit finds. The audit follows a call only when
the method name is unique in `src`, and it follows each name one time. For that
reason, each filter method calls `InputUtils.safe_input` directly, and the
workflow method has the unique name `resolve_open_actions`.

No prompt text and no context string holds the words `select`, `index`,
`choice`, or `y/n`. The unattended `--testinteractive` provider answers `0` to
those words. Every other prompt receives its default value, so an unattended
pass runs a mode 1 export of every action.

### Filter token grammar

The engineer enters one or more tokens, separated by commas. The code trims and
lowercases each token and ignores an empty token.

| Token | Category prompt | Subcategory prompt |
| - | - | - |
| `all`, or a blank answer that the prompt default fills in | Every topic in the table | Every topic that the category prompt selected |
| A number | The topics of that category row | The topic of that row |
| A category key, such as `switch` | The topics of that category | The selected topics of that category |
| A subcategory key, such as `sw_offline` | The topics with that subcategory | The selected topics with that subcategory |
| A pair, such as `switch/sw_offline` | That topic | That topic, if the category prompt selected it |

A key is known when the catalog, the schema, or the live data holds it. A known
key that selects nothing gives an empty result, and the operation states that no
action matches the filter. An unknown token refuses the whole run and names the
token. A number outside the table is an unknown token.

A Ctrl+C at a prompt makes `safe_input` return an empty answer instead of the
default. An answer that holds no token therefore selects no action. The run then
stops and changes nothing.

### Resolve algorithm

1. Take the open actions of the selected topics. Sort them by `start_time`, oldest
   first, then by `uuid`.
2. Read `MARVIS_RESOLVE_MAX_ACTIONS` (default 500). If the target count is larger,
   keep the oldest actions up to the cap, and log a warning that names the cap.
3. Log a preview line for each target.
4. Ask the code, the comment, and the confirmation. Refuse the run on a bad code, a
   missing comment for `nonsuggested`, a comment longer than 1,000 characters, or a
   confirmation that does not equal `RESOLVE <count>`.
5. Set one `resolve_time` for the run.
6. For each target, check the stop signal. Skip an action with no `row_key`. Send
   the resolve request, record the result, and call `AdaptivePacer.pace()`.
7. If at least one request returned 2xx, wait 2 seconds, then read the list again.
   Mark each 2xx result `resolved` when Mist reports a closed status. Mark it
   `sent_unverified` when Mist reports an open status, when the action is missing,
   or when the second read fails.
8. Write the result file and log the summary.

### Outcome values

| Outcome | Meaning |
| - | - |
| `resolved` | Mist accepted the request, and the second read shows a closed status. |
| `sent_unverified` | Mist accepted the request, but the second read did not show a closed status. |
| `error` | Mist returned a status that is not 2xx, or no answer arrived. |
| `not_sent` | The stop signal arrived before this action. |
| `skipped` | The action holds no `row_key`, so no request can address it. |

## Message Contract

The portal reads the main log to judge a run. `HANDLED_ERROR_MARKERS` holds
`could not` and `failed to`. `MISSING_INPUT_MARKERS` holds `no value provided`.
`NO_OUTPUT_REASON_MARKERS` holds `no ` and `0 `. The messages below use those
words only where the portal must react to them.

| Case | Level | Message | Portal result |
| - | - | - | - |
| Mode 1 or 2 export done | Display | `Completed the Marvis Actions export and wrote results to OrgMarvisActions.csv` | Completed, with the file |
| Mode 3 done | Display | `Completed the Marvis Actions resolve and wrote results to OrgMarvisActionsResolveResults.csv` | Completed, with the file |
| Empty organization | Display | `No Marvis Actions exist in this organization. No file was written.` | Completed, no file |
| No open action | Display | `No open Marvis Actions exist in this organization. No file was written.` (mode 3: `No action was changed.`) | Completed, no file |
| Filter selects nothing | Display | `No Marvis Actions match the filter. No file was written.` (modes 2 and 3 say `No open Marvis Actions`) | Completed, no file |
| Bad mode or token | ERROR | `MistHelper could not match the <prompt> answer '<token>'. ...` | Failed |
| List read failed | ERROR | `MistHelper could not read the Marvis Actions list. The API returned HTTP <status>. ...` | Failed |
| Empty confirmation | WARNING | `No value provided for the confirmation, so no action was changed. To resolve these N actions, type RESOLVE N.` | Failed, missing input |
| Missing comment | WARNING | `No value provided for the comment. The code nonsuggested needs a comment, so no action was changed.` | Failed, missing input |
| Wrong confirmation | ERROR | `MistHelper could not confirm the resolve. The answer '<answer>' does not match 'RESOLVE N'. No action was changed.` | Failed |
| Some requests failed | ERROR | `MistHelper could not resolve E of M Marvis Actions. Read OrgMarvisActionsResolveResults.csv for the HTTP status of each one.` | Failed, with the file |
| Export write failed | ERROR | `MistHelper could not write OrgMarvisActions.csv. Read the export error above.` | Failed |

A normal path never logs `could not`, `failed to`, or `no value provided`. No
message starts with a portal internal prefix, such as `Processing ` or `Retry `.

### Console level

The Display level is `DISPLAY_LEVEL` in `selection.py`, and its value is
`logging.WARNING`. The live `.env` can set `CONSOLE_LOG_LEVEL=30`. That value
hides every INFO line on the SSH console, so an operator would see the prompts
without the tables. Issue #886 Phase 2 moves operator-facing output to WARNING
for that reason, and `PromptUtils` does the same for the site menu.

These lines use the Display level:

- The mode table, the category table, the subcategory table, and the code table.
- The resolve preview, the `Sending N resolve requests, one at a time` line, and
  the `Resolve progress: N of M actions` line after each group of 25 requests.
- The status summary, the resolve summary, the completion lines, and the
  empty-result lines.

The action log lines stay at INFO and DEBUG. The file `data/script.log` keeps
them, because `LOGGING_LOG_LEVEL` controls the file and not the console. The
Display level stays below ERROR, because the portal marks a run as failed when
the run logs an ERROR line.

## Data Model

### `OrgMarvisActions.csv` (endpoint name `listOrgMarvisActions`)

| Group | Columns |
| - | - |
| Identity | `uuid`, `row_key`, `suggestion_id`, `org_id`, `site_id`, `site_name` |
| Topic | `category`, `category_name`, `symptom`, `symptom_name`, `topic`, `suggestion`, `recommended_action`, `impact_scope` |
| Status | `status`, `status_name`, `is_open`, `severity`, `label`, `label_name`, `comment`, `assignee` |
| Entity | `entity_type`, `entity_id`, `entity_names`, `entity_macs`, `entity_ports`, `impacted_entity_count`, `detail_reason` |
| Time | `start_time_iso`, `end_time_iso`, `suggestion_time_iso`, `resolve_time_iso`, `validation_time_iso`, `reoccur_time_iso`, `duration`, `reoccur_count`, `batch_count` |
| Self-drive | `self_drivable`, `self_driven`, `zendesk_ticket` |
| Audit | `details_json`, `exported_at` |

The time columns hold ISO 8601 text in UTC. The database document keeps the raw
epoch millisecond values.

### Database document

The document is the raw Mist row plus every CSV column except `details_json`.
The raw row already holds `details`, so the document keeps the nested value
once. The `uuid` field holds the action key, so a derived key reaches the
database too. The polyglot backend receives the documents through
`ExportBackendOptions(raw_data=documents)`.

### `OrgMarvisActionsResolveResults.csv` (endpoint name `resolveOrgMarvisActions`)

`result_id`, `uuid`, `row_key`, `org_id`, `site_id`, `site_name`, `category`,
`category_name`, `symptom`, `symptom_name`, `topic`, `entity_names`,
`previous_status`, `resolution_code`, `resolution_name`, `comment`, `outcome`,
`http_status`, `message`, `verified_status`, `resolve_time`, `resolve_time_iso`.

The `result_id` is `<uuid>_<resolve_time>`, so each run keeps its own rows and a
second run never replaces the audit record of the first run.

### Primary key strategies

```python
"listOrgMarvisActions": {
    "type": "natural_pk",
    "primary_key": ["uuid"],
    "indexes": ["org_id", "site_id", "category", "symptom", "status"],
    "unique_constraints": [],
},
"resolveOrgMarvisActions": {
    "type": "natural_pk",
    "primary_key": ["result_id"],
    "indexes": ["uuid", "outcome", "resolution_code"],
    "unique_constraints": [],
},
```

## Portal Contract

`registry["270"]` has the form category `interactive` and six controls.

| Control | Type | Options | Default | Required |
| - | - | - | - | - |
| `marvis_mode` | choice | `1` Export every action, `2` Export the open actions, `3` Resolve the open actions | `1` | Yes |
| `marvis_category` | choice | `all` and the eight category keys | `all` | Yes |
| `marvis_subcategory` | choice | `all` and the 36 topic pairs | `all` | Yes |
| `marvis_resolution_code` | choice | the four code keys | `suggested` | No |
| `marvis_comment` | text | none | empty | No |
| `marvis_confirmation` | text | none | empty | No |

The options come from `MarvisCatalog`, so the portal and the command line use one
catalog. `CATEGORY_RANGES` gets the row `(270, 270, "Marvis Actions")`.

## Configuration

| Variable | Default | Meaning |
| - | - | - |
| `MARVIS_RESOLVE_MAX_ACTIONS` | `500` | The largest number of actions that one mode 3 run resolves. A value that is not a positive whole number keeps the default and logs a warning. |

## Test Strategy

- Unit tests use synthetic identifiers and a fake session. No test calls the Mist
  cloud.
- The client tests cover the page reads and the three stop rules. They also cover
  the page guard, the discard of the list on a failed page 2, and the shape guard.
  The last client tests cover the schema fallback, the site read failure, and the
  resolve body.
- The selection tests cover every token form, the refusal of an unknown token, and
  the number range. They also cover the open filter, the code parser, the comment
  rules, and the exact confirmation match.
- The operation tests cover the three modes, the empty organization, the no-open
  path, and the filter refusal. They also cover the export call, the cap, the stop
  signal, a run with mixed failures, and the verification outcomes.
- The property tests prove that the token parser and the field readers never
  raise an exception. They also prove that the confirmation accepts only the exact
  text, and that the action key never changes for one row.
- The portal contract tests in `test_portal_contract.py` run the operation through
  `web_input_context` and `_RunLogHandler`. They prove the status that the portal
  shows for each mode and for each refusal.
- The console tests in `test_console_visibility.py` prove that each line for the
  operator uses the Display level. They also prove that the action log lines stay
  at INFO, so the console does not show them at `CONSOLE_LOG_LEVEL=30`.
- The guardrail test `test_marvis_actions_portal_exposure.py` proves that the
  portal admits menu 270 and that the six controls match the prompt order.
- The test `test_portal_required_controls.py` proves that `tools/prompt_audit.py`
  finds six prompts for menu 270.

### Guard proof

The new guards are the confirmation check, the comment check, the cap, and the
page guard. Each test calls the guard decision directly, with no network and no
environment need, and proves that the guard refuses a bad input. This is method 2
of the guard proof rule, as pull request #2611 used.

## Validation Plan

1. Run `py_compile`, `ruff`, `black`, `mypy`, `pylint`, `bandit`, `radon`,
   `vulture`, `pydocstyle`, `interrogate`, and `tools.symbol_diff` on the changed
   files.
2. Run the new tests, the menu guardrails, and the portal registry tests.
3. Copy the changed files into the running container with a Class B deploy, and
   reload the port 8055 workers. Start no new container.
4. Run modes 1, 2, and 3 from the portal with Playwright.
5. Run modes 1 and 3 over SSH on port 2200.
6. Read `podman logs misthelper-app`, `data/script.log`, and the portal error log.
7. Read `data/OrgMarvisActions.csv` and the ArangoDB collection
   `listOrgMarvisActions`, and compare both with the live list.

## Rollback

Revert the squash commit. The feature adds files and rows only, and it changes no
existing behavior. A resolved action returns to Open through the status dropdown
of the Mist UI, or through the undo body in the endpoint report.

## Risks

| Risk | Control |
| - | - |
| Mist changes a `labs` endpoint. | The shape guard stops the run and writes nothing. The endpoint report names the evidence date. |
| A bulk resolve closes the wrong actions. | The preview, the typed count, the open filter, and the cap. |
| A portal user submits a stale count. | The count must equal the current target count, or the run changes nothing. |
| The shared API token runs out of quota. | `AdaptivePacer` and the `mistapi` 429 retry. The cap bounds one run. |
| The lab holds no open action. | Mocked tests prove the write path. The live test reaches the no-open message only. |
