# Phase 0 Research: Hot-Classes Serial Extraction

**Feature**: `specs/1013-misthelper-refactor-hot-classes/`
**Date**: 2026-07-07
**Predecessors**: 1010 (13 PRs), 1011 (20 PRs), 1012 (bounded bundle) — all closed with baseline >=99.6/A+.

This document consolidates the design decisions needed to lower `spec.md` into an implementable serial per-PR workflow. Each decision follows the SpecKit research contract: **Decision / Rationale / Alternatives considered**.

The Phase 0 collision audit performed on 2026-07-07 partitions the 47 Hot-bucket candidates into two action-types (Cat A: facade removal; Cat B: fresh extraction). All subsequent decisions treat Cat A and Cat B as distinct sub-flows sharing common guardrails.

---

## Decision 1 — Action-type categorization: Cat A (facade removal) vs Cat B (fresh extraction), determined by 2026-07-07 collision audit

**Decision**: Each of the 47 Hot-bucket candidates is pre-classified into one of three action-types before dispatch. The classification is fixed at dispatch time by a filesystem grep against `src/` and does not change during PR execution.

**Category definitions**:

- **Cat A — facade removal**: A same-name class definition already exists under `src/` (the canonical body, established by 1010/1011). The `MistHelper.py` copy is a stale facade — either a thin delegation shim retained after a prior fold, or a re-imported wrapper. The Cat A PR **deletes the facade** at the `MistHelper.py` source anchor, rewrites callsites to import directly from the existing `src/` module, and creates **zero new files**. Method-parity between facade and canonical body is verified in-flight per FR-025.
- **Cat B — fresh extraction**: No same-name class definition exists under `src/`. The Cat B PR performs the standard extract-and-delete workflow: the class body moves to a newly-created file under the pinned landing package (per spec's Dispatch Queue), the `MistHelper.py` definition is deleted, callsites are rewritten to import from the new module. Every guideline flag surfaced by the analyzer is resolved in-flight per FR-006.
- **Cat C — ambiguous / partial overlap**: A same-name class exists under `src/` but the two bodies diverge non-trivially (public API drift, added methods, renamed private helpers, or genuinely distinct class of the same name). A Cat C PR would require pausing dispatch and landing a discovery commit before the extraction proceeds.

**Collision-audit methodology** (2026-07-07 sweep):

```bash
# For each of the 47 candidate class names, from repo root:
git checkout main
for CLASS in <47 candidate names>; do
  grep -rn "^class ${CLASS}[ (:]" src/ | tee -a data/collision_audit_1013.txt
done
```

Any hit under `src/` marks the candidate a Cat A/C. Zero hits marks it Cat B. Discrimination between Cat A and Cat C is by inspection of the facade body vs the canonical body — if the facade's public methods are all present on the canonical class with matching signatures, it is Cat A; if any method is missing, renamed, or diverges in signature, it is Cat C pending discovery.

**2026-07-07 audit result**: **4 Cat A / 43 Cat B / 0 Cat C**. The four Cat A candidates and their source-line anchors:

| Position | Class | MistHelper.py anchor | Existing canonical body | Facade shape |
|---|---|---|---|---|
| 1 | `GatewayTemplateConfigManager` | `MistHelper.py:15596` | `src/gateway/template_config.py:30` | 3 static delegation methods on the facade; all three are 1:1 present on the canonical class. |
| 2 | `FirmwareManager` | `MistHelper.py:17376` | `src/firmware/firmware_manager.py:134` | Factory facade with 270 defs (delegation to canonical class methods); method inventory audited 1:1 against canonical body. |
| 3 | `SiteConfigManager` | `MistHelper.py:16926` | `src/site/site_config_manager.py:54` | `_configure_module()` + 4 delegation methods; canonical class exports all 5 with matching signatures. |
| 4 | `DeviceUtilityCommands` | `MistHelper.py:13527` | `src/device/utility_commands.py:82` | Facade orchestrator with 35 op-subclasses (Command pattern fan-out); canonical class holds all 35 op-classes as nested types or same-module peers. Method-parity audit is the largest of the four (see Decision 12). |

The remaining 43 candidates (rows 5-47 in the Dispatch Queue) are Cat B: no same-name class definition exists under `src/`, so each is a fresh extraction to its pinned landing package.

**Landing conventions retained from prior initiatives**:

- Cat A: no new file is created. The facade deletion is the only edit to `MistHelper.py`; the existing canonical file is untouched (import-only rewrite of callsites).
- Cat B: one class → one file. Landing is a domain-fitting existing package per the spec's pinned landing-target column. Concrete groupings from the spec:
  - `src/site/` — `SiteConfigExporter`, `SiteClientExporter`, `SiteDeviceExporter`, `SiteAnomalyExporter`, `SitesByAPModelExporter`.
  - `src/export/` — `OrgAlarmEventExporter`, `OrgAdminExporter`, `OrgTemplateExporter`, `OrgConfigExporter`, `OrgClientSecurityExporter`, `OrgDeviceStatsExporter`, `OrgTicketManager`, `OrgExportUtils`, `SelfExportUtils`, `LicenseExportUtils`.
  - `src/gateway/` — `GatewayHaExporter`, `GatewayTestExporter`.
  - `src/refactors/` — receives **zero** Cat B candidates. Every Cat B row is pinned per-row to a semantic package in the spec's Dispatch Queue.

**Rationale**: Discovering facade collisions pre-dispatch is materially cheaper than discovering them mid-PR. The 2026-07-07 audit closes a class of surprise ("this class already exists in src/!") that otherwise blocks a PR mid-implementation. Fixing the action-type at dispatch time also gates the correct FR (FR-025 method-parity for Cat A; FR-006 in-flight decomposition for Cat B) so the reviewer knows which rubric applies before opening the diff.

**Alternatives considered**:

- *Treat all 47 as Cat B and discover collisions during PR execution*. Rejected — creates unpredictable PR abandonment when a collision surfaces at implementation time; wastes reviewer bandwidth on aborted PRs.
- *Merge Cat A into Cat B by renaming facade-collision candidates to `<Name>Legacy` and landing them as fresh extractions*. Rejected — creates duplicate implementations in the codebase (canonical + legacy) with no functional distinction, deferring the eventual facade removal to a follow-up initiative rather than closing it out here.
- *Fold Cat A candidates into the same PR as their canonical body's owner PR retroactively*. Rejected — canonical bodies were established under closed initiatives (1010/1011); a 1013 PR that reopens a closed 1010 PR's file violates initiative scoping.

---

## Decision 2 — Tiny classes (LOC < 25) still get their own module by default

**Decision**: Every Cat B extraction candidate — including tiny ones like `EndpointConfig` (10 LOC) — lands in its own module under the pinned landing package. Small size alone does not trigger folding into an existing file within the landing package. If the landing package holds a natural host class and folding preserves A+/100, folding is permitted only when at least two of the following are true: (1) the candidate's name suggests it as a peer/helper of the host class; (2) the candidate's public API is invoked alongside the host class's methods in `MistHelper.py`; (3) folding does not push the destination file below A+/100 (FR-022 hard gate).

**Rationale**: Uniform one-class-per-module output makes the post-initiative directory grep-friendly (`grep -l "^class EndpointConfig" src/refactors/`) and matches the pattern established by 1010/1011 which landed 30+ single-class modules. Consolidating tiny classes into a shared "small_helpers.py" grab-bag would produce exactly the kind of monolith this initiative is dismantling. The compliance-analyzer overhead per tiny file is negligible (each still scores A+/100 with the mandatory module docstring, class docstring, and comment cadence).

**Alternatives considered**:

- *Bundle tiny classes into a shared module*. Rejected — recreates the anti-pattern (many-classes-per-file) at a smaller scale and forces future readers to search for the file that hosts a given name.
- *Inline tiny classes into their sole caller's module*. Rejected — Hot-bucket definition requires 4+ callers, so no candidate has a single caller to inline into.

---

## Decision 3 — `FirmwareManager` resolution superseded by Cat A categorization

**Decision**: The Phase 0 `FirmwareManager` uncertainty (originally recorded as a dispatch-time diff decision) is **resolved by the 2026-07-07 collision audit**: `FirmwareManager` is confirmed **Cat A**. Its `MistHelper.py:17376` body is a factory facade over `src/firmware/firmware_manager.py:134`. The row-2 PR performs the Cat A workflow (facade delete, callsite rewrite, method-parity audit per FR-025) — no `firmware_manager_v2.py`, no `FirmwareManagerLegacy` rename, no `src/refactors/` landing.

The three outcomes previously enumerated (identical / distinct / ambiguous) collapse to outcome (1) — identical or trivially divergent body — confirmed by the pre-dispatch audit. Outcomes (2) and (3) would have been Cat C candidates, and no Cat C candidates surfaced in the 2026-07-07 audit.

**Rationale**: Formalizing the collision audit at Phase 0 (Decision 1) removed the last remaining "resolve at dispatch time" ambiguity that this decision previously covered. The row-2 PR now dispatches with the same clarity as row-1, row-3, and row-4 (all Cat A).

**Alternatives considered**:

- *Retain the dispatch-time diff as a belt-and-braces check*. Rejected — the audit result is deterministic; re-running the same check at dispatch time adds overhead without new information.
- *Rename the canonical class under `src/firmware/` to disambiguate from the facade*. Rejected — the canonical class name is stable (established by 1011); renaming it would churn every existing callsite that already imports from `src/firmware/firmware_manager.py`.

---

## Decision 4 — Decompose-during-move rules per `guideline_flag` category (Cat B only)

**Decision**: Every `guideline_flag` surfaced by the analyzer on a **Cat B** extraction candidate is resolved in the same PR (FR-006). Cat A PRs do not perform in-flight decomposition — the canonical body under `src/` is untouched and its analyzer scores are assumed compliant (pre-verified by the closing initiative that established it).

Cat B per-flag playbook:

| Flag | Remediation in the extraction PR |
|------|----------------------------------|
| `oversize_25_lines` | Split each offending method into helpers, each <= 25 lines. New helpers get private (`_leading_underscore`) names, class-body docstrings, and their own `logging.debug` breadcrumbs. Public method contracts preserved (same signature, same return type, same exceptions). |
| `missing_inline_comments` | Every executable line gets an inline comment describing its intent (Constitution VI cadence: comment every 5-10 lines minimum). Blank lines and pure-syntax lines (closing brackets, `else:`) do not need comments. |
| `missing_action_logging` | Every public method opens with `logging.info("[EXECUTE] <ClassName>.<method>: %s", <context>)`, closes with `logging.info("[SUCCESS] <ClassName>.<method>: %s", <result_summary>)`, and wraps any error path with `logging.error("[FAILURE] <ClassName>.<method>: %s", <exc>)`. Constitution VII prefix set enforced verbatim. `%s` formatting required (no f-strings in log calls). |
| `non_ascii_logs` | Every log literal is transliterated to ASCII. Curly quotes -> straight quotes, en-dash -> hyphen-minus, ellipsis -> three dots. `logging.info("...")` bodies must survive `str.encode('ascii')` without loss. |
| `hardcoded_separator` | Replace `os.path.join`, `os.sep`, and string-concatenated paths with `pathlib.Path`. All path construction goes through `Path(...)` and `Path.__truediv__`. |
| `raw_input_call` | Replace every `input(...)` with `InputUtils.safe_input(...)`. Import from wherever `InputUtils` currently lives (surfaced by grep at dispatch). |

Any additional flag surfaced by an analyzer update is handled with the same "resolve in-flight, never defer" rule. If a flag is genuinely unfixable in the extraction PR (extremely rare), the PR is deferred to the deferred pool with rationale.

**Rationale**: FR-006 mandates zero forward-carried guideline violations on Cat B extractions. A per-flag playbook removes contributor guesswork and lets reviewers audit remediation quality against a fixed rubric. Cat A PRs skip this rubric because the canonical body already passed it under the closing initiative; requiring re-verification would blur the initiative boundary. The `%s` formatting rule is Constitution V's action-log contract; f-strings in log calls are the most common lint failure and worth pre-empting explicitly.

**Alternatives considered**:

- *Apply the same rubric to Cat A canonical bodies as a "cleanup pass"*. Rejected — Cat A PRs are engineered to have zero footprint in `src/`; touching canonical bodies expands PR scope and violates the "facade removal only" contract.
- *Defer complex remediations (e.g. `oversize_25_lines` on 500+ LoC classes)*. Rejected — E-10 explicitly says large candidates land in one PR each; SC-011 requires zero forward-carried flags.
- *Allow f-strings in log calls if the message is static*. Rejected — Constitution V's `%s` rule exists to preserve structured-log-parseability across the codebase; the "static message" carve-out invites drift.

---

## Decision 5 — Pinned NOTE breadcrumb template (per-Cat variation)

**Decision**: Every extraction PR leaves exactly one NOTE breadcrumb at the deletion site in `MistHelper.py`, matching the FR-007 template with per-Cat variation:

**Cat A** (facade removal — points at existing canonical body):
```python
# NOTE: <ClassName> facade removed; canonical body at <src-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.
```

**Cat B** (fresh extraction — points at newly-created module):
```python
# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.
```

Placeholders:

- `<ClassName>` — the exact class name as it appeared in `MistHelper.py` before deletion (case-sensitive).
- `<src-path>` (Cat A) — the path to the existing canonical file (e.g. `src/firmware/firmware_manager.py`, `src/device/utility_commands.py`).
- `<new-module-path>` (Cat B) — the newly-created module path per the Dispatch Queue's Landing target column.

Position: the NOTE replaces the deleted `class <Name>:` line, appearing as the single-line successor at the same source position. No adjacent blank lines are added or removed.

**Rationale**: Breadcrumb uniformity is enforced by grep at review time (SC-012). Two pinned template shapes (one per Cat) let the reviewer's `grep -c "# NOTE: <ClassName>"` return exactly 1 while making the action-type visible at a glance from `MistHelper.py` alone. A future refactor sweep can distinguish facade-removals from fresh-extractions by grep pattern without opening the spec.

**Alternatives considered**:

- *Single unified template for both Cats*. Rejected — Cat A and Cat B are semantically different operations; a unified template would either omit the "facade removed" signal (obscuring history) or omit the "extracted to" signal (obscuring Cat B destinations).
- *Optional breadcrumbs at contributor discretion*. Rejected — quality drift; SC-012 becomes unverifiable.
- *Multi-line breadcrumb with structured YAML frontmatter*. Rejected — a single-line comment fits the existing `MistHelper.py` comment style and survives `black` re-flow without adjustment.

---

## Decision 6 — CI-time verification of "no wrapper shim" (SC-007) uses a fixed grep pattern

**Decision**: SC-007 (zero wrapper shims survive) is verified during PR review with the following grep pattern, invoked against the merged `MistHelper.py`. The pattern is identical for Cat A and Cat B — in both cases the class name should not appear as a definition, function shim, or alias in `MistHelper.py`:

```bash
# After each extraction, no residual class definition remains:
grep -n "^class <ClassName>[ (:]" MistHelper.py       # Expect: 0 hits
grep -n "^def <ClassName>" MistHelper.py              # Expect: 0 hits (guard against fn shim)
grep -n "<ClassName> = " MistHelper.py                # Expect: 0 hits (guard against alias)
grep -n "^from .* import <ClassName>$" MistHelper.py  # Expect: 1 hit (the new import line)
```

The last grep confirms the import replaces the definition. Any extra hits (e.g. a `<ClassName> = _real_<ClassName>` alias line, or a forwarding `def <ClassName>(...)` factory) fail SC-007 and block merge until removed.

For Cat A, the import target is the existing canonical module (`src/firmware/firmware_manager`, `src/device/utility_commands`, etc.). For Cat B, the import target is the newly-created module under the pinned landing package.

The pattern is documented in `quickstart.md` step "Verification greps" so contributors invoke it locally before opening the PR.

**Rationale**: Wrapper shims are the failure mode this initiative is engineered against. Codifying the exact grep pattern (not "look around and eyeball it") makes the review contract deterministic. All four sub-patterns are needed because different shim styles evade different single greps. The Cat A vs Cat B distinction affects the *destination* of the import line but not the *shape* of the shim check itself.

**Alternatives considered**:

- *AST-based verification via a custom tool*. Rejected — the grep pattern is trivial to run and understand; adding tooling introduces maintenance overhead for a check that runs once per PR.
- *Rely on the compliance-analyzer alone*. Rejected — the analyzer verifies compliance grade, not shim absence; the two checks are complementary.

---

## Decision 7 — Analyzer regression guardrail: baseline captured on the first branch commit, aggregate >= 99.6/A+ per PR

**Decision**: The `MistHelper.py` pylint baseline and repo-wide aggregate compliance snapshot are captured on the first commit of branch `1013-misthelper-refactor-hot-classes` (before any extraction lands). Concretely:

```bash
git checkout -b 1013-misthelper-refactor-hot-classes origin/main
python -m tools.compliance_analyzer --repo-wide > data/full_repo_compliance_1013_baseline.md
pylint MistHelper.py > data/pylint_MistHelper_1013_baseline.txt
git add data/full_repo_compliance_1013_baseline.md data/pylint_MistHelper_1013_baseline.txt
git commit -m "chore(1013): capture pre-initiative compliance and pylint baselines"
```

Per-PR gates (identical for Cat A and Cat B):

- `python -m tools.compliance_analyzer --repo-wide` reports aggregate >= 99.6/A+ (SC-003).
- Every file the PR touches (created or edited) scores A+/100 (SC-006). For Cat A, this reduces to `MistHelper.py` only (no new file created, canonical body untouched).
- `pylint MistHelper.py` reports a score >= the value captured in `data/pylint_MistHelper_1013_baseline.txt` (SC-015). Regression by any amount blocks merge for that PR.

The baseline captures are consumed as inputs to the merge gate, not modified by extraction PRs. If a legitimate baseline shift is needed (e.g. an unrelated `main` PR raises the pylint floor), a separate chore commit updates the baseline and the rationale is recorded in that commit's message.

**Rationale**: A moving baseline defeats the guardrail; a fixed baseline captured at branch time gives every PR a single number to beat. The three-level gate (aggregate score, per-file score, MistHelper.py pylint) covers the three regression paths: a new file that isn't A+ (Cat B only), an edit that drops an old A+ file, and MistHelper.py-only pylint drift from the deletion churn (both Cats).

**Alternatives considered**:

- *Recompute baseline on every merge*. Rejected — creates a drift window where a small regression per PR compounds into a large aggregate regression over 47 PRs.
- *Ignore MistHelper.py pylint entirely because the file is being shrunk anyway*. Rejected — pylint scoring is size-normalized; deleting code without keeping the remaining lines clean still shows up as regression.

---

## Decision 8 — Dispatch queue mutation policy: E-1 through E-10 conditions trigger deferral, never silent skip

**Decision**: The 47-row Dispatch Queue is mutated (candidates deferred, or in the rare case of E-6 reclassifying an external-caller candidate back to MistHelper-only, added) only via explicit spec revisions. The triggers apply uniformly to Cat A and Cat B PRs:

| Edge Case | Trigger | Response |
|-----------|---------|----------|
| E-1 | Destination package selection ambiguity | Cat B only — resolve in PR body; no queue change. (Cat A destinations are fixed by the canonical body.) |
| E-2 | Guideline-flag decomposition scope | Cat B only — resolve in-flight in the PR; no queue change. (Cat A does not perform decomposition.) |
| E-3 | Line-number drift only (no ref-count / classification change) | Proceed with fresh grep; no queue change. |
| E-4 | Missing NOTE breadcrumb at review | Reviewer requests change; PR revised; no queue change. |
| E-5 | Name collision at destination | Cat B only — rename or redirect in PR body; no queue change. (Cat A collisions are the audit's finding.) |
| E-6 | Ref-count shift discovered at fresh catalog regeneration | If drops below Hot band (< 4 refs), defer per FR-020 and record in Deferred Candidates. If rises above the queue's ceiling, no queue change (still Hot). If an excluded external-caller candidate becomes MistHelper-only, spec revision required to add it. |
| E-7 | `python MistHelper.py --test` failure from unrelated commit | Pause the initiative until the underlying regression is fixed; no queue change. |
| E-8 | Aggregate score drop below 99.6/A+ | Revise the PR (resolve more flags); no queue change unless deferred outright. |
| E-9 | SKIPPED conditionals | Non-blocking per policy; no queue change. |
| E-10 | Very large candidate needing decomposition | Cat B only — land as one PR with substantial internal decomposition; no queue change. |

Deferral procedure:

1. The dispatcher runs the pre-dispatch grep audit (`grep -rn "<ClassName>" src/ tests/`) and detects an external caller (FR-013) OR the fresh catalog shows a Hot -> Low-Use reclassification (FR-020).
2. The dispatcher opens a small docs-only commit that adds a row to the Deferred Candidates table in `spec.md`, populating (Class, Reason, Recording PR / Commit).
3. The dispatcher advances to the next queue head.
4. The docs-only commit is recorded in the next dispatched PR's body as prior context.

**Rationale**: A "silent skip" (advance past a candidate without recording why) breaks SC-014 (auditable Refs-ASC / LOC-DESC walk within each Cat block). A docs commit that predates the next PR keeps the sequence walkable and the Deferred Candidates table honest. Cat A candidates are unlikely to trigger deferral (audit already confirmed their canonical bodies exist), but the policy applies uniformly for consistency.

**Alternatives considered**:

- *Batch deferrals into a monthly docs commit*. Rejected — a deferral must be visible before the next PR opens so reviewers know why the queue jumped.
- *Delete deferred candidates from the queue entirely*. Rejected — the queue is spec history; deferrals live alongside the original 47 rows.

---

## Decision 9 — Interaction with in-flight residuals (1 Single-Use, 2 Low-Use) tracked separately

**Decision**: The post-1012 catalog shows 1 Unused (already 0), 1 Single-Use, and 2 Low-Use residuals in addition to the 47 Hot classes. Those 3 residuals are **out of scope for this initiative**; they are tracked by a separate future initiative (`1014-*` or similar). If a residual is coincidentally on the same call chain as a 1013 extraction and the extraction reduces its ref count further, the residual's classification may shift silently in `refactor_candidates.md` — that shift is recorded but not acted upon by 1013.

Ordering: 1013 PRs proceed sequentially through Cat A first (positions 1-4) then Cat B (positions 5-47); residuals are ignored throughout. No 1013 PR touches a residual class body. No 1013 PR's callsite rewrite depends on a residual class being already extracted.

If a merge conflict arises because a hypothetical future `1014-*` PR touches `MistHelper.py` concurrently with a 1013 PR, the 1013 PR resolves the conflict by rebasing onto the 1014 landing (serial workflow — one PR open at a time, FR-023) rather than by expanding scope.

**Rationale**: Cross-initiative scope creep is the fastest way to blow the "one class per PR" discipline. Treating residuals as an orthogonal concern keeps 1013's success criteria tractable. The 3 residuals are small enough (Single-Use + 2 Low-Use = at most 3 more PRs) that a follow-up initiative is trivially cheap.

**Alternatives considered**:

- *Absorb the 3 residuals into 1013's scope*. Rejected — a Hot-classes initiative that also processes Single-Use and Low-Use is a "everything left" initiative and loses the scoping discipline that makes it reviewable.
- *Wait for residuals to be cleared before starting 1013*. Rejected — nothing about the residuals blocks Hot-class extraction; parallel initiative kickoff is safe under the "one PR open at a time" rule.

---

## Decision 10 — Analyzer catalog regeneration cadence: per-PR after every merge

**Decision**: `refactor_candidates.md` is regenerated after every merged extraction PR, before the next PR is dispatched. Concretely:

```bash
git checkout main
git pull                                                # after PR merges
python -m tools.refactor_analyzer > refactor_candidates.md
git add refactor_candidates.md
git commit -m "chore(1013): regenerate refactor_candidates.md post-PR-<N>"
git push
```

The freshest `refactor_candidates.md` on `main` is the authoritative dispatch source for the next PR (FR-014, SC-010, SC-014).

Batching regenerations (e.g. "regenerate every 5 merges") is prohibited — a stale catalog is exactly how a candidate slips past the Refs-ASC / LOC-DESC ordering within each Cat block.

**Rationale**: Regeneration cost is bounded (a few seconds); a stale catalog cost is unbounded (misdispatch, wasted PRs). Per-PR regeneration also lets each PR body cite the specific catalog snapshot it was dispatched from, giving SC-014 an auditable trail.

**Alternatives considered**:

- *Regenerate only at end-of-initiative*. Rejected — every subsequent dispatch would be against a snapshot that may not reflect the merged state.
- *Regenerate every 5 merges (batched)*. Rejected — same problem, smaller drift window; the audit trail becomes non-linear.
- *Skip regeneration if the merged PR's callsite rewrites don't touch any other candidate*. Rejected — the dispatcher would have to predict downstream ref-count effects; the analyzer is the canonical answer, run it.

---

## Decision 11 — Cat A-first dispatch ordering (FR-026)

**Decision**: The Dispatch Queue processes all 4 Cat A candidates (positions 1-4) before any Cat B candidate (positions 5-47). Within each Cat block, ordering is Refs-ASC / LOC-DESC per FR-005. The four Cat A positions specifically:

1. `GatewayTemplateConfigManager` (`MistHelper.py:15596` -> `src/gateway/template_config.py`).
2. `FirmwareManager` (`MistHelper.py:17376` -> `src/firmware/firmware_manager.py`).
3. `SiteConfigManager` (`MistHelper.py:16926` -> `src/site/site_config_manager.py`).
4. `DeviceUtilityCommands` (`MistHelper.py:13527` -> `src/device/utility_commands.py`).

**Rationale**: Cat A-first is a deliberate risk-front-load warmup. Each Cat A PR:

- **Creates no new file** — reviewer surface reduces to `MistHelper.py` deletions + callsite import rewrites + method-parity audit table.
- **Is bounded in scope** — the canonical body under `src/` is out of scope; the reviewer's mental model is "does this facade delete break anything?" rather than "is this new class well-designed?".
- **Exercises the initiative's tooling once per PR** — baseline greps, method-parity gate (FR-025), NOTE breadcrumb template, per-file A+ verification — before the higher-friction Cat B work begins.

Placing the 4 Cat A PRs at the front of the queue lets the initiative validate its guardrails against the lower-risk action-type before committing to 43 fresh-extraction PRs. If the Cat A workflow surfaces an unforeseen gap (missing playbook entry, breadcrumb-template ambiguity, method-parity edge case), the fix lands in the spec/plan before Cat B PRs open — cheaper than discovering the gap on PR 27 of Cat B.

The Refs-ASC ordering within the Cat A block puts the least-referenced facades first, further reducing blast radius on the first PR.

**Alternatives considered**:

- *Pure Refs-ASC / LOC-DESC across all 47 without Cat separation*. Rejected — a Cat A candidate at position 12 would surface unexpectedly during a run of Cat B extractions, forcing the reviewer to context-switch between two mental models mid-initiative.
- *Cat B first, Cat A last as "cleanup"*. Rejected — placing facade removals after 43 fresh extractions creates reviewer fatigue exactly when the method-parity audit needs the most careful review. Reviewers are freshest on PR 1-4.
- *Interleave Cat A and Cat B based on ref-count*. Rejected — same context-switching cost as pure Refs-ASC, without the "warmup" benefit that Cat A-first provides.

---

## Decision 12 — Method-parity gate (FR-025) audit shape

**Decision**: Every Cat A PR includes a method-parity audit in the PR description under a **Method-Parity Audit** heading. The audit shape is fixed:

```bash
# 1. Enumerate methods on the src/ canonical body:
grep -n "^\s*def " <src-path>

# 2. Enumerate methods on the MistHelper.py facade (before deletion):
grep -n "^\s*def " MistHelper.py | sed -n '<facade-start>,<facade-end>p'

# 3. Compare the two sets: every method on the facade must correspond 1:1 to a
#    method on the canonical body with matching signature.
```

The audit output is pasted verbatim into the PR description as two side-by-side lists (facade methods | canonical methods), one row per method, with a check column marking each 1:1 correspondence. Any facade method absent from the canonical body is a Cat C signal — the PR is closed without merge and the row is deferred to a discovery commit per Decision 1.

Signature parity includes: parameter names, parameter defaults, `*args`/`**kwargs` presence, return type annotations (if any), decorators (`@staticmethod`, `@classmethod`, `@property`). A signature drift on any facade method is treated the same as a missing method — PR closed, row deferred.

**Special call-out for `DeviceUtilityCommands` (Cat A row 4)**: the facade orchestrates 35 op-subclasses (Command pattern fan-out). The method-parity audit for this row enumerates not only the 3-5 top-level facade methods but also the 35 op-subclass entry points reachable through the facade. Reviewer expectation: the audit table is long (~40 rows), and the audit-generation script may need to enumerate nested class methods:

```bash
grep -n "^\s*\(class\|def\) " <src-path>   # capture both class and method boundaries
```

The other three Cat A candidates have compact audits (3-5 rows for `GatewayTemplateConfigManager`, ~5 rows for `SiteConfigManager`; `FirmwareManager` audit is bounded by its factory-facade delegation list — the reviewer verifies each delegated method resolves to a canonical implementation).

**Rationale**: FR-025 gates Cat A on visible, reviewable evidence that no method was lost in the facade deletion. Grep-based enumeration keeps the audit deterministic (same command yields same table every time) and cheap (no custom tooling). Pasting the audit into the PR description makes the review artifact permanent — future readers can verify the parity claim without re-running the audit. The `DeviceUtilityCommands` call-out exists because a 35-subclass Command pattern is genuinely different in scale from a 3-method delegation shim; papering over that with a "one size fits all" audit template would encourage skimming past the highest-risk PR of the initiative.

**Alternatives considered**:

- *AST-based method-parity checker as a CI job*. Rejected — the four Cat A PRs are a one-shot audit surface; investing in tooling that runs four times is not economical. Grep + PR description review is sufficient.
- *Skip the audit for the three "small" Cat A candidates and only audit `DeviceUtilityCommands`*. Rejected — the audit's value is in the uniform reviewer contract ("every Cat A PR includes a parity table"); a per-row carve-out invites contributor confusion about when the audit applies.
- *Verify parity by running the test suite alone*. Rejected — the test suite (`python MistHelper.py --test`) exercises reachable code paths but does not enumerate the facade's public API surface. A method deleted by mistake but unreached by tests would slip through.

---

## Open Questions

None. All NEEDS CLARIFICATION items from Technical Context are resolved. The twelve decisions above cover the entire implementation surface for the serial 47-PR workflow (4 Cat A + 43 Cat B).
