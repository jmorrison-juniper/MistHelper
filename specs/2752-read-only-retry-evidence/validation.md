# Validation: Read-only retry evidence

## Ownership

Part of #2752. The full campaign remains open.
The authenticated account was `jmorrison-juniper`.
The issue had no assignee and no prior claim comment.
The complete paginated lists for `15` open PRs contained `116` file records and no owned overlap.

The bounded claim is [issue comment 5941591000](https://github.com/jmorrison-juniper/MistHelper/issues/2752#issuecomment-5941591000).
The app session is `954f5f73-5256-433b-bb9c-25d66549cdbe`.
The local session is `c17d672f-029b-49e6-8100-fcb40e7dccf2`.
The initial commit is `bcf391cd88c5b47090d044d85cadf4946e8ef8ce`.
Position `35` follows #3701. The parent controls publication.

After the parent's correction, the live assignee list contained `jmorrison-juniper`.
The source edit already existed when that correction arrived.
The second claim check found one comment, the same exact slice claim.
The issue remained open with the existing type, scope, and `in-progress` labels.

## Environment and Workflow Capabilities

The initial `.venv/bin/python -m pytest --version` command failed because the environment did not exist.
The documented bootstrap then failed in `venv.EnvBuilder` with this actual error:

```text
subprocess.CalledProcessError: Command '[.../.venv/bin/python3.13', '-m', 'ensurepip', '--upgrade', '--default-pip']' died with <Signals.SIGABRT: 6>.
```

The bootstrap exit code was `1`. No bootstrap source changed.
The recovery used `uv venv --python 3.13 --seed --link-mode copy --allow-existing .venv`.
The installed uv rejects `--copies`, so package copying used its supported `--link-mode copy` option.
The recovery used system certificates and modified only this worktree's ignored environment.
The unchanged requirement files resolved `160` packages, including the pip seed.
The recovered interpreter is Python `3.13.13`. The test runner is pytest `9.1.1`.

The mandatory feature hook used the current app branch as `GIT_BRANCH_NAME`.
The actual command failed with `env: pwsh: No such file or directory`, exit `127`.
The feature uses the current SpecKit templates directly.
No shared `.specify` state, governance, or branch configuration changed.

## Diagnostic and Gate Evidence

The existing suite and adjacent contracts passed `116` tests before the source edit.
An initial artifact-directory setup error prevented those tests from running.
The repeated baseline passed after the artifact parent existed.
The setup error is not a product failure.

| Proof | Checked scope | Result |
| - | - | - |
| Missing status on unchanged source | `13` controlled sequence cases | `7` failed, `6` passed, `7` other cases deselected |
| Incorrect first status | `1` native `503`, then `200` case | The real regression failed on reported `200` instead of required `503`. |
| Restored source | `55` existing and `20` new cases | `75` passed |
| Final source and adjacent contracts | `138` cases | `138` passed |
| Required input preflight | `6` inputs and `3` guides | `1` test passed, with `6` reads and validations. |

The temporary incorrect-status mutation is absent from the final source.
The new file covers `13` native sequences, `5` unsafe-status cases, and `2` raised transport exceptions.
The native sequences check `23` endpoint calls and `10` sleeps.
All `20` new cases check zero network requests and zero output or store writes.
Every native sequence asserts the returned object's identity and exact endpoint arguments.
The warning sequence preserves each failed status and its attempt number.
The final error preserves the last status after exhaustion.
The product diagnostics exclude the private body, header, and query sentinel.
The tests do not alter SDK logging or claim that SDK logs lack status `503`.

### Coverage and Preservation

The two changed methods cover `21` of `21` statements and `6` of `6` reported branch arcs.
The final combined module coverage is `99.34` percent.
The only uncovered combined branch belongs to the unchanged non-integer response acceptance path.
The owned-file-only coverage is `96.70` percent. Its changed regions still have complete coverage.

A body comparison checked `27` functions.
Only `_call_api_with_retry` and `_log_retry_attempt` changed.
The other `25` bodies remain byte-identical, including the HTTP and body rejectors.
The coupled existing test file retains exactly `1,013` lines.
No source setting, retry decision, retry ceiling, delay, rate limit, output schema, or primary key changed.

### Local Gates

| Gate | Scope | Result |
| - | - | - |
| Compilation | `MistHelper.py` and all `3` owned Python paths | Passed |
| Ruff | The complete configured repository scope | Passed |
| Black | `2,010` Python files | Passed |
| mypy | The active CI scope, `663` source files | Passed |
| Bandit | `786` files and `214,072` source lines | Zero findings and zero parse errors |
| Pylint | `src/api/api_data_fetcher.py` | `9.84` out of `10`, above `9.5` |
| Complexity | `src/api/api_data_fetcher.py` | Every block meets the maximum of `10`. |
| Docstring style | `src/api/api_data_fetcher.py` | Passed |
| Docstring coverage | `28` documented items | `100` percent |

Pylint reports two nonblocking exact-type style notices.
The exact integer guard prevents booleans and arbitrary SDK values from entering diagnostics.
No new suppression or exclusion was added.
The existing class debt remains outside this repair.
The configured docstring command created an ignored badge.
That temporary badge was removed. The retained badge is in the owned artifact directory.

### Ratchet Scopes

The full normal scan discovered `998` files and analyzed `949`.
It excluded `49` files through the normal Mist API predicate.
It reported `725` accepted baseline findings, zero new findings, and zero parse errors.
Both owned API test files appear in those `49` exclusions.

The explicit new-file scan uses `--include-mist-api`.
It discovered and analyzed exactly `1` file and reported zero findings.
Its `2` omitted-root advisories describe the intentional single-file scope.
They do not indicate a skipped owned file.

The initial forced scan could not infer HTTP families from positional case objects.
Explicit `status_codes` keywords expose the real native `4xx` and `5xx` coverage.
The repeated forced scan passed without baseline, rule, or policy changes.

### Dependency Audit and STE

The normal `pip-audit -r requirements.txt` command failed during temporary-environment creation.
Its `ensurepip` child died with `SIGABRT`, exit `1`.
That failure is not an audit.

The supported alternative resolves the complete native runtime closure with hashes.
Strict `--require-hashes --no-deps --disable-pip` auditing checked all `105` packages.
It reported zero known vulnerabilities and zero skipped packages.
The Git-only `misthelper-devtools` development package is outside that runtime closure.
This runtime audit does not certify that Git-only development package.

STE read all `8` owned prose files and met the minimum score of `80`.
Its coverage remains partial with `dictionary_unavailable`.
No licensed dictionary exists at the configured path.
No fabricated dictionary or new allowlist was used.

### Evidence Retention

The session artifact directory is
`/Users/jmorrison/.copilot/session-state/c17d672f-029b-49e6-8100-fcb40e7dccf2/files/retry-evidence/`.
It retains the red and green logs, XML results, coverage reports, ratchet reports, audit report, hashed closure, and STE report.
It also retains the complete offline PR draft with all `23` template items.
Temporary proof mutations do not remain in the source.

## Publication

No push, PR, merge, workflow run, auto-merge, or live Mist operation occurred.
Protected publication and actual-main verification remain unperformed and belong to the parent.
The full campaign acceptance boxes and unperformed delivery boxes remain unchecked in the offline draft.
The parent receives the full local commit SHA after the commit and clean-state checks.
