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

VALID_CLASSIFICATIONS = frozenset(
    {
        "REPORT_EXPORT",
        "API_ENHANCEMENT",
        "HYBRID",
        "GUI_ONLY",
        "HARDWARE_FEATURE",
        "ALREADY_SUPPORTED",
        "UNCLASSIFIED",
    }
)

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
    {"name": "mixtral:8x7b", "vram_gb": 10.0, "context": 32768, "quality": 1},
    {"name": "mistral:7b-instruct-q8_0", "vram_gb": 7.8, "context": 32768, "quality": 2},
    {"name": "qwen2.5:7b-instruct", "vram_gb": 4.7, "context": 32768, "quality": 3},
    {"name": "qwen3:8b", "vram_gb": 4.9, "context": 32768, "quality": 4},
    {"name": "mistral:7b", "vram_gb": 4.1, "context": 32768, "quality": 5},
    {"name": "llama3.1:8b", "vram_gb": 5.0, "context": 131072, "quality": 6},
    {"name": "gemma3:4b-it-qat", "vram_gb": 2.5, "context": 8192, "quality": 7},
    {"name": "llama3.2:3b", "vram_gb": 2.0, "context": 8192, "quality": 8},
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
        help=("Comma-separated Ollama servers (host:port). " "Example: localhost:11434,192.168.1.86:11434"),
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
        help=("CIDR or base IP for subnet scan (default: auto-detect). " "Example: 192.168.1.0/24"),
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
                        "Exact duplicate row %d (same as earlier row), " "incrementing demand",
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

        combined = normalize(title) + "\n" + normalize(desc) + "\n" + normalize(comments_json)
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

    @staticmethod
    def _requested_backend_name() -> str:
        """Normalize the requested backend name once for reuse."""
        return os.environ.get("AI_BACKEND", "").lower()  # Reuse one normalized value across detection steps.

    def _detect_requested_ollama(self) -> dict | None:
        """Honor an explicit Ollama request before trying cloud backends."""
        if self._requested_backend_name() != "ollama":  # Skip the local path unless the operator asked for it first.
            return None  # Defer to the normal backend priority order.
        return self._detect_ollama()  # Preserve explicit Ollama preference when it can be provisioned.

    def _detect_configured_backend(self) -> dict | None:
        """Check non-Ollama backends in priority order."""
        for detector in (  # Keep the provider order centralized so detect() stays linear.
            self._try_github_models,
            self._try_ava_mcp,
            self._try_generic,
        ):
            config = detector()  # Ask this provider whether it is configured and reachable enough to use.
            if config:  # First configured backend wins the priority race.
                return config  # Stop once a usable backend is found.
        return None  # Signal that no cloud-style backend is available.

    def detect(self) -> dict:
        """Return backend config dict or raise RuntimeError."""
        requested = self._detect_requested_ollama()  # Honor an explicit local-backend request before any fallback.
        if requested:  # Requested Ollama should win when it is healthy.
            return requested  # Return immediately to preserve operator intent.
        configured = self._detect_configured_backend()  # Check hosted backends using the existing priority order.
        if configured:  # First configured remote backend wins.
            return configured  # Reuse the existing backend selection contract.
        fallback = self._detect_ollama()  # Keep the historical final local-backend probe for compatibility.
        if fallback:  # Return the local backend when that last probe succeeds.
            return fallback  # Preserve original method behavior.
        raise RuntimeError(  # Surface a single actionable error once every backend path has failed.
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
        logger.info("Backend: Generic OpenAI (model=%s)", model)
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
        backend_env = self._requested_backend_name()  # Reuse the normalized environment value for the request gate.
        if backend_env != "ollama":  # Avoid auto-starting local containers unless explicitly requested.
            logger.debug(
                "Ollama not requested (AI_BACKEND=%s)", backend_env or "unset"
            )  # Explain why local startup was skipped.
            return None  # Leave backend selection to the hosted providers.
        runtime = self._find_container_runtime()  # Discover whether Podman or Docker can host Ollama locally.
        if not runtime:  # Containerized Ollama cannot run without a runtime.
            logger.debug("No container runtime found for Ollama")  # Preserve the existing diagnostic signal.
            return None  # Stop before any local provisioning work.
        model = (
            os.environ.get("AI_MODEL") or self._select_model_by_vram()
        )  # Prefer an explicit model before auto-sizing by VRAM.
        if not self._prepare_ollama_backend(
            runtime, model
        ):  # Provision container, model, and health in one cohesive step.
            return None  # Abort when any local prerequisite fails.
        logger.info(
            "Backend: Local Ollama (model=%s, runtime=%s)", model, runtime
        )  # Keep the operator-facing success log.
        return self._ollama_backend_config(model)  # Return the standard local backend contract.

    def _prepare_ollama_backend(self, runtime: str, model: str) -> bool:
        """Provision container, model, and health prerequisites for Ollama."""
        if not self._ensure_container_running(runtime):  # Start the container before pulling or probing models.
            return False  # No container means no local backend.
        if not self._pull_model(runtime, model):  # Make sure the requested model exists locally.
            return False  # Provisioning cannot continue without the model.
        return self._health_check()  # Final probe confirms the API is ready for actual analysis calls.

    @staticmethod
    def _ollama_backend_config(model: str) -> dict:
        """Build the standard local Ollama backend config."""
        return {  # Match the config shape expected by the OpenAI-compatible client layer.
            "backend": "ollama",  # Identify the backend family for downstream feature flags.
            "base_url": f"http://localhost:{OLLAMA_PORT}/v1",  # Point the client at the local AI endpoint.
            "model": model,  # Preserve the resolved model choice for later logging and requests.
            "api_key": "ollama",  # Ollama ignores the key but the client requires one.
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

        gpu_flag = ["--device", "nvidia.com/gpu=all"] if runtime == "podman" else ["--gpus", "all"]
        # OLLAMA_SCHED_SPREAD: offloads MoE expert weights to CPU RAM,
        #   keeping attention/embedding layers on GPU (critical for Mixtral 8x7b).
        # OLLAMA_KV_CACHE_TYPE: q8_0 halves KV cache VRAM with negligible
        #   quality loss vs f16 default. Combined with MoE offload this lets
        #   Mixtral run on 12 GB VRAM instead of 24 GB+.
        env_flags = [
            "-e",
            "OLLAMA_SCHED_SPREAD=1",
            "-e",
            "OLLAMA_KV_CACHE_TYPE=q8_0",
        ]
        cmd = [
            runtime,
            "run",
            "-d",
            "--name",
            OLLAMA_CONTAINER,
            *gpu_flag,
            *env_flags,
            "-p",
            f"{OLLAMA_PORT}:{OLLAMA_PORT}",
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
        import urllib.error
        import urllib.request

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
        scored: list[tuple[int, dict]] = []  # Capture only endpoints that match at least one search term.
        terms_lower = [
            term.lower() for term in query_terms
        ]  # Normalize once so scoring stays cheap inside the nested loops.
        for tag, endpoints in api_index.items():  # Search every endpoint under every OpenAPI tag.
            tag_lower = tag.lower()  # Include tag names in the searchable text without repeated lowercasing.
            for endpoint in endpoints:  # Score each endpoint independently for ranking.
                score = ApiIndexBuilder._score_endpoint_match(
                    endpoint, tag_lower, terms_lower
                )  # Isolate match scoring from traversal.
                if score > 0:  # Keep only endpoints with at least one term hit.
                    scored.append((score, endpoint))  # Preserve both score and endpoint for later sorting.
        scored.sort(key=lambda pair: pair[0], reverse=True)  # Highest term-hit count should appear first.
        return [ep for _, ep in scored[:10]]  # Trim to the caller's documented top-ten result limit.

    @staticmethod
    def _score_endpoint_match(endpoint: dict, tag_lower: str, terms_lower: list[str]) -> int:
        """Count how many query terms appear in an endpoint summary."""
        searchable = (  # Merge the searchable fields once so the per-term loop stays simple.
            endpoint["path"].lower() + " " + endpoint["summary"].lower() + " " + tag_lower
        )
        return sum(1 for term in terms_lower if term in searchable)  # Higher hit counts indicate stronger relevance.


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
    return sum(1 for f in cache_dir.iterdir() if f.suffix == ".json" and f.name != "api_index.json")


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
        return """You are a technical analyst classifying Mist community feature ideas
by MistHelper feasibility.

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
Ideas phrased as "add a column to the portal" or "show X in the dashboard"
are NOT automatically GUI_ONLY. If the underlying data IS accessible via a
documented Mist REST API endpoint, MistHelper can retrieve and present it.
Classify as REPORT_EXPORT or API_ENHANCEMENT.

## Classification Labels
- REPORT_EXPORT: Data extraction -- the idea asks for data that IS available
  via the Mist API and MistHelper can export it (CSV, SQLite, report)
- API_ENHANCEMENT: The idea asks for an action or workflow that the Mist API
  supports and MistHelper could automate (firmware, config push, bulk
  operations)
- HYBRID: The idea has both API-actionable and GUI-only components;
  MistHelper can partially address it
- GUI_ONLY: The idea requires changes to the Mist portal GUI that the API
  cannot replicate or expose
- HARDWARE_FEATURE: The idea requires hardware capabilities, radio firmware
  changes, or AP/switch physical behavior not controllable via API
- ALREADY_SUPPORTED: MistHelper already has this capability (or the Mist API
  already provides it natively)
- UNCLASSIFIED: Cannot determine feasibility -- the idea is too vague or
  references unknown capabilities

## AI_INSPIRED Instruction
If analyzing an idea reveals a valuable capability that neither the Mist portal
NOR MistHelper currently supports, but COULD be built as a new MistHelper
feature using existing API endpoints, record it in the ai_inspired_ideas list.
Include the source idea title that inspired it.

## Response Format
You will receive exactly ONE idea. Respond with a single JSON object.

ALL fields below are REQUIRED. Do NOT leave any field as null or empty unless
genuinely not applicable.

### REQUIRED Fields (must ALL be populated):
1. **classification**: One of the 7 labels above
2. **confidence**: "high", "medium", or "low"
3. **themes**: At least 2-3 topic tags (e.g. "inventory", "firmware",
   "NAC", "switch", "WLAN", "monitoring")
4. **rationale**: 2-3 sentences explaining your classification reasoning
5. **misthelper_enhancement**: A specific, actionable suggestion for how
   MistHelper could address this idea. Describe what the feature would do.
   Write "Not applicable - requires GUI/hardware changes" ONLY for GUI_ONLY
   or HARDWARE_FEATURE classifications.
6. **possible_duplicate_titles**: List any idea titles from the provided
   context that sound similar. Empty list [] ONLY if truly unique.
7. **is_foundational**: true if implementing this idea would enable or
   simplify multiple other feature requests. Think about whether this is a
   building-block capability.
8. **unlocks**: If is_foundational is true, list the types of features this
   would enable. Otherwise [].
9. **ai_inspired_ideas**: At least ONE new feature idea inspired by analyzing
   this request. Think: "What RELATED capability could MistHelper build using
   the API?" Every idea should spark at least one inspired idea.

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
  "rationale": "The Mist API provides switch port configuration data via the
  sites devices stats endpoint. MistHelper can extract port-to-VLAN mappings,
  but the visual topology view requested requires GUI changes.",
  "misthelper_enhancement": "Add a 'VLAN Port Report' operation that queries
  all switch port configs and generates a CSV grouped by VLAN, showing port
  name, status, speed, and assigned device.",
  "possible_duplicate_titles": ["Show VLAN assignments per port"],
  "is_foundational": true,
  "unlocks": ["VLAN audit reports", "port utilization dashboards",
  "switch migration planning"],
  "ai_inspired_ideas": [
    {
      "title": "VLAN Consistency Checker",
      "description": "Compare VLAN assignments across all switches in a site
      and flag inconsistencies or orphaned VLANs not assigned to any port.",
      "source_idea_title": "Switch port config - show all ports in a VLAN",
      "rationale": "VLAN misconfiguration is a common NOC issue. The API
      exposes all port configs but no tool cross-references them for
      consistency."
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
                endpoint_lines.append(f"- {ep['method']} {ep['path']}: {ep['summary']}")
            parts.append("\n## Relevant Mist API Endpoints\n" + "\n".join(endpoint_lines))

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
                validated = [self._validate_response(item) or self._unclassified_fallback() for item in raw]
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
        return [self._unclassified_fallback() for _ in range(count)]

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
        total = len(ideas)  # Preserve original result ordering for the final list.
        results, uncached = self._split_cached_ideas(ideas)  # Separate cache hits so AI calls only cover misses.
        cached_count = total - len(uncached)  # Report cache effectiveness for operators.
        batch_count = self._count_batches(len(uncached))  # Compute once so logging and loop math stay aligned.
        logger.info(  # Keep the existing batch-plan summary before any network work begins.
            "Cached: %d, uncached: %d, batches: %d (size %d)",
            cached_count,
            len(uncached),
            batch_count,
            self.batch_size,
        )
        for batch_num, chunk in self._iter_uncached_batches(uncached):  # Walk the cache misses in stable chunks.
            logger.info(
                "Batch %d/%d (%d ideas)", batch_num, batch_count, len(chunk)
            )  # Preserve per-batch progress logging.
            try:  # Daily quota exhaustion should stop cleanly while keeping prior cacheable work.
                batch_results = self._analyze_batch_chunk(
                    chunk
                )  # Hide single-vs-batch prompt branching behind one helper.
            except DailyLimitExhausted:  # Respect the existing stop-and-resume-later behavior.
                logger.warning(  # Tell operators why the run stopped partway through.
                    "Daily API quota exhausted at batch %d/%d. " "Re-run later to continue from cache.",
                    batch_num,
                    batch_count,
                )
                break  # Exit so completed cache entries survive for the next run.
            self._save_batch_results(
                chunk, batch_results, results
            )  # Persist each successful chunk immediately for resumability.
            time.sleep(INTER_REQUEST_DELAY)  # Keep the original pacing between requests.
        return [
            results.get(i, self._unclassified_fallback()) for i in range(total)
        ]  # Fill any missing slots with the standard fallback.

    def _split_cached_ideas(
        self,
        ideas: list[dict],
    ) -> tuple[dict[int, dict], list[tuple[int, dict]]]:
        """Separate cached ideas from ideas that still need AI analysis."""
        results: dict[int, dict] = {}  # Preserve cached results in their original index positions.
        uncached: list[tuple[int, dict]] = []  # Queue cache misses for batch analysis.
        for index, idea in enumerate(ideas):  # Walk in source order so final output order stays stable.
            cached = self._load_cached_idea(idea)  # Centralize refresh-aware cache lookup in one place.
            if cached:  # Cache hit means no AI call is needed for this idea.
                results[index] = cached  # Reuse the stored analysis exactly as before.
                continue  # Skip the batch queue for cache hits.
            uncached.append((index, idea))  # Keep misses for later batch processing.
        return results, uncached  # Hand both collections back to analyze_all().

    def _load_cached_idea(self, idea: dict) -> dict | None:
        """Return a cached analysis for one idea when refresh is disabled."""
        if self.refresh:  # Refresh mode intentionally bypasses every cache entry.
            return None  # Force a fresh AI call.
        return load_cached_response(CACHE_DIR, idea["content_hash"])  # Reuse the existing cache layout and validation.

    def _count_batches(self, uncached_count: int) -> int:
        """Return how many analysis batches are required."""
        if not uncached_count:  # Avoid divide-style math when there is nothing left to analyze.
            return 0  # No batches needed when every idea came from cache.
        return (
            uncached_count + self.batch_size - 1
        ) // self.batch_size  # Round up so partial tail batches still count.

    def _iter_uncached_batches(
        self,
        uncached: list[tuple[int, dict]],
    ) -> list[tuple[int, list[tuple[int, dict]]]]:
        """Return numbered chunks for the uncached worklist."""
        batches: list[tuple[int, list[tuple[int, dict]]]] = (
            []
        )  # Materialize batches once so the caller loop stays flat.
        for batch_start in range(
            0, len(uncached), self.batch_size
        ):  # Step through the misses using the configured batch size.
            batch_num = batch_start // self.batch_size + 1  # Convert offsets to human-friendly one-based batch numbers.
            chunk = uncached[batch_start : batch_start + self.batch_size]  # Slice only the work for this batch.
            batches.append((batch_num, chunk))  # Keep the number next to the payload for simpler logging.
        return batches  # Return a simple iterable structure for analyze_all().

    def _analyze_batch_chunk(self, chunk: list[tuple[int, dict]]) -> list[dict]:
        """Analyze one chunk, choosing single-item or batched prompting as needed."""
        batch_items = self._prepare_batch(chunk)  # Resolve related API endpoints before building prompts.
        if len(batch_items) == 1:  # Single ideas can keep the simpler single-result prompt.
            idea, endpoints = batch_items[0]  # Unpack the one prepared batch item.
            prompt = self._build_user_prompt(idea, endpoints)  # Build the detailed single-idea prompt.
            return [self._call_ai(prompt)]  # Wrap the single response so the caller always receives a list.
        prompt = self._build_batch_user_prompt(
            batch_items
        )  # Batch prompts amortize token overhead across multiple ideas.
        return self._call_ai_batch(prompt, len(batch_items))  # Reuse the existing batch response validator.

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
        for (orig_idx, idea), result in zip(
            chunk, batch_results, strict=False
        ):  # Preserve partial results even if the model returns fewer items.
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
                        "content": ("You identify duplicate feature ideas. " "Respond with valid JSON only."),
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
                batch_num,
                total_batches,
                len(batch),
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
        lower_to_actual = {
            title.lower(): title for title in known_titles
        }  # Resolve AI-provided titles against the real source set case-insensitively.
        validated: list[dict] = []  # Keep only groups that map cleanly back to known ideas.
        for group in groups:  # Validate each AI-produced dedup group independently.
            validated_group = IdeaAnalyzer._validate_dedup_group(
                group, lower_to_actual
            )  # Isolate one group's resolution and warning logic.
            if validated_group:  # Only keep groups that still contain at least one valid duplicate.
                validated.append(validated_group)  # Preserve the caller's expected list shape.
        return validated  # Return only resolvable, non-empty dedup groups.

    @staticmethod
    def _validate_dedup_group(group: dict, lower_to_actual: dict[str, str]) -> dict | None:
        """Validate one duplicate group and resolve titles to their canonical casing."""
        canonical = group.get("canonical_title", "")  # Read the AI-selected canonical title defensively.
        resolved = lower_to_actual.get(canonical.lower())  # Normalize casing by mapping back to the known title set.
        if not resolved:  # Unknown canonical titles should not create synthetic clusters.
            logger.warning(
                "Unknown canonical title, skipping: %s", canonical
            )  # Preserve the existing operator warning.
            return None  # Skip groups that do not anchor to a known title.
        duplicates = group.get(
            "duplicate_titles", []
        )  # Read the duplicate list once for reuse in logging and filtering.
        valid_dupes = [
            lower_to_actual[title.lower()] for title in duplicates if title.lower() in lower_to_actual
        ]  # Keep only duplicates that map to real titles.
        skipped = len(duplicates) - len(valid_dupes)  # Track how many AI-suggested titles failed validation.
        if skipped > 0:  # Warn operators when the model invents or misspells duplicate titles.
            logger.warning(
                "%d unknown duplicate titles skipped for '%s'", skipped, resolved
            )  # Keep the original warning semantics.
        if not valid_dupes:  # Empty duplicate lists do not create a meaningful merge group.
            return None  # Drop groups that lost every duplicate during validation.
        return {  # Keep the original output schema for downstream cluster building.
            "canonical_title": resolved,  # Use the resolved source title for stable casing.
            "duplicate_titles": valid_dupes,  # Preserve only validated duplicates.
            "merge_confidence": group.get(
                "merge_confidence", "medium"
            ),  # Carry forward AI confidence for later merge policy.
        }

    @staticmethod
    def build_clusters(
        ideas: list[dict],
        analyses: list[dict],
        duplicate_groups: list[dict],
    ) -> list[dict]:
        """Merge ideas into clusters based on dedup results."""
        title_to_idea = {idea["title"]: idea for idea in ideas}
        title_to_analysis = {}
        for idea, analysis in zip(
            ideas, analyses, strict=False
        ):  # Keep pairing tolerant because upstream recovery can shorten one side.
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
                all_titles,
                canonical,
                title_to_idea,
                title_to_analysis,
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
            matching = [c for c in self.clusters if c["classification"] == label]
            if not matching:
                continue
            matching.sort(key=lambda c: c["demand_count"], reverse=True)
            lines.append(f"## {label} ({len(matching)} clusters)\n")
            for cluster in matching:
                self._write_cluster_entry(lines, cluster)
            lines.append("")

    @staticmethod
    def _append_optional_cluster_line(
        lines: list[str],
        label: str,
        value: str | None,
    ) -> None:
        """Append one markdown bullet only when a value is present."""
        if not value:  # Avoid cluttering the report with empty optional fields.
            return  # Skip blank sections cleanly.
        lines.append(f"- **{label}**: {value}")  # Keep optional details formatted consistently.

    @staticmethod
    def _append_cluster_comments(lines: list[str], cluster: dict) -> None:
        """Append source comment bodies when at least one comment has text."""
        comment_texts = [  # Keep only human-readable comment bodies so blank placeholders disappear from the report.
            comment.get("body", "") for comment in cluster.get("source_comments", []) if comment.get("body")
        ]
        if not comment_texts:  # No visible comments means no report section.
            return  # Leave the cluster entry concise.
        lines.append(
            f"- **Comments**: {' | '.join(comment_texts)}"
        )  # Join multiple comments onto one bullet for readability.

    @staticmethod
    def _write_cluster_entry(lines: list[str], cluster: dict) -> None:
        """Append a single cluster entry."""
        lines.append(f"### {cluster['canonical_title']}")  # Start each cluster with a stable markdown heading.
        lines.append(  # Keep classification and confidence together because they are interpreted as one judgment.
            f"- **Classification**: {cluster['classification']} " f"({cluster['confidence']} confidence)"
        )
        lines.append(f"- **Demand**: {cluster['demand_count']}")  # Surface how many requests fed this cluster.
        ReportGenerator._append_optional_cluster_line(
            lines, "Themes", ", ".join(cluster.get("themes", []))
        )  # Show merged themes only when present.
        lines.append(f"- **Rationale**: {cluster['rationale']}")  # Always expose the AI rationale for reviewer context.
        ReportGenerator._append_optional_cluster_line(
            lines, "Enhancement", cluster.get("misthelper_enhancement")
        )  # Keep enhancement suggestions optional.
        ReportGenerator._append_optional_cluster_line(
            lines, "Possible duplicates", ", ".join(cluster.get("possible_duplicate_of") or [])
        )  # Preserve low-confidence duplicate hints when available.
        if cluster["demand_count"] > 1:  # Only merged clusters need the expanded source-title list.
            titles = ", ".join(cluster["merged_titles"])  # Collapse all merged titles into one readable bullet.
            lines.append(f"- **Merged ideas**: {titles}")  # Help reviewers see exactly what was grouped together.
        ReportGenerator._append_optional_cluster_line(
            lines, "Original description", cluster.get("source_description")
        )  # Include source text only when we actually have it.
        ReportGenerator._append_cluster_comments(
            lines, cluster
        )  # Keep comment flattening logic separate from the main formatter.
        lines.append("")  # Leave a blank line after each cluster for markdown readability.

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
                lines.append(f"- {cluster['canonical_title']} " f"(demand: {cluster['demand_count']})")
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
            lines.append(f"- **Inspired by**: {inspired.get('source_idea_title', 'N/A')}")
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
                    "dependents": [d["canonical_title"] for d in chain["dependents"]],
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
            writer.writerow(
                [
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
                ]
            )
            for cluster in self.clusters:
                comments_text = json.dumps(
                    cluster.get("source_comments", []),
                )
                writer.writerow(
                    [
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
                    ]
                )
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
            result.append(
                {
                    "theme": theme,
                    "clusters": members_sorted,
                    "total_demand": total_demand,
                }
            )

        result.sort(key=lambda t: t["total_demand"], reverse=True)
        return result

    @staticmethod
    def _find_unlock_match(unlock_title: str, clusters: list[dict]) -> dict | None:
        """Resolve one unlock title to the best matching cluster."""
        unlock_lower = unlock_title.lower()  # Normalize once so substring fallback stays cheap and consistent.
        for candidate in clusters:  # Walk the full cluster list only when exact lookup failed.
            if (
                unlock_lower in candidate["canonical_title"].lower()
            ):  # Preserve the original substring fallback behavior.
                return candidate  # First fuzzy match wins, matching prior semantics.
        return None  # Signal that no dependent cluster could be resolved.

    @staticmethod
    def _resolve_unlock_dependents(
        cluster: dict,
        clusters: list[dict],
        title_to_cluster: dict[str, dict],
    ) -> list[dict]:
        """Resolve all dependent clusters unlocked by one foundational cluster."""
        dependents: list[dict] = []  # Keep the dependents in unlock order for readable output.
        for unlock_title in cluster.get("unlocks", []):  # Resolve each unlock title independently.
            dependent = title_to_cluster.get(unlock_title) or ReportGenerator._find_unlock_match(
                unlock_title, clusters
            )  # Prefer exact title matches before fuzzy fallbacks.
            if dependent:  # Keep only unlocks that map to a real cluster.
                dependents.append(dependent)  # Preserve original dependent ordering.
        return dependents  # Hand back the resolved unlock chain for this root cluster.

    @staticmethod
    def build_snowball_chains(clusters: list[dict]) -> list[dict]:
        """Find foundational ideas and what they unlock."""
        title_to_cluster = {
            c["canonical_title"]: c for c in clusters
        }  # Enable fast exact unlock lookups by canonical title.
        chains: list[dict] = []  # Accumulate only foundational clusters that unlock something tangible.
        for cluster in clusters:  # Evaluate every cluster as a potential snowball root.
            if not cluster.get("is_foundational"):  # Non-foundational clusters cannot begin a chain.
                continue  # Skip directly to the next cluster.
            dependents = ReportGenerator._resolve_unlock_dependents(
                cluster, clusters, title_to_cluster
            )  # Keep exact-vs-fuzzy lookup details out of the main loop.
            if dependents:  # Ignore foundational ideas that do not resolve to any dependent cluster.
                chains.append({"root": cluster, "dependents": dependents})  # Preserve the existing report schema.
        chains.sort(key=lambda c: len(c["dependents"]), reverse=True)  # Show the most generative roots first.
        return chains  # Return the report-ready snowball chain list.


# ---------------------------------------------------------------------------
# Main  (T014, T018, T024)
# ---------------------------------------------------------------------------


def aggregate_ai_inspired(
    ideas: list[dict],
    analyses: list[dict],
) -> list[dict]:
    """Collect all ai_inspired_ideas from analyses into a flat list."""
    all_inspired: list[dict] = []
    for idea, analysis in zip(
        ideas, analyses, strict=False
    ):  # Keep flattening resilient when upstream analysis counts drift.
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
    import urllib.error
    import urllib.request

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
    base_url: str,
    model_name: str,
    label: str,
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
    base_url: str,
    model_name: str,
    label: str,
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
    base_url: str,
    model_name: str,
    label: str,
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
                label,
                model_name,
                size / (1024**3),
                size_vram / (1024**3),
                gpu_pct,
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
        vram_gb = size_vram / (1024**3)
        gpu_pct = round(size_vram / size * 100)
        if gpu_pct >= 100:
            logger.info("[%s] VRAM >= %.1f GB (model fully in GPU)", label, vram_gb)
            return vram_gb
        logger.info("[%s] VRAM = %.1f GB (model partially in GPU, %d%%)", label, vram_gb, gpu_pct)
        return vram_gb
    return 0.0


def _rank_candidates(
    available: set[str],
    vram_gb: float,
    label: str,
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
                label,
                entry["name"],
                entry["vram_gb"],
                vram_gb,
            )
            continue
        on_disk = _find_matching_model(entry["name"], available) is not None
        candidates.append({**entry, "on_disk": on_disk})
    return candidates


class ServerProvisioner:
    """Auto-provision the best-fitting Ollama model on one server across five tiers.

    Decomposes the former ``_provision_server`` (CC=24) into small, single-purpose
    methods (each CC <= 5) per the repo 5-Item Rule. Selection priority, highest to
    lowest:
      1. Already loaded + 100 % GPU  (zero cost)
      2. On disk + fits VRAM         (fast load, no download)
      3. Not on disk + fits VRAM     (needs pull -- expensive)
      4. Best on-disk even < 100 % GPU
      5. CPU fallback                (last resort)
    """

    # Minimum GPU placement (percent) a model must reach to win the fast on-disk / pull tiers.
    STRONG_GPU_PERCENT = 95  # Below this we defer to a later, lower-quality tier.

    def __init__(self, base_url: str, label: str) -> None:
        """Capture the target server URL and its log label."""
        self.base_url = base_url  # Ollama v1 API base URL for this server.
        self.label = label  # Human-readable server label used in every log line.
        self._available: set[str] = set()  # Models on disk; populated in provision().
        self._vram_gb: float = 0.0  # Detected GPU VRAM in GB; populated in provision().
        self._candidates: list[dict] = []  # VRAM-fitting ranked candidates; populated in provision().

    def provision(self) -> dict | None:
        """Try each provisioning tier in priority order; return the first usable config."""
        available = _get_server_models(self.base_url)  # Query the on-disk model set (None == unreachable).
        if available is None:  # The server did not answer the model-list call.
            logger.error("[%s] Server unreachable at %s", self.label, self.base_url)  # Record the outage.
            return None  # Cannot provision an unreachable server.
        logger.info("[%s] Available models on disk: %s", self.label, available or "(none)")  # Log inventory.
        self._available = available  # Cache for the tier methods to share.
        self._vram_gb = _detect_server_vram_gb(self.base_url, self.label)  # Detect VRAM once up front.
        self._candidates = self._ranked_candidates()  # Build the VRAM-filtered candidate list once.
        for tier in self._tier_methods():  # Walk the five strategies in priority order.
            config = tier()  # Each tier returns a ready backend config or None.
            if config:  # First tier that yields a usable model wins.
                return config  # Stop at the highest-priority success.
        return None  # No tier could provision a model on this server.

    def _tier_methods(self) -> tuple:
        """Return the five tier callables in priority order (no args; they share instance state)."""
        return (  # Ordered highest-quality/cheapest first.
            self._tier_reuse_loaded,  # Tier 1: reuse a 100% GPU model already in memory.
            self._tier_on_disk,  # Tier 2: load an on-disk model that lands strongly on GPU.
            self._tier_pull,  # Tier 3: pull a missing model that lands strongly on GPU.
            self._tier_best_on_disk,  # Tier 4: accept the best on-disk model at any GPU level.
            self._tier_cpu_fallback,  # Tier 5: small CPU-only model as a last resort.
        )

    def _ranked_candidates(self) -> list[dict]:
        """Rank VRAM-fitting candidate models and log the shortlist."""
        candidates = _rank_candidates(self._available, self._vram_gb, self.label)  # Filter+rank by VRAM fit.
        if candidates:  # Only log when at least one model fits.
            logger.info(  # Surface the shortlist for operators auditing model selection.
                "[%s] %d candidate models (VRAM=%.1f GB): %s",
                self.label,
                len(candidates),
                self._vram_gb,
                ", ".join(c["name"] for c in candidates),
            )
        return candidates  # Hand the ranked list back to provision().

    def _tier_reuse_loaded(self) -> dict | None:
        """Tier 1: reuse a model already loaded at 100 % GPU (zero cost)."""
        ps_data = _ollama_api_call(self.base_url, "/api/ps")  # Ask which models are currently loaded.
        if not ps_data:  # No running-model data returned.
            return None  # Nothing to reuse.
        for loaded in ps_data.get("models", []):  # Inspect each currently-loaded model.
            config = self._config_if_full_gpu(loaded)  # Accept only fully-GPU-resident models.
            if config:  # First 100% GPU model wins this tier.
                return config  # Reuse it at zero load cost.
        return None  # No loaded model sits entirely in GPU.

    def _config_if_full_gpu(self, loaded: dict) -> dict | None:
        """Return a config for a loaded model only when it sits 100 % in GPU VRAM."""
        name = loaded.get("name", "")  # Loaded model identifier.
        size = loaded.get("size", 0)  # Total model size in bytes.
        size_vram = loaded.get("size_vram", 0)  # Portion resident in GPU VRAM.
        gpu_pct = round(size_vram / size * 100) if size > 0 else 0  # Percent on GPU (guard divide-by-zero).
        if gpu_pct < 100:  # Any CPU spill disqualifies it from the zero-cost tier.
            return None  # Defer to a later tier.
        logger.info("[%s] Reusing already-loaded %s (100%% GPU, zero cost)", self.label, name)  # Log the reuse.
        return self._config(name, gpu_pct)  # Build the standard backend config.

    def _tier_on_disk(self) -> dict | None:
        """Tier 2: load an on-disk candidate that lands >= 95 % on GPU (no download)."""
        for candidate in self._on_disk_candidates():  # Walk only models already on disk.
            config = self._try_disk_candidate(candidate, self.STRONG_GPU_PERCENT)  # Require strong placement.
            if config:  # First strongly-placed on-disk model wins.
                return config  # Use it; no download was needed.
        return None  # No on-disk model met the strong-GPU bar.

    def _tier_pull(self) -> dict | None:
        """Tier 3: pull a not-on-disk candidate, then accept it at >= 95 % GPU."""
        for candidate in self._candidates:  # Consider every ranked candidate.
            if candidate["on_disk"]:  # On-disk ones were already tried in tier 2.
                continue  # Skip to the next candidate.
            config = self._try_pull_candidate(candidate)  # Download, load, and threshold-check it.
            if config:  # Freshly-pulled model met the strong-GPU bar.
                return config  # Use it.
        return None  # No pulled model qualified.

    def _try_pull_candidate(self, candidate: dict) -> dict | None:
        """Download a candidate and accept it only at >= 95 % GPU placement."""
        if not _pull_model_on_server(self.base_url, candidate["name"], self.label):  # Attempt the download.
            return None  # Pull failed; caller moves on.
        config = _try_model_on_server(self.base_url, candidate["name"], self.label)  # Load+health-check it.
        if config and config.get("gpu_percent", 0) >= self.STRONG_GPU_PERCENT:  # Require strong placement.
            return config  # Freshly-pulled model is good enough.
        return None  # Placement too weak to accept.

    def _tier_best_on_disk(self) -> dict | None:
        """Tier 4: accept the best on-disk candidate even below 100 % GPU."""
        for candidate in self._on_disk_candidates():  # Re-walk on-disk models.
            config = self._try_disk_candidate(candidate, 0)  # Any working placement is acceptable now.
            if config:  # First model that loads at all wins.
                return config  # Better a partial-GPU model than none.
        return None  # No on-disk model could be loaded.

    def _tier_cpu_fallback(self) -> dict | None:
        """Tier 5: last resort -- a small CPU-friendly model."""
        return _try_cpu_fallback(self.base_url, self.label, self._available)  # Delegate to the CPU strategy.

    def _on_disk_candidates(self) -> list[dict]:
        """Return only the ranked candidates that are already present on disk."""
        return [c for c in self._candidates if c["on_disk"]]  # Filter the shared candidate list.

    def _try_disk_candidate(self, candidate: dict, min_gpu: int) -> dict | None:
        """Try a matched on-disk model, accepting it when GPU placement meets ``min_gpu``."""
        match = _find_matching_model(candidate["name"], self._available)  # Resolve to an installed model name.
        if not match:  # No installed model matches the candidate.
            return None  # Cannot use this candidate.
        config = _try_model_on_server(self.base_url, match, self.label)  # Load+health-check the matched model.
        if config and config.get("gpu_percent", 0) >= min_gpu:  # Placement clears the caller's threshold.
            return config  # Accept this model.
        return None  # Placement too weak for the current tier.

    def _config(self, model: str, gpu_percent: int) -> dict:
        """Build the standard Ollama backend config dict for a chosen model."""
        return {  # Shape consumed by the rest of the analyzer's backend layer.
            "backend": "ollama",  # All provisioned servers are Ollama backends.
            "base_url": self.base_url,  # Where to reach this server.
            "model": model,  # The selected model identifier.
            "api_key": "ollama",  # Ollama ignores the key but the client requires one.
            "gpu_percent": gpu_percent,  # Record placement quality for downstream logging.
        }


def _model_base_name(model_name: str) -> str:
    """Return the family/base name for a model string."""
    return (
        model_name.split(":")[0] if ":" in model_name else model_name
    )  # Match families even when tags use variant suffixes.


def _model_tokens(model_name: str) -> set[str]:
    """Return normalized comparison tokens for fuzzy model matching."""
    tokens = set(
        model_name.replace(":", "-").split("-")
    )  # Normalize separators before comparing size and quantization tokens.
    tokens.add(_model_base_name(model_name))  # Always include the family token even when the original string omits it.
    return tokens  # Reuse this token set for both preferred and candidate models.


def _candidate_matches_model(candidate: str, preferred: str, preferred_tokens: set[str]) -> bool:
    """Return True when a candidate belongs to the same family and covers the preferred tokens."""
    if _model_base_name(candidate) != _model_base_name(preferred):  # Reject cross-family matches before token checks.
        return False  # Only same-family variants can be fuzzy matches.
    candidate_tokens = _model_tokens(candidate)  # Normalize the candidate the same way as the preferred model.
    return preferred_tokens.issubset(
        candidate_tokens
    )  # Require every preferred token to appear in the candidate variant.


def _find_matching_model(preferred: str, available: set[str]) -> str | None:
    """Find a model in available set that matches the preferred model name.

    Tries exact match first, then fuzzy match using key tokens
    (base name, size, quantization). This handles variants like
    'mistral:7b-instruct-v0.3-q8_0' matching 'mistral:7b-instruct-q8_0'.
    """
    if preferred in available:  # Exact matches should win before any fuzzy heuristics.
        return preferred  # Preserve the most predictable model selection behavior.
    preferred_tokens = _model_tokens(preferred)  # Precompute tokens once for all candidate comparisons.
    for candidate in sorted(available):  # Sort for deterministic fuzzy-match selection and logging.
        if not _candidate_matches_model(
            candidate, preferred, preferred_tokens
        ):  # Keep the loop flat by hiding comparison details.
            continue  # Move on until a compatible variant is found.
        logger.info(
            "Fuzzy match: '%s' -> '%s'", preferred, candidate
        )  # Surface the substitution so operators know which variant won.
        return candidate  # First deterministic fuzzy match preserves existing semantics.
    return None  # Signal that no installed variant satisfies the preferred model request.


def _try_cpu_fallback(
    base_url: str,
    label: str,
    available: set[str],
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


def _normalize_server_entry(entry: str) -> str:
    """Normalize a CLI --servers entry to host:port form."""
    normalized = entry.strip()  # Remove comma-separated whitespace noise from CLI input.
    if not normalized:  # Empty fragments should be ignored by the caller.
        return ""  # Signal that no server should be provisioned.
    if ":" in normalized:  # Respect explicitly supplied host:port pairs.
        return normalized  # Caller can use the supplied address verbatim.
    return f"{normalized}:{OLLAMA_PORT}"  # Fill in the default Ollama port for bare hostnames.


def _provision_server_entry(entry: str) -> dict | None:
    """Provision one normalized server entry into an analyzer config."""
    base_url = f"http://{entry}/v1"  # Convert the CLI host into the OpenAI-compatible Ollama base URL.
    logger.info("--- Provisioning server: %s ---", entry)  # Keep per-server provisioning logs unchanged.
    return ServerProvisioner(
        base_url, label=entry
    ).provision()  # Delegate tiered model selection to the existing provisioner.


def _log_server_config_summary(configs: list[dict]) -> None:
    """Log a summary for every successfully provisioned server."""
    if not configs:  # Avoid a summary banner when provisioning produced nothing usable.
        return  # Keep failure cases concise.
    logger.info("--- Server Fleet Summary ---")  # Match the original fleet summary header.
    for index, config in enumerate(configs):  # Surface each server's chosen model and GPU placement.
        logger.info(  # Preserve the existing operator-facing summary format.
            "  Server %d: %s -> %s (%d%% GPU)",
            index,
            config["base_url"],
            config["model"],
            config.get("gpu_percent", 0),
        )


def _build_server_configs(server_list: str) -> list[dict]:
    """Parse --servers string and auto-provision each Ollama server.

    Accepts comma-separated host:port or just hostnames (default port 11434).
    Each server is auto-provisioned: detect best model, pull if needed, health check.
    """
    configs: list[dict] = []  # Keep only successfully provisioned server configs.
    for raw_entry in server_list.split(","):  # Preserve CLI ordering when trying servers.
        entry = _normalize_server_entry(raw_entry)  # Normalize whitespace and missing default ports once.
        if not entry:  # Empty fragments from malformed input should not create log noise.
            continue  # Skip blank server entries cleanly.
        config = _provision_server_entry(entry)  # Hide URL building and provisioner wiring behind one helper.
        if config:  # Keep only servers that completed provisioning successfully.
            configs.append(config)  # Hand successful configs back to the caller unchanged.
            continue  # Skip the warning path for healthy servers.
        logger.warning(
            "Skipping server %s (provisioning failed)", entry
        )  # Preserve the existing per-server failure warning.
    _log_server_config_summary(configs)  # Keep fleet summary formatting outside the provisioning loop.
    return configs  # Return the successfully provisioned fleet in input order.


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
            self._active_configs = [cfg for cfg in self._active_configs if cfg["base_url"] != base_url]
            count = len(self._active_configs)
        logger.warning("Server %s marked DEAD (%d servers remain)", base_url, count)

    # -- Subnet Scanning ----------------------------------------------------

    def _discover_servers(self) -> list[str]:
        """Find Ollama servers via subnet scan + explicit list + localhost."""
        found: list[str] = []  # Preserve discovery order while de-duplicating hosts.
        self._append_localhost_if_ready(found)  # Prefer localhost first so single-node setups start quickly.
        self._extend_unique_hosts(
            found, self._explicit.split(",")
        )  # Merge explicitly configured hosts before broad subnet scans.
        scan_targets = self._build_scan_targets()  # Build the subnet target list only once.
        if scan_targets:  # Skip the scan entirely when no subnet target can be derived.
            scanned = self._scan_subnet(scan_targets)  # Probe the discovered subnet for additional servers.
            self._extend_unique_hosts(found, scanned)  # Preserve first-seen order while avoiding duplicates.
        logger.info(
            "Discovered %d Ollama server(s): %s", len(found), found
        )  # Keep the final discovery summary unchanged.
        return found  # Return the ordered host list for provisioning.

    def _append_localhost_if_ready(self, found: list[str]) -> None:
        """Add localhost first when a local Ollama server is reachable."""
        if not self._is_ollama_server("127.0.0.1"):  # Avoid aliasing localhost unless the API really responds there.
            return  # Leave localhost out when nothing listens locally.
        found.append("localhost")  # Prefer the friendly alias in logs and provisioning output.

    @staticmethod
    def _extend_unique_hosts(found: list[str], candidates: list[str]) -> None:
        """Append non-empty hosts that are not already present."""
        for candidate in candidates:  # Process candidates in discovery order to keep logs stable.
            host = candidate.strip()  # Normalize explicit entries and scan results the same way.
            if not host or host in found:  # Skip blanks and duplicates from overlapping discovery sources.
                continue  # Preserve only unique usable hosts.
            found.append(host)  # Keep the first occurrence so ordering stays deterministic.

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
        configs: list[dict] = []  # Collect only servers that finish provisioning successfully.
        with ThreadPoolExecutor(
            max_workers=4
        ) as pool:  # Bound provisioning parallelism so subnet scans do not stampede the host.
            futures = self._submit_provision_futures(pool, hosts)  # Isolate host normalization and future wiring.
            for future in as_completed(
                futures
            ):  # Consume completions in finish order so slow servers do not block fast ones.
                self._collect_provision_result(
                    future, futures[future], configs
                )  # Centralize success, warning, and exception handling.
        if configs:  # Only print a summary when at least one server is usable.
            self._log_fleet_summary(configs)  # Preserve the existing fleet summary output.
        return configs  # Return the surviving fleet configs to the caller.

    def _submit_provision_futures(
        self,
        pool: ThreadPoolExecutor,
        hosts: list[str],
    ) -> dict:
        """Submit provisioning work for every discovered host."""
        futures: dict = {}  # Map each future back to its host label for logs.
        for raw_host in hosts:  # Preserve discovery order when launching work.
            host = _normalize_server_entry(raw_host)  # Reuse the same host normalization as the CLI path.
            base_url = f"http://{host}/v1"  # Convert the host into the API base URL expected by the provisioner.
            future = pool.submit(
                ServerProvisioner(base_url, label=host).provision
            )  # Submit the bound provision method once per host.
            futures[future] = host  # Retain the human-readable host for result handling.
        return futures  # Hand the future map back to the caller's completion loop.

    @staticmethod
    def _collect_provision_result(future, host: str, configs: list[dict]) -> None:
        """Collect one provisioning future into the shared config list."""
        try:  # Keep per-server exceptions isolated so one bad host does not stop the fleet.
            config = future.result()  # Wait for the provisioner to finish for this host.
        except Exception:  # Preserve the existing traceback for unexpected provisioning failures.
            logger.exception("Error provisioning %s", host)  # Keep host context in the failure log.
            return  # Leave this host out of the final fleet.
        if config:  # Only real configs should reach the shared fleet list.
            configs.append(config)  # Preserve the existing config payload unchanged.
            return  # Skip the warning path for successful hosts.
        logger.warning("Provisioning failed for %s", host)  # Keep the original warning for clean failures.

    @staticmethod
    def _log_fleet_summary(configs: list[dict]) -> None:
        """Log a summary table of the fleet."""
        logger.info("=== Fleet Summary: %d servers ===", len(configs))
        for index, cfg in enumerate(configs):
            logger.info(
                "  [%d] %s -> %s (%d%% GPU)",
                index,
                cfg["base_url"],
                cfg["model"],
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
        with self._lock:  # Snapshot under lock so health probes run without holding shared state.
            configs_snapshot = list(self._active_configs)  # Probe a stable copy while workers keep using the live list.
        dead = self._collect_dead_servers(configs_snapshot)  # Isolate probe logic from shared-state mutation.
        if not dead:  # Healthy fleets do not need lock churn or warning logs.
            return  # Exit quickly when every server responded.
        remaining = self._prune_dead_servers(dead)  # Remove dead servers under lock and return the new fleet size.
        logger.warning(
            "[health] Removed %d dead server(s), %d remain", len(dead), remaining
        )  # Preserve the original fleet-shrink warning.

    @staticmethod
    def _collect_dead_servers(configs_snapshot: list[dict]) -> list[str]:
        """Probe every config in a snapshot and return the dead base URLs."""
        dead: list[str] = []  # Collect only unreachable servers for later pruning.
        for config in configs_snapshot:  # Probe the snapshot without holding the fleet lock.
            base_url = config["base_url"]  # Use the stored API base URL for the health request.
            label = base_url.replace("http://", "").replace(
                "/v1", ""
            )  # Keep logs readable by stripping protocol noise.
            data = _ollama_api_call(
                base_url, "/api/tags", timeout=5
            )  # Reuse the lightweight tags endpoint as a liveness probe.
            if data is None:  # Missing response means the server is no longer healthy enough for work.
                logger.warning("[health] Server %s UNREACHABLE", label)  # Preserve the existing unreachable warning.
                dead.append(base_url)  # Mark the server for pruning after the probe loop completes.
                continue  # Skip the healthy log for dead servers.
            logger.debug("[health] Server %s OK", label)  # Preserve the existing low-noise healthy heartbeat log.
        return dead  # Hand back the dead server list for one locked prune step.

    def _prune_dead_servers(self, dead: list[str]) -> int:
        """Remove dead servers from shared fleet state and return remaining count."""
        with self._lock:  # Apply fleet mutations atomically so worker threads see a consistent list.
            for url in dead:  # Track every removed server in the dead-server set.
                self._dead_servers.add(url)  # Preserve the existing dead-server memory for diagnostics.
            self._active_configs = [
                cfg for cfg in self._active_configs if cfg["base_url"] not in dead
            ]  # Drop all dead configs in one pass.
            return len(self._active_configs)  # Report remaining capacity for the warning log.

    def _rediscover_servers(self) -> None:
        """Scan for new servers that weren't in the fleet before."""
        with self._lock:  # Snapshot known URLs atomically before the discovery scan runs.
            known_urls = {
                cfg["base_url"] for cfg in self._active_configs
            }  # Compare rediscovery results against the current live fleet.
        new_hosts = self._discover_servers()  # Reuse the full discovery pipeline to find any new reachable servers.
        new_to_provision = self._filter_new_hosts(
            new_hosts, known_urls
        )  # Keep only hosts that are not already provisioned.
        if not new_to_provision:  # Avoid provisioning and logs when rediscovery found nothing new.
            return  # Fleet remains unchanged.
        logger.info(
            "[rediscovery] Found %d new server(s): %s", len(new_to_provision), new_to_provision
        )  # Preserve the original expansion log.
        new_configs = self._provision_all(new_to_provision)  # Provision only the previously unseen hosts.
        if not new_configs:  # No successful provisioning means the active fleet should not change.
            return  # Stop after the failed expansion attempt.
        total = self._extend_active_configs(new_configs)  # Update the live fleet atomically and capture the new size.
        logger.info("[rediscovery] Fleet expanded to %d servers", total)  # Keep the original fleet-growth summary.

    @staticmethod
    def _filter_new_hosts(new_hosts: list[str], known_urls: set[str]) -> list[str]:
        """Return only hosts that are not already part of the live fleet."""
        new_to_provision: list[str] = []  # Preserve discovery order for newly found hosts.
        for raw_host in new_hosts:  # Normalize rediscovered hosts the same way as initial provisioning.
            host = _normalize_server_entry(raw_host)  # Reuse the shared host-normalization logic.
            url = f"http://{host}/v1"  # Compare using the same base_url form stored in configs.
            if url in known_urls:  # Already-provisioned hosts should not be provisioned again.
                continue  # Skip duplicates quietly.
            new_to_provision.append(host)  # Queue only genuinely new hosts for provisioning.
        return new_to_provision  # Hand back the new-host worklist.

    def _extend_active_configs(self, new_configs: list[dict]) -> int:
        """Append newly provisioned configs to the live fleet and return the new size."""
        with self._lock:  # Protect the shared fleet list while adding new capacity.
            self._active_configs.extend(new_configs)  # Preserve the new configs exactly as provisioned.
            return len(self._active_configs)  # Return the updated fleet size for logging.


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
            server_label,
            items_done,
            done,
            total,
        )
        time.sleep(INTER_REQUEST_DELAY)

    return items_done


def _split_fleet_cached_ideas(
    ideas: list[dict],
    refresh: bool,
) -> tuple[dict[int, dict], list[tuple[int, dict]]]:
    """Separate cached fleet results from work that still needs servers."""
    results: dict[int, dict] = {}  # Preserve cached analyses at their original positions.
    uncached: list[tuple[int, dict]] = []  # Queue only cache misses for distributed execution.
    for index, idea in enumerate(ideas):  # Walk source order so the final list remains stable.
        cached = (
            None if refresh else load_cached_response(CACHE_DIR, idea["content_hash"])
        )  # Respect refresh mode while reusing the normal cache format.
        if cached:  # Cache hits should not consume any fleet capacity.
            results[index] = cached  # Reuse the stored analysis exactly as before.
            continue  # Skip enqueueing cache hits.
        uncached.append((index, idea))  # Keep misses in queue order for balanced processing.
    return results, uncached  # Hand both collections back to the fleet orchestrator.


def _finalize_fleet_results(results: dict[int, dict], total: int) -> list[dict]:
    """Materialize final results with fallback entries for any missing slot."""
    return [
        results.get(i, IdeaAnalyzer._unclassified_fallback()) for i in range(total)
    ]  # Preserve the analyzer's existing missing-result fallback contract.


def _run_fleet_rebalancing(
    fleet: OllamaFleetManager,
    api_index: dict,
    refresh: bool,
    remaining: list[tuple[int, dict]],
    results: dict[int, dict],
) -> None:
    """Process remaining work until the fleet empties or every item finishes."""
    while remaining:  # Keep rebalancing until work is drained or no healthy servers remain.
        configs = (
            fleet.get_healthy_configs()
        )  # Refresh the live fleet view each cycle to honor failures and rediscovery.
        if not configs:  # No healthy servers means any remaining work cannot progress.
            logger.error(
                "No healthy servers available -- %d ideas unprocessed", len(remaining)
            )  # Preserve the existing terminal error message.
            return  # Leave unresolved items to the fallback materializer.
        batch_results, remaining = _run_fleet_batch(
            fleet, configs, api_index, remaining, refresh
        )  # Let one fleet batch drain as much queued work as possible.
        results.update(batch_results)  # Persist completed work before any further rebalance attempt.
        if remaining:  # Log only when another rebalance pass will be necessary.
            logger.info(  # Keep operators informed when work was orphaned by dead servers.
                "Rebalancing %d orphaned ideas across %d healthy servers",
                len(remaining),
                len(fleet.get_healthy_configs()),
            )


def analyze_with_fleet(
    fleet: OllamaFleetManager,
    api_index: dict,
    ideas: list[dict],
    refresh: bool = False,
) -> list[dict]:
    """Run analysis using dynamic fleet with failover and rebalancing."""
    total = len(ideas)  # Preserve original result ordering for the final materialized list.
    results, uncached = _split_fleet_cached_ideas(
        ideas, refresh
    )  # Avoid sending cached ideas through the distributed fleet.
    cached_count = total - len(uncached)  # Surface cache effectiveness for the fleet run.
    configs = fleet.get_healthy_configs()  # Snapshot current capacity for the opening summary log.
    logger.info(  # Keep the top-level fleet summary unchanged for operators.
        "Fleet analysis: cached=%d, uncached=%d, servers=%d",
        cached_count,
        len(uncached),
        len(configs),
    )
    if not uncached:  # Skip fleet work entirely when everything came from cache.
        return _finalize_fleet_results(results, total)  # Materialize the cached-only result list immediately.
    remaining = list(uncached)  # Keep a mutable copy for the rebalance loop.
    _run_fleet_rebalancing(
        fleet, api_index, refresh, remaining, results
    )  # Let the helper own the failover and rebalance loop.
    fleet.stop()  # Preserve the original guarantee that the monitor thread stops after fleet analysis finishes.
    return _finalize_fleet_results(results, total)  # Fill any unfinished slots with the standard fallback payload.


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
                _queue_worker,
                analyzer,
                label,
                work_queue,
                results_lock,
                batch_results,
                progress,
                fleet,
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
                        _queue_worker,
                        analyzer,
                        server_label,
                        work_queue,
                        results_lock,
                        batch_results,
                        progress,
                        fleet,
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
                backend_config,
                api_index,
                refresh=args.refresh,
                batch_size=args.batch_size,
            )
            analyses = analyzer.analyze_all(ideas)
        else:
            analyses = analyze_with_fleet(
                fleet,
                api_index,
                ideas,
                refresh=args.refresh,
            )
            analyzer = IdeaAnalyzer(
                configs[0],
                api_index,
                refresh=args.refresh,
                batch_size=1,
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
