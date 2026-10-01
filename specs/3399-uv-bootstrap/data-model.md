# Data Model: uv worktree bootstrap

**Specification**: [spec.md](spec.md)
**Contract**: [bootstrap-installation.md](contracts/bootstrap-installation.md)

## Model boundary

These entities describe existing objects and local values.
They do not require new production classes, dataclasses, database tables, or persistent records.
The corrected implementation uses one nested installation-policy class to keep changed functions within their limits.
That class holds only the run-local values below.

## 1. Install run

**Owner**: `WorktreeBootstrapper.install_requirements()`.
**Lifetime**: One invocation.

| Field | Representation | Rule |
| --- | --- | --- |
| Installer choice | Resolved uv path or `None`. | Discover once. `None` selects pip installation. |
| Interpreter | Existing `Path` property. | Target the worktree `.venv`. |
| Index decision | Public override or `None`, with a fresh probe snapshot. | Make a new decision for every invocation. |
| Completed files | Ordered `list[str]`. | Append only after success. |
| Timing and outcome | Monotonic start values and success or exception. | Report file duration on each attempt. |

An install run owns zero, one, or two requirement-file attempts.
It uses one installer choice for all attempts.
It uses one index decision for all attempts.
It creates a separate child environment for each attempt.

**Validation**:

- The selected uv path comes only from `shutil.which("uv")`.
- Paths remain separate command arguments.
- A later invocation discards earlier installer selection and index settings.
- A failed invocation returns no success list.

## 2. Requirement file

**Owner**: Existing `REQUIREMENT_FILES` and the worktree root.

| Field | Representation | Rule |
| --- | --- | --- |
| Name | `requirements.txt` or `requirements-dev.txt`. | Preserve the existing order. |
| Path | `root / name`. | Use `pathlib.Path`. |
| Presence | `path.is_file()`. | Skip an absent file. |
| Result | Return code or launch failure. | A nonzero code raises. |
| Duration | Monotonic elapsed seconds. | Display one decimal place. |

Do not change file contents, pins, or dependency declarations.
Do not add an upgrade flag.

## 3. Index decision

**Owner**: One new `PipIndexProbe` instance.

| Field | Representation | Rule |
| --- | --- | --- |
| Global primary | Captured `global.index-url` value. | Preserve it when applicable. |
| Install primary | Captured `install.index-url` value. | Precede the global value for installation. |
| Global extra sources | Captured `global.extra-index-url` value. | Preserve source order when applicable. |
| Install extra sources | Captured `install.extra-index-url` value. | Precede the global value for installation. |
| Override | `PUBLIC_INDEX_URL` or `None`. | Use public only when the existing probe selects it. |

Nonempty caller `PIP_*` source values precede the captured file settings.
The probe retains its existing first-matching primary-line decision.
Effective installation precedence does not change that probe decision.

Configuration absence or discovery failure produces an empty snapshot.
A public host needs no connection probe.
An unusable host retains the existing no-override behavior.
A reachable mirror produces no public override.
An unreachable mirror produces an exclusive public override.

The existing `self.index_override` remains available to the unchanged browser environment helper.
Reset it before every new install invocation.
Store no uv selection on the bootstrapper.

## 4. Install environment

**Owner**: One file-install subprocess.
**Representation**: A new `dict[str, str]`.

| Field group | Rule |
| --- | --- |
| Caller settings | Copy current `os.environ`. Preserve unrelated values. |
| Pip retry settings | Retain `PIP_RETRIES=1` and `PIP_TIMEOUT=15`. |
| uv runtime settings | Force copy mode and both documented and required system-trust variables only for uv installation. |
| Source settings | Apply the command-specific mapping in the contract. |
| Configuration control | Suppress uv source configuration. Suppress pip file configuration only for public fallback installation. |

No environment dictionary shares mutable state with another file or later invocation.
Changing one child dictionary must not change another child or the caller.
Never print this dictionary or its secret values.

## State transitions

```text
Start
  -> Discover installer
  -> Reset prior override
  -> Read configuration and make one index decision
  -> Start total timer
  -> Inspect next requirement file
       Absent -> Skip -> Inspect next file
       Present -> Build child -> Attempt install
                    Code 0 -> Record file -> Inspect next file
                    Nonzero code -> Report duration -> Raise -> main returns 1
                    Launch error -> Report duration -> Raise -> main returns 1
  -> Report successful total -> Return completed file names
  -> Existing health, browser, readiness, and account sequence
```

No failure transition starts pip after uv.
No failure transition starts another requirement file or later setup action.
A later invocation starts with fresh discovery, configuration, environments, and clocks.
