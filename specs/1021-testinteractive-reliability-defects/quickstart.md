# Quickstart: Validate the Serial Reliability Fixes

## Preconditions

1. Work on **one** issue only. Start a fresh `fix/<issue>-<slug>` branch from
   the latest merged `main`; never stack branches or PRs.
2. Run the focused mock-based tests before any optional remote smoke test.
3. Do not create, update, or delete Mist resources. Use only an approved
   read-only credential if a smoke test is authorized.
4. Keep generated telemetry/log files inside the controlled `data/` test
   artifact location; do not check them in.

## Per-issue validation sequence

### #1636 — telemetry false-pass semantics

```powershell
python -m pytest tests/unit/troubleshooting/test_interactive_test_runner.py -v
python -m pytest tests/unit/analytics/test_telemetry_emitter.py -v
python -m py_compile MistHelper.py
```

Expected: a stub handler that logs `ERROR` then returns is a non-clean event,
is counted in the summary, and causes a non-zero runner result.

### #1637 — selector fallback

```powershell
python -m pytest tests/unit/troubleshooting/test_interactive_test_runner.py -v -k "selector or resolve"
python -m py_compile MistHelper.py
```

Expected: exact id/full-name selectors resolve; a partial or unknown supplied
selector aborts before the operation callable is invoked.

### #1638 — meaningful site context

```powershell
python -m pytest tests/unit/troubleshooting/test_interactive_test_runner.py -v -k "site_context or cancellation or invoke"
python -m pytest tests/unit/analytics/test_telemetry_emitter.py -v
```

Expected: the terminal event differentiates injected and unavailable
`site_id` context and reports EOF/interrupt cancellation distinctly from clean
completion.

### #1639 — WAN SDK namespace

```powershell
python -m pytest tests/unit/export/test_wan_client_events_exporter.py -v
python -m py_compile MistHelper.py
```

Expected: a stub exposing only
`sites.wan_clients.searchSiteWanClientEvents` succeeds; the test proves the
obsolete `.events.search` lookup is not used.

### #1640 — unsupported flag UX

```powershell
python -m pytest tests/unit/refactors/test_main_entrypoint.py -v
python -m pytest tests/unit -v -k "testinteractive or test_interactive"
```

Expected: `--test-interactive` exits non-zero with a suggestion, while
`--testinteractive` retains its existing dispatch behavior.

### #1641 — side-effect-free help

```powershell
python -m pytest tests/unit/refactors/test_main_entrypoint.py -v
python -m py_compile MistHelper.py
```

Expected: `--help`, `-h`, and combined help flags print usage and exit without
calling deferred import/dependency/session/dispatch seams.

## Merge gate

Before submitting each single-issue PR:

```powershell
python -m pytest tests/unit/troubleshooting/test_interactive_test_runner.py tests/unit/analytics/test_telemetry_emitter.py tests/unit/refactors/test_main_entrypoint.py -v
python -m py_compile MistHelper.py
```

Run any issue-specific exporter test added by #1639 as well. Review generated
JSONL fixtures/artifacts and remove anything outside the approved `data/`
location. Complete CI and squash-merge the PR before starting the next issue.

## Optional read-only smoke check

Only after all local tests pass and an operator authorizes the check:

```powershell
$env:MIST_INTERACTIVE_TEST_SITE = '<exact approved site name or UUID>'
python MistHelper.py --testinteractive
```

Expected: only read-only Mist interactions, an identified actual site in
telemetry, no credentials in output, and local telemetry confined to `data/`.
Do not use a partial selector. Do not run this smoke test as a substitute for
the mock-based regressions.
