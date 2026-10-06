# Implementation Plan: Juniper Docs Classification Reprocessing Package

**Branch**: `3991-juniper-docs-classify-reprocessing` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification from `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/spec.md`

## Summary

Move `manual_sorter.py` and `reclassifier.py` into
`src/mist/intelligence/juniper_docs/classify/reprocessing/`. Update all imports and
focused tests to use the canonical paths. Add a focused structure guard that proves
the classification package has no more than five direct structural children and that
the two reprocessing modules exist. Preserve module-level symbols and behavior
without wrappers, aliases, or fallback imports. Add one issue-specific release-note
fragment during implementation.

The implementation uses only the authorized source moves, import updates, tests,
guards, release-note fragment, and three routed specification files.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python standard library, existing Juniper Docs
classification modules, `pytest`, and repository guardrail helpers

**Storage**: SQLite state database and local PDF corpus remain unchanged

**Testing**: Focused and full `pytest` checks, coverage, structure and symbol
guards, Python compilation, Ruff, Black, Mypy, Pylint, Radon, Vulture,
pydocstyle, Interrogate, Bandit, pip-audit, test-quality analysis, citation and
diagram checks, changelog validation, and generated-reference drift checks

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python library and command-line operational tooling

**Performance Goals**: Preserve current classification and reprocessing behavior
without adding a runtime path or duplicate processing

**Constraints**: Keep the classification package within five direct structural
children. Remove both old module paths. Do not add wrappers, aliases, fallback
imports, shared registry changes, generated reference changes, historical spec
changes, `AGENTS.md` changes, or `CLAUDE.md` changes.

**Scale/Scope**: Two moved modules, affected imports and tests, one focused
structure guard, one release-note fragment, and no Mist Cloud transport change

## Constitution Check

*GATE: Pass before research and after design.*

- **Five-Item Rule**: PASS. The current `classify` package has six direct module
  files. Moving two modules under `reprocessing` produces five direct structural
  children: `asset_classifier.py`, `content_sampler.py`, `reprocessing/`,
  `signal_scorer.py`, and `slug_classifier.py`. The new package has two module
  children.
- **Class-Based Architecture**: PASS. The move preserves `ManualDocumentSorter`
  and `CorpusReclassifier`. The plan prohibits wrapper modules and aliases.
- **Safety-First**: PASS. The move does not add input handling or destructive
  behavior. Existing dry-run and typed operational controls remain unchanged.
- **Full Deployment Pipeline**: REQUIRED. Run each applicable local gate, commit
  the bounded change, and run the post-commit test-quality checks.
- **Observability and Logging**: PASS. The moved modules retain their existing
  logging. The implementation must not alter log content or add secret output.
- **Inline Comments**: PASS FOR PLANNING. The implementation must preserve the
  repository comment standard on changed executable lines.
- **Process-folder intake**: PASS. The requested plan is under the managed
  `specs/numbered/` root and the fixed eight-level route. No direct `specs/`
  child is added.
- **Existing debt**: The repository contains existing hierarchy and process-folder
  debt recorded by the current guard baselines. This feature does not increase
  unrelated debt. A separate remediation action is deferred to the existing
  structure and process-folder maintenance work.
- **Mist Cloud transport**: NOT APPLICABLE. This feature changes local package
  structure only and does not add or change a Mist Cloud request.

## Research and Design Decisions

### Decision: Use a nested `reprocessing` package

**Rationale**: The current classification package contains six direct module
  files. A package containing the two reprocessing modules reduces the parent
  to five direct structural children and gives related behavior one owner.

**Alternatives considered**:

- Merge the two modules into one existing classifier module. Rejected because it
  would mix manual sorting and corpus reclassification responsibilities.
- Add a compatibility wrapper at each old path. Rejected because the
  specification requires one canonical path and no wrappers or aliases.
- Change the shared source structure guard only. Rejected because the feature
  requires a focused guard with direct invalid-layout tests.

### Decision: Preserve source text and symbols while moving files

**Rationale**: A filesystem move with import-path updates preserves behavior and
  avoids a second implementation. The existing `CorpusReclassifier` tests cover
  reclassification behavior. The implementation must retain all module-level
  symbols at the new paths.

**Alternatives considered**:

- Reimplement the classes in new files. Rejected because it increases behavior
  drift and duplicates the tested implementation.
- Export old names from `classify/__init__.py`. Rejected because it creates an
  alias path instead of one canonical module path.

### Decision: Add a focused guard with valid and invalid fixtures

**Rationale**: Existing broad structure guards do not prove the exact Juniper Docs
  classification contract. A focused guard can report examined children and fail
  directly for an over-limit parent and missing or misplaced moved modules.

**Alternatives considered**:

- Depend only on `test_src_domain_structure.py`. Rejected because it checks broad
  domain levels and does not express the feature-specific module layout.
- Depend only on import tests. Rejected because imports do not prove child counts
  or the absence of duplicate old module locations.

### Decision: Keep the implementation boundary explicit

**Rationale**: The feature specification excludes shared registries, generated
  references, historical specifications, `AGENTS.md`, and `CLAUDE.md`. The plan
  names only source, affected tests, focused guards, the release note, and the
  authorized routed specification records.

**Alternatives considered**:

- Update generated references during implementation. Rejected because the
  specification explicitly excludes generated references.
- Create `research.md`, `data-model.md`, `quickstart.md`, or contracts. Rejected
  for this request because the user authorized only `plan.md` in the routed
  directory.

## Implementation Plan

### Phase 1: Move the reprocessing modules

1. Create `src/mist/intelligence/juniper_docs/classify/reprocessing/` with package
   metadata required by the project.
2. Move `classify/manual_sorter.py` to
   `classify/reprocessing/manual_sorter.py`.
3. Move `classify/reclassifier.py` to
   `classify/reprocessing/reclassifier.py`.
4. Remove the old paths as part of the move. Do not leave forwarding modules,
   aliases, or fallback imports.
5. Preserve module-level symbols, class behavior, logging, command-line parsing,
   dry-run defaults, and local path handling.

### Phase 2: Update canonical imports and tests

1. Search tracked text files for both old module paths and update each affected
   runtime or test import to `classify.reprocessing`.
2. Update `tests/unit/juniper_docs/test_reclassifier.py` to import
   `CorpusReclassifier` from the canonical reprocessing path.
3. Use the reclassifier unit test and shared symbol guard to prove canonical paths.
4. Confirm no tracked text file retains an old import or old module location,
   except an explicitly required historical record that is outside this feature.

### Phase 3: Add the focused structure guard

1. Add a guard under `tests/guardrails/` that measures direct structural children
   below `src/mist/intelligence/juniper_docs/classify`.
2. Require exactly the five expected structural children and require
   `reprocessing/manual_sorter.py` and `reprocessing/reclassifier.py`.
3. Require both old module paths to be absent.
4. Add a direct failure test for a sixth direct structural child.
5. Add a direct failure test for a missing or misplaced reprocessing module.
6. Report the examined child count and the failing paths in each assertion.
7. Run the existing source structure and symbol preservation guards with the new
   focused guard.

### Phase 4: Record the bounded change

1. Add one release-note fragment named
   `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md`.
2. Use one `###` heading and one `Changed` bullet that names issue #3991.
3. Do not edit the shared `CHANGELOG.md`, generated references, shared registries,
   historical specs, `AGENTS.md`, or `CLAUDE.md`.

### Phase 5: Validate the implementation

Run the focused behavior and structure checks first:

```text
python -m pytest tests/unit/juniper_docs/test_reclassifier.py
python -m pytest tests/guardrails/test_juniper_docs_classify_structure.py
python -m pytest tests/guardrails/test_src_domain_structure.py tests/guardrails/test_src_public_symbol_preservation.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m py_compile src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py
git diff --check
```

Run the applicable repository quality gates. These path values are copied
exactly from `.github/workflows/ci.yml`:

```text
python -m ruff check .
python -m black --check --diff .

MYPY_PATHS='src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py'
python -m mypy $MYPY_PATHS --config-file pyproject.toml

bandit -c pyproject.toml -r src/mist/intelligence/juniper_docs/classify tests/guardrails/test_juniper_docs_classify_structure.py -q
pylint src/ --fail-under=9.5

RADON_PATHS='src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py'
radon cc $RADON_PATHS -j | complexity-gate --max 10

VULTURE_PATHS='src/ MistHelper.py wsgi.py web_portal'
vulture $VULTURE_PATHS --min-confidence 70

PYDOCSTYLE_PATHS='src/ wsgi.py web_portal'
pydocstyle $PYDOCSTYLE_PATHS

INTERROGATE_PATHS='src/ MistHelper.py wsgi.py wsgi_capture.py web_portal'
interrogate $INTERROGATE_PATHS --fail-under 90 -v
```

Run the required test-quality preflight and changed-test gate after the
implementation commit:

```text
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
git rev-parse --verify "origin/main^{commit}"
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

The dependency, container, menu-reference, portal, safe-sweep, and full
integration gates do not read this bounded package move.

Verify the authorized file boundary after each generator and gate:

```text
git status --short --untracked-files=all
git diff --name-only origin/main...HEAD
```

The final implementation diff must contain only the two moved modules, the new
package metadata, affected canonical imports and focused tests, structure and
symbol guards, the issue-specific release-note fragment, and the three
authorized routed specification files. No gate can authorize an excluded file.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/
├── plan.md
├── spec.md
└── tasks.md
```

No `research.md`, `data-model.md`, `quickstart.md`, or `contracts/` record is
created by this feature.

### Source Code

```text
src/mist/intelligence/juniper_docs/
├── acquire/
├── classify/
│   ├── __init__.py
│   ├── asset_classifier.py
│   ├── content_sampler.py
│   ├── reprocessing/
│   │   ├── __init__.py
│   │   ├── manual_sorter.py
│   │   └── reclassifier.py
│   ├── signal_scorer.py
│   └── slug_classifier.py
├── discovery/
├── harvest/
└── models.py
```

**Structure Decision**: Keep the existing Juniper Docs package and add one nested
`classify/reprocessing` package. This gives the classification parent five direct
structural children and gives reprocessing one clear owner.

## Complexity Tracking

No constitution violation requires an exception. The plan records the existing
classification-package child-count violation and resolves it through the nested
package move. The existing repository-wide structural and process-folder debt
remains covered by its current baselines and requires a separate remediation action.
