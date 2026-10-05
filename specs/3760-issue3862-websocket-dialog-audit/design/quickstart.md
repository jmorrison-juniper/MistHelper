# Bounded Audit Validation Guide

The harness has measured 72 real forms in isolated and live GET-only modes.
The parent installed the environment and started the authorized normal portal on loopback8055.
The harness does not start services or read `.env`.
Default inspection executes no operation; a separate opt-in permits only the reviewed read-only channel lifecycle.
Use [audit-contract.md](contracts/audit-contract.md) for request rules and expected reports.
Use [data-model.md](data-model.md) for evidence fields and status meanings.

## Prerequisites

- Python 3.13 or newer and uv.
- A repository-compatible worktree environment.
- Playwright Chromium. System Chrome is not required.
- The authorized portal URL from the parent/user.
- Existing authentication, without credential disclosure.
- Verified deployed/source revisions and the exact installed SDK/runner path for the selected read-only channel.
  The user's read-only authorization includes that observation lifecycle; no additional whole-server guard is required.

Use only the user-authorized origin. Target availability and UX gaps can still block full acceptance.

## Prepare an absent environment

From the worktree root, run each command separately.
Stop after a failed command.

```text
uv run --python 3.13 --no-project python scripts/bootstrap_worktree.py
source .venv/bin/activate
python --version
python -m playwright install chromium
```

The bootstrap already installs Chromium. The final command is only a bounded repair if the browser download failed.
On Windows, activate `.venv\Scripts\Activate.ps1` instead.
The bootstrap installs both requirement files.
It can configure the repository-local Git credential username.
It does not require reading or printing `.env`.
Do not run `pip install .`, which can shadow the worktree `src` package.
Do not disable the repository bootstrap guard to use fewer packages.

## Scenario 1: Real inventory and isolated form inspection

After the parent prepares the environment, run:

```text
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/tools/websocket_dialog_audit/test_inventory.py tests/tools/websocket_dialog_audit/test_dialogs.py tests/tools/websocket_dialog_audit/test_live.py::TestLiveResponseFailures --ws-audit-mode=isolated --timeout=120 --ws-audit-artifacts="$PWD/test-artifacts/websocket-dialog-audit"
```

Expected outcomes:

- Real catalog keys match real rendered operation buttons.
- Every operation has a form result or a blocker.
- Actual inspected forms determine the nonempty measured-dialog count.
- All utilities can be inspected without executing them.
- Empty/error site choices and delayed map replies have separate tests.
- Policy traps record zero forbidden requests and frames.
- Source revision and installed SDK version appear in the report.

Keep the real catalog and browser assets.
Use synthetic selector data only at the documented boundary.
An isolated pass is not live evidence.
Do not report the existing fake browser suite as live validation.

### Targeted support coverage publication gate

Use the parent's temporary branch-coverage configuration with no omit patterns:

```text
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/tools/websocket_dialog_audit/test_inventory.py tests/tools/websocket_dialog_audit/test_dialogs.py tests/tools/websocket_dialog_audit/test_live.py::TestLiveResponseFailures --ws-audit-mode=isolated --timeout=120 --cov=tests/tools/websocket_dialog_audit/support --cov-config=/Users/jmorrison/.copilot/session-state/4927d431-5214-440a-acc1-c9e86cfe62e6/files/audit-coverage.ini --cov-report=term-missing:skip-covered --cov-fail-under=80
```

Final result: 103 passed in 23.72 seconds, support branch coverage 81.22%.
All prior 86 tests are preserved; 17 isolated cases add real-form failure/parent evidence,
scope rejection, unsolicited socket denial and restricted-writer checks.
The existing repository configuration omits tests and cannot establish this targeted denominator.
No coverage exclusions, suppressions or repository-wide settings were changed.
This is total support coverage, not a claim that each support module reaches 80%.
The table reports `journeys.py` at 60%, `policy.py` at 92%, `inventory.py` at 95%,
with reporting and package initializer fully covered.

## Scenario 2: Opt-in live GET-only dialog inspection

Use the authorized URL stored locally in `PORTAL_URL`.
Do not paste authentication values into commands or reports.

```text
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/tools/websocket_dialog_audit/test_live.py --ws-audit-mode=live-inspection --ws-audit-base-url="$PORTAL_URL" --timeout=120 --ws-audit-artifacts="$PWD/test-artifacts/websocket-dialog-audit"
```

Expected outcomes:

- Default-deny routing precedes browser creation. Only reviewed same-origin GETs are forwarded.
- Deployed browser assets must match reviewed worktree bytes before execution.
- Catalog/sites responses authorize only their returned scope IDs.
- All returned sites and maps are visited serially. Family filters and dependent refreshes are checked.
- Choice counts distinguish first-parent emptiness from empty-everywhere blockers.
- Redirects, writes, unknown reads, subscriptions, starts, utilities, captures, and shell remain denied.
- Responses stay in memory within one browser context. Cache reuse and locally fulfilled unrelated UI reads are disclosed.
- Connection refusal reports BLOCKED / portal unreachable with nonzero pytest status.
- A blocked required target produces a nonzero pytest status, even when all forms rendered correctly.
- Installed SDK/reviewed source are evidence, not independent deployed-backend attestation.
- Latest measured live coverage: 72 forms, 315 selector-scope observations, 69 target passes, three blockers.
- This is not a subscription or complete UX audit pass.

Do not fabricate authentication errors or rate limits against live Mist.
Use Scenario 1 for deterministic failure injection.

## Scenario 3: Exact-key read-only observation lifecycle

The user authorized this read-only subscription journey.
The parent verifies that the running container revision `2900f56` matches the local reviewed base before running it.
This is revision verification, not another approval requirement.

```text
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/tools/websocket_dialog_audit/test_live.py::TestReadonlyLive --ws-audit-mode=live-readonly --ws-audit-base-url="$PORTAL_URL" --timeout=120 --ws-audit-artifacts="$PWD/test-artifacts/websocket-dialog-audit"
```

The test reconciles the live catalog and asset bytes, chooses an actual returned site with device choices,
and starts only `site.stats.devices` through the visible form.
Its exact JSON body includes one selected site, channel kind, empty parameters, null confirmation, and local title labels.
`StartRequestChecker` selects the channel definition. `RunnerFactory` constructs `ChannelStreamRunner`.
`ChannelSourceMap` builds `/sites/{site_id}/stats/devices`.
`SubscriptionCoordinator` sends only `{"subscribe": path}` to the observation stream.
Installed SDK `mistapi.websockets.sites.DeviceStatsEvents` uses the same path.
No utility SDK trigger or remote Mist write is involved.

The browser guard consumes one start permission before forwarding, with redirects and retries disabled.
Only the returned session's bounded message GETs and one local stop POST are then permitted.
The normal user observes live state for five seconds, clicks Stop, and verifies stopped within five seconds.
Failure cleanup may issue the same own-session local stop when the UI is unavailable.
The global session list remains locally substituted with only the owned session.
Foreign sessions, arbitrary starts, utilities, shell, captures, downloads, deletes, and input remain denied.

`subscription-report.json/md` are separate owner-only artifacts.
They record fixed states, counts, duration, data/no-data, and stopped verification.
The local "connection opened" notice is not counted as remote stats data.
No private session/site IDs or raw output is saved.
The journey budget is 90 seconds; the outer pytest timeout is 120 seconds for fixture setup/report teardown.
The corrected exact-key live run passed: connecting/live/stopping/stopped, one own stop,
eight message reads, zero remote events during bounded observation (explicit no-data).
Measured journey 10.416 seconds; pytest 12.14 seconds.
The earlier parent run exposed a harness UUID assumption: production session IDs are 16 hex characters.
That contract is corrected and tested; the earlier run was not a remote stream failure.
Other subscription keys remain out of scope, not blanket-blocked by an invented approval condition.

## Scenario 4: Reports and distinct defects

Review the restricted JSON report and sanitized Markdown summary locally.
The small writer does not implement the complete proposed data model.
Confirm separate inventory, isolated inspection, live inspection, and live subscription totals.
Confirm every inventory entry has a result or blocker.
Confirm no blocked or skipped result counts as passed.

For each candidate defect, reproduce the actual behavior with real assets.
Then identify its cause and repair boundary.
Reuse an existing matching issue or create one repair issue under #3862 in the later authorized phase.
The parent files confirmed defects. This implementation does not create issues.
Records contain the public operation key, source anchors, and normal-user reproduction.
Missing operation-form Cancel is one measured shared user-story gap, not successful cancellation.
`ex.releaseDhcpLeases`, `srx.releaseDhcpLeases`, `ssr.releaseDhcpLeases`, and `ex.retrieveMacTable`
have optional MAC text inputs without site-scoped client pickers.
These are optional UX enhancements, not proven execution failures.
Existing tracking: #3888 cancellation, #3889 client choices, #3890 wording.
Wording #3890 is closed through merged PR #3891.
Reports describe the unchanged `2900f56` portal, not validation of that newer repair.
SDK semantics and actual form evidence are recorded independently of catalog field declarations.
Site/map aggregate streams do not need individual-client selectors. AP MAC inputs are AP targeting.
Do not publish screenshots, raw browser errors, selector values, or authentication state.

## Scenario 5: Later repair and merge checks

Run each repaired defect's regression before and after the repair.
Run applicable syntax, lint, formatting, type, complexity, security, SDK, and browser checks.
Use the repository's required test-quality procedure.

Before the analyzer, run:

```text
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Use the intended fetched base, not a guessed `main`.
After the authorized local commit, require clean relevant files and run:

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Before push/manual CI, run the full local equivalent after the same input preflight:

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Require exit zero and zero new findings.
Do not rewrite the baseline to hide failures.
For the untracked harness before the parent commits, use explicit files:

```text
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/tools/websocket_dialog_audit/test_inventory.py tests/tools/websocket_dialog_audit/test_dialogs.py tests/tools/websocket_dialog_audit/test_live.py --report test-artifacts/websocket-dialog-audit/quality-report.json --summary test-artifacts/websocket-dialog-audit/quality-summary.md
```

This gate inspected three files with zero new findings. It is not the later full release gate.
Keep generated quality-report files owner-only too.
Use the repository procedure for the intended base fetch and resolution.
Repeat affected checks when checked content or the base changes.
Keep exact commands, outcomes, durations, and selected scope.

Merge requires passing current required checks, review, ownership clearance, and the complete pull request template.
A blocked live audit cannot be reported as a complete audit.
Separate required harness checks from explicitly excluded live cases in the approved validation scope.
Missing required evidence prohibits merge.
Deployment and production restart need separate human approval.

## Cleanup

The fixture closes only its browser context.
It creates no session, server listener, authentication state, screenshot, or trace.
Reports use directory mode `0700` and file mode `0600`.
Keep reports local and owner-only.
Keep only sanitized summaries for issue and pull request publication.
Isolated mode needs no container. Live mode accepts the authorized localhost origin
or an explicitly supplied isolated origin such as port9600.
Do not change or stop the user-requested persistent normal portal from this harness.
The parent owns its lifecycle and any later test-container cleanup.
