# Implementation Plan: Mist API Endpoint Reference Documentation

**Branch**: `008-mist-api-docs` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-mist-api-docs/spec.md`

## Summary

Generate comprehensive per-endpoint Mist API documentation as markdown files optimized for AI consumption. A Python script (Phase 1) parses the OpenAPI 3.1 spec to produce ~1,013 raw markdown files with fully dereferenced schemas, parameters, and response definitions. An AI agent (Phase 2) then rewrites each file with enriched content — usage context, gotchas, cross-references, and MistHelper-specific notes. Output lives in `documentation/api/` organized by tag category (orgs, sites, msps, etc.) with a master INDEX.md.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `json` (stdlib) for OpenAPI parsing; `pathlib` for file I/O; `re` for operationId-to-mistapi mapping
**Storage**: Filesystem — ~1,013 markdown files in `documentation/api/` subdirectories
**Testing**: Manual validation — spot-check 5 random endpoints against OpenAPI spec; verify INDEX.md link integrity
**Target Platform**: Windows 11 (local dev), any OS with Python 3.13+
**Project Type**: Code generation tool (one-shot script + AI enrichment pass)
**Performance Goals**: Script completes full generation in <60 seconds
**Constraints**: Offline-capable (all source data in `documentation/` folder); no external API calls during generation
**Scale/Scope**: 1,013 API operations, 1,799 schemas, 206 tags, 8 category directories, ~1,013 output files + 1 index file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | Script has <=5 classes. Output directories (8) exceed 5 but are externally determined by the Mist API tag structure — not our architectural choice. |
| II. Class-Based Architecture | PASS | Generator script uses class-based design: `SpecParser`, `SchemaResolver`, `MarkdownRenderer`, `IndexGenerator`. No wrapper functions. |
| III. Safety-First | PASS | No destructive operations. Script is read-only (parses input spec, writes output files). No user input required. |
| IV. Full Deployment Pipeline | N/A | This feature generates documentation files, not runtime code. No container deployment needed. |
| V. Observability & Logging | PASS | Script uses `logging` module for progress reporting. ASCII-only output. |

## Project Structure

### Documentation (this feature)

```text
specs/008-mist-api-docs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code

```text
scripts/
└── generate_api_docs.py     # Python script: OpenAPI -> raw markdown files

documentation/
├── mist-api-openapi31json.json   # Source: OpenAPI 3.1 spec (17MB, already downloaded)
├── mist-api-openapi31yaml.yaml   # Source: OpenAPI 3.1 spec (11MB, already downloaded)
└── api/                          # Output: generated markdown files
    ├── INDEX.md                  # Master index grouped by tag
    ├── orgs/                     # 449 operations
    │   ├── GET_orgs_org_id_sites.md
    │   ├── POST_orgs_org_id_sites.md
    │   └── ...
    ├── sites/                    # 330 operations
    │   ├── GET_sites_site_id_devices.md
    │   └── ...
    ├── msps/                     # 50 operations
    ├── utilities/                # 103 operations
    ├── constants/                # 27 operations
    ├── installer/                # 23 operations
    ├── self/                     # 18 operations
    └── admins/                   # 13 operations
```

**Structure Decision**: Single-project layout. One Python script in `scripts/` generates all output files into `documentation/api/`. No tests directory needed — validation is manual spot-checking. The 8 output subdirectories are determined by the Mist API's tag categories, not by our design choices.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 8 output directories (exceeds Five-Item Rule) | Mist API has 8 tag categories (Orgs, Sites, MSPs, Utilities, Constants, Installer, Self, Admins) — directory structure mirrors API structure for intuitive navigation | Fewer directories would require grouping unrelated endpoints or flattening all 1,013 files into one directory, making discovery harder |
