# Implementation Plan: Site Analytics Package

**Branch**: `jmorrison-juniper-refactor-group-site-analytics-modules` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification for issue #3992.

**Authority**: GitHub `main` at `0b04cda81c8ef75096f3bedae0885038c775d665`.

## Summary

Move three site analytics modules into one bounded `site` package. Update every active path to use
the new canonical package.

Preserve all behavior, all module-level symbols, and the four analytics root exports. Delete the
old modules with no wrappers.

Add one scoped guard for the analytics hierarchy and active old paths. Leave historical
specifications and the released `CHANGELOG.md` unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Python standard library, `mistapi>=0.64.0,<0.65`, and existing MistHelper
helpers.

**Storage**: No storage change.

**Testing**: Pytest, Ruff, Black, mypy, Radon, Bandit, Pylint, Vulture, pydocstyle, Interrogate,
test-quality-analyzer, and repository generators.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman image.

**Project Type**: Python command-line application with generated Markdown documentation.

**Performance Goals**: Keep existing analytics runtime and API request behavior unchanged.

**Constraints**: Make a path-only refactor. Add no compatibility path, wrapper, alias, fallback,
new API call, or output change.

**Scale/Scope**: Move three modules. Update eight active Python path surfaces, six documentation
files, three guards, and one changelog fragment.

## Constitution Check

*GATE: The design passes before implementation and must pass after implementation.*

- **Five-item rule**: The analytics root changes from six direct modules to four structural
  children.
- **Nested-package ratchet**: Remove only the resolved analytics entry from
  `tests/guardrails/nested_package_baseline.json` and update its measured count from 36/243 to
  35/242. Preserve every unrelated baseline entry.
- **New package rule**: The `site` package has three structural children. Its `__init__.py` is
  metadata and contains only a package docstring.
- **No-wrapper rule**: Delete each old module after its move. Add no forwarding module,
  compatibility import, alias module, or fallback.
- **Preservation rule**: Keep all 122 authority symbols and all existing behavior.
- **Safety rule**: Keep prompts, confirmation words, cancellation behavior, and Mist calls
  unchanged.
- **Documentation rule**: Update maintained source links. Leave historical specifications and
  released changelog text unchanged.
- **Release-note rule**: Add only `changelog.d/issue-3992-site-analytics-package.md`.
- **Process-folder debt**: `specs/` and `changelog.d/` contain grandfathered children. This change
  adds only its unique required records.
- **Incremental remediation**: The existing process-folder migration remains separate from issue
  #3992.
- **Quality rule**: Run every applicable gate in the Validation Plan.
- **Git rule**: Use a Conventional Commit subject and pull request title.

No constitution exception is required.

## Project Structure

### Feature Documentation

```text
specs/numbered/0/0/1/1/1/4/3/2/3992-site-analytics-package/
├── checklists/
│   └── requirements.md
├── plan.md
├── spec.md
└── tasks.md
```

The feature needs no separate research, data model, contract, or quickstart artifact.

### Target Source Structure

```text
src/mist/intelligence/analytics/
├── __init__.py
├── data_collection_manager.py
├── insight_metrics_utils.py
├── telemetry_emitter.py
└── site/
    ├── __init__.py
    ├── site_analytics_configurator.py
    ├── site_inventory_health_analyzer.py
    └── zone_analyzer.py
```

The root has four structural children after metadata exclusions. The `site` package has three
structural children after metadata exclusions.

**Structure Decision**: Group only site-focused analytics. Do not move unrelated analytics
modules or analytics tests.

## Exact Move Manifest

| Action | Authority path | Canonical path |
| - | - | - |
| Add | N/A | `src/mist/intelligence/analytics/site/__init__.py` |
| Move | `src/mist/intelligence/analytics/site_analytics_configurator.py` | `src/mist/intelligence/analytics/site/site_analytics_configurator.py` |
| Move | `src/mist/intelligence/analytics/site_inventory_health_analyzer.py` | `src/mist/intelligence/analytics/site/site_inventory_health_analyzer.py` |
| Move | `src/mist/intelligence/analytics/zone_analyzer.py` | `src/mist/intelligence/analytics/site/zone_analyzer.py` |

The new initializer contains only a package docstring. Delete all three old modules after the
moves.

Do not leave a wrapper, alias, forwarding module, fallback import, or deprecation path at an old
location.

## Canonical Import and Path Changes

Apply only these active path changes.

| File | Required change |
| - | - |
| `MistHelper.py` | Change both configurator imports and both inventory imports to the `analytics.site` package. Preserve imported names and aliases. |
| `src/mist/intelligence/analytics/__init__.py` | Import the four existing exports from the two new module paths. Keep `__all__` unchanged. |
| `src/operations/exporting/export/site_export_utils.py` | Change the delayed zone import and its docstring path to `analytics.site.zone_analyzer`. |
| `scripts/replace_zone.py` | Change the embedded source path and delayed zone import to `analytics.site.zone_analyzer`. |
| `tests/guardrails/test_performance_hook_catalog.py` | Resolve immutable historical catalog paths to current source paths and test the site analytics mapping. |
| `documentation/architecture.md` | Change the site analytics package path to `analytics/site/`. |
| `documentation/diagrams/core/architecture-overview.md` | Change the site analytics package path to `analytics/site/`. |
| `tests/unit/analytics/test_site_analytics_configurator.py` | Change imports and patch targets to the new configurator path. |
| `tests/unit/analytics/test_site_inventory_health_analyzer.py` | Change imports, patch targets, and `_MODULE_LOGGER` to the new inventory path. |
| `tests/unit/test_zone_analyzer.py` | Change the module docstring, imports, patch targets, and logger targets to the new zone path. |
| `tests/unit/export/test_site_export_utils_extended.py` | Import `zone_analyzer` from `src.mist.intelligence.analytics.site`. |

The analytics root continues to export only these names:

1. `SiteAnalyticsConfigurator`
2. `SiteAnalyticsConfiguratorDeps`
3. `SiteInventoryHealthAnalyzer`
4. `SiteInventoryHealthAnalyzerDeps`

Do not export `ZoneConfigurationAnalyzer` from the analytics root.

## Symbol Preservation Mapping

Update `MODULE_PATHS` in `tests/guardrails/test_src_public_symbol_preservation.py` with these exact
source-relative mappings. Preserve immutable performance catalog paths and resolve them through
`tests/guardrails/test_performance_hook_catalog.py`.

| Authority path | Canonical path | Required symbols |
| - | - | -: |
| `mist/intelligence/analytics/site_analytics_configurator.py` | `mist/intelligence/analytics/site/site_analytics_configurator.py` | 16 |
| `mist/intelligence/analytics/site_inventory_health_analyzer.py` | `mist/intelligence/analytics/site/site_inventory_health_analyzer.py` | 14 |
| `mist/intelligence/analytics/zone_analyzer.py` | `mist/intelligence/analytics/site/zone_analyzer.py` | 92 |

Use authority commit `0b04cda81c8ef75096f3bedae0885038c775d665` for the approved source
inventory. Preserve all 122 symbols.

The comparison includes classes, functions, assignments, annotated assignments, imported names,
private names, constants, type aliases, and helpers.

Do not add an intentional symbol removal for this change.

## Active Documentation and Generator Handling

Update only the moved source links in these maintained files:

- `documentation/architecture.md`
- `documentation/diagrams/core/architecture-overview.md`
- `documentation/menu-api/safe.md`
- `documentation/menu-api/destructive.md`
- `documentation/wiki/Menu-API-Endpoints-Safe.md`
- `documentation/wiki/Menu-API-Endpoints-Destructive.md`

Change each old slash path to the matching path below `analytics/site/`. Preserve all other
generated and maintained documentation content.

Run `python scripts/generate_menu_wiki.py`. Inspect its output and reject any unrelated change.

Run `python -m scripts.menu_api_map`. Accept only the four approved endpoint-page path updates.

Run both generators again after the implementation commit. Require a clean result for their
managed files.

Do not edit another issue specification. Do not edit a historical specification that contains an
old path.

Leave the released `CHANGELOG.md` unchanged. Add
`changelog.d/issue-3992-site-analytics-package.md` with one heading and one `Changed` bullet.

## Scoped Structural Guard Design

Add `tests/guardrails/test_analytics_package_structure.py`.

Create an `AnalyticsStructureInspector` class. Give it the analytics root and repository root.

The inspector uses these rules:

1. Inspect only `src/mist/intelligence/analytics` and its `site` package.
2. Validate both required directories before any count result is returned.
3. Exclude `__init__.py`, `__pycache__`, `.mypy_cache`, and `.pytest_cache`.
4. Count direct files and directories that remain after the exclusions.
5. Fail when a checked directory has more than five structural children.
6. Report the checked directory count, violating path, and measured child count.
7. Return stable repository-relative paths in sorted order.

The repository test requires this exact result:

```python
{
    "src/mist/intelligence/analytics": 4,
    "src/mist/intelligence/analytics/site": 3,
}
```

The success message reports exactly two checked package directories.

Add these direct failure proofs:

1. Create one temporary package with six children. Require one checked directory, its path, and
   the count of six.
2. Use one absent analytics root. Require the absent path and a clear inspection cause.
3. Mock one tracked active file with an old path. Require that file in the violation result.

The active-path check reads `git ls-files -z`. It fails if Git cannot provide the required tracked
file input. Exclude only the historical catalog file that resolves old paths through explicit
canonical mappings.

Scan tracked text files in `MistHelper.py`, `src/`, `tests/`, `scripts/`, and `documentation/`.
Match old dotted imports and old slash paths.

Exclude `specs/` and `CHANGELOG.md` from the active scan. Do not inspect any hierarchy outside
`src/mist/intelligence/analytics`.

## Preservation Boundaries

Preserve these contracts without modification:

- Every module-level symbol at the authority commit.
- Every class name, function name, constant, type alias, import, and private helper.
- Every method signature and dependency container field.
- The four analytics root exports and their object identities.
- Analytics calculations, prompts, confirmation words, logs, CSV content, and filenames.
- Mist API methods, arguments, rate behavior, errors, and cancellation behavior.
- Existing test file locations.
- Active documentation content except for moved source links.
- Generated documentation content except for moved source links.
- Historical specifications, including specifications that contain old paths.
- The released `CHANGELOG.md`, byte for byte.

Do not split, combine, or otherwise refactor the moved module bodies. Do not repair unrelated
structural debt.

## Implementation Sequence

1. Record the authority SHA and the current symbol inventories.
2. Add the docstring-only `site` package initializer.
3. Move the three modules without content changes.
4. Delete the three old module paths with no wrappers.
5. Update the runtime, package, script, test, mock, and logger paths.
6. Update the symbol-preservation map with the three exact mappings.
7. Add the scoped structure and active-path guard with its failure proofs.
8. Update maintained documentation links and regenerate their managed outputs.
9. Add the issue #3992 changelog fragment.
10. Run the full validation plan and inspect the final file set.

## Validation Plan

Run each command from the repository root with the worktree environment active.

### Authority and Scope

```bash
git cat-file -e 0b04cda81c8ef75096f3bedae0885038c775d665^{commit}
git diff --name-status 0b04cda81c8ef75096f3bedae0885038c775d665...HEAD
git diff --exit-code -- CHANGELOG.md
git diff --exit-code -- specs ':(exclude)specs/numbered/0/0/1/1/1/4/3/2/3992-site-analytics-package'
```

Inspect the name-status result. Require three renames, one package initializer, approved path
updates, two guard changes, and one changelog fragment.

### Compile, Lint, Format, and Types

```bash
python -m py_compile MistHelper.py \
  src/mist/intelligence/analytics/__init__.py \
  src/mist/intelligence/analytics/site/__init__.py \
  src/mist/intelligence/analytics/site/site_analytics_configurator.py \
  src/mist/intelligence/analytics/site/site_inventory_health_analyzer.py \
  src/mist/intelligence/analytics/site/zone_analyzer.py \
  src/operations/exporting/export/site_export_utils.py \
  scripts/replace_zone.py
python -m ruff check .
python -m black --check --diff .
python -m mypy src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
```

### Focused Behavior and Guard Tests

```bash
python -m pytest tests/unit/analytics/test_site_analytics_configurator.py
python -m pytest tests/unit/analytics/test_site_inventory_health_analyzer.py
python -m pytest tests/unit/test_zone_analyzer.py
python -m pytest tests/unit/export/test_site_export_utils_extended.py
python -m pytest tests/guardrails/test_src_public_symbol_preservation.py
python -m pytest tests/guardrails/test_performance_hook_catalog.py
python -m pytest tests/guardrails/test_analytics_package_structure.py -q -s
python -m pytest \
  tests/unit/analytics/test_site_analytics_configurator.py \
  tests/unit/analytics/test_site_inventory_health_analyzer.py \
  tests/unit/test_zone_analyzer.py \
  tests/unit/export/test_site_export_utils_extended.py \
  tests/guardrails/test_src_public_symbol_preservation.py \
  tests/guardrails/test_performance_hook_catalog.py \
  tests/guardrails/test_analytics_package_structure.py
```

### Runtime and Coverage

```bash
python MistHelper.py --test
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

The safe sweep can skip Mist API checks only for the documented missing-credential reason.

### Complexity, Security, and Code Quality

```bash
radon cc src/ MistHelper.py wsgi.py \
  scripts/analyze_marvis_pcap.py \
  scripts/probe_zscaler_endpoints.py \
  tests/unit/utils/test_zscaler_catalogue.py \
  -a -nb
radon cc src/ MistHelper.py wsgi.py \
  scripts/analyze_marvis_pcap.py \
  scripts/probe_zscaler_endpoints.py \
  tests/unit/utils/test_zscaler_catalogue.py \
  -j | complexity-gate --max 10
bandit-exclude-check \
  --include-sample ./src/foundation/support/utils/zen_city_metadata.py \
  --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'
bandit -c pyproject.toml -r .
pip-audit -r requirements.txt
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
```

### Documentation and Generators

```bash
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
ste-linter --config .ste-linter.toml --min-score 80 \
  specs/numbered/0/0/1/1/1/4/3/2/3992-site-analytics-package/plan.md \
  documentation/menu-api/safe.md \
  documentation/menu-api/destructive.md \
  documentation/wiki/Menu-API-Endpoints-Safe.md \
  documentation/wiki/Menu-API-Endpoints-Destructive.md \
  changelog.d/issue-3992-site-analytics-package.md
```

After the implementation commit, run the two generators again. Then run:

```bash
git diff --exit-code HEAD -- \
  documentation/menu-api/safe.md \
  documentation/menu-api/destructive.md \
  documentation/wiki/Menu-API-Endpoints-Safe.md \
  documentation/wiki/Menu-API-Endpoints-Destructive.md \
  documentation/menu_reference.md \
  documentation/wiki/Menu-Reference.md
```

### Test Quality

```bash
git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'
git rev-parse --verify 'origin/main^{commit}'
python -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --changed-from origin/main \
  --full-gate-path .github/workflows/ci.yml \
  --full-gate-path requirements-dev.txt
```

Run the changed-test quality gate only after the implementation commit. Require
`gate: 0 new findings vs baseline`.

### Final Preservation Checks

```bash
python -m pytest tests/guardrails/test_src_public_symbol_preservation.py \
  tests/guardrails/test_analytics_package_structure.py -q -s
git grep -n -E \
  'src\.mist\.intelligence\.analytics\.(site_analytics_configurator|site_inventory_health_analyzer|zone_analyzer)|src/mist/intelligence/analytics/(site_analytics_configurator|site_inventory_health_analyzer|zone_analyzer)\.py' \
  -- MistHelper.py src tests scripts documentation \
  ':!tests/guardrails/test_performance_hook_catalog.py'
git diff --exit-code -- CHANGELOG.md
```

The `git grep` command must return no match. The guards must report 122 preserved symbols and
exactly two checked analytics package directories.

## Complexity Tracking

No constitution violation is accepted. This change reduces one analytics hierarchy violation and
does not expand the guard to unrelated debt.
