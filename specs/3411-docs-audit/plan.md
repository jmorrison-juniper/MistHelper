# Implementation Plan: Correct the documents and map each menu option to its Mist API endpoints

**Issue**: #3411 | **Branch**: `feat/3411-docs-audit` | **Spec**: [spec.md](spec.md)

## Summary

Two streams of work run at the same time.

1. A new tool, `tools/menu_api_map`, reads the menu registry and the source tree
   with the `ast` module. It writes the endpoint map pages and their Mermaid
   diagrams. A check mode guards the pages in CI.
2. A fleet of audit agents corrects the documents. Each agent owns one slice of
   files, and no two slices share a file.

## Technical context

- **Language**: Python 3.13, standard library only. The CI drift job installs
  no requirements, so the tool must run on a bare interpreter.
- **SDK data**: `mistapi` 0.64.0. Each SDK function holds its path in a
  `uri = f"/api/v1/..."` line and its HTTP method in a `mist_session.mist_*`
  call. The refresh command reads these lines with `ast` and writes
  `tools/menu_api_map/reference/sdk_index.json`.
- **Scale**: 622 modules, 11,412 functions, 1,185 classes, and 1,063 SDK
  functions. One run of the prototype takes about 13 seconds.
- **Gates**: ruff, black, bandit, and interrogate read `tools/`. mypy, radon,
  vulture, and pydocstyle exclude `tools/`. The tool aims to pass them anyway.

## Design

### Tool layout

| Path | Purpose |
| - | - |
| `tools/menu_api_map/__main__.py` | The command line: write, `--check`, and `--refresh-sdk-index`. |
| `tools/menu_api_map/analysis/` | The source index, the type resolver, the body scanner, the menu walker, and the SDK index reader. |
| `tools/menu_api_map/render/` | The Markdown tables, the Mermaid diagrams, and the page writer. |
| `tools/menu_api_map/reference/` | `sdk_index.json` and `curated.json`. |

### Analysis rules

The prototype in the session files proved these rules. The tool keeps them.

- The import map is scoped. A module map holds the top-level imports. Each
  function holds its own local imports, and a nested function also sees the
  imports of the enclosing function.
- The resolver infers a type from a parameter annotation, a constructor call,
  a return annotation, a `return` expression, and a `self.X = ...` statement.
- A class that defines `__getattr__` forwards an unknown member. The resolver
  then looks for a unique method of that name. It prefers a method in the
  package of the owner class.
- `getattr(obj, "name")` and `self._call("name")` dispatch by name. The scanner
  follows the name.
- The walker does not enter a shared helper class, such as `DataExporter` or
  `RateLimitingUtils`. It records the helper for the menu option. The index
  page lists the endpoints of each helper one time. If every root of a handler
  is in one helper class, the walker enters that class.
- `curated.json` names each case that static analysis cannot follow, with the
  reason. Two examples are the blueprint registry of the upgrade portal and the
  `pkgutil` walk of the constant exporter.

### Output

| Path | Content |
| - | - |
| `documentation/menu-api/README.md` | The index: how to read the map, the limits, the categories, and the shared helpers. |
| `documentation/menu-api/<category>.md` | One page for each registry category, with diagrams and one section for each menu option. |
| `documentation/wiki/Menu-API-Endpoints*.md` | The same pages with wiki links. |

Each file uses `\n` line ends and a sorted order, so two runs give the same
bytes on Windows and on Linux.

### CI

The `menu_reference_drift` job runs `python -m tools.menu_api_map --check`
after the existing menu reference check. A unit test compares the SDK index
with the installed `mistapi` package, because the unit test job installs the
requirements.

### Audit fleet

| Slice | Files |
| - | - |
| A | `README.md` and `documentation/wiki/`, except the generated menu reference |
| B | The core, infrastructure, and operations diagrams, `architecture.md`, and `network-routing-diagram.md` |
| C | The class hierarchy diagrams |
| D | The operator guides |
| E | The API and reference documents |
| F | The contributor and internal documents |
| G | The NOC runbooks and the CodeQL verdict register |
| H | The agent instruction files, with factual corrections only |
| I | The other root files, `mist-ops-platform/docs/`, and the tool README files |

Each agent works in the worktree, runs no git command that changes state, and
writes a ledger under `specs/3411-docs-audit/audit/`. Each ledger row names the
old claim, the new claim, and the evidence.

## Validation

- The Mermaid lint and the diagram reference lint.
- `python scripts/generate_menu_wiki.py --check` and
  `python -m tools.menu_api_map --check`.
- The STE linter at 80 on every changed Markdown file.
- ruff, black, bandit, interrogate, and pytest on the new tool and its tests.
- The test quality ratchet.

## Constitution check

- **Class-based design**: each module holds classes. No wrapper function exists.
- **STE**: each page and each message follows the writing guide.
- **Safety**: the tool reads files only. It calls no API and imports no project
  module.
