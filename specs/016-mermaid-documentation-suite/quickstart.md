# Quickstart: Mermaid Documentation Suite

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## What This Feature Delivers

A suite of 20+ Mermaid diagrams documenting MistHelper's architecture, data pipeline, class hierarchy, menu system, deployment pipeline, database strategy, and container architecture. All diagrams use T-Mobile dark-mode colors and render natively on GitHub.

## File Locations

| What | Where |
|------|-------|
| README inline diagrams (2) | `README.md` (architecture overview + menu mindmap) |
| Navigation index | `documentation/diagrams/README.md` |
| Core diagrams (architecture, pipeline, database) | `documentation/diagrams/core/*.md` |
| Class hierarchy sub-diagrams | `documentation/diagrams/class-hierarchy/*.md` |
| Operations diagrams (menu, metrics, workflow) | `documentation/diagrams/operations/*.md` |
| Infrastructure diagrams (deploy, container, network) | `documentation/diagrams/infrastructure/*.md` |
| PNG fallbacks for beta diagrams | Alongside source: `core/*.png`, `operations/*.png`, `infrastructure/*.png` |
| CI lint script | `scripts/lint_diagram_refs.py` |
| Lint script tests | `tests/unit/test_lint_diagram_refs.py` |

## How to View Diagrams

1. Open the repository on GitHub.com
2. The README shows 2 inline diagrams immediately
3. Scroll to the "Visual Documentation" section for links to all other diagrams
4. Or navigate directly to `documentation/diagrams/README.md` for the full index

## How to Add a New Diagram

1. Create or edit a markdown file in the appropriate subdirectory under `documentation/diagrams/` (`core/`, `class-hierarchy/`, `operations/`, or `infrastructure/`)
2. Add a Mermaid fenced code block with the T-Mobile theme init:
   ```
   %%{init: {'theme': 'dark', 'themeVariables': {
     'primaryColor': '#E20074',
     'primaryTextColor': '#E0E0E0',
     'primaryBorderColor': '#99004D',
     'lineColor': '#FF4DA6',
     'secondaryColor': '#16213E',
     'tertiaryColor': '#1A1A2E'
   }}}%%
   ```
3. Keep diagrams under 50 nodes
4. If using a beta diagram type, generate a PNG fallback with `mmdc` and save alongside the source markdown file
5. Add a navigation link in `documentation/diagrams/README.md`
6. Run the lint script: `python scripts/lint_diagram_refs.py`
7. Commit and push

## How to Update the Lint Script

The lint script (`scripts/lint_diagram_refs.py`) validates that class/method names in diagrams still exist in the codebase.

- It runs automatically in CI as part of the quality-gates matrix
- To run locally: `python scripts/lint_diagram_refs.py`
- To add exceptions (Mermaid keywords that look like identifiers): edit the allowlist in the script
- Tests: `pytest tests/unit/test_lint_diagram_refs.py`

## Color Reference (Quick Copy)

```
Primary:   #E20074  (T-Mobile Magenta)
Secondary: #FF6F91  (Light Magenta)
Tertiary:  #99004D  (Deep Magenta)
Background: #1A1A2E (Near Black)
Surface:   #16213E  (Dark Gray)
Text:      #E0E0E0  (Off White)
Links:     #FF4DA6  (Soft Magenta)
Safe:      #00C853  (Green)
Warning:   #FFD600  (Amber)
Danger:    #FF1744  (Red)
WIP:       #448AFF  (Blue)
```
