# Tasks: Mist Ideas Analyzer

**Input**: Design documents from `/specs/183-mist-ideas-analyzer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, file creation, CLI scaffolding

- [X] T001 Create `scripts/mist_ideas_analyzer.py` with shebang, module docstring, imports (`openai`, `csv`, `json`, `hashlib`, `argparse`, `logging`, `os`, `subprocess`, `pathlib`), and `if __name__ == "__main__"` entry point
- [X] T002 Implement CLI argument parser with flags: `--input` (CSV path, default `mist_ideas.csv`), `--refresh` (ignore cache), `--refresh-index` (rebuild API index), `--verbose` (debug logging)
- [X] T003 Configure Python `logging` module: ASCII-only formatter, Info default (Debug with `--verbose`), log to stderr so stdout stays clean for progress output

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core classes that ALL user stories depend on — CSV parsing, AI backend detection, API index building, and caching infrastructure

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `IdeaParser` class in `scripts/mist_ideas_analyzer.py`: `parse(csv_path) -> list[dict]` method that reads CSV with `csv.reader(newline='', encoding='utf-8')`, extracts 3 positional columns (title, description, comments JSON), parses comments via `json.loads()` with `JSONDecodeError` fallback to empty list, skips rows with empty title (logs warning), and computes `content_hash` per idea using SHA256 on normalized `title + "\n" + description + "\n" + comments_json` (R3 decision)
- [X] T005 [P] Implement `AiBackendDetector` class in `scripts/mist_ideas_analyzer.py`: `detect() -> dict` method that checks `.env` credentials in priority order and returns `{"backend": str, "base_url": str, "model": str, "api_key": str}`. Priority chain: 1) GitHub Models (`GITHUB_TOKEN` → `https://models.inference.ai.azure.com`, default `gpt-4o-mini`), 2) AVA MCP (`AVA_API_URL`, default `llama3.3`), 3) Generic (`AI_API_KEY` + optional `AI_API_BASE_URL`, default `gpt-4o-mini`), 4) Local Ollama (see T006). All models overridable via `AI_MODEL`. Logs selected backend and model at Info level. Raises `RuntimeError` if no backend available
- [X] T006 Implement Ollama backend support in `AiBackendDetector`: `_detect_ollama() -> dict` method that: a) detects container runtime (`podman` then `docker` via `shutil.which()`), b) queries GPU VRAM via `nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits` using `subprocess.run()`, c) maps VRAM to best-fit model using built-in lookup (R6 decision: 8GB→`llama3.1:8b`, 12GB→`mistral:7b-instruct-q8`, 16GB+→`mistral:7b-instruct-q8`, 24GB+→`mixtral:8x7b-instruct-q4`, no GPU→`llama3.2:3b` with CPU warning), d) checks if `ollama-misthelper` container is running via `podman ps`, e) starts container if needed with GPU passthrough (`--device nvidia.com/gpu=all` for Podman, `--gpus all` for Docker), f) pulls selected model via `podman exec ollama-misthelper ollama pull <model>`, g) health-checks `http://localhost:11434/api/tags` with a 30-second timeout and up to 3 retries at 5-second intervals (Ollama may still be loading the model), h) returns config dict with `base_url=http://localhost:11434/v1` and `api_key=ollama`
- [X] T007 [P] Implement `ApiIndexBuilder` class in `scripts/mist_ideas_analyzer.py`: `build(openapi_path, cache_path) -> dict` method that loads `documentation/mist-api-openapi3json.json`, extracts all paths with their HTTP method, summary, tags, and key parameter names into a lightweight lookup dict grouped by tag. Saves to `data/mist_ideas_cache/api_index.json`. On subsequent runs, loads from cache unless `--refresh-index` is passed. `search(query_terms) -> list[dict]` method that returns the top 10 most relevant endpoint summaries for a set of keywords (simple term matching against path + summary + tags)
- [X] T008 Implement caching infrastructure: helper functions `load_cached_response(cache_dir, content_hash) -> dict|None` and `save_cached_response(cache_dir, content_hash, response) -> None` that read/write `data/mist_ideas_cache/{content_hash}.json`. Handle `JSONDecodeError` on load by returning None and logging warning (triggers re-analysis per FR-005)

**Checkpoint**: Foundation ready — IdeaParser can read CSV, AiBackendDetector can configure any of the 4 backends (including local Ollama with GPU auto-detection), ApiIndexBuilder can index/search OpenAPI endpoints, and cache infrastructure is operational. User story implementation can now begin.

---

## Phase 3: User Story 1 — AI Classifies Each Idea (Priority: P1) MVP

**Goal**: For every idea in the CSV, send it to the AI with relevant API context and receive a structured classification with rationale

**Independent Test**: Run against a 10-idea sample, verify every idea has a `classification` and non-empty `rationale`. Confirm GUI layout ideas get GUI_ONLY and data export ideas get REPORT_EXPORT.

### Implementation for User Story 1

- [X] T009 [US1] Implement `IdeaAnalyzer` class in `scripts/mist_ideas_analyzer.py` with `__init__(self, backend_config, api_index)` that creates an `openai.OpenAI` client using the detected backend config (base_url, api_key, model)
- [X] T010 [US1] Implement `IdeaAnalyzer._build_system_prompt() -> str` method: defines MistHelper scope (API caller, not builder), lists all 7 classification labels with definitions (REPORT_EXPORT, API_ENHANCEMENT, HYBRID, GUI_ONLY, HARDWARE_FEATURE, ALREADY_SUPPORTED, UNCLASSIFIED), explains the GUI-vs-API rule (PR-002: portal phrasing does NOT auto-mean GUI_ONLY), specifies JSON response schema from contracts/ai-response-schema.md, and includes the AI_INSPIRED instruction (PR-005)
- [X] T011 [US1] Implement `IdeaAnalyzer._build_user_prompt(idea, relevant_endpoints) -> str` method: formats idea title, full description, all comments (author + text), and the top relevant endpoint summaries from the API index as clearly delimited sections
- [X] T012 [US1] Implement `IdeaAnalyzer.analyze_idea(idea) -> dict` method: checks cache first (skip if hit and not `--refresh`), searches API index for relevant endpoints using keywords from the idea title/description, calls `client.chat.completions.create()` with `response_format={"type": "json_object"}` (R1 decision), parses JSON response, validates `classification` is in the enum set (retry once if not), handles `json.JSONDecodeError` with one retry then fallback to UNCLASSIFIED (FR-012), saves to cache on success, applies inter-request delay of 0.5s (R2 decision)
- [X] T013 [US1] Implement `IdeaAnalyzer.analyze_all(ideas) -> list[dict]` method: iterates all ideas, calls `analyze_idea()` per idea, displays progress indicator `[N/Total] Analyzing: <title>` (FR-014), collects all results. Uses exponential backoff with jitter on HTTP 429 (R2 decision: base 2s, 2^attempt, max 3 retries)
- [X] T014 [US1] Wire up `main()` function: parse CLI args, load `.env`, detect backend, build/load API index, parse CSV, call `analyze_all()`, print summary counts per classification to stdout

**Checkpoint**: User Story 1 complete — every idea gets an AI classification with rationale, grounded in local OpenAPI endpoints, with caching and progress display. The script is end-to-end runnable as an MVP.

---

## Phase 4: User Story 2 — Duplicate Detection and Merging (Priority: P1)

**Goal**: After per-idea analysis, perform a second AI pass to identify semantically duplicate ideas and merge them into clusters

**Independent Test**: Provide 5 ideas (2 pairs of duplicates + 1 unique), verify output has 3 clusters with correct membership.

### Implementation for User Story 2

- [X] T015 [US2] Implement `IdeaAnalyzer._build_dedup_prompt(ideas) -> str` method: formats all idea titles with short description excerpts (~20 words each) into a single prompt asking the AI to identify duplicate groups per the dedup batch contract schema (R5 decision: single request, ~6K tokens for 200 ideas)
- [X] T016 [US2] Implement `IdeaAnalyzer.detect_duplicates(ideas, analyses) -> list[dict]` method: calls the AI with the dedup prompt, parses the JSON response into `duplicate_groups` (canonical_title, duplicate_titles, merge_confidence), validates that all titles exist in the input dataset (skip unknown titles with warning), treats `merge_confidence=low` as `possible_duplicate_of` cross-reference rather than forced merge (FR-006)
- [X] T017 [US2] Implement `IdeaAnalyzer.build_clusters(ideas, analyses, duplicate_groups) -> list[dict]` method: merges confirmed duplicates into `IdeaCluster` dicts (canonical_title, merged_titles, demand_count, classification from primary idea's analysis, combined themes, combined unlocks). Unmerged ideas become single-member clusters. Cross-references from low-confidence matches stored as `possible_duplicate_of` field
- [X] T018 [US2] Wire dedup into `main()`: after `analyze_all()`, call `detect_duplicates()` then `build_clusters()`, log cluster count vs. raw idea count. Also aggregate all `ai_inspired_ideas` from every idea's analysis into a flat `all_ai_inspired` list (attaching `source_idea_title` from the parent idea's title) for later use by `ReportGenerator`

**Checkpoint**: User Stories 1 and 2 complete — ideas are classified AND deduplicated into clusters with demand counts.

---

## Phase 5: User Story 5 — Structured Output Report (Priority: P1)

**Goal**: Produce all three output files (Markdown, JSON, CSV) with executive summary, classification sections, and per-cluster detail

**Independent Test**: Run the script and verify the Markdown renders in GitHub, JSON is valid via `json.loads()`, and CSV opens with one row per cluster.

### Implementation for User Story 5

- [X] T019 [US5] Implement `ReportGenerator` class in `scripts/mist_ideas_analyzer.py` with `__init__(self, clusters, all_ai_inspired)` storing the cluster list and collected AI-inspired ideas
- [X] T020 [US5] Implement `ReportGenerator._executive_summary() -> str` method: total ideas processed, count per classification, count of unique themes, top 5 clusters by demand count, total AI-inspired ideas generated
- [X] T021 [US5] Implement `ReportGenerator.generate_markdown(output_path) -> None` method: writes `data/mist_ideas_analysis.md` with executive summary followed by sections in order: REPORT_EXPORT, API_ENHANCEMENT, HYBRID, GUI_ONLY, HARDWARE_FEATURE, ALREADY_SUPPORTED, UNCLASSIFIED (FR-009). Each cluster entry shows: canonical title, classification badge, themes, demand count, rationale, enhancement suggestion (if applicable), snowball reference (if applicable). Final section: AI Inspired Ideas
- [X] T022 [P] [US5] Implement `ReportGenerator.generate_json(output_path) -> None` method: writes `data/mist_ideas_analysis.json` with the full structured analysis — all clusters, themes, snowball chains, per-idea AI responses, and AI-inspired ideas. Validated with `json.dumps(indent=2)`
- [X] T023 [P] [US5] Implement `ReportGenerator.generate_csv(output_path) -> None` method: writes `data/mist_ideas_analysis.csv` with one row per cluster — columns: canonical_title, classification, confidence, demand_count, themes (pipe-separated), rationale, misthelper_enhancement, is_foundational, possible_duplicate_of
- [X] T024 [US5] Wire report generation into `main()`: after clustering, instantiate `ReportGenerator`, call all three generate methods, log output file paths

**Checkpoint**: User Stories 1, 2, and 5 complete — full end-to-end pipeline from CSV to three output files with executive summary.

---

## Phase 6: User Story 3 — Theme Grouping (Priority: P2)

**Goal**: Group idea clusters into named themes derived from actual content, with multi-theme support

**Independent Test**: Run against full CSV and verify themes have content-specific names (not generic), and clusters span multiple themes where appropriate.

### Implementation for User Story 3

- [X] T025 [US3] Implement `ReportGenerator.group_by_theme(clusters) -> list[dict]` method: collects all unique themes from cluster analyses, creates `ThemeGroup` dicts (theme name, list of member clusters sorted by demand descending, total_demand count). Clusters with multiple themes appear in multiple groups
- [X] T026 [US3] Add theme section to Markdown report in `generate_markdown()`: after the classification sections, insert a "Themes Overview" section listing each theme with cluster count, total demand, and member cluster titles
- [X] T027 [US3] Add theme data to JSON output in `generate_json()`: include `theme_groups` array with full theme structure

**Checkpoint**: Theme grouping operational — clusters are organized by AI-derived themes with demand signal.

---

## Phase 7: User Story 4 — Snowball Chains (Priority: P2)

**Goal**: Identify foundational ideas and the clusters they unlock, showing directed dependency relationships

**Independent Test**: Verify ideas sharing the same API endpoint family appear connected in snowball output.

### Implementation for User Story 4

- [X] T028 [US4] Implement `ReportGenerator.build_snowball_chains(clusters) -> list[dict]` method: finds all clusters where `is_foundational=True`, matches their `unlocks` list to other cluster titles (fuzzy match if exact title not found), creates `SnowballChain` dicts (root cluster, list of dependents with shared capability description)
- [X] T029 [US4] Add snowball chain section to Markdown report in `generate_markdown()`: after themes, insert "Snowball Chains" section showing each chain as: foundational idea title → list of unlocked ideas with explanations
- [X] T030 [US4] Add snowball chain data to JSON output in `generate_json()`: include `snowball_chains` array

**Checkpoint**: Snowball chains operational — developers can see which implementations unlock the most downstream value.

---

## Phase 8: User Story 6 — Resume and Cache (Priority: P3)

**Goal**: Cached responses enable interrupted runs to resume without re-calling the AI, and `--refresh` forces re-analysis

**Independent Test**: Run against 20 ideas, interrupt at 10, re-run — verify second run skips the first 10 and only calls AI for remaining 10.

### Implementation for User Story 6

- [X] T031 [US6] Add cache statistics to `main()` output: on startup, count existing cache files in `data/mist_ideas_cache/`, log `Cached: N / Total: M — will analyze K new ideas`, display cache hit/miss per idea during progress output
- [X] T032 [US6] Implement `--refresh` flag behavior: when set, `analyze_idea()` skips cache lookup and always calls the AI, overwrites existing cache files. Log `[REFRESH] Re-analyzing: <title>` instead of `[CACHED] Skipping: <title>`
- [X] T033 [US6] Handle corrupt cache gracefully: in `load_cached_response()`, validate that loaded JSON contains required fields (`classification`, `rationale`); if missing, return None (triggers re-analysis) and log warning with the cache file path

**Checkpoint**: Cache is fully operational — runs resume from interruption, `--refresh` forces re-analysis, corrupt caches self-heal.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Error handling hardening, edge cases, documentation

- [X] T034 [P] Handle edge case: empty or malformed CSV exits cleanly with descriptive error, no partial output written (FR-013, US5 acceptance scenario 5)
- [X] T035 [P] Handle edge case: AI returns classification not in the enum set — retry once with a reminder prompt; on second failure, default to UNCLASSIFIED with warning
- [X] T036 [P] Handle edge case: blank idea title with non-empty description — use first 80 characters of description as synthetic title, log warning
- [X] T037 [P] Handle edge case: exact character-for-character duplicate CSV rows — deduplicate at parse time (same content_hash), increment demand count
- [X] T038 Ensure all file paths use `pathlib.Path` for cross-platform compatibility (Windows + Linux container)
- [X] T039 [P] Ensure no secrets logged: redact `api_key` value in all log messages (show only last 4 characters); redact `GITHUB_TOKEN` and `AI_API_KEY` at the logging boundary
- [X] T040 Run `python -m py_compile scripts/mist_ideas_analyzer.py` to validate syntax
- [X] T041 Run the script against `mist_ideas.csv` end-to-end and verify all three output files are produced correctly. Measure total elapsed time and validate SC-004 (completes within 10 minutes with a responsive AI API)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. This is the MVP core
- **User Story 2 (Phase 4)**: Depends on US1 (needs `analyze_all()` output)
- **User Story 5 (Phase 5)**: Depends on US2 (needs clusters for report generation)
- **User Story 3 (Phase 6)**: Depends on US5 (extends ReportGenerator with theme sections)
- **User Story 4 (Phase 7)**: Depends on US5 (extends ReportGenerator with snowball sections)
- **User Story 6 (Phase 8)**: Can technically start after Foundational (cache infra in T008), but best done after US1 is stable
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Core MVP — no dependency on other stories
- **US2 (P1)**: Depends on US1 output (per-idea analyses needed for dedup)
- **US5 (P1)**: Depends on US2 output (clusters needed for report)
- **US3 (P2)**: Depends on US5 (adds theme section to existing report)
- **US4 (P2)**: Depends on US5 (adds snowball section to existing report)
- **US6 (P3)**: Independent of US2-US5 but benefits from US1 being stable

### Within Each User Story

- Models/data structures before logic
- Core logic before integration with `main()`
- Story complete before moving to next priority

### Parallel Opportunities

- T005 (AiBackendDetector) and T007 (ApiIndexBuilder) can run in parallel — different classes, no shared state
- T022 (JSON output) and T023 (CSV output) can run in parallel — different files, independent methods
- T034-T037 and T039 (Polish edge cases + secret redaction) can all run in parallel — independent concerns
- US3 (themes) and US4 (snowball chains) can run in parallel once US5 is complete — both extend ReportGenerator independently

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes:

# These Foundational tasks can run in parallel:
Task T005: "AiBackendDetector class"
Task T007: "ApiIndexBuilder class"

# Then US1 tasks run sequentially:
Task T009 → T010 → T011 → T012 → T013 → T014
```

## Parallel Example: Polish Phase

```bash
# All edge case handlers can run in parallel:
Task T034: "Empty CSV handling"
Task T035: "Invalid classification retry"
Task T036: "Blank title fallback"
Task T037: "Exact duplicate rows"
Task T039: "Secret redaction"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 5)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008) — prerequisite for everything
3. Complete Phase 3: US1 — AI classification per idea (T009-T014)
4. **STOP and VALIDATE**: Run against 10-idea sample, verify classifications
5. Complete Phase 4: US2 — Dedup and clustering (T015-T018)
6. Complete Phase 5: US5 — Report generation (T019-T024)
7. **STOP and VALIDATE**: Full end-to-end run, verify all 3 output files
8. Deploy MVP — classification + dedup + report is immediately useful

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. Add US1 → Per-idea AI classification (MVP core)
3. Add US2 → Dedup merging into clusters
4. Add US5 → Three output files with executive summary (MVP complete!)
5. Add US3 → Theme grouping enriches the report
6. Add US4 → Snowball chains show implementation leverage
7. Add US6 → Cache statistics and resume polish
8. Polish → Edge cases, secret redaction, final validation

---

## Notes

- [P] tasks = different files or independent methods, no dependencies
- [Story] label maps task to specific user story for traceability
- All code lives in a single file: `scripts/mist_ideas_analyzer.py`
- All output goes to `data/` directory per MistHelper convention
- The 4th AI backend (Ollama via Podman) is implemented in T006 as part of AiBackendDetector — no separate class needed
- Commit after each phase completion for clean git history
- Stop at any checkpoint to validate independently
