# Implementation Plan: Stable capture session signing

**Branch**: `jmorrison-juniper-capture-session-signing-key` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3213-capture-session-signing/spec.md`

## Summary

Document the existing stable signing-key deployment.
Add exact deployment contracts and real Flask cookie tests.
Keep the working production implementation unchanged.

The initial base is `1615a4444752c7b0fe91a103920c1cc045145ed0`.
It contains the merged default-disabled multi-site write gate.
The issue claim reserves every test, specification, template, and release-note path.
The parent confirmed that `documentation/upgrade_capture_portal.md` has no active reservation.
The issue comment reserves that exact path before its edit.

## Technical Context

**Language/Version**: Python 3.13 or later.

**Primary Dependencies**: Existing Flask, Flask-WTF, PyYAML, pytest, and project tools. No dependency changes.

**Storage**: The real in-memory `SessionRegistry`. Each test owns its registry.

**Testing**: Actual application configuration, application factory, Flask clients, authentication routes, session cookies, and form tokens.

**Target Platform**: Local macOS validation. The deployment instructions remain compatible with Windows and Linux.

**Project Type**: Deployment guidance and regression tests.

**Performance Goals**: Focused tests need no network service or server process.

**Constraints**: No publication, container restart, live operation, source change, shared specification change, or policy change.

**Scale/Scope**: One deployment template, one unowned operator guide, two dedicated test packages, three specification files, and one release fragment.

## Constitution Check

Use dedicated nested test packages rather than more flat test modules.
Keep each new package within five direct files.
Use the existing production classes and interfaces.
Add no production class, wrapper, compatibility path, schema, or primary key.

The existing source modules, test parents, documentation directory, and fragment directory exceed the structural limit.
This repair does not restructure them or add a new production source child.
A separate maintenance change can group those existing files after its own ownership review.

Keep credentials in environment values only.
Generate test signing keys at runtime.
Use synthetic cloud credentials at external transport boundaries only.
Keep the actual signing, session guard, cookie, form-token, and registry decisions in the test path.
Do not represent retained test authentication state as persistent production authentication.

The parent's explicit publication restriction replaces automatic publication and deployment hooks for this local preparation.

## Project Structure

### Documentation (this feature)

```text
specs/3213-capture-session-signing/
  spec.md
  plan.md
  tasks.md
```

### Source Code (repository root)

```text
deploy/.env.example
documentation/upgrade_capture_portal.md
tests/contract/upgrade_portal/session_signing/
  __init__.py
  conftest.py
  test_deployment.py
  test_restart.py
  test_no_leak.py
tests/unit/upgrade_portal/session_signing/
  __init__.py
  test_key_configuration.py
changelog.d/issue-3213-capture-session-signing.md
```

**Structure Decision**: Edit the existing deployment template and the confirmed operator guide.
Read `compose.yml` and the production signing and authentication modules without editing them.

## Execution and Validation

1. Prove the existing cookie path before any source decision.
2. Add the deployment contract first and record its failure on the unchanged template.
3. Add the optional commented setting and the operator instructions.
4. Run owned tests and adjacent configuration, authentication, and security contracts.
5. Run syntax, Ruff, Black, the current CI type scope, Bandit, writing checks, and the unchanged ratchet preflight.
6. Commit only the explicit owned file set with the required coauthor.
7. Run the committed-difference test-quality gate against the verified intended base.
8. Preserve the complete pull request template in an offline draft.
9. Report the local commit and remain unpublished until the parent grants release.

### Native capability results

`pwsh -NoProfile -File .specify/scripts/powershell/setup-plan.ps1 -Json` failed because `pwsh` is absent.
The branch hook passed in `--dry-run` mode with the exact app-managed branch.
It created no branch and changed no shared specification file.
The feature-only equivalent uses the current specification, plan, and task templates.
Optional automatic commit hooks do not run before local validation.
Companion hooks do not change shared context files.

The initial system Python is 3.9.6 and cannot install the current requirements.
The unchanged bootstrap with Python 3.13.13 failed when copied-interpreter `ensurepip` received `SIGABRT`.
Only this worktree's ignored `.venv` recovered with UV seeds, copy mode, and system certificates.
No bootstrap source changed.

The standard `pip-audit -r requirements.txt` command also failed in copied-interpreter `ensurepip`.
That failure is not an audit pass.
Use the complete hashed runtime closure with `--require-hashes --no-deps --disable-pip`.
Report the counted dependencies and the separate Git-only development tool limit.

## Complexity Tracking

No production logic changes.
The signed-cookie acceptance does not imply cloud-session persistence.
The worker-registry control must keep that limit explicit in tests and operator instructions.
Report this bounded repair as Part of #3213, not a full sign-in continuity repair.
Record the existing registry-loss defect in a separate bug issue without implementing persistence.
[The authentication issue](https://github.com/jmorrison-juniper/MistHelper/issues/3714) records the verified three-mode refusal.
