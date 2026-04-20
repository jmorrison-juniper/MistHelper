# Implementation Plan: Mist Ideas Analyzer

**Branch**: `183-mist-ideas-analyzer` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/183-mist-ideas-analyzer/spec.md`

## Summary

A standalone Python script (`scripts/mist_ideas_analyzer.py`) that reads `mist_ideas.csv`, sends each idea to an AI model for semantic analysis using the OpenAI-compatible API, and produces three output files (Markdown, JSON, CSV). The AI classifies each idea by MistHelper feasibility using 7 labels + AI_INSPIRED, identifies duplicates, groups into themes, and discovers snowball chains. Feasibility judgments are grounded in the local OpenAPI spec (`documentation/mist-api-openapi3json.json`, 714 endpoints). Results are cached per-idea for resume support.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `openai>=1.0` (AI API client, OpenAI-compatible surface for all 4 backends including local Ollama), `python-dotenv` (credential loading), `argparse` (stdlib, CLI flags), `subprocess` (stdlib, GPU detection via `nvidia-smi` and Podman/Docker container management for Ollama backend)
**Storage**: JSON files in `data/mist_ideas_cache/` (per-idea cache + `api_index.json`); output to `data/mist_ideas_analysis.{md,json,csv}`
**Testing**: pytest
**Target Platform**: Windows 11 local dev, Linux container (cross-platform)
**Project Type**: CLI standalone script (permanently external to MistHelper menu)
**Performance Goals**: Full run of 50-200 ideas completes within 10 minutes with responsive AI API
**Constraints**: Must work offline except for AI API calls (or fully offline with local Ollama); no Mist Cloud API calls; all credentials from `.env`
**Scale/Scope**: 50-200 ideas in CSV, spanning 2018-present; significant expected duplicates and already-implemented ideas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | 5 classes planned (AiBackendDetector, ApiIndexBuilder, IdeaParser, IdeaAnalyzer, ReportGenerator); AiBackendDetector handles all 4 backends including Ollama/GPU detection; each under 5 public methods; functions will stay under 25 lines |
| II. Class-Based Architecture | PASS | All logic in semantic classes; no standalone wrapper functions; full descriptive names |
| III. Safety-First | PASS | No interactive user input (CLI args only); no destructive operations; validate file paths; no secrets in logs (redact API keys at logging boundary) |
| IV. Full Deployment Pipeline | N/A | Standalone script in `scripts/`; does not modify MistHelper.py; no container rebuild needed |
| V. Observability & Logging | PASS | Python `logging` module; ASCII only; Debug (API responses), Info (progress), Error (with traceback). Note: constitution says `structlog` for new modules, but stdlib `logging` is acceptable for a standalone CLI utility that is not a long-running service |
| Security: Fix Over Suppress | PASS | No SQL injection surface; no user-controlled format strings; file paths validated; API keys from `.env` only |

## Project Structure

### Documentation (this feature)

```text
specs/183-mist-ideas-analyzer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (AI response schema)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
scripts/
└── mist_ideas_analyzer.py    # Main standalone script (single file)

tests/
└── test_mist_ideas_analyzer.py  # Unit + integration tests

data/
├── mist_ideas_cache/             # AI response cache (generated at runtime)
│   ├── api_index.json            # Pre-indexed OpenAPI endpoint lookup
│   └── <content-hash>.json       # Per-idea cached AI responses
├── mist_ideas_analysis.md        # Output: Markdown report (generated)
├── mist_ideas_analysis.json      # Output: JSON sidecar (generated)
└── mist_ideas_analysis.csv       # Output: CSV sidecar (generated)
```

**Structure Decision**: Single-file script under `scripts/` following the project's existing convention for standalone utilities. Tests in a dedicated test file under `tests/`. All generated output in `data/` directory per MistHelper convention. No new packages or directories beyond what already exists.

## Complexity Tracking

No violations requiring justification. All five classes fit within a single module file. The Five-Item Rule is satisfied at every level.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
