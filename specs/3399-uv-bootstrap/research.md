# Offline Research: uv worktree bootstrap

**Issue**: #3399
**Branch**: `jmorrison-juniper-unclaimed-issue-repairs`
**Specification**: [spec.md](spec.md)
**Date**: 2026-09-30

## Research boundary

This research used repository files and installed command help.
It used no web requests, package installations, browser downloads, or GitHub account requests.
It did not use the worktree environment.
The separate dependency bootstrap remains outside this planning task.

The initial constitution review passed for this plan-only task.
The design edits existing source and test files without new source classes or modules.
Section 8 records existing structural debt.

## 1. Python and runtime ownership

**Decision**: Target Python 3.13 or newer.
Use the completed worktree environment for later tests.
Do not use the macOS default `python3` for those tests.

**Rationale**: `pyproject.toml` requires Python 3.13 or newer.
The caller reports macOS Python 3.9.6 and an existing uv-managed Python 3.13.13.
Interpreter selection for environment creation is not part of this feature.

**Alternatives considered**: Supporting Python 3.9 would violate the constitution.
Changing environment creation would expand the feature.
Using `uv run` could change the environment or start a download.

**Evidence**: `pyproject.toml`, `WorktreeBootstrapper.create_environment()`, and the caller's environment statement.

## 2. Installer discovery and commands

**Decision**: Call `shutil.which("uv")` once in each `install_requirements()` invocation.
Keep the result in a local variable.
Pass that result to the run-local installation policy.

The uv argument list is:

```text
[resolved_uv, "pip", "install", "--python", str(interpreter), "-r", str(requirement_file)]
```

The pip argument list is:

```text
[str(interpreter), "-m", "pip", "install", "-r", str(requirement_file)]
```

**Rationale**: Both commands target the worktree interpreter.
Argument lists preserve paths with spaces.
One local installer choice covers both requirement files.
The existing pip configuration read remains necessary when uv performs installation.

**Alternatives considered**: Version probes add discovery calls.
Interpreter-adjacent searches and module searches change the required discovery rule.
Automatic uv installation changes dependencies.

**Evidence**: `scripts/bootstrap_worktree.py` and the interpreter option in `src/foundation/runtime/bootstrap/package_installer.py`.
Installed `uv 0.11.8` help confirms the `--python` and `--requirements` options.

## 3. Child-only uv settings

**Decision**: Give each file install a fresh copy of `os.environ`.
Each uv child gets `UV_LINK_MODE=copy` and `UV_NATIVE_TLS=1`.
Also set `UV_SYSTEM_CERTS=1` in that child.
Do not add these overrides to the caller or browser environment.

**Rationale**: Copy mode supports OneDrive storage.
The caller requires `UV_NATIVE_TLS=1`.
Installed uv help names `UV_SYSTEM_CERTS` for system certificate trust.
Setting both trust variables supports the required contract and the installed command contract without another discovery call.
Neither setting disables certificate verification.

**Alternatives considered**: Global environment assignments break isolation.
Using only the older trust variable relies on behavior that installed help does not document.
Removing the required older variable would violate the caller's instruction.

**Evidence**: `uv help pip install`, the link-mode options, and the system-certificate options.
Offline help does not prove whether this uv version accepts the older variable as an alias.
The additional documented variable removes that design dependency.

## 4. One pip configuration read and one existing probe

**Decision**: Keep `PipIndexProbe` and its five existing methods.
Capture source settings during its existing `pip config list` subprocess.
Store those settings on the new, run-local probe object.

Extend `_parse_index_url()` with an optional output mapping.
Capture `global.index-url`, `install.index-url`, and their `extra-index-url` counterparts.
Keep its existing first-matching primary URL result for the connection probe.
Do not change public-host detection, unusable-host behavior, or the three-second timeout.

**Rationale**: A second configuration subprocess is unnecessary.
The existing probe decision and the effective installation sources serve different purposes.
The source snapshot must include extra indexes, which the current parser does not return.

**Alternatives considered**: A second pip configuration read breaks the once-per-run requirement.
A new configuration service adds structure without a feature need.
Changing which configured host the probe selects expands the existing probe behavior.

**Evidence**: `PipIndexProbe.read_index_url()`, `_parse_index_url()`, `fallback_index()`, and existing index-probe tests.
The installed pip parser applies environment settings after command-specific and global settings.

## 5. Working source settings

**Decision**: Treat existing pip source choices as authoritative.
For installation, use a nonempty caller `PIP_INDEX_URL` before `install.index-url`, then `global.index-url`.
Apply the same precedence to extra indexes.
If no primary source applies, retain the installer's implicit public default.

For uv, clear inherited `UV_INDEX`, `UV_DEFAULT_INDEX`, `UV_INDEX_URL`, and `UV_EXTRA_INDEX_URL` in the child copy.
Map the selected primary source to `UV_INDEX_URL`.
Map selected extra sources to `UV_EXTRA_INDEX_URL`.
Keep their order.
Set child `UV_NO_CONFIG=1` and remove child `UV_CONFIG_FILE`.

**Rationale**: uv must not replace a working pip mirror with its own default.
Competing uv aliases have precedence that installed help does not fully describe.
Clearing those aliases removes that uncertainty.
Suppressing uv configuration discovery prevents a saved uv index from replacing the existing pip choices.

The legacy uv index variables remain documented options in installed uv help.
They also avoid a new minimum uv version requirement.
Keep uv's existing `first-index` resolution policy.
This feature preserves source choices, not identical package selection across different resolvers.

**Alternatives considered**: Passing only `PIP_*` values does not establish a uv source contract.
Keeping competing uv source aliases can restore another index.
Changing uv to `unsafe-best-match` would weaken its default source protection.

**Evidence**: The index and configuration sections of `uv help pip install`.
Offline help does not explicitly establish pip-configuration support in uv.
Explicit source mapping does not depend on such support.

## 6. Exclusive public override

**Decision**: If the existing probe returns `PUBLIC_INDEX_URL`, use that source for both file installs.
Set child `PIP_INDEX_URL` to `https://pypi.org/simple`.
Remove child `PIP_EXTRA_INDEX_URL` and all four uv source aliases.

For uv, set child `UV_INDEX_URL` to the public URL.
Keep child `UV_NO_CONFIG=1`.
For pip installation, set child `PIP_CONFIG_FILE` to `os.devnull`.
Do not apply this file-config suppression to normal pip installs or browser setup.

**Rationale**: Removing an extra-index environment variable does not remove a saved pip extra index.
The child-only null configuration prevents saved primary and extra indexes from restoring the dead mirror.
The caller's proxy and certificate environment variables remain unchanged.
Saved configuration files remain unchanged.

**Alternatives considered**: Retaining inherited extra indexes violates the exclusive public override.
Changing saved configuration violates run isolation.
Using insecure-host settings would weaken certificate verification.

**Evidence**: Existing `_install_environment()` behavior and installed pip configuration source.
The installed pip 21.2.4 `_load_config_files()` method skips file configuration when `PIP_CONFIG_FILE == os.devnull`.
This is offline evidence from a system installation, not a test of the active worktree environment.

## 7. Failures and timing

**Decision**: Raise `RuntimeError` for a nonzero installer result.
Identify the installer, file name, and return code.
Convert an installer launch error into a failure with installer and file context.
Do not change installers after discovery.

Keep `main()` as the existing failure boundary.
Its exception handler returns `1` before later setup actions.
Use `time.monotonic()` for each attempted file.
Report file duration in a `finally` path.
Keep the total-duration boundary after discovery and the index probe.
Report a total only when `install_requirements()` returns successfully.

**Rationale**: A failed uv installation is not executable absence.
The existing bootstrap already stops later setup actions after an installation exception.
Controlled clocks permit meaningful offline timing tests.

**Alternatives considered**: Returning a false success result can produce a ready report.
Automatic pip retry hides uv failure.
Real performance benchmarks would need downloads and storage access.

**Evidence**: Existing `_install_file()`, `install_requirements()`, and `main()`.

## 8. Existing structure and test isolation

**Decision**: Edit `scripts/bootstrap_worktree.py` in place.
Reuse `WorktreeBootstrapper`, `PipIndexProbe`, and their existing methods.
Do not import `PackageInstaller` into this script.

Extend `tests/unit/bootstrap/test_pip_index_probe.py`.
Place new test groups inside the existing `TestInstallEnvironment` class.
Add one nested group with no more than five direct children.
Keep each new method within the constitution limits.

Also edit one existing dependency-install test in `tests/unit/scripts/test_browser_download_certificates.py`.
That test must simulate absent uv rather than depend on the host's installed tools.
Do not change its browser assertions.

**Rationale**: `PackageInstaller` supplies useful argument-list prior art.
Its multiple discovery attempts, automatic uv installation, and recoverable failure policy do not satisfy this specification.
The existing bootstrap test directory already has seven children.
Adding another file or package there would increase existing structural debt.

`WorktreeBootstrapper` already has ten direct methods.
The source module and `scripts/` also exceed five direct children.
`TestFallbackIndex` already has six methods.
The browser-certificate test module also exceeds five direct definitions.
Do not increase those counts.

**Separate remediation**: Later maintenance can reduce these existing counts without changing bootstrap behavior.
That maintenance requires parent authorization.
It is not part of issue #3399.

**Alternatives considered**: New helper modules or top-level test classes add direct children to existing noncompliant parents.
Broad structural changes conflict with the focused feature scope.

**Evidence**: Static source inspection, the existing test files, and constitution principle I.

## Research result

All design choices are resolved.
No `NEEDS CLARIFICATION` item remains.
Offline evidence does not prove live installation speed or network behavior.
The plan requires offline behavioral tests and makes no fixed speed claim.
