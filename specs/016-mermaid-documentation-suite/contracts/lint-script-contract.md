# Contract: Diagram Reference Lint Script

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## Purpose

The lint script (`scripts/lint_diagram_refs.py`) validates that identifiers referenced in Mermaid diagram code blocks correspond to real symbols in the Python codebase. It runs in CI to prevent diagrams from becoming stale after refactors.

## Interface

### CLI

```
python scripts/lint_diagram_refs.py [--docs-dir PATH] [--extra-files PATH...] [--source-files PATH...] [--allowlist PATH] [--verbose]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--docs-dir` | `documentation/diagrams/` | Directory containing diagram markdown files (scanned recursively) |
| `--extra-files` | `README.md` | Additional markdown files outside docs-dir that contain inline Mermaid diagrams |
| `--source-files` | `MistHelper.py` | Python source files to extract symbols from |
| `--allowlist` | (built-in) | File of identifiers to skip (Mermaid keywords, abbreviations) |
| `--verbose` | False | Print all checked references, not just failures |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All references valid |
| 1 | Stale references found |
| 2 | Script error (missing files, parse failure) |

### Output Format (stdout)

```
OK: 142 references validated across 15 diagram files
```

On failure:
```
STALE: documentation/diagrams/class-hierarchy/exporters.md:42 "OrgFooExporter" not found in codebase
  Closest match: "OrgConfigExporter" (edit distance: 3)
STALE: documentation/diagrams/data-pipeline.md:18 "fetch_all_pages" not found in codebase
  Closest match: "fetch_with_pagination" (edit distance: 8)

FAILED: 2 stale references found across 15 diagram files
```

## Extraction Rules

### From Mermaid Code Blocks

The script extracts identifiers from these Mermaid syntax patterns:

| Diagram Type | Pattern | Example |
|-------------|---------|---------|
| classDiagram | `class ClassName` | `class DataExporter` |
| classDiagram | `ClassName : method()` | `DataExporter : write_with_format_selection()` |
| classDiagram | `ClassName <|-- ChildClass` | inheritance arrows |
| sequenceDiagram | `participant Name` | `participant APIFetchUtils` |
| sequenceDiagram | `Name->>Target: method()` | `APIFetchUtils->>DataExporter: write()` |
| flowchart | `NodeId[Label Text]` | `export[DataExporter]` |
| all types | Text matching `r'[A-Z][a-zA-Z]+(?:Utils|Manager|Exporter|Config|Runner|Writer|Fetcher|Processor)'` | PascalCase class names |

### From Python Source

The script uses `ast.parse()` to extract:
- All class names (`ast.ClassDef`)
- All method names within classes (`ast.FunctionDef` inside `ast.ClassDef`)
- All top-level function names (`ast.FunctionDef` at module level)

### Allowlist (Built-in Defaults)

Identifiers that look like class names but are Mermaid keywords or domain terms:
```
API, SSH, CSV, SQLite, GHCR, CI, CD, UUID, PK, ER, EOF,
MistHelper, GitHub, Podman, Docker, Flask, Gunicorn, Mermaid,
Ruff, Bandit, CodeQL, Playwright, WebSocket, ForceCommand
```

## CI Integration

Add as matrix entry in `.github/workflows/ci.yml`:

```yaml
- name: Diagram Reference Lint
  run: python scripts/lint_diagram_refs.py
```

Position: alongside existing quality-gates matrix checks (Ruff, mypy, pytest, Bandit, pip-audit).
