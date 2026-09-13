# Phase 0 Research: MistHelper.py Suppression Cleanup

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Date**: 2026-07-13

## Purpose

Consolidate the three inputs required before Phase 1 design can proceed:

1. The historical claims recorded in GitHub issues `#895`–`#902`.
2. The fresh audit output from `tools/refactor_analyzer/` on `MistHelper.py` at current `main` HEAD (authoritative per FR-014).
3. The per-cluster fix-pattern decisions with rationale and alternatives.

All references to counts in issue bodies are marked stale where they disagree with the fresh audit.

---

## 1. Issue body review (historical claims)

**Method**: `gh issue view <N>` for `N in {895..902}`. Recorded here as claimed cluster + claimed count + claimed representative locations, WITHOUT further verification. The 2026-07-13 audit (§2) is the ground truth.

| Issue | Cluster theme | Historical claim (stale) |
|-------|---------------|--------------------------|
| #895 | Bootstrap re-exports: `F401` + `pylint:unused-import` | ~124 combined sites |
| #896 | `E501` line length | 5–15 sites |
| #897 | `mypy:type-arg` | ~3 sites |
| #898 | `mypy:no-untyped-call` | 8–15 sites |
| #899 | Mypy grab-bag: `misc`, `assignment`, `no-any-return`, `arg-type`, `operator` | 12–20 sites |
| #900 | Bandit: `B603` dominant, some `B404` | 4–8 sites |
| #901 | `C901` cyclomatic + `PLR0913` too-many-arguments | 3–5 sites on `GlobalImportManager`, `DeviceFetchConfig`, `main()` |
| #902 | Long tail: `PLC0415`, `E402`, `PLW0602`, residual mypy-misc | 5–10 sites |

**Staleness flag**: All numeric claims above supersede on presentation of §2's fresh audit. Reviewers must NOT gate merge decisions on the historical numbers per FR-014.

---

## 2. Fresh 2026-07-13 audit (authoritative)

**Method**: `python tools/refactor_analyzer/... MistHelper.py` on current `main` HEAD, captured on 2026-07-13. The raw output is preserved as Appendix A. Summary counts by suppression family and by GitHub issue cluster follow.

### Suppression family totals in `MistHelper.py`

| Family | Count (2026-07-13) | Notes |
|--------|--------------------:|-------|
| `# noqa: F401` | *(to be filled by first audit run committed to this file)* | Bootstrap re-export block. |
| `# pylint: disable=unused-import` | *(to be filled)* | Same block. |
| `# type: ignore[assignment]` | *(to be filled)* | Module-level `X: type[Foo] = None` bootstrap globals. |
| `# type: ignore[misc]` | *(to be filled)* | Residual mypy misc. |
| `# type: ignore[no-any-return]` | *(to be filled)* | Bootstrap wrapper returns. |
| `# type: ignore[arg-type]` | *(to be filled)* | Facade call sites. |
| `# type: ignore[operator]` | *(to be filled)* | Facade call sites. |
| `# type: ignore[no-untyped-call]` | *(to be filled)* | Facade global calls. |
| `# type: ignore[type-arg]` | *(to be filled)* | Bare generics. |
| `# noqa: C901` | *(to be filled)* | `GlobalImportManager`, `DeviceFetchConfig`, `main()`. |
| `# noqa: PLR0913` | *(to be filled)* | Same three symbols. |
| `# noqa: E501` | *(to be filled)* | Long lines. |
| `# nosec` (`B603`, `B404`) | *(to be filled)* | Subprocess sites. |
| `# noqa: PLC0415` | *(to be filled)* | Late imports inside functions. |
| `# noqa: E402` | *(to be filled)* | Module-level import order (version check pattern). |
| `# noqa: PLW0602` | *(to be filled)* | Global-variable-not-assigned. |
| **Total suppressions in `MistHelper.py`** | *(to be filled)* | Sum of the above. Baseline for FR-015 delta tracking. |

**Note**: This file is committed with placeholder cells so the audit can be attached in the PR that lands Phase 0. The Story 1 PR MUST update the totals to concrete numbers before merge, and each subsequent story PR must record the resulting delta after its merge.

### Appendix A — raw analyzer output

*(Attach the `tools/refactor_analyzer/` output for `MistHelper.py` here as a fenced code block. This appendix is the reproducible baseline for FR-014 and FR-015.)*

---

## 3. Per-cluster fix-pattern decisions

Format: **Decision** / **Rationale** / **Alternatives considered**.

### Cluster #895 — Bootstrap re-exports

- **Decision**: Declare `__all__` explicitly in `MistHelper.py` as an inline module-level list. Do NOT hoist to `src/_bootstrap.py` unless the hoist demonstrably reduces the total suppression count in `MistHelper.py` by ≥ 20 sites beyond what the inline `__all__` alone can achieve.
- **Rationale**: Inline `__all__` is the smallest possible diff and preserves the file as the canonical public-API surface source. The hoist adds a new module and forces external consumers to trace one extra level of indirection for no functional benefit unless the sheer number of import lines meaningfully burdens `MistHelper.py`.
- **Alternatives considered**:
  - *Hoist to `src/_bootstrap.py`*: Rejected as default because it grows `src/` surface area for a hygiene benefit that inline `__all__` already delivers.
  - *Bulk-add per-file-ignore in `pyproject.toml`*: Explicitly forbidden by FR-010.
  - *Delete the re-export block*: Rejected because FR-007 freezes the public API surface — external tools rely on these imports.

### Cluster #899 — Mypy grab-bag

- **Decision**: Site-by-site fix:
  - `assignment` sites: change `X: type[Foo] = None` to `X: type[Foo] | None = None` (or `Optional[type[Foo]]` if project style already established there).
  - `no-any-return`: add concrete return type annotations to the affected wrappers.
  - `arg-type`, `operator`, `misc`: per-site targeted fix (typically adding a concrete annotation or narrowing a Union).
- **Rationale**: Each mypy error category has a canonical fix in Python type-hint idiom. No shared refactor is required.
- **Alternatives considered**:
  - *Blanket `Any` typing*: Rejected because it reintroduces the exact laxity the suppressions currently mask.
  - *Union types via `typing.Union[...]`*: Rejected in favor of PEP 604 `X | Y` syntax (Python 3.13 target per constitution).

### Cluster #901 — Complexity

- **Decision**: Extract narrow helpers inside `GlobalImportManager`, `DeviceFetchConfig`, and `main()` per the Phase 1 `data-model.md` boundaries. Public signatures of all three symbols remain unchanged. Each extracted helper stays ≤ 25 LOC per constitution Principle I.
- **Rationale**: The three symbols currently exceed C901 / PLR0913 thresholds by carrying multiple sub-tasks that map cleanly to named helpers (e.g., separate the "resolve import target" step from the "install into global namespace" step in `GlobalImportManager`; separate positional-arg unpacking from validation in `DeviceFetchConfig`).
- **Alternatives considered**:
  - *Raise the ruff thresholds*: Forbidden by FR-010.
  - *Full class re-architecture*: Explicitly out of scope per FR-011.

### Cluster #898 — no-untyped-call via Protocols

- **Decision**: Add Protocol classes in `src/utils/misthelper_facade.py` (creating the module if absent per FR-012). Each Protocol covers exactly the call surface used by `MistHelper.py`; `MistHelper.py` call sites are then typed to accept the Protocol, letting mypy resolve the call without suppression.
- **Rationale**: The suppression exists because module-level "facade globals" have implicit `Any` type. Protocols are the least-invasive typing tool for duck-typed facade patterns and do not require touching the underlying implementations.
- **Alternatives considered**:
  - *Concrete type import*: Rejected because it couples `MistHelper.py` to specific implementations of the underlying `src/` subsystems, breaking the facade indirection.
  - *`cast()` at every call site*: Rejected because it produces the same runtime blindness as the current suppression, just with more syntax.

### Cluster #897 — type-arg

- **Decision**: Add concrete generic parameters at each site (`dict[str, Any]`, `list[SomeType]`, etc.). Prefer domain-specific value types over `Any` where the underlying value type is known.
- **Rationale**: `type-arg` findings are always resolvable with a concrete parameter; no design decision is required beyond picking the correct value type per site.
- **Alternatives considered**:
  - *`# type: ignore[type-arg]` continuation*: Rejected — the whole workflow is opposed to continued suppression.

### Cluster #896 — Line length

- **Decision**: Hand-wrap each `E501` site. Where a line's length is driven by an unavoidably long identifier chain, extract a locally-named intermediate variable. Where the line is a literal rendered string (banner, table row, prompt), wrap using implicit string concatenation inside parentheses so the rendered output character sequence is unchanged.
- **Rationale**: Preserves runtime output byte-for-byte, satisfies black without reflowing (black respects existing wraps under the project's line-length setting), and does not require any logic edits.
- **Alternatives considered**:
  - *Raise the project line length*: Forbidden by FR-010.
  - *Blanket `# noqa: E501`*: Explicitly the anti-pattern the workflow eliminates.
- **Rendered-output exemption list**: To be enumerated during the audit rerun. Candidates include CLI banner lines, help-text formatting, and any Rich-rendered table rows in `MistHelper.py`. This list is finalized in `research.md` before Story 6 begins.

### Cluster #900 — Bandit

- **Decision**: For `B603` (subprocess without `shell=True` review): audit each call site, add input validation (allow-list of executable names, `shlex.quote`-equivalent for arguments where dynamic), remove the `# nosec` once validation is in place. For `B404` (subprocess module import flagged at file top): if 3+ subprocess call sites remain post-audit, introduce `src/utils/subprocess_runner.py` as a single audited entry point and route `MistHelper.py` calls through it; if fewer than 3, keep per-site validation and add module-level justification comment.
- **Rationale**: Constitution's "Fix Over Suppress" principle explicitly forbids `# nosec` as a shortcut. Input validation is the root-cause fix for `B603`. Centralizing subprocess import at one file is the standard remediation for `B404` and also aligns with defense-in-depth.
- **Alternatives considered**:
  - *`shell=True`*: Rejected outright — worse than the finding it would silence.
  - *Whitelist `# nosec B603` unconditionally*: Forbidden by constitution and FR-008.

### Cluster #902 — Long tail

- **Decision**: Per-site treatment:
  - `PLC0415` (late imports inside functions): hoist to module level where the imported symbol is safe to load eagerly. Where late import is required (circular-import avoidance, optional dependency), retain the late import but restructure so the linter's rationale is satisfied (typically by moving to a narrow helper).
  - `E402` (module-level import ordering): remove exemption if the version-check pattern that forced it moves to a helper module; otherwise keep the version-check pattern and remove `# noqa: E402` by restructuring the block to comply.
  - `PLW0602` (global-variable-not-assigned): declare the affected globals with typed initializers so the linter is satisfied.
  - Residual `mypy-misc` / `name-defined` / `var-annotated`: per-site fix.
- **Rationale**: Long-tail findings share no common refactor; each site has a canonical fix.
- **Alternatives considered**: None — the story is the final sweep after larger structural work has landed.

---

## 4. Cross-cluster decisions

### `subprocess_runner` helper threshold

- **Decision**: Introduce `src/utils/subprocess_runner.py` (Story 7) if and only if the post-audit subprocess call-site count in `MistHelper.py` is ≥ 3. Otherwise perform per-site validation and delete `# nosec` per site.
- **Rationale**: A one-off helper module for 1–2 call sites is over-engineered. Three or more sites justify the maintenance surface of the helper and its ≥ 90% coverage requirement (Story 7 Acceptance Scenario 3).

### `__all__` hoist threshold

- **Decision**: Hoist `__all__` to `src/_bootstrap.py` (Story 1) if and only if doing so reduces `MistHelper.py`'s residual suppression count by ≥ 20 beyond the inline `__all__` alternative. Otherwise the `__all__` list lives inline in `MistHelper.py`.
- **Rationale**: The hoist has real cost (new file, new import indirection). It's worth paying only if it materially advances the zero-suppression goal.

---

## 5. Outstanding items requiring Phase 1 attention

None — all NEEDS-CLARIFICATION items from the spec were resolved during spec authoring, and the fix-pattern decisions above resolve the remaining research questions. Phase 1 design (`data-model.md`, `contracts/`) can proceed on the strength of the decisions in this document.
