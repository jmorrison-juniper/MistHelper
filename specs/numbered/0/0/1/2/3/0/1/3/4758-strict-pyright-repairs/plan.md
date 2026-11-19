# Implementation Plan: Strict entry-point type repairs

**Branch**: `jmorrison-juniper-strict-pyright-repairs` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Resolve strict entry-point diagnostics and their required API and cache contracts.
Preserve dynamic entry points and correct shared contracts.
The final candidate starts from current main `26ac261392ac29119fa4f83e30c6ce9a0df12ab3`.
The final strict report has zero errors across three files.
Do not push or open a pull request until the coordinator opens a publication slot.

## Technical Context

**Language/Version**: Python 3.15.2.

**Primary Dependencies**: Locked dependencies from `uv.lock`. Pyright 1.1.414 runs through `uvx`.

**Storage**: No schema or data changes.

**Testing**: Pytest, Ruff, Black, mypy, Bandit, symbol comparison, and focused repository guards.

**Target Platform**: macOS analysis. Preserve Windows and Linux paths.

**Project Type**: CLI entry point with dynamic module exports and injected callbacks.

**Performance Goals**: No new network, file, or cache operation.

**Constraints**: No ignores, disabled rules, Any casts, dummy references, removed live declarations, or weakened tests.

**Scale/Scope**: One strict entry-point analysis and its supporting contracts.

## Constitution Check

- Use the managed numeric route calculated by PowerShell 7.7.0.
- Keep the feature selector command-scoped.
- Preserve existing oversized modules. Do not increase their structural debt without a necessary contract.
- Track broader module division separately from this behavior-preserving repair.
- Use typed class methods for new behavior.
- Keep external requests mocked and retain production confirmation boundaries.
- Keep dependency manifests unchanged in this repair.
- Use the granted narrow handoff for `web_portal/app.py`, which PR #4208 also changes.
- Do not push, open a pull request, merge, build a container, or deploy before the coordinator opens a slot.
- Unique process records enter only this managed feature and its own changelog fragment.

The app-created branch replaces the branch-creation hook.
Optional commit hooks are deferred to explicit verified commits.
No mandatory post-specification or planning hook is enabled.

## Project Structure

Primary changes belong in `MistHelper.py`.
Supporting annotations belong in their existing owner modules under `src/`.
Third-party declarations must describe actual used contracts without masking other imports.
Focused tests belong in the established entry-point test tree.
Supporting feature records belong under `design/`.

## Repair Sequence

1. Record the locked environment, live base, ownership, and baseline.
2. Resolve local collection inference, exception scope, optional imports, and dynamic module methods.
3. Give verified host helpers public names and update every owned caller.
4. Replace string-based mode lookup with direct typed handlers in the actual dispatcher.
5. Correct callbacks, site records, selector methods, and deferred initialization contracts.
6. Add focused regression cases, then run strict analysis and applicable standard gates.
7. Record exact outcomes and commit only verified owned files.

## Validation

The strict command is:

```text
rtk bypass uvx --from pyright==1.1.414 pyright --project specs/numbered/0/0/1/2/3/0/1/3/4758-strict-pyright-repairs/design/contracts/pyright.json --outputjson
```

The committed configuration uses strict mode, Python 3.15, the worktree environment, and bounded third-party declarations.
This explicit analysis does not replace the default project checks.
Require `filesAnalyzed: 3`, `errorCount: 0`, and `warningCount: 0`.
Preserve raw JSON and gate output in session artifacts.
The feature analysis records exact commands, results, and intentional symbol changes.

## Complexity Tracking

Existing `MistHelper.py` and several supporting classes exceed structural limits.
This repair changes contracts and necessary typed methods, not unrelated control flow.
Broader module division requires a separate change and must not remove exported symbols.

## Implementation decisions

Review rejected the original private-export expansion and dynamic-import substitutions.
The correction restores the original 196 explicit exports and the historical snapshot.
Static imports use the bounded declarations beside the committed analyzer configuration.
Verified cross-module helpers receive public names without aliases.
Their owned callers use those names through the existing resolver or WSGI host.
The first initializer handoff permits exactly four references inside `initialize()`.
The additional handoff permits the authentication-status reference and its directly related module documentation.
The actual mode dispatcher binds direct callbacks on each invocation.
It preserves predicate order, short-circuit evaluation, and handler replacement before dispatch.
No parallel registry, getter layer, or compatibility adapter exists.
The dispatcher now builds its small local table instead of caching predicates globally.
Its required typed dispatch remains in one existing function.
See [the correction record](design/contracts/correction.md) for call paths, limitations, and remaining diagnostics.

The module context type now has named, typed methods and one shared attribute mapping.
Tests exercise all seven context names and ordinary module attributes.
The module type retains its name and its `MistHelper` module origin.

The existing MSP selectors become public methods.
Every exact-name Python consumer uses `select_msps` and `select_orgs_from_msp`.
No compatibility alias remains.

Menu 291 retains a lazy lambda, one `None` default, and its original keyword call.
An explicitly typed absent-mode constant provides the tri-state argument type.
Its cast applies only to the literal `None`, never to external data or a held source contract.
A direct method reference failed the existing default-shape regression and was rejected.

Policy menus reject an absent session before client construction.
Authenticated sessions retain their identity.
No confirmation, backup, or production request occurs in the absent-session tests.

The combined candidate applies the authorized API and cache annotations without changing their function bodies or defaults.
It removes nine unused private declarations and four helpers used only by those declarations.
It renames verified cross-module helpers to explicit public names and updates their owned consumers.
The implementation keeps all explicit exports unchanged.
The final strict report and focused regression results are recorded in [analysis.md](analysis.md).
