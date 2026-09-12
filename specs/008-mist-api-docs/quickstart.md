# Quickstart: Mist API Endpoint Reference Documentation

**Feature**: 008-mist-api-docs | **Date**: 2026-03-06

## Prerequisites

- Python 3.13+
- OpenAPI 3.1 spec file at `documentation/mist-api-openapi31json.json` (already downloaded)

## Phase 1: Generate Raw Markdown Files

```bash
python scripts/generate_api_docs.py
```

This parses the OpenAPI spec and generates ~1,013 raw markdown files in `documentation/api/` plus one `INDEX.md`.

**Expected output**:
```
Parsing OpenAPI spec...
Resolved 1799 schemas
Processing 1013 operations...
  orgs/: 449 files
  sites/: 330 files
  utilities/: 103 files
  msps/: 50 files
  constants/: 27 files
  installer/: 23 files
  self/: 18 files
  admins/: 13 files
Generated INDEX.md with 1013 entries across 206 tags
Done.
```

## Phase 2: AI Enrichment

After raw generation, an AI agent reads each file and rewrites it with enriched content:
- Usage context and common use cases
- Known gotchas and pitfalls
- Cross-references to related endpoints
- MistHelper-specific notes

This is done interactively in batches (e.g., one category directory per session).

## Verification

1. Count output files: `Get-ChildItem documentation/api -Recurse -Filter *.md | Measure-Object`
   - Expected: ~1,014 files (1,013 endpoints + INDEX.md)

2. Spot-check a file: `Get-Content documentation/api/orgs/GET_orgs_org_id_sites.md | Select-Object -First 30`
   - Should contain: HTTP method, path, parameters table, response schema

3. Verify INDEX.md links: Open `documentation/api/INDEX.md` and confirm relative links resolve to actual files

## Regeneration

To regenerate from scratch after an OpenAPI spec update:

1. Download new spec: `Invoke-WebRequest -Uri "https://doc.mist-lab.fr/openapi/spec/mist-api-openapi31json.json" -OutFile "documentation/mist-api-openapi31json.json"`
2. Run generator: `python scripts/generate_api_docs.py`
3. Re-run AI enrichment pass on changed files
