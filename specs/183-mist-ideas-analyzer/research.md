# Research: Mist Ideas Analyzer

**Feature**: 183-mist-ideas-analyzer | **Date**: 2026-04-09

## R1: OpenAI Structured JSON Output

**Decision**: Use `response_format={"type": "json_object"}` as the baseline (broadest model compatibility). Include the full JSON schema in the system prompt so the model knows what to produce. Validate parsed JSON against the expected schema in Python; retry once with a reminder if parsing fails.

**Rationale**: The `json_schema` strict mode (`response_format={"type": "json_schema", ...}`) guarantees schema adherence but requires all properties to be `required` (no optional fields) and is only supported on gpt-4o-mini and gpt-4o. Since we support 3 backends (GitHub Models, AVA MCP, generic), not all may support strict mode. `json_object` mode is safer and broader. We compensate by validating in Python and retrying.

**Alternatives considered**:
- Structured Outputs with `strict: true` — narrower model support, complicates AVA MCP fallback
- Function calling — designed for tool use, not response formatting
- Manual parsing with regex — fragile, unnecessary when json_object mode is available

## R2: Rate Limiting and Retry Strategy

**Decision**: Use exponential backoff with jitter on HTTP 429. Base delay 2 seconds, multiply by 2^attempt, add random jitter ±10%. Maximum 3 retries per idea. Between ideas, add a configurable inter-request delay (default 0.5 seconds) to stay under rate limits proactively.

**Rationale**: GitHub Models free tier has modest rate limits (~15-150 RPM depending on model). The `openai` library has built-in retry for 429/408/5xx (2 retries by default), so our retry logic layers on top for cache-miss scenarios. The inter-request delay prevents burst patterns that trigger rate limiting in the first place.

**Alternatives considered**:
- No delay (burst all requests) — hits rate limits immediately on 100+ ideas
- Token bucket / sliding window — overengineered for sequential per-idea processing
- Batch API — not available on GitHub Models free tier

## R3: Content Hashing for Cache Keys

**Decision**: SHA256 on normalized `(title + "\n" + description + "\n" + comments_json)`. Normalize by collapsing whitespace runs to single space, stripping leading/trailing whitespace, and lowercasing. Store as `{hex_digest}.json` in `data/mist_ideas_cache/`.

**Rationale**: SHA256 is standard, collision-resistant, and produces 64-character filenames. Normalization ensures that trivial formatting differences (extra spaces, case changes) don't create duplicate cache entries. The newline separator between fields prevents hash collisions from field boundary shifts (e.g., title="AB" + desc="C" vs title="A" + desc="BC").

**Alternatives considered**:
- MD5 — known collision vulnerabilities, no performance advantage over SHA256 in Python
- Blake2 — marginally faster, less universally recognized, unnecessary for this scale
- Title-only hash — insufficient; same title could have different descriptions across submissions

## R4: CSV Parsing Strategy

**Decision**: Use `csv.reader()` with `newline=''` and `encoding='utf-8'`. Since the CSV has no header row, access fields by index: `[0]=title`, `[1]=description`, `[2]=comments`. Parse the comments field as JSON after CSV extraction. Handle `json.JSONDecodeError` gracefully (log warning, set comments to empty list).

**Rationale**: Python's `csv` module handles RFC 4180 correctly — quoted fields, multiline content, embedded commas, escaped quotes. The `newline=''` parameter is critical on Windows to prevent universal newline translation from corrupting multiline fields. Parsing JSON post-extraction is clean and avoids any CSV/JSON delimiter confusion.

**Alternatives considered**:
- `csv.DictReader` with `fieldnames` — adds overhead since we only have 3 positional columns
- `pandas.read_csv()` — heavy dependency for a simple 3-column CSV
- Manual line splitting — fragile for quoted fields with embedded newlines

## R5: Deduplication Batch Strategy

**Decision**: Send all titles (with short description excerpts) in a single LLM request. For 200 ideas at ~10 words per title plus ~20 words of description excerpt, the total is approximately 6,000 input tokens — well within gpt-4o-mini's 128K context window. Use LLM-based deduplication (not embeddings) for higher semantic accuracy.

**Rationale**: A single request is faster (one API call vs. many) and cheaper (one prompt overhead). LLM-based dedup with 95%+ accuracy outperforms embedding cosine similarity (~85-90%) for catching subtle reformulations, which is critical given the 2018-present dataset where users phrase the same request differently.

**Alternatives considered**:
- Chunked batches of 50 — unnecessary below 200 ideas, adds complexity
- Embedding-based (text-embedding-3-small + cosine threshold) — cheaper but misses contextual nuance
- Hybrid (embeddings pre-filter + LLM confirm) — optimal for 1000+ ideas but over-engineered for 50-200

## R6: Local Ollama via Podman with GPU Auto-Detection

**Decision**: Use `subprocess.run()` to call `nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits` for GPU VRAM detection. Map VRAM to best-fit model using a built-in lookup table. Manage the Ollama container via Podman CLI (`podman run`, `podman exec`, `podman ps`). Ollama exposes `http://localhost:11434/v1` as an OpenAI-compatible endpoint, so the same `openai` library handles all communication.

**Model-to-VRAM Mapping** (conservative, leaves headroom for KV cache):
- 6-8 GB VRAM: `llama3.1:8b` (4.7 GB)
- 10-12 GB VRAM: `mistral:7b-instruct-q8` (7.7 GB) or `llama3.1:8b`
- 16+ GB VRAM: `llama3.1:70b-q4_K_M` (requires ~40 GB, so realistically `mixtral:8x7b-instruct-q4` at ~26 GB for 32+ GB) — for 16 GB, stick with `mistral:7b-instruct-q8`
- 24+ GB VRAM: `mixtral:8x7b-instruct-q4` (26 GB)
- No NVIDIA GPU detected: fall back to CPU-only `llama3.2:3b` (small enough for CPU inference) with a warning about slow performance

**Container Management**:
- Check if container `ollama-misthelper` already exists and is running → reuse
- If not running: `podman run -d --name ollama-misthelper --device nvidia.com/gpu=all -p 11434:11434 docker.io/ollama/ollama`
- Docker fallback: replace `--device nvidia.com/gpu=all` with `--gpus all`
- Pull model: `podman exec ollama-misthelper ollama pull <model>`
- Health check: GET `http://localhost:11434/api/tags` before sending analysis requests
- Container is NOT auto-stopped after the script finishes (user may want to re-run)

**Rationale**: Podman is already the primary container runtime for MistHelper. Using `nvidia-smi` for GPU detection is universal across Windows and Linux NVIDIA drivers. The model mapping is conservative to avoid OOM kills. Ollama's OpenAI-compatible endpoint means zero code changes to the AI client — only the base URL and model name change.

**Alternatives considered**:
- vLLM — more performant for batch inference but much heavier setup, no simple container story
- llama.cpp directly — requires building per-platform binaries; Ollama wraps this cleanly
- Run Ollama natively (not in container) — less isolated, conflicts with system-level Ollama installs
- Detect AMD GPUs via `rocm-smi` — deferred; NVIDIA is the primary target given MistHelper's user base

## Summary

| Topic | Decision | Key Detail |
| - | - | - |
| JSON Output | `json_object` mode + Python validation | Broadest model compatibility; retry once on parse failure |
| Rate Limiting | Exponential backoff + 0.5s inter-request delay | 3 retries max; catches 429 and 5xx |
| Hashing | SHA256 on normalized title+desc+comments | Newline separator prevents field-boundary collisions |
| CSV Parsing | `csv.reader()` with `newline=''` | JSON comments parsed post-extraction |
| Dedup Batching | Single LLM request for all titles | ~6K tokens for 200 ideas; LLM-based for accuracy |
| Local Ollama | Podman container + `nvidia-smi` GPU detection | Auto-selects model by VRAM; OpenAI-compatible API reuse |
