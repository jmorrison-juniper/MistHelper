# Contract: Preflight Failure Behavior (Credential & Venv Guards)

**Feature**: `1020-safe-test-clean-run`
**Consumers**: `_establish_mist_session()` / `ConfigUtils` (credential/org-id
preflight), `DependencyCheckOrchestrator` (venv preflight), operators reading
console output, `tests/` unit tests asserting these behaviors.

## Credential/host/token preflight (`_establish_mist_session()` entry, FR-013/FR-015/FR-017)

- **Trigger**: `MIST_HOST` is empty/placeholder, or neither `MIST_APITOKEN`
  nor `MIST_API_TOKEN` resolves to a non-empty value.
- **Behavior on failure**:
  1. No `mistapi.APISession(...)` construction is attempted (structurally —
     the preflight function does not import `mistapi` or `requests`).
  2. Process prints a remediation message to the console referencing
     `deploy/.env.example` and the exact env var names actually read by the
     code (`MIST_HOST`, `MIST_APITOKEN`/`MIST_API_TOKEN`).
  3. Any token value that IS present but rejected for being malformed is
     shown only via `_redact_tokens()` output (`first4...last4` or `***`),
     never the raw value, in any message or log line.
  4. Process exits non-zero (`sys.exit(1)` or equivalent) before returning
     to `_dispatch_main_mode()` — this applies uniformly to `--test`,
     `--testinteractive`, TUI, and CLI single-command modes, since all pass
     through `_establish_mist_session()`.
- **Behavior on success**: preflight returns/continues silently; existing
  session-establishment logic (`MistSessionInitializer.initialize()`)
  proceeds unchanged.
- **Test guarantee**: unit tests for this preflight construct the check with
  fake/empty env values and assert (a) the failure message, (b) that no
  network-capable call occurred (achieved structurally, not by mocking
  network calls that would otherwise fire) and (c) non-zero exit / raised
  signal. Tests MUST NOT set real credentials and MUST NOT be tagged
  `integration` (per `pyproject.toml`'s marker convention) since no real API
  call is made or permitted here.

## Org-id non-interactive preflight (`ConfigUtils`, FR-016)

- **Trigger**: running in a systematic/non-interactive test mode (detected
  via local `sys.argv` inspection for `--test`/`--testinteractive`) **and**
  `get_cached_or_prompted_org_id()` was unable to resolve an org id from
  cache, env (`org_id`/`ORG_ID`), or `.env` (`org_id=` line) — i.e., the
  resolution would otherwise fall through to
  `_resolve_org_id_via_prompt()` → `mistapi.cli.select_org(...)`.
- **Behavior on failure**: raise/exit with an actionable message naming the
  exact env var (`org_id`) and `.env` key the operator must set, instead of
  calling `mistapi.cli.select_org(...)` — this prevents the
  malformed-URL-on-blank-host HTTP request from ever being issued in
  non-interactive contexts.
- **Behavior preserved**: genuinely interactive sessions (no test-mode flag
  present) are unaffected — `_resolve_org_id_via_prompt()` continues to
  prompt normally when a human is actually present to answer it.

## Isolated venv preflight (`DependencyCheckOrchestrator`, FR-008–FR-012)

- **Trigger**: `sys.prefix == sys.base_prefix` (and no legacy
  `sys.real_prefix`) **and** no explicit override env var is set **and** the
  pre-existing `DISABLE_AUTO_INSTALL` gate has not already blocked the
  action.
- **Behavior on failure (i.e., install/upgrade would target system Python)**:
  the install/upgrade action inside `DependencyCheckOrchestrator.run()` is
  skipped; a diagnostic message distinguishes, where determinable, "no
  `.venv` was ever created/activated" from "a `.venv` appears configured but
  its launcher is missing/broken," so the operator knows whether to create
  or repair the environment. The process does not silently continue as if
  dependencies were satisfied — it surfaces the block clearly.
- **Behavior preserved**: when run inside a genuine venv (or with the new
  override env var explicitly set, or the pre-existing
  `DISABLE_AUTO_INSTALL` opt-out already in effect for its own reasons), the
  existing install/upgrade behavior is unchanged.

## Exit-code / signal convention

This feature does not introduce new numeric exit codes beyond the existing
convention of "0 = success, non-zero = failure" already used elsewhere in
`MistHelper.py`'s `sys.exit(...)` call sites. No new exit-code taxonomy is
required by any FR; implementation should reuse `sys.exit(1)` for all
preflight failures described above, consistent with existing early-exit
patterns in `_early_dependency_check()` and CLI argument-validation errors.
