# Feature Specification: Mist Ideas Analyzer

**Feature Branch**: `183-mist-ideas-analyzer`  
**Created**: 2026-04-09  
**Status**: Draft  
**Clarifications**: In progress
**Input**: User description:"generate a script that reads mist_ideas.csv, sends each idea to an AI model for semantic analysis, and produces a structured output report where the AI evaluates the intent behind each idea, classifies whether MistHelper can solve it via API enhancement, identifies duplicates and near-duplicates for merging, groups ideas into themes, and shows snowball chains where one implementation unlocks many others."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Classifies Each Idea by Implementation Feasibility (Priority: P1)

A MistHelper developer runs the analyzer script. For each idea in the CSV, the script sends the title, description, and comments to an AI model. The AI reads the actual intent of the request — not just surface keywords — and responds with a structured classification: whether it is solvable by a MistHelper API enhancement, requires changes to the Mist portal GUI, requires new hardware, or is a mix. The AI writes a one-paragraph rationale in plain English explaining its reasoning.

**Why this priority**: This is the core capability. Without AI-driven classification, every other output is guesswork. The AI understands context a keyword matcher cannot — for example, recognizing that "add a column to the inventory table" is GUI-only, but "include manufacturing date in the inventory report" is API-accessible through the Mist API.

**Independent Test**: Run the script against a 10-idea sample, verify every idea has a classification field and a non-empty AI-generated rationale. Confirm ideas about portal UI layout receive GUI_ONLY and ideas about data export receive REPORT_EXPORT.

**Acceptance Scenarios**:

1. **Given** the CSV has 100 ideas, **When** the script runs, **Then** the AI analyzes each idea individually and every output entry contains a non-empty `classification` and `rationale` field
2. **Given** an idea whose description says "I want to see a new tab in the Mist portal showing client history", **When** the AI analyzes it, **Then** it returns `GUI_ONLY` because the request is exclusively about portal UI layout requiring Mist Engineering to build
3. **Given** an idea requesting a capability the Mist portal already supports today, **When** the AI analyzes it, **Then** it returns `ALREADY_SUPPORTED` with a rationale explaining where in the portal the feature exists
4. **Given** an idea requesting "ability to export the full device inventory including manufacturing date and license expiry to CSV", **When** the AI analyzes it, **Then** it returns `REPORT_EXPORT` because the data is API-accessible and MistHelper already exports inventory CSV
5. **Given** an idea requesting "iperf built into the AP tools screen", **When** the AI analyzes it, **Then** it returns `API_ENHANCEMENT` (the Mist API WebSocket supports sending commands to APs) rather than HARDWARE_FEATURE
6. **Given** an idea whose intent is ambiguous, **When** the AI analyzes it, **Then** it returns `UNCLASSIFIED` with a rationale explaining what additional context would resolve the ambiguity

---

### User Story 2 - AI Identifies Duplicate and Near-Duplicate Ideas for Merging (Priority: P1)

After all ideas are analyzed individually, the AI performs a second pass to identify ideas that express the same underlying request. The AI understands semantic similarity — two ideas worded very differently can still be asking for the same thing. The script merges confirmed duplicates into a single cluster, preserves the best-worded version as the canonical title, and records all merged originals.

**Why this priority**: The Mist Ideas portal accumulates years of submissions. The same request (e.g., "custom admin roles") appears under dozens of different titles. Merging reveals true demand signal and prevents developers from treating ten instances of the same request as ten separate work items.

**Independent Test**: Provide five ideas — two saying "custom admin role" in different words, two saying "helpdesk can bounce ports" in different words, and one unrelated. Verify the output has three clusters (not five) with correct membership.

**Acceptance Scenarios**:

1. **Given** two ideas that phrase the same request differently, **When** the AI compares them, **Then** they appear as a single merged cluster in the output with a combined submission count
2. **Given** a merged cluster, **When** viewed in the output, **Then** all original idea titles are listed under the cluster so nothing is lost
3. **Given** ideas that are related but address different aspects (e.g., "export inventory" vs. "export client list"), **When** compared, **Then** they remain separate clusters but appear in the same theme group
4. **Given** a cluster of merged ideas, **When** classified, **Then** the AI uses the union of all merged ideas' content to determine the classification — not just the canonical title
5. **Given** the AI is uncertain whether two ideas are truly duplicates, **When** output, **Then** they appear as separate clusters with a `possible_duplicate_of` cross-reference note rather than a forced merge

---

### User Story 3 - AI Groups Ideas into Named Theme Clusters (Priority: P2)

After individual analysis and deduplication, the AI groups idea clusters into named themes. The AI derives theme names from actual content — it does not use a predefined hardcoded list. Themes emerge from what the ideas actually discuss. Ideas may appear under more than one theme if they span multiple domains.

**Why this priority**: Theme clusters show which domains have the most demand and where a single development sprint could address the most requests. A developer can look at the "Reporting & Exports" cluster and see 15 ideas addressed by 3 new menu operations.

**Independent Test**: Run against the full CSV and verify the output contains recognizable theme names matching the actual content (e.g., a theme covering firmware ideas should not be named "Network Management" generically but something like "Firmware & Upgrade Management").

**Acceptance Scenarios**:

1. **Given** all idea clusters, **When** the AI assigns themes, **Then** each cluster has at least one theme assignment and no cluster is left without a theme
2. **Given** ideas about firmware upgrades, rollback, and version management, **When** themed, **Then** they all appear under a theme whose name clearly indicates firmware or upgrade management
3. **Given** an idea that spans RBAC (role-based access control) and switch port management, **When** themed, **Then** it appears under both an access-control theme and a switch-management theme with both listed in the output
4. **Given** the output, **When** reviewed, **Then** each theme section shows: theme name, count of clusters, count of original ideas (pre-merge), and sorted list of clusters by demand (highest first)

---

### User Story 4 - AI Identifies Snowball Chains (Priority: P2)

The AI identifies ideas where implementing one creates the data access pattern, code structure, or API knowledge that makes implementing several related ideas significantly easier. These "snowball chains" are shown in the output as directed relationships: foundational idea → list of ideas it unlocks, with the AI's explanation of the shared capability basis.

**Why this priority**: MistHelper has already demonstrated this pattern internally — adding one API pagination helper accelerated five subsequent menu operations. Formalizing this for the ideas backlog lets the team plan sprint order to maximize compound velocity.

**Independent Test**: Verify that ideas sharing the same Mist API endpoint family (e.g., all ideas requiring `listOrgDevices` data) are connected in the snowball chain output with that shared API pattern identified as the basis.

**Acceptance Scenarios**:

1. **Given** a set of ideas that all require reading the same type of API data, **When** the AI identifies snowball chains, **Then** the foundational idea (the one that establishes the pattern) is marked as the chain head with the others listed as unlocked by it
2. **Given** a snowball chain in the output, **When** reviewed, **Then** it shows: the foundational idea title, a plain-English explanation of why it is foundational, and an ordered list of ideas it unlocks with a brief note on what each shares
3. **Given** an idea with no identified snowball relationship, **When** output, **Then** it appears without a snowball annotation rather than being incorrectly linked

---

### User Story 5 - Generate Structured, Prioritized Output Report (Priority: P1)

The script produces a single Markdown output file. The file opens with an executive summary (total ideas, classification breakdown, theme count, top 5 highest-demand clusters), followed by sections for each classification tier. Within each tier, ideas are sorted by demand. The AI's analysis is preserved verbatim in each entry so a human reader understands the reasoning without needing to re-run the analysis.

**Why this priority**: The output is the only deliverable a developer interacts with. Without it being well-structured and immediately actionable, the entire analysis is wasted.

**Independent Test**: Run the script and verify the output file opens in a Markdown viewer, contains the executive summary, has clearly delineated classification sections, and each idea entry includes: canonical title, classification, theme(s), demand count, AI rationale, and any snowball annotations.

**Acceptance Scenarios**:

1. **Given** analysis is complete, **When** the output file is opened, **Then** the first section is an executive summary with total ideas processed, count per classification, count of unique themes, and the top 5 clusters by demand
2. **Given** the output file, **When** reviewed, **Then** sections appear in this order: API-solvable (REPORT_EXPORT first, then API_ENHANCEMENT), HYBRID, GUI_ONLY, HARDWARE_FEATURE, UNCLASSIFIED
3. **Given** a cluster entry in the output, **When** reviewed, **Then** it contains: canonical title, classification badge, theme list, demand count (original submissions merged), AI-generated rationale paragraph, MistHelper enhancement suggestion (for API-solvable ideas), and snowball chain reference if applicable
4. **Given** the script encounters an AI API error for a specific idea, **When** that happens, **Then** the idea still appears in the output marked as UNCLASSIFIED with a note that AI analysis failed, and script execution continues for all remaining ideas
5. **Given** the analyzer runs against an empty or malformed CSV, **When** it completes, **Then** it exits cleanly with a descriptive error message and no partial output file is written

---

### User Story 6 - Resume and Cache AI Responses (Priority: P3)

Because AI API calls cost money and take time, the script caches each idea's AI response to a local file after the first analysis. On subsequent runs, cached responses are used instead of re-calling the AI. This allows the script to be interrupted and resumed without losing progress or incurring duplicate API costs.

**Why this priority**: A full run against hundreds of ideas may take several minutes and cost non-trivial API credits. A cache ensures re-runs for report format changes are free and instant.

**Independent Test**: Run the script against 20 ideas, interrupt it at 10, re-run — verify the second run skips the first 10 (uses cache) and only calls the AI for the remaining 10.

**Acceptance Scenarios**:

1. **Given** an idea that has already been analyzed, **When** the script runs again, **Then** the cached response is used and no API call is made for that idea
2. **Given** the user passes a `--refresh` flag, **When** the script runs, **Then** all cached responses are ignored and the AI is called fresh for every idea
3. **Given** a cached response that is malformed or corrupted, **When** the script encounters it, **Then** it discards the cache entry, re-calls the AI, and logs a warning

---

### Edge Cases

- What happens when the AI returns a classification not in the expected set?
- What happens when an idea's description is in a non-English language? The AI handles non-English ideas best-effort; no language detection or translation is performed. If the AI's confidence is low, it will indicate so in the `confidence` field
- What if an idea title is blank but the description contains useful content?
- What if the AI API rate limit is hit mid-run?
- What if two ideas are exact character-for-character duplicates in the CSV?
- What if the ideas CSV has been updated with new columns since the script was last run? Extra CSV columns beyond position 2 are silently ignored; the parser uses positional indexing only (columns 0-2)
- What happens when all ideas in a theme cluster are GUI_ONLY — does the theme still appear?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The script MUST accept the mist_ideas.csv file path as a command-line argument, defaulting to `mist_ideas.csv` in the current working directory
- **FR-002**: The script MUST parse each CSV row extracting: title, description/body, and comments (as structured text flattened from JSON)
- **FR-003**: For every idea, the script MUST submit title + description + comments to an AI model and receive back a structured response containing: classification, theme suggestions, duplicate candidates, MistHelper enhancement note, and rationale
- **FR-004**: The AI prompt MUST include a system context section that explains what MistHelper is, what counts as GUI-only, and the classification labels. For each idea, the script MUST also inject the most relevant endpoint summaries extracted from the local OpenAPI spec so the AI's feasibility judgment is grounded in documented endpoints rather than training-data guesses
- **FR-004a**: On first run (or when `--refresh-index` is passed), the script MUST pre-index `documentation/mist-api-openapi3json.json` into a lightweight lookup structure (endpoint path + HTTP method + summary + tags) stored in `data/mist_ideas_cache/api_index.json`. This index is used for keyword matching to retrieve candidate endpoints before each AI call
- **FR-005**: The script MUST cache each idea's AI response locally (keyed by a hash of the idea content) and reuse cached responses on subsequent runs unless `--refresh` is passed
- **FR-006**: The script MUST perform a second AI pass to identify duplicate and near-duplicate ideas across the full set, producing merge recommendations. The duplicate threshold is **moderate**: ideas asking for the exact same underlying capability (even if worded differently) should be merged; ideas that share a topic area but address different specific capabilities must remain separate clusters. The AI should express uncertainty as a `possible_duplicate_of` cross-reference rather than a forced merge
- **FR-007**: The script MUST merge confirmed duplicates into clusters and retain all original titles as members
- **FR-008**: The script MUST produce three output files in the `data/` directory:
  - `mist_ideas_analysis.md` — primary human-readable Markdown report
  - `mist_ideas_analysis.json` — machine-readable JSON with the full structured analysis (all clusters, themes, snowball chains, and per-idea AI responses)
  - `mist_ideas_analysis.csv` — flat CSV with one row per idea cluster (canonical title, classification, demand count, themes as pipe-separated string, AI rationale)
- **FR-009**: The output report MUST open with an executive summary and present ideas in this order: REPORT_EXPORT → API_ENHANCEMENT → HYBRID → GUI_ONLY → HARDWARE_FEATURE → ALREADY_SUPPORTED → UNCLASSIFIED, followed by a dedicated **AI Inspired Ideas** section listing all AI_INSPIRED entries separately from customer ideas
- **FR-010**: Within each classification section, idea clusters MUST be sorted by demand count (descending)
- **FR-011**: The script MUST include a snowball chain section identifying foundational ideas and the clusters they unlock
- **FR-012**: The script MUST handle AI API errors per-idea gracefully: log a warning, mark the idea UNCLASSIFIED, and continue processing
- **FR-013**: Malformed or incomplete CSV rows MUST be skipped with a logged warning; script MUST NOT crash on bad input
- **FR-014**: The script MUST display a progress indicator showing how many ideas have been analyzed vs. total during the AI pass
- **FR-016**: During per-idea analysis, if the AI identifies a valuable feature opportunity that neither the Mist portal GUI nor MistHelper currently supports, it MUST record it as an AI_INSPIRED entry. The original customer idea is preserved unchanged. The AI_INSPIRED entry must include: a generated title, the AI's description of the feature, the classification AI_INSPIRED, the source idea title that inspired it, and a rationale explaining why neither existing solution addresses it
- **FR-015**: The script MUST auto-detect which AI backend is available using this priority chain, checking `.env` for the relevant credentials:
  1. **GitHub Models** (VS Code AI integration): if `GITHUB_TOKEN` is set, use `https://models.inference.ai.azure.com` with the OpenAI Python library; model defaults to `gpt-4o-mini` but is overridable via `AI_MODEL`
  2. **AVA MCP HTTP endpoint**: if `AVA_API_URL` is set, use that base URL with the OpenAI Python library; model defaults to `llama3.3` but is overridable via `AI_MODEL`
  3. **Generic OpenAI-compatible fallback**: if `AI_API_KEY` is set (with optional `AI_API_BASE_URL`), use that; model defaults to `gpt-4o-mini` but is overridable via `AI_MODEL`
  4. **Local Ollama via Podman**: if none of the above are configured (or if `OLLAMA_ENABLED=true` is set), the script auto-provisions a local Ollama instance in Podman with GPU passthrough. The script queries local GPU specs (VRAM capacity) and selects the best-fitting model automatically. Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1`, so the same `openai` library is used. Model selection is automatic based on VRAM but overridable via `AI_MODEL`
  - No credentials may be hardcoded; all must come from `.env`
  - On startup the script MUST print which AI backend it selected and which model it will use
- **FR-017**: When the Ollama backend is selected, the script MUST:
  1. Detect the container runtime (Podman preferred, Docker fallback) and verify it is available
  2. Query local GPU specs: on Windows via `nvidia-smi` or WMI; on Linux via `nvidia-smi` or `/proc/driver/nvidia/`
  3. Select the largest model that fits in available VRAM using a built-in model-to-VRAM mapping (e.g., 6-8GB → `llama3.1:8b`, 10-12GB → `mistral:7b-instruct-q8`, 16GB+ → `mistral:7b-instruct-q8`, 24GB+ → `mixtral:8x7b-instruct-q4`, no GPU → `llama3.2:3b` CPU-only with warning)
  4. Check if the Ollama container is already running; if not, start it with GPU passthrough (`--device nvidia.com/gpu=all` for Podman or `--gpus all` for Docker)
  5. Pull the selected model if not already present in the container
  6. Log the detected GPU, VRAM, selected model, and container runtime at Info level

### AI Prompt Design Requirements

- **PR-001**: The system prompt MUST define MistHelper as a Python script that *calls* the existing Mist REST API — it extracts data to CSV/SQLite, manages firmware upgrades, sends device commands via WebSocket, and runs SSH against devices; it is a client, not the API itself
- **PR-002**: The system prompt MUST define what MistHelper CANNOT do: modify the Mist portal GUI, add new API endpoints to Mist Cloud, enable new hardware capabilities, or change any behavior that requires Mist Engineering to modify their backend. The prompt MUST also instruct the AI that ideas phrased as "add a column to the portal" or "show X in the GUI" are NOT automatically GUI_ONLY — if the underlying data is accessible via an existing documented Mist REST API endpoint, MistHelper can retrieve and present it through a new menu operation or CSV/report export, making it API_ENHANCEMENT or REPORT_EXPORT rather than GUI_ONLY
- **PR-003**: The user prompt per idea MUST include: idea title, full description text, and all comment text (author + content), clearly delimited
- **PR-004**: The AI response MUST be requested as structured JSON to enable reliable parsing
- **PR-005**: The AI response schema MUST include: `classification` (enum: REPORT_EXPORT | API_ENHANCEMENT | HYBRID | GUI_ONLY | HARDWARE_FEATURE | ALREADY_SUPPORTED | UNCLASSIFIED), `confidence` (high/medium/low), `themes` (list of strings), `rationale` (string), `misthelper_enhancement` (string describing the operation type and capability area in plain English, or null if not applicable — no specific endpoint URL required), `possible_duplicate_titles` (list of strings), `is_foundational` (bool), `unlocks` (list of strings), `ai_inspired_ideas` (list of objects, each with `title`, `description`, `source_idea_title`, `rationale` — AI-generated feature ideas inspired by this customer idea but not present in the original request; may be empty list)

### Key Entities

- **Idea**: A single community request with title, description body, and comments list — the raw input unit
- **IdeaAnalysis**: The AI's structured response for one Idea — classification, themes, rationale, enhancement suggestion, duplicate hints
- **IdeaCluster**: One or more Ideas merged as duplicates, with one designated canonical; demand count equals sum of all members
- **ThemeGroup**: Named grouping of IdeaClusters sharing a domain; name is AI-generated from actual content
- **SnowballChain**: Directed relationship from a foundational IdeaCluster to the IdeaClusters it unlocks, with shared capability basis described by the AI
- **AnalysisCache**: Local store of (content-hash → IdeaAnalysis) enabling runs to skip already-analyzed ideas
- **ApiIndex**: Pre-built lookup from `mist-api-openapi3json.json` mapping tags and keywords to endpoint summaries; injected into AI prompts to ground feasibility verdicts
- **AiInspiredIdea**: A net-new feature idea generated by the AI (not submitted by a customer) during analysis of a customer idea; attributed as AI-generated, linked to the source idea that prompted it, and listed in a dedicated output section

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of parseable ideas receive an AI-generated classification and rationale in the output — no idea is silently dropped
- **SC-002**: A resumed run (after interruption) reuses cached responses such that re-analysis API calls are proportional only to the number of new or changed ideas
- **SC-003**: The executive summary alone gives a developer enough information to identify the top 5 highest-demand API-solvable ideas without reading further
- **SC-004**: The script processes the full mist_ideas.csv (estimated 50–200 ideas) and produces a complete output report within 10 minutes on a standard developer machine with a responsive AI API
- **SC-005**: At least 75% of classified ideas in the API-solvable categories include a concrete `misthelper_enhancement` suggestion that names the operation type (e.g., "new export menu item", "new WebSocket command") and describes the capability area in plain English — it does not need to name a specific endpoint URL, as that is discoverable during implementation
- **SC-006**: All three output files are produced correctly: the Markdown renders in GitHub's Markdown viewer, the JSON is valid parseable JSON (verified with `json.loads()`), and the CSV opens correctly in a spreadsheet with one row per cluster
- **SC-007**: Duplicate/near-duplicate clustering reduces the total cluster count to meaningfully fewer entries than the raw idea count, demonstrating the AI identified real patterns rather than treating every idea as unique

## Assumptions

- MistHelper is a caller of the Mist REST API, not a builder of it; all enhancement suggestions in the output refer to new MistHelper script operations, not changes to the Mist API itself
- The script uses an externally configured AI API (e.g., OpenAI, Anthropic, or compatible endpoint) set via environment variables; the project does not mandate a specific provider
- The mist_ideas.csv columns are: title (column 1), description/body (column 2), comments as JSON array (column 3) — matching the format currently in the repository
- Classification is the AI's best judgment based on available text; a human reviewer may override classifications without re-running the full analysis
- "API-accessible" means the existing documented Mist REST API already exposes what is needed; features requiring unreleased or undocumented Mist endpoints are classified UNCLASSIFIED or HYBRID
- The permanently standalone utility (`scripts/mist_ideas_analyzer.py`) — it is never integrated into MistHelper's main interactive menu and is invoked directly via `python scripts/mist_ideas_analyzer.py`
- The ideas dataset spans from 2018 to present; a significant portion of ideas are expected to be duplicates of each other (same request submitted by different users over the years) or ALREADY_SUPPORTED (features that were implemented by Mist Engineering since the idea was originally submitted); the deduplication pass and ALREADY_SUPPORTED classification are specifically designed to surface both patterns
- The AI performs the deduplication comparison pass as a second prompt against a condensed list of all idea titles and short summaries (not individually re-sending full content for every pairwise comparison)
- Comment data is included in the AI prompt as supporting evidence to help clarify intent — not treated as separate feature requests
- The cache is stored in `data/mist_ideas_cache/` as individual JSON files keyed by content hash

## Clarifications

### Session 2026-04-09

- Q: Are we building or modifying the Mist API, or calling the existing one? → A: MistHelper is strictly a client script that calls the existing Mist REST API. We are not building or adding to the Mist API itself. All "API_ENHANCEMENT" classifications mean MistHelper can add a new menu operation that calls an already-existing Mist endpoint.
- Q: Which AI provider should the analyzer script use? → A: Prefer the VS Code AI integration (GitHub Models API — accessible via a GitHub PAT at `https://models.inference.ai.azure.com`, OpenAI-compatible). If that is not available/configured, fall back to the AVA MCP HTTP endpoint (also OpenAI-compatible, Juniper-internal). If neither is available, fall back to any configured OpenAI-compatible API. Auto-detect based on which credentials are present in `.env`.
- Q: How should the script determine if an idea is actually feasible via the Mist API? → A: Ground feasibility in the local OpenAPI documentation already present in the repository. Specifically: `documentation/mist-api-openapi3json.json` (714 endpoints, 1682 schemas, 15.7 MB) and the structured human-readable API reference under `documentation/api/` (organised by `orgs/`, `sites/`, `admins/`, etc.). The script must parse or pre-index this local spec and inject relevant endpoint summaries into the AI prompt for each idea, so the AI's feasibility verdict is grounded in documented reality rather than training-data assumptions.
- Q: Should the script produce only Markdown or additional machine-readable formats? → A: All three: Markdown primary report (`mist_ideas_analysis.md`), JSON sidecar (`mist_ideas_analysis.json`), and CSV sidecar (`mist_ideas_analysis.csv`).
- Q: If a user asks for something described as a GUI change, can MistHelper still help via the API? → A: Yes. Many ideas are phrased as "show this in the portal" or "add a column to the GUI" but the underlying data is already available via the Mist REST API. MistHelper can retrieve and export that data via a script/automation. The AI must NOT classify as GUI_ONLY solely because the request mentions a portal view or column — it must evaluate whether the underlying data is API-accessible and whether MistHelper could expose it through a new menu operation or report export.
- Q: How strict should the duplicate/near-duplicate threshold be for merging ideas? → A: Moderate — merge only ideas asking for the exact same underlying capability, even if worded differently. Ideas that are in the same topic area but address different specific capabilities remain separate clusters.
- Q: What if the AI is inspired by a customer idea to conceive a feature that neither the Mist GUI nor MistHelper currently supports? → A: The AI should record it as a separate AI_INSPIRED entry. The original customer idea is preserved unchanged with its own classification. The AI_INSPIRED entry is a net-new feature idea generated by the AI, attributed as AI-generated (not a customer submission), and listed in its own dedicated section of the output report.
- Q: How specific should the `misthelper_enhancement` suggestion be? → A: Between vague and exact. The AI should name the operation type (e.g., "new export", "new WebSocket command", "new inventory report") and describe the capability area in plain English (e.g., "retrieve per-port RADIUS assignment details"). It does NOT need to name a specific endpoint URL — the exact endpoint can be discovered during implementation using the local OpenAPI spec.
- Q: Should the analyzer ever be callable from MistHelper's main interactive menu? → A: No — permanently standalone. It is a developer utility script (`scripts/mist_ideas_analyzer.py`) and will never be integrated into the MistHelper menu system.
- Q: How should the AI classify ideas the Mist portal already supports natively (no build needed)? → A: Add ALREADY_SUPPORTED as a distinct classification label with its own output section. This is meaningfully different from GUI_ONLY (which requires Mist Engineering to build a GUI change) — ALREADY_SUPPORTED means the capability exists today and the idea can be closed with a "here's how" response.
- Q: What if no cloud AI credentials are available? → A: The script can self-host a local LLM using Ollama in a Podman container with GPU passthrough. The script auto-detects available GPU VRAM and selects the best-fitting model. This is the 4th and final backend in the priority chain (after GitHub Models, AVA MCP, and Generic). Can also be forced via `OLLAMA_ENABLED=true` even when cloud credentials exist. Podman is preferred (already in use for MistHelper containers); Docker is a compatible fallback.

## Dependencies

- At least one of the following: cloud AI credentials in `.env` (`GITHUB_TOKEN`, `AVA_API_URL`, or `AI_API_KEY`), OR a local GPU with Podman/Docker installed for Ollama self-hosting
- `AI_MODEL` env var (optional) to override the default model for whichever backend is selected
- `OLLAMA_ENABLED=true` env var (optional) to force Ollama backend even when cloud credentials are present
- OpenAI Python library (`openai>=1.0`) — works with all four backends since all expose an OpenAI-compatible API surface
- Podman (preferred) or Docker — required only for the Ollama backend; already available in the project environment
- Local Mist API documentation already present in the repository:
  - `documentation/mist-api-openapi3json.json` — 714 endpoints, 1682 schemas (primary feasibility ground truth)
  - `documentation/api/` directory — human-readable structured reference (supplementary context)
- Existing `mist_ideas.csv` file in the MistHelper repository
- MistHelper's existing `dotenv` loading pattern for secrets
- No Mist Cloud API calls are required — this is a local text analysis pipeline
