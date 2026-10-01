# Contract: Worktree dependency installation

**Issue**: #3399
**Implementation owner**: Existing classes in `scripts/bootstrap_worktree.py`.
**Model**: [data-model.md](../data-model.md)

## Command contract

Keep the existing entry points:

```text
python scripts/bootstrap_worktree.py
python scripts/bootstrap_worktree.py --recreate
```

Keep the PowerShell entry point unchanged.
The caller must use Python 3.13 or newer.
This feature does not select the interpreter that creates the environment.

`install_requirements()` returns successful file names as `list[str]`.
It installs `requirements.txt` before `requirements-dev.txt`.
It skips absent files.
It does not change file contents or package pins.

### uv installation

Call `shutil.which("uv")` exactly once per invocation.
If it returns a path, use that exact path for all present files.

```text
[resolved_uv, "pip", "install", "--python", str(venv_interpreter), "-r", str(requirement_file)]
```

Do not run another uv version probe, module search, or automatic uv installation.
Do not use the caller's interpreter as the uv target.

### Pip installation

If discovery returns `None`, use:

```text
[str(venv_interpreter), "-m", "pip", "install", "-r", str(requirement_file)]
```

No other automatic condition selects pip installation.
A uv launch error is not uv absence.
A nonzero uv result is not uv absence.

### Subprocess behavior

Use argument lists with `check=False` and a child environment.
Do not use a shell.
Keep installer output visible.
Do not capture it for a new success report.
Do not add `--upgrade` or a lockfile operation.

Windows targets `.venv/Scripts/python.exe`.
Linux and macOS target `.venv/bin/python`.
The executable, interpreter, and requirement paths remain individual arguments, including paths with spaces.

## Source discovery contract

Read pip configuration through the worktree interpreter once per invocation:

```text
[str(venv_interpreter), "-m", "pip", "config", "list"]
```

This command reads configuration.
It is not a pip installation.
Keep the existing capture options and configuration-read failure behavior.

During that read, capture these four settings:

- `global.index-url`
- `install.index-url`
- `global.extra-index-url`
- `install.extra-index-url`

Keep the current probe's first-matching primary URL result.
Do not add another configuration read or per-file probe.
Keep the connection timeout at three seconds.
Keep public-host, absent-configuration, unreadable-configuration, and unusable-host decisions unchanged.

For uv installation, resolve primary and extra sources separately:

1. Use the corresponding nonempty caller `PIP_*` value.
2. Otherwise, use the corresponding `install.*` setting.
3. Otherwise, use the corresponding `global.*` setting.
4. If no source applies, retain the implicit default or absent extra-source list.

## Child environment contract

Create a new copy of `os.environ` for each file attempt.
Do not reuse that dictionary for another file or invocation.
Do not change `os.environ`.
Do not write pip or uv configuration.

Preserve unrelated caller values.
Examples include proxy variables, certificate variables, `NODE_OPTIONS`, and GitHub token variables.
Tests use fake token values and never print them.

### Shared installation settings

Retain `PIP_RETRIES=1` and `PIP_TIMEOUT=15`.
These values remain effective for pip.
Do not claim that uv reads them as retry controls.

### uv runtime settings

Each uv installation child receives:

| Variable | Value | Purpose |
| --- | --- | --- |
| `UV_LINK_MODE` | `copy` | Use file copies for worktree storage. |
| `UV_NATIVE_TLS` | `1` | Keep the caller-required system-trust contract. |
| `UV_SYSTEM_CERTS` | `1` | Use the system trust option documented by installed uv. |
| `UV_NO_CONFIG` | `1` | Prevent uv source files from replacing the existing pip choices. |
| `UV_HTTP_RETRIES` | `1` | Keep the existing installation retry budget. |
| `UV_HTTP_TIMEOUT` | `15` | Keep the existing bounded transport wait. |

Remove child `UV_CONFIG_FILE`.
Do not force these settings in pip or browser environments.
Do not add insecure-host flags or disable certificate verification.

### No public override

The ordinary pip path retains its source environment and configuration behavior.
It must not receive a new `PIP_CONFIG_FILE` override.

For uv, normalize the source variables in the child:

| Variable | Action |
| --- | --- |
| `UV_INDEX` | Remove the inherited value. |
| `UV_DEFAULT_INDEX` | Remove the inherited value. |
| `UV_INDEX_URL` | Remove it, then set the effective pip primary source when present. |
| `UV_EXTRA_INDEX_URL` | Remove it, then set effective pip extra sources when present. |

Keep the source order of the selected extra indexes.
Do not set the public primary variable when a working mirror applies.
If pip has no explicit primary source, leave the uv primary variable absent.
The implicit public default then matches existing pip default behavior.

This normalization replaces only related source and configuration settings.
It prevents ambiguous precedence between old and current uv aliases.
Keep uv's default source-resolution policy.

### Public override

If the probe returns `PUBLIC_INDEX_URL`, apply this policy to each installation child:

1. Set `PIP_INDEX_URL=https://pypi.org/simple`.
2. Remove `PIP_EXTRA_INDEX_URL`.
3. Remove all four uv source aliases from the copied environment.
4. If uv is selected, set `UV_INDEX_URL=https://pypi.org/simple`.
5. If pip is selected, set `PIP_CONFIG_FILE=os.devnull`.

The uv path also retains `UV_NO_CONFIG=1`.
The pip null configuration prevents saved extra indexes from restoring a failed source.
Do not use the pip null configuration on an ordinary install or browser environment.
Preserve caller proxy and certificate environment values.

No inherited or saved primary or extra index may restore the failed mirror.
This feature does not translate every pip setting into uv.
It does not change source directives inside requirement files.
The current two requirement files contain no index directives.

### Later invocations

Reset `self.index_override` before the new probe.
Use a new probe object and source snapshot.
Discover uv again.
Do not retain prior child dictionaries.

These rules apply after successful and failed invocations.
A later reachable mirror must not inherit an earlier public override.

## Failure and report contract

Report the selected installer before file installation.
If uv is absent, state that absence as the pip-selection reason.
Report the installer, file name, and elapsed seconds for each attempt.
Use one decimal place.
Report duration after nonzero results and launch errors.

After a zero result, append the file name to the success list.
After a nonzero result, raise `RuntimeError`.
Include the installer, file name, and return code.
After a launch error, raise with installer and file context.
Include safe error detail, not environment contents or captured installer output.

The existing `main()` handler returns `1` after installation failure.
It must not start:

- Another requirement-file install or another installer.
- The environment health check.
- The browser download.
- The readiness report.
- GitHub credential configuration or account checks.

A successful run reports total dependency-install seconds.
That timer starts after one-time discovery and the index probe.
It ends after all present files succeed or all files are skipped.
An empty run returns `[]` and reports total duration.
A failed run does not report successful completion.

New bootstrap-owned reports use ASCII and STE.
Report only safe source hosts or source decisions.
Do not report tokens, credential-bearing URLs, or environment dictionaries.

## Preserved setup contract

Keep `--recreate`, environment creation, pip availability, and interpreter paths unchanged.
Keep the existing successful setup order:

```text
create_environment
install_requirements
check_environment_health
install_browser_driver
report_result
configure_git_username
warn_on_mismatch
```

Keep browser selection, download commands, repair guidance, and nonblocking download failure unchanged.
Keep caller `NODE_OPTIONS` and add `--use-system-ca` only when absent.
Do not apply new uv overrides through `_browser_environment()`.
Keep the existing zero-argument `_install_environment()` behavior for that caller.

Keep the expected GitHub account `jmorrison-juniper`.
Keep credential-variable warnings and repository credential configuration unchanged.
Offline tests replace all actual Git and GitHub actions.

## Offline test contract

New coverage belongs in `tests/unit/bootstrap/test_pip_index_probe.py`.
Use nested groups under `TestInstallEnvironment`.
Edit only the existing pip-selection fixture case in `tests/unit/scripts/test_browser_download_certificates.py`.

| Case | Required observations | Requirements |
| --- | --- | --- |
| uv is available | Discover once. Both files use the resolved path and explicit worktree interpreter, in order. | FR-001, FR-002, FR-004 |
| uv is absent | Both files use interpreter pip. The report names uv absence. Retry and timeout values remain. | FR-003, FR-011, FR-014 |
| Paths contain spaces | uv path, Windows interpreter path, and file path remain complete arguments. Also test non-Windows targeting. | FR-002, FR-003, FR-017 |
| Files are absent | Parameterize both, runtime-only, development-only, and neither. Return only successful names. | FR-004 |
| Caller uv settings conflict | Force copy and both system-trust variables for each uv child. Leave caller values unchanged. | FR-005, FR-006 |
| Unrelated caller settings exist | Preserve proxy, certificate, Node, and fake token values without reports of those values. | FR-006, FR-015 |
| Child dictionaries change | Record distinct identities. Change one dictionary and prove the other child and caller remain unchanged. | FR-006 |
| A mirror answers | Keep its primary and extra sources with uv and pip. Make no public override. | FR-007, FR-008 |
| Source precedence applies | Test environment, install-specific, and global primary and extra settings, including multiple extra indexes. | FR-008 |
| A mirror does not answer | Test both installers with conflicting pip and uv aliases. Suppress saved extras and use public only. | FR-007, FR-009 |
| Probe edge outcomes apply | Test absent, public, unreadable, empty, and unusable settings. Keep one read and at most one connection. | FR-007 |
| Two runs share a bootstrapper | Test changed uv availability and dead-then-reachable decisions, including a failed first run. | FR-010 |
| Either file fails | Test first and second file failures for both installers. Raise and suppress every later action. | FR-012, FR-013 |
| Discovered uv cannot start | Simulate `OSError`. Report file and installer context. Start no pip install. | FR-012, FR-013 |
| Controlled clocks apply | Assert one-decimal file durations, failed-attempt duration, successful total, and empty-run total. | FR-014 |
| Source values contain credentials | Use fake credentials. Assert no secret values in bootstrap-owned logs. | FR-015 |
| Setup compatibility applies | Use local creation substitutes. Preserve interpreter layout, parser options, package pins, and successful call order. | FR-016, FR-017, FR-019 |
| Browser compatibility applies | Preserve Node options, one system-CA option, repair guidance, and nonblocking browser failure. | FR-018 |

Use temporary files and controlled subprocess results.
Fail a test if an unexpected command or connection starts.
Do not accept skips as proof.
Require at least 80% coverage of changed behavior and retain the configured 90% report threshold.

Run the unchanged browser-driver and GitHub-account regression files with these tests.
The [quickstart guide](../quickstart.md) defines the later run boundary and commands.
