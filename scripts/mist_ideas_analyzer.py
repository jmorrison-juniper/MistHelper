#!/usr/bin/env python3
"""Mist Ideas Analyzer — AI-powered classification of Mist community ideas.

Reads mist_ideas.csv, sends each idea to an AI model for semantic analysis
using the OpenAI-compatible API, and produces three output files (Markdown,
JSON, CSV). The AI classifies each idea by MistHelper feasibility using 7
labels + AI_INSPIRED, identifies duplicates, groups into themes, and discovers
snowball dependency chains.

Usage:
    python scripts/mist_ideas_analyzer.py [--input PATH] [--refresh]
        [--refresh-index] [--verbose] [--batch-size N]
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import queue
import random
import shutil
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CLASSIFICATIONS = frozenset({
    "REPORT_EXPORT",
    "API_ENHANCEMENT",
    "HYBRID",
    "GUI_ONLY",
    "HARDWARE_FEATURE",
    "ALREADY_SUPPORTED",
    "UNCLASSIFIED",
})

VALID_CONFIDENCE = frozenset({"high", "medium", "low"})

INTER_REQUEST_DELAY = 0.5
RETRY_BASE_DELAY = 2.0
MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 15
RATE_LIMIT_WAIT = 60
DAILY_LIMIT_THRESHOLD = 3600


class DailyLimitExhausted(Exception):
    """Raised when the daily API quota is exhausted."""

# Model catalog: sorted best-to-worst quality. Each entry includes the
# approximate VRAM footprint (GB) and context-window size (tokens) so the
# provisioner can pick the highest-quality model that fits 100 % in VRAM
# while still meeting our prompt requirements (~2 400 tokens per request).
# VRAM footprints assume OLLAMA_SCHED_SPREAD=1 (MoE experts offloaded to CPU RAM)
# and OLLAMA_KV_CACHE_TYPE=q8_0 (KV cache halved vs fp16 default).
# Mixtral 8x7b drops from ~26 GB to ~10 GB GPU VRAM with both flags active;
# the expert weights (~16 GB) move to system RAM, q8_0 KV cache saves ~2 GB
# at 32K context vs the fp16 default.
MODEL_CATALOG: list[dict] = [
    {"name": "mixtral:8x7b",              "vram_gb": 10.0, "context": 32768, "quality": 1},
    {"name": "mistral:7b-instruct-q8_0",  "vram_gb":  7.8, "context": 32768, "quality": 2},
    {"name": "qwen2.5:7b-instruct",       "vram_gb":  4.7, "context": 32768, "quality": 3},
    {"name": "qwen3:8b",                  "vram_gb":  4.9, "context": 32768, "quality": 4},
    {"name": "mistral:7b",                "vram_gb":  4.1, "context": 32768, "quality": 5},
    {"name": "llama3.1:8b",               "vram_gb":  5.0, "context": 131072, "quality": 6},
    {"name": "gemma3:4b-it-qat",          "vram_gb":  2.5, "context":  8192, "quality": 7},
    {"name": "llama3.2:3b",               "vram_gb":  2.0, "context":  8192, "quality": 8},
]
MIN_CONTEXT_REQUIRED = 4096
CPU_FALLBACK_MODEL = "llama3.2:3b"

# Legacy mapping used only by the local single-server nvidia-smi path.
# Thresholds reflect MoE-on-CPU + q8_0 KV cache: Mixtral now fits in 12 GB.
VRAM_MODEL_MAP = [
    (12_000, "mixtral:8x7b"),
    (10_000, "mistral:7b-instruct-q8_0"),
    (6_000, "llama3.1:8b"),
]

OLLAMA_CONTAINER = "ollama-misthelper"
OLLAMA_PORT = 11434
OLLAMA_HEALTH_TIMEOUT = 30
OLLAMA_HEALTH_RETRIES = 3
OLLAMA_HEALTH_INTERVAL = 5
MIN_GPU_PERCENT = 50
MODEL_PULL_TIMEOUT = 5400  # 90 min -- enough for mixtral:8x7b (26 GB) on a slow LAN
MODEL_LOAD_TIMEOUT = 1200
HEALTH_CHECK_PROMPT = "Say OK"
SUBNET_SCAN_TIMEOUT = 0.3
SUBNET_SCAN_THREADS = 64
FLEET_HEALTH_INTERVAL = 30
FLEET_REDISCOVERY_INTERVAL = 120

DATA_DIR = Path("data")
CACHE_DIR = DATA_DIR / "mist_ideas_cache"
OPENAPI_PATH = Path("documentation") / "mist-api-openapi3json.json"

logger = logging.getLogger("mist_ideas_analyzer")


# ---------------------------------------------------------------------------
# CLI & Logging  (T002, T003)
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze Mist Ideas CSV with AI classification",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("mist_ideas.csv"),
        help="Path to CSV file (default: mist_ideas.csv)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore cache and re-analyze all ideas",
    )
    parser.add_argument(
        "--refresh-index",
        action="store_true",
        help="Rebuild the OpenAPI endpoint index",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Ideas per API call (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--servers",
        type=str,
        default="",
        help=(
            "Comma-separated Ollama servers (host:port). "
            "Example: localhost:11434,192.168.1.86:11434"
        ),
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Auto-discover Ollama servers on the local subnet",
    )
    parser.add_argument(
        "--scan-range",
        type=str,
        default="",
        help=(
            "CIDR or base IP for subnet scan (default: auto-detect). "
            "Example: 192.168.1.0/24"
        ),
    )
    return parser


def configure_logging(verbose: bool) -> None:
    """Set up ASCII-only logging to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)


def redact_key(value: str) -> str:
    """Show only last 4 characters of a secret."""
    if not value or len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


# ---------------------------------------------------------------------------
# IdeaParser  (T004)
# ---------------------------------------------------------------------------


class IdeaParser:
    """Parse the Mist Ideas CSV into structured idea dicts."""

    def parse(self, csv_path: Path) -> list[dict]:
        """Read CSV and return list of idea dicts with content hashes."""
        ideas: list[dict] = []
        seen_hashes: dict[str, int] = {}

        if not csv_path.exists():
            logger.error("CSV file not found: %s", csv_path)
            return ideas

        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            for row_num, row in enumerate(reader, start=1):
                idea = self._parse_row(row, row_num)
                if idea is None:
                    continue

                content_hash = idea["content_hash"]
                if content_hash in seen_hashes:
                    seen_hashes[content_hash] += 1
                    logger.warning(
                        "Exact duplicate row %d (same as earlier row), "
                        "incrementing demand",
                        row_num,
                    )
                    continue

                seen_hashes[content_hash] = 1
                ideas.append(idea)

        self._apply_demand_counts(ideas, seen_hashes)
        logger.info("Parsed %d unique ideas from %s", len(ideas), csv_path)
        return ideas

    def _parse_row(self, row: list[str], row_num: int) -> dict | None:
        """Parse a single CSV row into an idea dict or None."""
        if len(row) < 2:
            logger.warning("Row %d: too few columns, skipping", row_num)
            return None

        title = row[0].strip()
        description = row[1].strip() if len(row) > 1 else ""
        comments = self._parse_comments(row[2] if len(row) > 2 else "")

        if not title:
            if description:
                title = description[:80]
                logger.warning(
                    "Row %d: blank title, using first 80 chars of description",
                    row_num,
                )
            else:
                logger.warning("Row %d: blank title and description, skipping", row_num)
                return None

        comments_json = json.dumps(comments, sort_keys=True)
        content_hash = self._compute_hash(title, description, comments_json)

        return {
            "title": title,
            "description": description,
            "comments": comments,
            "content_hash": content_hash,
            "demand_count": 1,
        }

    @staticmethod
    def _parse_comments(raw: str) -> list[dict]:
        """Parse the comments JSON field, returning empty list on failure."""
        if not raw.strip():
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            logger.warning("Failed to parse comments JSON, using empty list")
            return []

    @staticmethod
    def _compute_hash(title: str, desc: str, comments_json: str) -> str:
        """SHA256 of normalized title+desc+comments."""
        import re

        def normalize(text: str) -> str:
            return re.sub(r"\s+", " ", text.strip().lower())

        combined = (
            normalize(title) + "\n"
            + normalize(desc) + "\n"
            + normalize(comments_json)
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @staticmethod
    def _apply_demand_counts(
        ideas: list[dict],
        seen_hashes: dict[str, int],
    ) -> None:
        """Set demand_count on ideas with exact duplicates."""
        for idea in ideas:
            idea["demand_count"] = seen_hashes[idea["content_hash"]]


# ---------------------------------------------------------------------------
# AiBackendDetector  (T005, T006)
# ---------------------------------------------------------------------------


class AiBackendDetector:
    """Detect the best available AI backend from environment."""

    def detect(self) -> dict:
        """Return backend config dict or raise RuntimeError."""
        if os.environ.get("AI_BACKEND", "").lower() == "ollama":
            config = self._detect_ollama()
            if config:
                return config

        config = self._try_github_models()
        if config:
            return config

        config = self._try_ava_mcp()
        if config:
            return config

        config = self._try_generic()
        if config:
            return config

        config = self._detect_ollama()
        if config:
            return config

        raise RuntimeError(
            "No AI backend available. Set GITHUB_TOKEN, AVA_API_URL, "
            "AI_API_KEY, or AI_BACKEND=ollama (with Podman/Docker)."
        )

    def _try_github_models(self) -> dict | None:
        """Check for GitHub Models backend."""
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return None
        model = os.environ.get("AI_MODEL", "gpt-4o-mini")
        logger.info(
            "Backend: GitHub Models (model=%s, key=%s)",
            model,
            redact_key(token),
        )
        return {
            "backend": "github_models",
            "base_url": "https://models.inference.ai.azure.com",
            "model": model,
            "api_key": token,
        }

    def _try_ava_mcp(self) -> dict | None:
        """Check for AVA MCP backend."""
        url = os.environ.get("AVA_API_URL", "")
        if not url:
            return None
        model = os.environ.get("AI_MODEL", "llama3.3")
        api_key = os.environ.get("AVA_API_KEY", "ava")
        logger.info(
            "Backend: AVA MCP (model=%s, url=%s)",
            model,
            url,
        )
        return {
            "backend": "ava_mcp",
            "base_url": url,
            "model": model,
            "api_key": api_key,
        }

    def _try_generic(self) -> dict | None:
        """Check for generic OpenAI-compatible backend."""
        api_key = os.environ.get("AI_API_KEY", "")
        if not api_key:
            return None
        base_url = os.environ.get(
            "AI_API_BASE_URL",
            "https://api.openai.com/v1",
        )
        model = os.environ.get("AI_MODEL", "gpt-4o-mini")
        redacted = redact_key(api_key)
        logger.info(
            "Backend: Generic OpenAI (model=%s, key=%s)",
            model,
            redacted,
        )
        return {
            "backend": "generic",
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
        }

    def _detect_ollama(self) -> dict | None:
        """Detect and start local Ollama via Podman/Docker.

        Only activates when AI_BACKEND=ollama is set explicitly,
        to avoid auto-starting containers when no backend is configured.
        """
        backend_env = os.environ.get("AI_BACKEND", "").lower()
        if backend_env != "ollama":
            logger.debug("Ollama not requested (AI_BACKEND=%s)", backend_env or "unset")
            return None

        runtime = self._find_container_runtime()
        if not runtime:
            logger.debug("No container runtime found for Ollama")
            return None

        model = os.environ.get("AI_MODEL") or self._select_model_by_vram()
        if not self._ensure_container_running(runtime):
            return None
        if not self._pull_model(runtime, model):
            return None
        if not self._health_check():
            return None

        logger.info("Backend: Local Ollama (model=%s, runtime=%s)", model, runtime)
        return {
            "backend": "ollama",
            "base_url": f"http://localhost:{OLLAMA_PORT}/v1",
            "model": model,
            "api_key": "ollama",
        }

    @staticmethod
    def _find_container_runtime() -> str | None:
        """Return 'podman' or 'docker' if available."""
        for runtime in ("podman", "docker"):
            if shutil.which(runtime):
                return runtime
        return None

    @staticmethod
    def _select_model_by_vram() -> str:
        """Query nvidia-smi and pick the best-fit model."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                vram_mb = int(result.stdout.strip().split("\n")[0].strip())
                for threshold, model_name in VRAM_MODEL_MAP:
                    if vram_mb >= threshold:
                        logger.info("GPU VRAM: %d MB -> model: %s", vram_mb, model_name)
                        return model_name
        except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
            pass

        logger.warning("No NVIDIA GPU detected -- using CPU-only model (slow)")
        return CPU_FALLBACK_MODEL

    @staticmethod
    def _ensure_container_running(runtime: str) -> bool:
        """Start the Ollama container if not already running."""
        check = subprocess.run(
            [runtime, "ps", "--filter", f"name={OLLAMA_CONTAINER}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if OLLAMA_CONTAINER in check.stdout:
            logger.debug("Ollama container already running")
            return True

        gpu_flag = (
            ["--device", "nvidia.com/gpu=all"]
            if runtime == "podman"
            else ["--gpus", "all"]
        )
        # OLLAMA_SCHED_SPREAD: offloads MoE expert weights to CPU RAM,
        #   keeping attention/embedding layers on GPU (critical for Mixtral 8x7b).
        # OLLAMA_KV_CACHE_TYPE: q8_0 halves KV cache VRAM with negligible
        #   quality loss vs f16 default. Combined with MoE offload this lets
        #   Mixtral run on 12 GB VRAM instead of 24 GB+.
        env_flags = [
            "-e", "OLLAMA_SCHED_SPREAD=1",
            "-e", "OLLAMA_KV_CACHE_TYPE=q8_0",
        ]
        cmd = [
            runtime, "run", "-d",
            "--name", OLLAMA_CONTAINER,
            *gpu_flag,
            *env_flags,
            "-p", f"{OLLAMA_PORT}:{OLLAMA_PORT}",
            "docker.io/ollama/ollama",
        ]
        logger.info("Starting Ollama container: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode != 0:
            logger.error("Failed to start Ollama container: %s", result.stderr.strip())
            return False
        return True

    @staticmethod
    def _pull_model(runtime: str, model: str) -> bool:
        """Pull the selected model inside the Ollama container."""
        logger.info("Pulling model %s (this may take a while)...", model)
        result = subprocess.run(
            [runtime, "exec", OLLAMA_CONTAINER, "ollama", "pull", model],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to pull model %s: %s", model, result.stderr.strip())
            return False
        return True

    @staticmethod
    def _health_check() -> bool:
        """Check Ollama API is responsive with retries."""
        import urllib.request
        import urllib.error

        url = f"http://localhost:{OLLAMA_PORT}/api/tags"
        for attempt in range(1, OLLAMA_HEALTH_RETRIES + 1):
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=OLLAMA_HEALTH_TIMEOUT) as resp:
                    if resp.status == 200:
                        logger.debug("Ollama health check passed (attempt %d)", attempt)
                        return True
            except (urllib.error.URLError, TimeoutError, OSError):
                logger.debug(
                    "Ollama health check attempt %d/%d failed, retrying in %ds",
                    attempt,
                    OLLAMA_HEALTH_RETRIES,
                    OLLAMA_HEALTH_INTERVAL,
                )
                if attempt < OLLAMA_HEALTH_RETRIES:
                    time.sleep(OLLAMA_HEALTH_INTERVAL)

        logger.error("Ollama health check failed after %d attempts", OLLAMA_HEALTH_RETRIES)
        return False


# ---------------------------------------------------------------------------
# ApiIndexBuilder  (T007)
# ---------------------------------------------------------------------------


class ApiIndexBuilder:
    """Build and search a lightweight index of Mist API endpoints."""

    def build(self, openapi_path: Path, cache_path: Path) -> dict:
        """Load or build the API index, return dict keyed by tag."""
        if cache_path.exists():
            logger.info("Loading API index from cache: %s", cache_path)
            with cache_path.open(encoding="utf-8") as fh:
                return json.load(fh)

        return self._build_from_spec(openapi_path, cache_path)

    def _build_from_spec(self, openapi_path: Path, cache_path: Path) -> dict:
        """Parse the OpenAPI spec and create the index."""
        logger.info("Building API index from %s...", openapi_path)
        with openapi_path.open(encoding="utf-8") as fh:
            spec = json.load(fh)

        index: dict[str, list[dict]] = {}
        paths = spec.get("paths", {})

        for path_str, methods in paths.items():
            for method, details in methods.items():
                if method in ("parameters", "servers", "summary", "description"):
                    continue
                entry = self._extract_endpoint(path_str, method, details)
                for tag in details.get("tags", ["Untagged"]):
                    index.setdefault(tag, []).append(entry)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2)

        total = sum(len(eps) for eps in index.values())
        logger.info("API index built: %d tags, %d endpoints", len(index), total)
        return index

    @staticmethod
    def _extract_endpoint(
        path_str: str,
        method: str,
        details: dict,
    ) -> dict:
        """Extract a single endpoint summary from the OpenAPI spec."""
        params = []
        for param in details.get("parameters", []):
            name = param.get("name", "")
            if name:
                params.append(name)
        return {
            "path": path_str,
            "method": method.upper(),
            "summary": details.get("summary", ""),
            "parameters": params,
        }

    @staticmethod
    def search(api_index: dict, query_terms: list[str]) -> list[dict]:
        """Return up to 10 endpoints matching the query terms."""
        scored: list[tuple[int, dict]] = []
        terms_lower = [term.lower() for term in query_terms]

        for tag, endpoints in api_index.items():
            tag_lower = tag.lower()
            for endpoint in endpoints:
                score = 0
                searchable = (
                    endpoint["path"].lower() + " "
                    + endpoint["summary"].lower() + " "
                    + tag_lower
                )
                for term in terms_lower:
                    if term in searchable:
                        score += 1
                if score > 0:
                    scored.append((score, endpoint))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [ep for _, ep in scored[:10]]


# ---------------------------------------------------------------------------
# Caching  (T008, T031-T033)
# ---------------------------------------------------------------------------


def load_cached_response(
    cache_dir: Path,
    content_hash: str,
) -> dict | None:
    """Load a cached AI response or return None."""
    path = cache_dir / f"{content_hash}.json"
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if "classification" not in data or "rationale" not in data:
            logger.warning("Corrupt cache file (missing fields): %s", path)
            return None
        return data
    except json.JSONDecodeError:
        logger.warning("Corrupt cache file (invalid JSON): %s", path)
        return None


def save_cached_response(
    cache_dir: Path,
    content_hash: str,
    response: dict,
) -> None:
    """Save an AI response to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{content_hash}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(response, fh, indent=2)


def count_cache_files(cache_dir: Path) -> int:
    """Count existing .json cache files (excluding api_index.json)."""
    if not cache_dir.exists():
        return 0
    return sum(
        1 for f in cache_dir.iterdir()
        if f.suffix == ".json" and f.name != "api_index.json"
    )


# ---------------------------------------------------------------------------
# IdeaAnalyzer  (T009-T018)
# ---------------------------------------------------------------------------


class IdeaAnalyzer:
    """Classify ideas using AI and perform deduplication."""

    def __init__(
        self,
        backend_config: dict,
        api_index: dict,
        refresh: bool = False,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.backend_config = backend_config
        self.client = OpenAI(
            base_url=backend_config["base_url"],
            api_key=backend_config["api_key"],
        )
        self.model = backend_config["model"]
        self.is_ollama = backend_config.get("backend") == "ollama"
        self.api_index = api_index
        self.refresh = refresh
        self.batch_size = batch_size
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with MistHelper scope and schema."""
        return """You are a technical analyst classifying Mist community feature ideas by MistHelper feasibility.

## MistHelper Scope
MistHelper is a Python script that CALLS the existing Mist REST API. It:
- Extracts data to CSV/SQLite (device inventory, events, stats, licenses)
- Manages firmware upgrades and AP reboots
- Sends WebSocket commands to devices
- Runs SSH commands against network devices

MistHelper is a CLIENT of the Mist API, not the API itself. It cannot:
- Modify the Mist portal GUI
- Add new API endpoints
- Enable hardware capabilities not exposed by the API
- Change Mist backend behavior

## GUI vs API Rule (CRITICAL)
Ideas phrased as "add a column to the portal" or "show X in the dashboard" are NOT automatically GUI_ONLY. If the underlying data IS accessible via a documented Mist REST API endpoint, MistHelper can retrieve and present it. Classify as REPORT_EXPORT or API_ENHANCEMENT.

## Classification Labels
- REPORT_EXPORT: Data extraction — the idea asks for data that IS available via the Mist API and MistHelper can export it (CSV, SQLite, report)
- API_ENHANCEMENT: The idea asks for an action or workflow that the Mist API supports and MistHelper could automate (firmware, config push, bulk operations)
- HYBRID: The idea has both API-actionable and GUI-only components; MistHelper can partially address it
- GUI_ONLY: The idea requires changes to the Mist portal GUI that the API cannot replicate or expose
- HARDWARE_FEATURE: The idea requires hardware capabilities, radio firmware changes, or AP/switch physical behavior not controllable via API
- ALREADY_SUPPORTED: MistHelper already has this capability (or the Mist API already provides it natively)
- UNCLASSIFIED: Cannot determine feasibility — the idea is too vague or references unknown capabilities

## AI_INSPIRED Instruction
If analyzing an idea reveals a valuable capability that neither the Mist portal NOR MistHelper currently supports, but COULD be built as a new MistHelper feature using existing API endpoints, record it in the ai_inspired_ideas list. Include the source idea title that inspired it.

## Response Format
You will receive exactly ONE idea. Respond with a single JSON object.

ALL fields below are REQUIRED. Do NOT leave any field as null or empty unless genuinely not applicable.

### REQUIRED Fields (must ALL be populated):
1. **classification**: One of the 7 labels above
2. **confidence**: "high", "medium", or "low"
3. **themes**: At least 2-3 topic tags (e.g. "inventory", "firmware", "NAC", "switch", "WLAN", "monitoring")
4. **rationale**: 2-3 sentences explaining your classification reasoning
5. **misthelper_enhancement**: A specific, actionable suggestion for how MistHelper could address this idea. Describe what the feature would do. Write "Not applicable - requires GUI/hardware changes" ONLY for GUI_ONLY or HARDWARE_FEATURE classifications.
6. **possible_duplicate_titles**: List any idea titles from the provided context that sound similar. Empty list [] ONLY if truly unique.
7. **is_foundational**: true if implementing this idea would enable or simplify multiple other feature requests. Think about whether this is a building-block capability.
8. **unlocks**: If is_foundational is true, list the types of features this would enable. Otherwise [].
9. **ai_inspired_ideas**: At least ONE new feature idea inspired by analyzing this request. Think: "What RELATED capability could MistHelper build using the API?" Every idea should spark at least one inspired idea.

### ai_inspired_ideas entry format:
{
  "title": "Descriptive feature title",
  "description": "What the feature would do and how it helps NOC engineers",
  "source_idea_title": "The customer idea that inspired this",
  "rationale": "Why this is valuable and not currently available"
}

### Example Response (HYBRID classification):
{
  "classification": "HYBRID",
  "confidence": "high",
  "themes": ["switch configuration", "VLAN", "inventory"],
  "rationale": "The Mist API provides switch port configuration data via the sites devices stats endpoint. MistHelper can extract port-to-VLAN mappings, but the visual topology view requested requires GUI changes.",
  "misthelper_enhancement": "Add a 'VLAN Port Report' operation that queries all switch port configs and generates a CSV grouped by VLAN, showing port name, status, speed, and assigned device.",
  "possible_duplicate_titles": ["Show VLAN assignments per port"],
  "is_foundational": true,
  "unlocks": ["VLAN audit reports", "port utilization dashboards", "switch migration planning"],
  "ai_inspired_ideas": [
    {
      "title": "VLAN Consistency Checker",
      "description": "Compare VLAN assignments across all switches in a site and flag inconsistencies or orphaned VLANs not assigned to any port.",
      "source_idea_title": "Switch port config - show all ports in a VLAN",
      "rationale": "VLAN misconfiguration is a common NOC issue. The API exposes all port configs but no tool cross-references them for consistency."
    }
  ]
}t configs and generates a CSV grouped by VLAN, showing port name, status, speed, and assigned device.",
  "possible_duplicate_titles": ["Show VLAN assignments per port"],
  "is_foundational": true,
  "unlocks": ["VLAN audit reports", "port utilization dashboards", "switch migration planning"],
  "ai_inspired_ideas": [
    {
      "title": "VLAN Consistency Checker",
      "description": "Compare VLAN assignments across all switches in a site and flag inconsistencies or orphaned VLANs not assigned to any port.",
      "source_idea_title": "Switch port config - show all ports in a VLAN",
      "rationale": "VLAN misconfiguration is a common NOC issue. The API exposes all port configs but no tool cross-references them for consistency."
    }
  ]
}"""

    @staticmethod
    def _build_user_prompt(
        idea: dict,
        relevant_endpoints: list[dict],
    ) -> str:
        """Format a user prompt for one idea with API context."""
        parts = [
            f"## Idea Title\n{idea['title']}",
            f"\n## Description\n{idea['description']}",
        ]

        if idea.get("comments"):
            comment_lines = []
            for comment in idea["comments"]:
                author = comment.get("author", "Anonymous")
                text = comment.get("text", "")
                comment_lines.append(f"- {author}: {text}")
            parts.append("\n## Comments\n" + "\n".join(comment_lines))

        if relevant_endpoints:
            endpoint_lines = []
            for ep in relevant_endpoints:
                endpoint_lines.append(
                    f"- {ep['method']} {ep['path']}: {ep['summary']}"
                )
            parts.append(
                "\n## Relevant Mist API Endpoints\n"
                + "\n".join(endpoint_lines)
            )

        return "\n".join(parts)

    def _build_batch_user_prompt(
        self,
        batch: list[tuple[dict, list[dict]]],
    ) -> str:
        """Format multiple ideas into a single numbered prompt."""
        sections = []
        for index, (idea, endpoints) in enumerate(batch, start=1):
            header = f"# Idea {index}"
            body = self._build_user_prompt(idea, endpoints)
            sections.append(f"{header}\n{body}")
        return "\n\n---\n\n".join(sections)

    def analyze_idea(self, idea: dict) -> dict:
        """Classify a single idea, using cache if available."""
        content_hash = idea["content_hash"]

        if not self.refresh:
            cached = load_cached_response(CACHE_DIR, content_hash)
            if cached:
                logger.debug("[CACHED] %s", idea["title"])
                return cached

        query_terms = idea["title"].lower().split()
        relevant_endpoints = ApiIndexBuilder.search(
            self.api_index,
            query_terms[:5],
        )
        user_prompt = self._build_user_prompt(idea, relevant_endpoints)
        result = self._call_ai(user_prompt)

        if result:
            result = self._attach_source_fields(idea, result)
            save_cached_response(CACHE_DIR, content_hash, result)

        time.sleep(INTER_REQUEST_DELAY)
        return result

    @staticmethod
    def _attach_source_fields(idea: dict, result: dict) -> dict:
        """Embed the original idea title, description, and comments into the result."""
        result["source_title"] = idea.get("title", "")
        result["source_description"] = idea.get("description", "")
        result["source_comments"] = idea.get("comments", [])
        return result

    def _call_ai(self, user_prompt: str) -> dict:
        """Call the AI and validate the response, with retry logic."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                extra = {"options": {"num_ctx": 8192}} if self.is_ollama else None
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    extra_body=extra,
                )
                content = response.choices[0].message.content
                logger.debug("Raw AI response: %s", content[:500])
                data = json.loads(content)
                if "results" in data and isinstance(data["results"], list):
                    data = data["results"][0] if data["results"] else data
                validated = self._validate_response(data)
                if validated:
                    return validated
                logger.warning("Invalid classification on attempt %d", attempt)
            except RateLimitError as exc:
                msg = str(exc)
                if self._is_daily_limit(msg):
                    raise DailyLimitExhausted(msg) from exc
                logger.warning(
                    "Rate limited on attempt %d, waiting %ds",
                    attempt,
                    RATE_LIMIT_WAIT * attempt,
                )
                time.sleep(RATE_LIMIT_WAIT * attempt)
                continue
            except json.JSONDecodeError:
                logger.warning("JSON parse error on attempt %d", attempt)
            except Exception:
                logger.exception("AI call failed on attempt %d", attempt)
                self._backoff(attempt)
                continue

            if attempt < MAX_RETRIES:
                self._backoff(attempt)

        logger.error("All retries exhausted, defaulting to UNCLASSIFIED")
        return self._unclassified_fallback()

    def _call_ai_batch(
        self,
        user_prompt: str,
        count: int,
    ) -> list[dict]:
        """Call AI with a batch prompt, returning one result per idea."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                extra = {"options": {"num_ctx": 8192}} if self.is_ollama else None
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    extra_body=extra,
                )
                content = response.choices[0].message.content
                logger.debug("Raw batch response: %s", content[:500])
                data = json.loads(content)
                raw = data.get("results", [data])
                validated = [
                    self._validate_response(item)
                    or self._unclassified_fallback()
                    for item in raw
                ]
                while len(validated) < count:
                    logger.warning(
                        "Batch returned %d/%d, padding",
                        len(validated),
                        count,
                    )
                    validated.append(self._unclassified_fallback())
                return validated[:count]
            except RateLimitError as exc:
                msg = str(exc)
                if self._is_daily_limit(msg):
                    raise DailyLimitExhausted(msg) from exc
                wait_time = RATE_LIMIT_WAIT * attempt
                logger.warning(
                    "Rate limited, waiting %ds: %s",
                    wait_time,
                    exc,
                )
                time.sleep(wait_time)
            except json.JSONDecodeError:
                logger.warning(
                    "JSON parse error on batch attempt %d",
                    attempt,
                )
                self._backoff(attempt)
            except Exception:
                logger.exception(
                    "Batch AI call failed on attempt %d",
                    attempt,
                )
                self._backoff(attempt)
        logger.error(
            "Batch retries exhausted for %d ideas",
            count,
        )
        return [
            self._unclassified_fallback() for _ in range(count)
        ]

    @staticmethod
    def _is_daily_limit(message: str) -> bool:
        """Check if a 429 error indicates the daily quota is hit."""
        import re
        match = re.search(r"wait (\d+) seconds", message)
        if match and int(match.group(1)) > DAILY_LIMIT_THRESHOLD:
            return True
        return False

    @staticmethod
    def _validate_response(data: dict) -> dict | None:
        """Validate the AI response against expected schema."""
        classification = data.get("classification", "").upper()
        data["classification"] = classification
        if classification not in VALID_CLASSIFICATIONS:
            logger.debug("Rejected classification: %r", classification)
            return None

        confidence = data.get("confidence", "medium").lower()
        data["confidence"] = confidence
        if confidence not in VALID_CONFIDENCE:
            data["confidence"] = "medium"

        rationale = data.get("rationale", "")
        if not rationale or len(rationale) < 20:
            logger.warning("Short or empty rationale accepted with warning")

        data.setdefault("themes", [])
        data.setdefault("misthelper_enhancement", None)
        data.setdefault("possible_duplicate_titles", [])
        data.setdefault("is_foundational", False)
        data.setdefault("unlocks", [])
        data.setdefault("ai_inspired_ideas", [])

        return data

    @staticmethod
    def _backoff(attempt: int) -> None:
        """Exponential backoff with jitter."""
        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
        jitter = delay * 0.1 * (2 * random.random() - 1)
        time.sleep(delay + jitter)

    @staticmethod
    def _unclassified_fallback() -> dict:
        """Return an UNCLASSIFIED result for failed analyses."""
        return {
            "classification": "UNCLASSIFIED",
            "confidence": "low",
            "themes": [],
            "rationale": "AI analysis failed after all retries",
            "misthelper_enhancement": None,
            "possible_duplicate_titles": [],
            "is_foundational": False,
            "unlocks": [],
            "ai_inspired_ideas": [],
        }

    def analyze_all(self, ideas: list[dict]) -> list[dict]:
        """Analyze all ideas using batched API calls."""
        total = len(ideas)
        results: dict[int, dict] = {}
        uncached: list[tuple[int, dict]] = []

        for index, idea in enumerate(ideas):
            if not self.refresh:
                cached = load_cached_response(
                    CACHE_DIR,
                    idea["content_hash"],
                )
                if cached:
                    results[index] = cached
                    continue
            uncached.append((index, idea))

        cached_count = total - len(uncached)
        batch_count = (
            (len(uncached) + self.batch_size - 1) // self.batch_size
            if uncached
            else 0
        )
        logger.info(
            "Cached: %d, uncached: %d, batches: %d (size %d)",
            cached_count,
            len(uncached),
            batch_count,
            self.batch_size,
        )

        for batch_start in range(
            0,
            len(uncached),
            self.batch_size,
        ):
            chunk = uncached[
                batch_start : batch_start + self.batch_size
            ]
            batch_num = batch_start // self.batch_size + 1
            logger.info(
                "Batch %d/%d (%d ideas)",
                batch_num,
                batch_count,
                len(chunk),
            )

            batch_items = self._prepare_batch(chunk)

            try:
                if len(batch_items) == 1:
                    idea, endpoints = batch_items[0]
                    prompt = self._build_user_prompt(idea, endpoints)
                    batch_results = [self._call_ai(prompt)]
                else:
                    prompt = self._build_batch_user_prompt(batch_items)
                    batch_results = self._call_ai_batch(
                        prompt,
                        len(batch_items),
                    )
            except DailyLimitExhausted:
                logger.warning(
                    "Daily API quota exhausted at batch %d/%d. "
                    "Re-run later to continue from cache.",
                    batch_num,
                    batch_count,
                )
                break

            self._save_batch_results(chunk, batch_results, results)
            time.sleep(INTER_REQUEST_DELAY)

        return [results.get(i, self._unclassified_fallback()) for i in range(total)]

    def _prepare_batch(
        self,
        chunk: list[tuple[int, dict]],
    ) -> list[tuple[dict, list[dict]]]:
        """Build (idea, endpoints) pairs for a batch chunk."""
        batch_items: list[tuple[dict, list[dict]]] = []
        for _, idea in chunk:
            query_terms = idea["title"].lower().split()[:5]
            endpoints = ApiIndexBuilder.search(
                self.api_index,
                query_terms,
            )
            batch_items.append((idea, endpoints))
        return batch_items

    @staticmethod
    def _save_batch_results(
        chunk: list[tuple[int, dict]],
        batch_results: list[dict],
        results: dict[int, dict],
    ) -> None:
        """Save batch results to cache and results dict."""
        for (orig_idx, idea), result in zip(chunk, batch_results):
            result["source_title"] = idea.get("title", "")
            result["source_description"] = idea.get("description", "")
            result["source_comments"] = idea.get("comments", [])
            save_cached_response(
                CACHE_DIR,
                idea["content_hash"],
                result,
            )
            results[orig_idx] = result
            logger.debug(
                "  -> %s: %s",
                idea["title"][:50],
                result.get("classification"),
            )

    def _build_dedup_prompt(self, ideas: list[dict]) -> str:
        """Build a prompt to detect duplicates within a batch of ideas."""
        lines = ["Identify groups of duplicate or near-duplicate ideas.\n"]
        for idea in ideas:
            excerpt = idea["description"][:80].replace("\n", " ")
            lines.append(f'- "{idea["title"]}": {excerpt}')

        lines.append(
            "\nRespond with JSON: "
            '{"duplicate_groups": [{"canonical_title": "...", '
            '"duplicate_titles": ["..."], '
            '"merge_confidence": "high|medium|low"}]}'
        )
        return "\n".join(lines)

    def _detect_duplicates_batch(self, batch: list[dict]) -> list[dict]:
        """Run duplicate detection on one batch; return validated groups."""
        known_titles = {idea["title"] for idea in batch}
        prompt = self._build_dedup_prompt(batch)
        extra = {"options": {"num_ctx": 8192}} if self.is_ollama else None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You identify duplicate feature ideas. "
                            "Respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                extra_body=extra,
            )
            data = json.loads(response.choices[0].message.content)
            groups = data.get("duplicate_groups", [])
            return self._validate_dedup_groups(groups, known_titles)
        except Exception:
            logger.exception("Duplicate detection batch failed, skipping batch")
            return []

    def detect_duplicates(
        self,
        ideas: list[dict],
        analyses: list[dict],
    ) -> list[dict]:
        """Detect duplicates across all ideas, batched to stay within token limits.

        GitHub Models gpt-4o-mini: 8K token limit.
        Each idea line is ~30 tokens; 200 ideas/batch leaves safe headroom.
        Ollama models can handle larger contexts but we keep the same batch
        size for consistency -- dedup quality improves with smaller focused sets.
        """
        DEDUP_BATCH_SIZE = 200
        logger.info("Running duplicate detection across %d ideas...", len(ideas))
        all_groups: list[dict] = []
        for start in range(0, len(ideas), DEDUP_BATCH_SIZE):
            batch = ideas[start : start + DEDUP_BATCH_SIZE]
            batch_num = start // DEDUP_BATCH_SIZE + 1
            total_batches = (len(ideas) + DEDUP_BATCH_SIZE - 1) // DEDUP_BATCH_SIZE
            logger.debug(
                "Dedup batch %d/%d (%d ideas)",
                batch_num, total_batches, len(batch),
            )
            all_groups.extend(self._detect_duplicates_batch(batch))
        logger.info("Found %d duplicate groups", len(all_groups))
        return all_groups

    @staticmethod
    def _validate_dedup_groups(
        groups: list[dict],
        known_titles: set[str],
    ) -> list[dict]:
        """Validate dedup groups against known titles (case-insensitive)."""
        lower_to_actual = {title.lower(): title for title in known_titles}
        validated: list[dict] = []
        for group in groups:
            canonical = group.get("canonical_title", "")
            resolved = lower_to_actual.get(canonical.lower())
            if not resolved:
                logger.warning("Unknown canonical title, skipping: %s", canonical)
                continue
            valid_dupes = []
            for title in group.get("duplicate_titles", []):
                actual = lower_to_actual.get(title.lower())
                if actual:
                    valid_dupes.append(actual)
            skipped = len(group.get("duplicate_titles", [])) - len(valid_dupes)
            if skipped > 0:
                logger.warning(
                    "%d unknown duplicate titles skipped for '%s'",
                    skipped,
                    resolved,
                )
            if valid_dupes:
                validated.append({
                    "canonical_title": resolved,
                    "duplicate_titles": valid_dupes,
                    "merge_confidence": group.get("merge_confidence", "medium"),
                })
        return validated

    @staticmethod
    def build_clusters(
        ideas: list[dict],
        analyses: list[dict],
        duplicate_groups: list[dict],
    ) -> list[dict]:
        """Merge ideas into clusters based on dedup results."""
        title_to_idea = {idea["title"]: idea for idea in ideas}
        title_to_analysis = {}
        for idea, analysis in zip(ideas, analyses):
            title_to_analysis[idea["title"]] = analysis

        merged_titles: set[str] = set()
        clusters: list[dict] = []
        low_confidence: dict[str, list[str]] = {}

        for group in duplicate_groups:
            confidence = group.get("merge_confidence", "medium")
            canonical = group["canonical_title"]
            dupes = group["duplicate_titles"]

            if confidence == "low":
                low_confidence.setdefault(canonical, []).extend(dupes)
                continue

            all_titles = [canonical] + dupes
            merged_titles.update(all_titles)
            cluster = _build_cluster_from_titles(
                all_titles, canonical, title_to_idea, title_to_analysis,
            )
            clusters.append(cluster)

        for idea in ideas:
            if idea["title"] not in merged_titles:
                analysis = title_to_analysis.get(idea["title"], {})
                cluster = _build_single_cluster(idea, analysis)
                clusters.append(cluster)

        _apply_low_confidence_refs(clusters, low_confidence)
        clusters.sort(key=lambda c: c["demand_count"], reverse=True)
        logger.info(
            "Built %d clusters from %d ideas",
            len(clusters),
            len(ideas),
        )
        return clusters


def _build_cluster_from_titles(
    all_titles: list[str],
    canonical: str,
    title_to_idea: dict,
    title_to_analysis: dict,
) -> dict:
    """Create a merged cluster from a group of duplicate titles."""
    primary_analysis = title_to_analysis.get(canonical, {})
    combined_themes: list[str] = []
    combined_unlocks: list[str] = []
    demand = 0

    for title in all_titles:
        idea = title_to_idea.get(title, {})
        analysis = title_to_analysis.get(title, {})
        demand += idea.get("demand_count", 1)
        for theme in analysis.get("themes", []):
            if theme not in combined_themes:
                combined_themes.append(theme)
        for unlock in analysis.get("unlocks", []):
            if unlock not in combined_unlocks:
                combined_unlocks.append(unlock)

    primary_idea = title_to_idea.get(canonical, {})
    return {
        "canonical_title": canonical,
        "merged_titles": all_titles,
        "demand_count": demand,
        "classification": primary_analysis.get("classification", "UNCLASSIFIED"),
        "confidence": primary_analysis.get("confidence", "low"),
        "themes": combined_themes,
        "rationale": primary_analysis.get("rationale", ""),
        "misthelper_enhancement": primary_analysis.get("misthelper_enhancement"),
        "is_foundational": primary_analysis.get("is_foundational", False),
        "unlocks": combined_unlocks,
        "possible_duplicate_of": None,
        "source_title": primary_idea.get("title", ""),
        "source_description": primary_idea.get("description", ""),
        "source_comments": primary_idea.get("comments", []),
    }


def _build_single_cluster(idea: dict, analysis: dict) -> dict:
    """Create a single-member cluster for a non-duplicate idea."""
    return {
        "canonical_title": idea["title"],
        "merged_titles": [idea["title"]],
        "demand_count": idea.get("demand_count", 1),
        "classification": analysis.get("classification", "UNCLASSIFIED"),
        "confidence": analysis.get("confidence", "low"),
        "themes": analysis.get("themes", []),
        "rationale": analysis.get("rationale", ""),
        "misthelper_enhancement": analysis.get("misthelper_enhancement"),
        "is_foundational": analysis.get("is_foundational", False),
        "unlocks": analysis.get("unlocks", []),
        "possible_duplicate_of": None,
        "source_title": idea.get("title", ""),
        "source_description": idea.get("description", ""),
        "source_comments": idea.get("comments", []),
    }


def _apply_low_confidence_refs(
    clusters: list[dict],
    low_confidence: dict[str, list[str]],
) -> None:
    """Set possible_duplicate_of on clusters for low-confidence matches."""
    title_to_cluster = {c["canonical_title"]: c for c in clusters}
    for canonical, dupes in low_confidence.items():
        cluster = title_to_cluster.get(canonical)
        if cluster:
            cluster["possible_duplicate_of"] = dupes


# ---------------------------------------------------------------------------
# ReportGenerator  (T019-T030)
# ---------------------------------------------------------------------------


class ReportGenerator:
    """Generate Markdown, JSON, and CSV reports from clusters."""

    def __init__(
        self,
        clusters: list[dict],
        all_ai_inspired: list[dict],
    ) -> None:
        self.clusters = clusters
        self.all_ai_inspired = all_ai_inspired

    def _executive_summary(self) -> dict:
        """Compute summary statistics."""
        total = sum(c["demand_count"] for c in self.clusters)
        counts: dict[str, int] = {}
        all_themes: set[str] = set()

        for cluster in self.clusters:
            label = cluster["classification"]
            counts[label] = counts.get(label, 0) + 1
            all_themes.update(cluster.get("themes", []))

        top_by_demand = sorted(
            self.clusters,
            key=lambda c: c["demand_count"],
            reverse=True,
        )[:5]

        return {
            "total_ideas_processed": total,
            "cluster_count": len(self.clusters),
            "counts_by_classification": counts,
            "unique_theme_count": len(all_themes),
            "top_clusters": [
                {
                    "title": c["canonical_title"],
                    "demand": c["demand_count"],
                }
                for c in top_by_demand
            ],
            "ai_inspired_count": len(self.all_ai_inspired),
        }

    def generate_markdown(self, output_path: Path) -> None:
        """Write the full Markdown report."""
        summary = self._executive_summary()
        themes = self.group_by_theme(self.clusters)
        chains = self.build_snowball_chains(self.clusters)
        lines: list[str] = []

        lines.append("# Mist Ideas Analysis Report\n")
        self._write_summary_section(lines, summary)
        self._write_classification_sections(lines)
        self._write_themes_section(lines, themes)
        self._write_snowball_section(lines, chains)
        self._write_inspired_section(lines)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Markdown report written: %s", output_path)

    def _write_summary_section(
        self,
        lines: list[str],
        summary: dict,
    ) -> None:
        """Append the executive summary section."""
        lines.append("## Executive Summary\n")
        lines.append(f"- **Total ideas processed**: {summary['total_ideas_processed']}")
        lines.append(f"- **Unique clusters**: {summary['cluster_count']}")
        lines.append(f"- **Unique themes**: {summary['unique_theme_count']}")
        lines.append(f"- **AI-inspired ideas**: {summary['ai_inspired_count']}")
        lines.append("\n### Classification Breakdown\n")
        for label, count in sorted(summary["counts_by_classification"].items()):
            lines.append(f"- {label}: {count}")
        lines.append("\n### Top Clusters by Demand\n")
        for item in summary["top_clusters"]:
            lines.append(f"1. **{item['title']}** (demand: {item['demand']})")
        lines.append("")

    def _write_classification_sections(self, lines: list[str]) -> None:
        """Append one section per classification label."""
        section_order = [
            "REPORT_EXPORT",
            "API_ENHANCEMENT",
            "HYBRID",
            "GUI_ONLY",
            "HARDWARE_FEATURE",
            "ALREADY_SUPPORTED",
            "UNCLASSIFIED",
        ]
        for label in section_order:
            matching = [
                c for c in self.clusters if c["classification"] == label
            ]
            if not matching:
                continue
            matching.sort(key=lambda c: c["demand_count"], reverse=True)
            lines.append(f"## {label} ({len(matching)} clusters)\n")
            for cluster in matching:
                self._write_cluster_entry(lines, cluster)
            lines.append("")

    @staticmethod
    def _write_cluster_entry(lines: list[str], cluster: dict) -> None:
        """Append a single cluster entry."""
        lines.append(f"### {cluster['canonical_title']}")
        lines.append(
            f"- **Classification**: {cluster['classification']} "
            f"({cluster['confidence']} confidence)"
        )
        lines.append(f"- **Demand**: {cluster['demand_count']}")
        if cluster.get("themes"):
            lines.append(f"- **Themes**: {', '.join(cluster['themes'])}")
        lines.append(f"- **Rationale**: {cluster['rationale']}")
        if cluster.get("misthelper_enhancement"):
            lines.append(
                f"- **Enhancement**: {cluster['misthelper_enhancement']}"
            )
        if cluster.get("possible_duplicate_of"):
            lines.append(
                f"- **Possible duplicates**: "
                f"{', '.join(cluster['possible_duplicate_of'])}"
            )
        if cluster["demand_count"] > 1:
            titles = ", ".join(cluster["merged_titles"])
            lines.append(f"- **Merged ideas**: {titles}")
        if cluster.get("source_description"):
            lines.append(f"- **Original description**: {cluster['source_description']}")
        if cluster.get("source_comments"):
            comment_texts = [
                comment.get("body", "") for comment in cluster["source_comments"]
                if comment.get("body")
            ]
            if comment_texts:
                lines.append(f"- **Comments**: {' | '.join(comment_texts)}")
        lines.append("")

    def _write_themes_section(
        self,
        lines: list[str],
        themes: list[dict],
    ) -> None:
        """Append the themes overview section."""
        if not themes:
            return
        lines.append("## Themes Overview\n")
        for theme_group in themes:
            lines.append(
                f"### {theme_group['theme']} "
                f"({len(theme_group['clusters'])} clusters, "
                f"demand: {theme_group['total_demand']})"
            )
            for cluster in theme_group["clusters"]:
                lines.append(
                    f"- {cluster['canonical_title']} "
                    f"(demand: {cluster['demand_count']})"
                )
            lines.append("")

    @staticmethod
    def _write_snowball_section(
        lines: list[str],
        chains: list[dict],
    ) -> None:
        """Append the snowball chains section."""
        if not chains:
            return
        lines.append("## Snowball Chains\n")
        for chain in chains:
            root_title = chain["root"]["canonical_title"]
            lines.append(f"### {root_title} (foundational)")
            lines.append("Unlocks:")
            for dep in chain["dependents"]:
                lines.append(f"- {dep['canonical_title']}")
            lines.append("")

    def _write_inspired_section(self, lines: list[str]) -> None:
        """Append the AI-inspired ideas section."""
        if not self.all_ai_inspired:
            return
        lines.append("## AI-Inspired Ideas\n")
        for inspired in self.all_ai_inspired:
            lines.append(f"### {inspired.get('title', 'Untitled')}")
            lines.append(f"- **Description**: {inspired.get('description', 'N/A')}")
            lines.append(
                f"- **Inspired by**: {inspired.get('source_idea_title', 'N/A')}"
            )
            lines.append(f"- **Rationale**: {inspired.get('rationale', 'N/A')}")
            lines.append("")

    def generate_json(self, output_path: Path) -> None:
        """Write the full JSON sidecar."""
        themes = self.group_by_theme(self.clusters)
        chains = self.build_snowball_chains(self.clusters)
        summary = self._executive_summary()

        output = {
            "executive_summary": summary,
            "clusters": self.clusters,
            "theme_groups": themes,
            "snowball_chains": [
                {
                    "root": chain["root"]["canonical_title"],
                    "dependents": [
                        d["canonical_title"] for d in chain["dependents"]
                    ],
                }
                for chain in chains
            ],
            "ai_inspired_ideas": self.all_ai_inspired,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
        logger.info("JSON report written: %s", output_path)

    def generate_csv(self, output_path: Path) -> None:
        """Write the CSV sidecar with one row per cluster."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([
                "canonical_title",
                "classification",
                "confidence",
                "demand_count",
                "themes",
                "rationale",
                "misthelper_enhancement",
                "is_foundational",
                "possible_duplicate_of",
                "source_title",
                "source_description",
                "source_comments",
            ])
            for cluster in self.clusters:
                comments_text = json.dumps(
                    cluster.get("source_comments", []),
                )
                writer.writerow([
                    cluster["canonical_title"],
                    cluster["classification"],
                    cluster["confidence"],
                    cluster["demand_count"],
                    "|".join(cluster.get("themes", [])),
                    cluster["rationale"],
                    cluster.get("misthelper_enhancement") or "",
                    cluster.get("is_foundational", False),
                    "|".join(cluster.get("possible_duplicate_of") or []),
                    cluster.get("source_title", ""),
                    cluster.get("source_description", ""),
                    comments_text,
                ])
        logger.info("CSV report written: %s", output_path)

    @staticmethod
    def group_by_theme(clusters: list[dict]) -> list[dict]:
        """Group clusters into theme groups."""
        theme_map: dict[str, list[dict]] = {}
        for cluster in clusters:
            for theme in cluster.get("themes", []):
                theme_map.setdefault(theme, []).append(cluster)

        result: list[dict] = []
        for theme, members in sorted(theme_map.items()):
            members_sorted = sorted(
                members,
                key=lambda c: c["demand_count"],
                reverse=True,
            )
            total_demand = sum(c["demand_count"] for c in members_sorted)
            result.append({
                "theme": theme,
                "clusters": members_sorted,
                "total_demand": total_demand,
            })

        result.sort(key=lambda t: t["total_demand"], reverse=True)
        return result

    @staticmethod
    def build_snowball_chains(clusters: list[dict]) -> list[dict]:
        """Find foundational ideas and what they unlock."""
        title_to_cluster = {c["canonical_title"]: c for c in clusters}
        chains: list[dict] = []

        for cluster in clusters:
            if not cluster.get("is_foundational"):
                continue
            dependents: list[dict] = []
            for unlock_title in cluster.get("unlocks", []):
                dep = title_to_cluster.get(unlock_title)
                if dep:
                    dependents.append(dep)
                else:
                    for candidate in clusters:
                        if unlock_title.lower() in candidate["canonical_title"].lower():
                            dependents.append(candidate)
                            break
            if dependents:
                chains.append({"root": cluster, "dependents": dependents})

        chains.sort(key=lambda c: len(c["dependents"]), reverse=True)
        return chains


# ---------------------------------------------------------------------------
# Main  (T014, T018, T024)
# ---------------------------------------------------------------------------


def aggregate_ai_inspired(
    ideas: list[dict],
    analyses: list[dict],
) -> list[dict]:
    """Collect all ai_inspired_ideas from analyses into a flat list."""
    all_inspired: list[dict] = []
    for idea, analysis in zip(ideas, analyses):
        for inspired in analysis.get("ai_inspired_ideas", []):
            entry = dict(inspired)
            if "source_idea_title" not in entry:
                entry["source_idea_title"] = idea["title"]
            all_inspired.append(entry)
    return all_inspired


# ---------------------------------------------------------------------------
# Multi-Server Orchestration
# ---------------------------------------------------------------------------


def _ollama_api_call(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    body: dict | None = None,
    timeout: int = 30,
) -> dict | None:
    """Make an HTTP call to the Ollama API. Returns parsed JSON or None."""
    import urllib.request
    import urllib.error

    api_base = base_url.replace("/v1", "")
    url = f"{api_base}{endpoint}"
    try:
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.debug("Ollama API %s %s -> %s", method, url, exc)
        return None


def _get_server_models(base_url: str) -> set[str] | None:
    """Return set of model names on an Ollama server, or None if unreachable."""
    data = _ollama_api_call(base_url, "/api/tags")
    if data is None:
        return None
    return {m["name"] for m in data.get("models", [])}


def _pull_model_on_server(
    base_url: str, model_name: str, label: str,
) -> bool:
    """Pull a model on a remote Ollama server via API."""
    logger.info("[%s] Pulling model %s (this may take a while)...", label, model_name)
    result = _ollama_api_call(
        base_url,
        "/api/pull",
        method="POST",
        body={"name": model_name, "stream": False},
        timeout=MODEL_PULL_TIMEOUT,
    )
    if result and result.get("status") == "success":
        logger.info("[%s] Model %s pulled successfully", label, model_name)
        return True
    logger.error("[%s] Failed to pull model %s: %s", label, model_name, result)
    return False


def _try_model_on_server(
    base_url: str, model_name: str, label: str,
) -> dict | None:
    """Test inference and GPU allocation for a model. Returns config or None."""
    logger.info("[%s] Testing %s...", label, model_name)
    result = _ollama_api_call(
        base_url,
        "/api/generate",
        method="POST",
        body={"model": model_name, "prompt": HEALTH_CHECK_PROMPT, "stream": False},
        timeout=MODEL_LOAD_TIMEOUT,
    )
    if not result or "response" not in result:
        logger.warning("[%s] Inference failed for %s", label, model_name)
        return None

    gpu_percent = _check_gpu_percent(base_url, model_name, label)
    mode = "GPU" if gpu_percent >= MIN_GPU_PERCENT else "CPU"
    if gpu_percent == 0:
        logger.info("[%s] READY (%s-only): %s", label, mode, model_name)
    else:
        logger.info("[%s] READY (%s, %d%% GPU): %s", label, mode, gpu_percent, model_name)
    return {
        "backend": "ollama",
        "base_url": base_url,
        "model": model_name,
        "api_key": "ollama",
        "gpu_percent": gpu_percent,
    }


def _check_gpu_percent(
    base_url: str, model_name: str, label: str,
) -> int:
    """Check GPU allocation percentage for a loaded model via /api/ps."""
    ps_data = _ollama_api_call(base_url, "/api/ps")
    if not ps_data:
        logger.warning("[%s] Cannot query /api/ps, assuming 0%% GPU", label)
        return 0

    for loaded in ps_data.get("models", []):
        if model_name in loaded.get("name", ""):
            size = loaded.get("size", 0)
            size_vram = loaded.get("size_vram", 0)
            gpu_pct = round(size_vram / size * 100) if size > 0 else 0
            logger.info(
                "[%s] %s: %.1f GB total, %.1f GB VRAM (%d%% GPU)",
                label, model_name,
                size / (1024 ** 3), size_vram / (1024 ** 3), gpu_pct,
            )
            return gpu_pct

    logger.warning("[%s] %s not found in /api/ps", label, model_name)
    return 0


def _detect_server_vram_gb(base_url: str, label: str) -> float:
    """Detect the server's available VRAM by inspecting any loaded model.

    Uses /api/ps to see what's already loaded.  If a model is loaded at
    100 % GPU the server has *at least* that much VRAM -- we return the
    model size as a conservative floor.  If GPU < 100 % we know the exact
    VRAM capacity (size_vram is the limit).  Returns 0.0 if nothing is
    loaded or the server is unreachable.
    """
    ps_data = _ollama_api_call(base_url, "/api/ps")
    if not ps_data:
        return 0.0
    for loaded in ps_data.get("models", []):
        size = loaded.get("size", 0)
        size_vram = loaded.get("size_vram", 0)
        if size <= 0:
            continue
        vram_gb = size_vram / (1024 ** 3)
        gpu_pct = round(size_vram / size * 100)
        if gpu_pct >= 100:
            logger.info("[%s] VRAM >= %.1f GB (model fully in GPU)", label, vram_gb)
            return vram_gb
        logger.info("[%s] VRAM = %.1f GB (model partially in GPU, %d%%)", label, vram_gb, gpu_pct)
        return vram_gb
    return 0.0


def _rank_candidates(
    available: set[str], vram_gb: float, label: str,
) -> list[dict]:
    """Return MODEL_CATALOG entries that fit in VRAM, tagged as on-disk or not.

    Each returned dict gets an extra ``on_disk`` bool so callers can
    prefer models already downloaded over those that need a pull.
    """
    candidates: list[dict] = []
    for entry in MODEL_CATALOG:
        if entry["context"] < MIN_CONTEXT_REQUIRED:
            continue
        fits_vram = vram_gb == 0.0 or entry["vram_gb"] <= vram_gb
        if not fits_vram:
            logger.debug(
                "[%s] Skipping %s (needs %.1f GB, only %.1f GB VRAM)",
                label, entry["name"], entry["vram_gb"], vram_gb,
            )
            continue
        on_disk = _find_matching_model(entry["name"], available) is not None
        candidates.append({**entry, "on_disk": on_disk})
    return candidates


def _provision_server(base_url: str, label: str) -> dict | None:
    """Smart auto-provisioning: pick the highest-quality model that fits 100 %
    in the server's VRAM while meeting our context-window requirements.

    Selection priority (highest to lowest):
      1. Already loaded + 100 % GPU  (zero cost)
      2. On disk + fits VRAM         (fast load, no download)
      3. Not on disk + fits VRAM     (needs pull -- expensive)
      4. CPU fallback                (last resort)
    """
    available = _get_server_models(base_url)
    if available is None:
        logger.error("[%s] Server unreachable at %s", label, base_url)
        return None
    logger.info("[%s] Available models on disk: %s", label, available or "(none)")

    # ---- Tier 1: reuse whatever is already loaded and fits well ----
    ps_data = _ollama_api_call(base_url, "/api/ps")
    vram_gb = _detect_server_vram_gb(base_url, label)

    if ps_data:
        for loaded in ps_data.get("models", []):
            loaded_name = loaded.get("name", "")
            size = loaded.get("size", 0)
            size_vram = loaded.get("size_vram", 0)
            gpu_pct = round(size_vram / size * 100) if size > 0 else 0
            if gpu_pct >= 100:
                logger.info(
                    "[%s] Reusing already-loaded %s (100%% GPU, zero cost)",
                    label, loaded_name,
                )
                return {
                    "backend": "ollama",
                    "base_url": base_url,
                    "model": loaded_name,
                    "api_key": "ollama",
                    "gpu_percent": gpu_pct,
                }

    # ---- Build ranked candidate list filtered by VRAM ----
    candidates = _rank_candidates(available, vram_gb, label)
    if candidates:
        logger.info(
            "[%s] %d candidate models (VRAM=%.1f GB): %s",
            label, len(candidates), vram_gb,
            ", ".join(c["name"] for c in candidates),
        )

    # ---- Tier 2: on-disk candidates (fast load, no download) ----
    on_disk = [c for c in candidates if c["on_disk"]]
    for candidate in on_disk:
        match = _find_matching_model(candidate["name"], available)
        if match:
            config = _try_model_on_server(base_url, match, label)
            if config and config.get("gpu_percent", 0) >= 95:
                return config

    # ---- Tier 3: pull candidates not on disk ----
    to_pull = [c for c in candidates if not c["on_disk"]]
    for candidate in to_pull:
        if not _pull_model_on_server(base_url, candidate["name"], label):
            continue
        config = _try_model_on_server(base_url, candidate["name"], label)
        if config and config.get("gpu_percent", 0) >= 95:
            return config

    # ---- Tier 4: best on-disk model even if GPU < 100 % ----
    for candidate in on_disk:
        match = _find_matching_model(candidate["name"], available)
        if match:
            config = _try_model_on_server(base_url, match, label)
            if config:
                return config

    # ---- Tier 5: CPU fallback ----
    return _try_cpu_fallback(base_url, label, available)


def _find_matching_model(preferred: str, available: set[str]) -> str | None:
    """Find a model in available set that matches the preferred model name.

    Tries exact match first, then fuzzy match using key tokens
    (base name, size, quantization). This handles variants like
    'mistral:7b-instruct-v0.3-q8_0' matching 'mistral:7b-instruct-q8_0'.
    """
    if preferred in available:
        return preferred
    base_name = preferred.split(":")[0] if ":" in preferred else preferred
    tokens = set(preferred.replace(":", "-").split("-"))
    tokens.add(base_name)
    for candidate in sorted(available):
        candidate_base = candidate.split(":")[0] if ":" in candidate else candidate
        if candidate_base != base_name:
            continue
        candidate_tokens = set(candidate.replace(":", "-").split("-"))
        if tokens.issubset(candidate_tokens):
            logger.info("Fuzzy match: '%s' -> '%s'", preferred, candidate)
            return candidate
    return None


def _try_cpu_fallback(
    base_url: str, label: str, available: set[str],
) -> dict | None:
    """Phase 3: Fall back to small CPU-friendly model."""
    logger.warning("[%s] No GPU-suitable model, trying CPU fallback: %s", label, CPU_FALLBACK_MODEL)
    actual_model = _find_matching_model(CPU_FALLBACK_MODEL, available)
    if not actual_model:
        if not _pull_model_on_server(base_url, CPU_FALLBACK_MODEL, label):
            logger.error("[%s] Cannot provision any model, skipping server", label)
            return None
        actual_model = CPU_FALLBACK_MODEL
    result = _ollama_api_call(
        base_url,
        "/api/generate",
        method="POST",
        body={"model": actual_model, "prompt": HEALTH_CHECK_PROMPT, "stream": False},
        timeout=MODEL_LOAD_TIMEOUT,
    )
    if result and "response" in result:
        logger.info("[%s] READY (CPU): %s", label, actual_model)
        return {
            "backend": "ollama",
            "base_url": base_url,
            "model": actual_model,
            "api_key": "ollama",
            "gpu_percent": 0,
        }
    logger.error("[%s] CPU fallback failed, skipping server", label)
    return None


def _build_server_configs(server_list: str) -> list[dict]:
    """Parse --servers string and auto-provision each Ollama server.

    Accepts comma-separated host:port or just hostnames (default port 11434).
    Each server is auto-provisioned: detect best model, pull if needed, health check.
    """
    configs: list[dict] = []
    for entry in server_list.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            entry = f"{entry}:11434"
        base_url = f"http://{entry}/v1"
        logger.info("--- Provisioning server: %s ---", entry)
        config = _provision_server(base_url, label=entry)
        if config:
            configs.append(config)
        else:
            logger.warning("Skipping server %s (provisioning failed)", entry)

    if configs:
        logger.info("--- Server Fleet Summary ---")
        for index, config in enumerate(configs):
            logger.info(
                "  Server %d: %s -> %s (%d%% GPU)",
                index, config["base_url"], config["model"],
                config.get("gpu_percent", 0),
            )
    return configs


# ---------------------------------------------------------------------------
# OllamaFleetManager — Subnet Discovery + Health Check + Failover
# ---------------------------------------------------------------------------


class OllamaFleetManager:
    """Manages a dynamic fleet of Ollama servers with auto-discovery and failover.

    Features:
    - Subnet scanning to find Ollama servers on default port
    - Automatic model provisioning per server
    - Periodic health checks with dead-server detection
    - Work rebalancing when servers join or leave the fleet
    """

    def __init__(
        self,
        scan_range: str = "",
        explicit_servers: str = "",
    ):
        self._scan_range = scan_range
        self._explicit = explicit_servers
        self._lock = threading.Lock()
        self._active_configs: list[dict] = []
        self._dead_servers: set[str] = set()
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None

    # -- Public API ---------------------------------------------------------

    def start(self) -> list[dict]:
        """Discover servers, provision them, start health monitor. Returns configs."""
        discovered = self._discover_servers()
        self._active_configs = self._provision_all(discovered)
        if not self._active_configs:
            logger.error("No Ollama servers available after provisioning")
            return []
        self._start_monitor()
        return list(self._active_configs)

    def stop(self) -> None:
        """Stop the health monitor thread."""
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)

    def get_healthy_configs(self) -> list[dict]:
        """Return current list of healthy server configs (thread-safe)."""
        with self._lock:
            return list(self._active_configs)

    def mark_server_dead(self, base_url: str) -> None:
        """Mark a server as dead (called by workers on repeated failures)."""
        with self._lock:
            self._dead_servers.add(base_url)
            self._active_configs = [
                cfg for cfg in self._active_configs
                if cfg["base_url"] != base_url
            ]
            count = len(self._active_configs)
        logger.warning("Server %s marked DEAD (%d servers remain)", base_url, count)

    # -- Subnet Scanning ----------------------------------------------------

    def _discover_servers(self) -> list[str]:
        """Find Ollama servers via subnet scan + explicit list + localhost."""
        found: list[str] = []

        if self._is_ollama_server("127.0.0.1"):
            found.append("localhost")

        if self._explicit:
            for entry in self._explicit.split(","):
                entry = entry.strip()
                if entry and entry not in found:
                    found.append(entry)

        scan_targets = self._build_scan_targets()
        if scan_targets:
            scanned = self._scan_subnet(scan_targets)
            for host in scanned:
                if host not in found:
                    found.append(host)

        logger.info("Discovered %d Ollama server(s): %s", len(found), found)
        return found

    def _build_scan_targets(self) -> list[str]:
        """Build list of IPs to scan from CIDR or auto-detect."""
        if self._scan_range:
            return self._parse_cidr(self._scan_range)
        return self._auto_detect_subnet()

    def _auto_detect_subnet(self) -> list[str]:
        """Detect local subnet by finding the default gateway IP range."""
        local_ip = self._get_local_ip()
        if not local_ip:
            logger.warning("Cannot detect local IP for subnet scan")
            return []
        octets = local_ip.rsplit(".", 1)
        if len(octets) != 2:
            return []
        base = octets[0]
        logger.info("Auto-detected subnet: %s.0/24 (from %s)", base, local_ip)
        return [f"{base}.{i}" for i in range(1, 255)]

    @staticmethod
    def _get_local_ip() -> str:
        """Get local IP by connecting to a public DNS (no data sent)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.connect(("8.8.8.8", 53))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except OSError:
            return ""

    @staticmethod
    def _parse_cidr(cidr: str) -> list[str]:
        """Parse a CIDR like 192.168.1.0/24 into a list of host IPs."""
        if "/" not in cidr:
            base = cidr.rsplit(".", 1)[0]
            return [f"{base}.{i}" for i in range(1, 255)]
        parts = cidr.split("/")
        base_ip = parts[0]
        prefix = int(parts[1])
        if prefix != 24:
            logger.warning("Only /24 subnets supported, got /%d", prefix)
            base = base_ip.rsplit(".", 1)[0]
            return [f"{base}.{i}" for i in range(1, 255)]
        base = base_ip.rsplit(".", 1)[0]
        return [f"{base}.{i}" for i in range(1, 255)]

    def _scan_subnet(self, targets: list[str]) -> list[str]:
        """Scan a list of IPs for Ollama on default port. Returns responsive hosts."""
        logger.info("Scanning %d IPs for Ollama on port %d...", len(targets), OLLAMA_PORT)
        found: list[str] = []
        lock = threading.Lock()

        def _probe(ip: str) -> None:
            if self._is_ollama_server(ip):
                with lock:
                    found.append(ip)

        with ThreadPoolExecutor(max_workers=SUBNET_SCAN_THREADS) as pool:
            pool.map(_probe, targets)

        logger.info("Subnet scan found %d Ollama server(s): %s", len(found), found)
        return found

    @staticmethod
    def _is_ollama_server(ip: str) -> bool:
        """Quick probe: TCP connect + /api/tags check."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(SUBNET_SCAN_TIMEOUT)
            result = sock.connect_ex((ip, OLLAMA_PORT))
            sock.close()
            if result != 0:
                return False
        except OSError:
            return False

        data = _ollama_api_call(f"http://{ip}:{OLLAMA_PORT}/v1", "/api/tags", timeout=3)
        return data is not None

    # -- Provisioning -------------------------------------------------------

    def _provision_all(self, hosts: list[str]) -> list[dict]:
        """Provision all discovered hosts in parallel."""
        configs: list[dict] = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {}
            for host in hosts:
                if ":" not in host:
                    host = f"{host}:{OLLAMA_PORT}"
                base_url = f"http://{host}/v1"
                future = pool.submit(_provision_server, base_url, label=host)
                futures[future] = host

            for future in as_completed(futures):
                host = futures[future]
                try:
                    config = future.result()
                    if config:
                        configs.append(config)
                    else:
                        logger.warning("Provisioning failed for %s", host)
                except Exception:
                    logger.exception("Error provisioning %s", host)

        if configs:
            self._log_fleet_summary(configs)
        return configs

    @staticmethod
    def _log_fleet_summary(configs: list[dict]) -> None:
        """Log a summary table of the fleet."""
        logger.info("=== Fleet Summary: %d servers ===", len(configs))
        for index, cfg in enumerate(configs):
            logger.info(
                "  [%d] %s -> %s (%d%% GPU)",
                index, cfg["base_url"], cfg["model"],
                cfg.get("gpu_percent", 0),
            )

    # -- Health Monitor -----------------------------------------------------

    def _start_monitor(self) -> None:
        """Start background thread for periodic health checks + rediscovery."""
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="fleet-monitor",
            daemon=True,
        )
        self._monitor_thread.start()
        logger.info("Fleet health monitor started (check every %ds)", FLEET_HEALTH_INTERVAL)

    def _monitor_loop(self) -> None:
        """Background loop: health check existing servers, rediscover periodically."""
        cycles_since_rediscovery = 0
        rediscovery_cycles = max(1, FLEET_REDISCOVERY_INTERVAL // FLEET_HEALTH_INTERVAL)

        while not self._stop_event.is_set():
            self._stop_event.wait(FLEET_HEALTH_INTERVAL)
            if self._stop_event.is_set():
                break

            self._check_fleet_health()
            cycles_since_rediscovery += 1

            if cycles_since_rediscovery >= rediscovery_cycles:
                cycles_since_rediscovery = 0
                self._rediscover_servers()

    def _check_fleet_health(self) -> None:
        """Ping each active server; remove dead ones."""
        with self._lock:
            configs_snapshot = list(self._active_configs)

        dead: list[str] = []
        for config in configs_snapshot:
            base_url = config["base_url"]
            label = base_url.replace("http://", "").replace("/v1", "")
            data = _ollama_api_call(base_url, "/api/tags", timeout=5)
            if data is None:
                logger.warning("[health] Server %s UNREACHABLE", label)
                dead.append(base_url)
            else:
                logger.debug("[health] Server %s OK", label)

        if dead:
            with self._lock:
                for url in dead:
                    self._dead_servers.add(url)
                self._active_configs = [
                    cfg for cfg in self._active_configs
                    if cfg["base_url"] not in dead
                ]
                remaining = len(self._active_configs)
            logger.warning(
                "[health] Removed %d dead server(s), %d remain",
                len(dead), remaining,
            )

    def _rediscover_servers(self) -> None:
        """Scan for new servers that weren't in the fleet before."""
        with self._lock:
            known_urls = {cfg["base_url"] for cfg in self._active_configs}

        new_hosts = self._discover_servers()
        new_to_provision: list[str] = []
        for host in new_hosts:
            if ":" not in host:
                host = f"{host}:{OLLAMA_PORT}"
            url = f"http://{host}/v1"
            if url not in known_urls:
                new_to_provision.append(host)

        if not new_to_provision:
            return

        logger.info("[rediscovery] Found %d new server(s): %s", len(new_to_provision), new_to_provision)
        new_configs = self._provision_all(new_to_provision)
        if new_configs:
            with self._lock:
                self._active_configs.extend(new_configs)
                total = len(self._active_configs)
            logger.info("[rediscovery] Fleet expanded to %d servers", total)


def _queue_worker(
    analyzer: IdeaAnalyzer,
    server_label: str,
    work_queue: queue.Queue,
    results_lock: threading.Lock,
    shared_results: dict[int, dict],
    progress: dict,
    fleet: OllamaFleetManager | None = None,
) -> int:
    """Worker that pulls items from a shared queue for natural load-balancing."""
    consecutive_failures = 0
    max_consecutive_failures = 3
    items_done = 0

    while True:
        try:
            orig_idx, idea = work_queue.get(timeout=2.0)
        except queue.Empty:
            break

        batch_items = analyzer._prepare_batch([(orig_idx, idea)])

        try:
            idea_data, endpoints = batch_items[0]
            prompt = analyzer._build_user_prompt(idea_data, endpoints)
            result = analyzer._call_ai(prompt)
            consecutive_failures = 0
        except DailyLimitExhausted:
            logger.warning("[%s] Daily limit hit after %d items", server_label, items_done)
            work_queue.put((orig_idx, idea))
            break
        except Exception:
            consecutive_failures += 1
            logger.exception("[%s] Failed on idea %d (%d consecutive)", server_label, orig_idx, consecutive_failures)
            if consecutive_failures >= max_consecutive_failures and fleet:
                logger.error("[%s] %d consecutive failures -- marking server DEAD", server_label, consecutive_failures)
                fleet.mark_server_dead(analyzer.backend_config["base_url"])
                work_queue.put((orig_idx, idea))
                break
            result = analyzer._unclassified_fallback()

        analyzer._save_batch_results(
            [(orig_idx, idea)],
            [result],
            {},
        )

        with results_lock:
            shared_results[orig_idx] = result
            progress["done"] += 1
            done = progress["done"]
            total = progress["total"]

        items_done += 1
        logger.info(
            "[%s] %d done (overall %d/%d)",
            server_label, items_done, done, total,
        )
        time.sleep(INTER_REQUEST_DELAY)

    return items_done


def analyze_with_fleet(
    fleet: OllamaFleetManager,
    api_index: dict,
    ideas: list[dict],
    refresh: bool = False,
) -> list[dict]:
    """Run analysis using dynamic fleet with failover and rebalancing."""
    total = len(ideas)
    results: dict[int, dict] = {}
    uncached: list[tuple[int, dict]] = []

    for index, idea in enumerate(ideas):
        if not refresh:
            cached = load_cached_response(CACHE_DIR, idea["content_hash"])
            if cached:
                results[index] = cached
                continue
        uncached.append((index, idea))

    cached_count = total - len(uncached)
    configs = fleet.get_healthy_configs()
    logger.info(
        "Fleet analysis: cached=%d, uncached=%d, servers=%d",
        cached_count, len(uncached), len(configs),
    )

    if not uncached:
        return [results.get(i, IdeaAnalyzer._unclassified_fallback()) for i in range(total)]

    remaining = list(uncached)

    while remaining:
        configs = fleet.get_healthy_configs()
        if not configs:
            logger.error("No healthy servers available -- %d ideas unprocessed", len(remaining))
            break

        batch_results, remaining = _run_fleet_batch(
            fleet, configs, api_index, remaining, refresh,
        )
        results.update(batch_results)

        if remaining:
            logger.info(
                "Rebalancing %d orphaned ideas across %d healthy servers",
                len(remaining), len(fleet.get_healthy_configs()),
            )

    fleet.stop()
    return [results.get(i, IdeaAnalyzer._unclassified_fallback()) for i in range(total)]


def _run_fleet_batch(
    fleet: OllamaFleetManager,
    configs: list[dict],
    api_index: dict,
    work_items: list[tuple[int, dict]],
    refresh: bool,
) -> tuple[dict[int, dict], list[tuple[int, dict]]]:
    """Run work across the fleet using a shared queue with dynamic server spawning."""
    work_queue: queue.Queue[tuple[int, dict]] = queue.Queue()
    for item in work_items:
        work_queue.put(item)

    server_count = len(configs)
    for idx, cfg in enumerate(configs):
        label = cfg["base_url"].replace("http://", "").replace("/v1", "")
        logger.info("  [%d] %s", idx, label)

    results_lock = threading.Lock()
    batch_results: dict[int, dict] = {}
    progress = {"done": 0, "total": len(work_items)}
    known_urls: set[str] = {cfg["base_url"] for cfg in configs}
    next_server_idx = server_count

    max_workers = max(server_count * 2, 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: dict = {}
        for idx, cfg in enumerate(configs):
            analyzer = IdeaAnalyzer(cfg, api_index, refresh=refresh, batch_size=1)
            label = f"server-{idx}"
            future = executor.submit(
                _queue_worker, analyzer, label, work_queue,
                results_lock, batch_results, progress, fleet,
            )
            futures[future] = label

        while futures:
            current_configs = fleet.get_healthy_configs()
            for cfg in current_configs:
                url = cfg["base_url"]
                if url not in known_urls and not work_queue.empty():
                    known_urls.add(url)
                    server_label = f"server-{next_server_idx}"
                    next_server_idx += 1
                    short = url.replace("http://", "").replace("/v1", "")
                    logger.info("Spawning worker %s for new server: %s", server_label, short)
                    analyzer = IdeaAnalyzer(cfg, api_index, refresh=refresh, batch_size=1)
                    future = executor.submit(
                        _queue_worker, analyzer, server_label, work_queue,
                        results_lock, batch_results, progress, fleet,
                    )
                    futures[future] = server_label

            done_futures = [f for f in futures if f.done()]
            for finished in done_futures:
                label = futures.pop(finished)
                try:
                    items_done = finished.result()
                    logger.info("Worker %s finished (%d items)", label, items_done)
                except Exception:
                    logger.exception("Worker %s failed", label)

            if futures:
                time.sleep(2)

    orphaned: list[tuple[int, dict]] = []
    while not work_queue.empty():
        try:
            orphaned.append(work_queue.get_nowait())
        except queue.Empty:
            break

    return batch_results, orphaned


def main() -> None:
    """Entry point: parse, analyze, deduplicate, report."""
    parser = build_arg_parser()
    args = parser.parse_args()
    load_dotenv()
    configure_logging(args.verbose)

    start_time = time.time()

    csv_path = Path(args.input)
    if not csv_path.exists():
        logger.error("Input file not found: %s", csv_path)
        return

    idea_parser = IdeaParser()
    ideas = idea_parser.parse(csv_path)
    if not ideas:
        logger.error("No valid ideas found in %s -- exiting", csv_path)
        return

    backend_config = AiBackendDetector().detect()

    index_builder = ApiIndexBuilder()
    index_cache = CACHE_DIR / "api_index.json"
    if args.refresh_index and index_cache.exists():
        index_cache.unlink()
    api_index = index_builder.build(OPENAPI_PATH, index_cache)

    cached_count = count_cache_files(CACHE_DIR)
    logger.info(
        "Cached: %d / Total: %d -- will analyze %d new ideas",
        cached_count,
        len(ideas),
        max(0, len(ideas) - cached_count),
    )

    if args.scan or args.servers:
        fleet = OllamaFleetManager(
            scan_range=getattr(args, "scan_range", ""),
            explicit_servers=args.servers,
        )
        if not args.scan:
            fleet._scan_range = ""
        configs = fleet.start()
        if not configs:
            logger.error("No servers available, falling back to auto-detect")
            fleet.stop()
            analyzer = IdeaAnalyzer(
                backend_config, api_index,
                refresh=args.refresh, batch_size=args.batch_size,
            )
            analyses = analyzer.analyze_all(ideas)
        else:
            analyses = analyze_with_fleet(
                fleet, api_index, ideas, refresh=args.refresh,
            )
            analyzer = IdeaAnalyzer(
                configs[0], api_index, refresh=args.refresh, batch_size=1,
            )
    else:
        analyzer = IdeaAnalyzer(
            backend_config,
            api_index,
            refresh=args.refresh,
            batch_size=args.batch_size,
        )
        analyses = analyzer.analyze_all(ideas)

    duplicate_groups = analyzer.detect_duplicates(ideas, analyses)
    clusters = IdeaAnalyzer.build_clusters(ideas, analyses, duplicate_groups)
    all_ai_inspired = aggregate_ai_inspired(ideas, analyses)

    logger.info(
        "Clusters: %d (from %d ideas, %d duplicate groups)",
        len(clusters),
        len(ideas),
        len(duplicate_groups),
    )

    report = ReportGenerator(clusters, all_ai_inspired)
    md_path = DATA_DIR / "mist_ideas_analysis.md"
    json_path = DATA_DIR / "mist_ideas_analysis.json"
    csv_path_out = DATA_DIR / "mist_ideas_analysis.csv"
    report.generate_markdown(md_path)
    report.generate_json(json_path)
    report.generate_csv(csv_path_out)

    elapsed = time.time() - start_time
    logger.info("Completed in %.1f seconds", elapsed)

    counts: dict[str, int] = {}
    for cluster in clusters:
        label = cluster["classification"]
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items()):
        logger.info("  %s: %d", label, count)


if __name__ == "__main__":
    main()
