#!/usr/bin/env python3
"""Mist Ideas Distiller v2 — Reduce 2,400+ community ideas to ~100 buildable features.

Quality-focused pipeline (no truncation, full context, cross-theme dedup):
  Pre-filter  : MistHelper-centric API coverage + demand signal scoring
  Pass 1      : Theme-based consolidation into feature clusters (Ollama fleet)
  Pass 1b     : Cross-theme deduplication — merge similar clusters across themes
  Pass 2      : Feasibility scoring with real API endpoint data (Ollama fleet)
  Pass 3      : Stack ranking to top 100 (Ollama fleet)
  Pass 4      : Dependency ordering for build sequence

Usage:
  python scripts/mist_ideas_distiller_v2.py [--verbose] [--pass N] [--skip-fleet]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import queue
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DIR = Path("data/mist_ideas_cache")
API_INDEX_PATH = CACHE_DIR / "api_index.json"
OUTPUT_DIR = Path("data")

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
OLLAMA_PORT = 11434
OLLAMA_TIMEOUT = 300
OLLAMA_NUM_CTX_DEFAULT = 4096
OLLAMA_NUM_CTX_MAX = 32768
COMMON_GPU_VRAM_GIB = [4, 6, 8, 10, 11, 12, 16, 24, 32, 40, 48, 80]
KV_BYTES_PER_TOKEN_7B = 128 * 1024
GPU_OVERHEAD_GIB = 0.5
# MoE (Mixture-of-Experts) offload: keep attention/embedding layers on GPU,
# run expert FFN layers from CPU RAM.  24 GPU layers covers the shared weights
# for Mixtral 8x7b (32 transformer layers) while experts spill to RAM,
# dropping VRAM from ~26 GB to ~10 GB.
MOE_PATTERN = r"\d+x\d+b"  # matches 8x7b, 4x22b, etc.
MOE_NUM_GPU = 24
# KV cache quantization applied to all models (q8_0: half the VRAM of fp16,
# negligible quality loss vs q4_0 which causes measurable perplexity drift).
KV_CACHE_TYPE = "q8_0"
CONSOLIDATION_BATCH_SIZE = 25
CROSS_THEME_BATCH_SIZE = 40
MIN_THEME_SIZE_FOR_OWN_BATCH = 5
TOP_N = 100

EFFORT_MAP = {"S": 1, "M": 2, "L": 4, "XL": 8}

logger = logging.getLogger("distiller")


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------


class CacheLoader:
    """Load and index all cached classification results."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir

    def load_all(self) -> list[dict]:
        """Load every cached idea (excluding api_index.json)."""
        entries = []
        for path in sorted(self.cache_dir.glob("*.json")):
            if path.name == "api_index.json":
                continue
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            data["_cache_file"] = path.name
            entries.append(data)
        logger.info("Loaded %d cached ideas", len(entries))
        return entries

    def load_api_index(self) -> dict:
        """Load the API endpoint index."""
        with open(API_INDEX_PATH, encoding="utf-8") as handle:
            index = json.load(handle)
        total_endpoints = sum(len(endpoints) for endpoints in index.values())
        logger.info(
            "Loaded API index: %d categories, %d endpoints",
            len(index),
            total_endpoints,
        )
        return index


# ---------------------------------------------------------------------------
# Pre-Filter: MistHelper-Centric API Coverage + Demand Signal
# ---------------------------------------------------------------------------


class ApiCoverageFilter:
    """Score and filter ideas by API coverage and community demand."""

    KEEP_CLASSIFICATIONS = {"API_ENHANCEMENT", "REPORT_EXPORT", "HYBRID"}

    def __init__(self, api_index: dict):
        self.api_index = api_index
        self._keyword_to_categories = self._build_keyword_index()

    def filter_and_score(self, ideas: list[dict]) -> list[dict]:
        """Filter to buildable classifications, score API coverage + demand."""
        kept = [idea for idea in ideas if idea.get("classification") in self.KEEP_CLASSIFICATIONS]
        for idea in kept:
            self._score_api_coverage(idea)
            self._score_demand_signal(idea)

        kept.sort(
            key=lambda x: (x.get("demand_signal", 0), x.get("api_score", 0)),
            reverse=True,
        )

        with_api = sum(1 for idea in kept if idea.get("api_score", 0) > 0)
        logger.info(
            "Pre-filter: %d -> %d ideas (removed GUI_ONLY/ALREADY_SUPPORTED)",
            len(ideas),
            len(kept),
        )
        logger.info(
            "  %d have API coverage > 0, %d have no coverage",
            with_api,
            len(kept) - with_api,
        )
        return kept

    def _score_api_coverage(self, idea: dict) -> None:
        """Score idea by matching themes/title against API endpoint keywords."""
        idea_words: set[str] = set()
        for theme in idea.get("themes", []):
            idea_words.update(self._extract_words(theme))
        idea_words.update(self._extract_words(idea.get("source_title", "")))

        matched: set[str] = set()
        for word in idea_words:
            if word in self._keyword_to_categories:
                matched.update(self._keyword_to_categories[word])

        idea["api_score"] = len(matched)
        idea["api_matched_categories"] = sorted(matched)[:10]

    @staticmethod
    def _score_demand_signal(idea: dict) -> None:
        """Compute demand signal from duplicate count + foundational + unlocks."""
        duplicate_count = len(idea.get("possible_duplicate_titles", []))
        foundational_bonus = 5 if idea.get("is_foundational") else 0
        unlocks_count = len(idea.get("unlocks", []))
        idea["demand_signal"] = duplicate_count + foundational_bonus + unlocks_count

    def _build_keyword_index(self) -> dict[str, list[str]]:
        """Build keyword -> [category] mapping from all API endpoints."""
        keyword_map: dict[str, list[str]] = {}
        for category, endpoints in self.api_index.items():
            words = self._extract_words(category)
            for endpoint in endpoints:
                words.extend(self._extract_words(endpoint.get("summary", "")))
                words.extend(self._extract_path_words(endpoint.get("path", "")))
            for word in set(words):
                keyword_map.setdefault(word, []).append(category)
        return keyword_map

    @staticmethod
    def _extract_words(text: str) -> list[str]:
        """Extract normalized keywords from text."""
        text = text.lower().replace("_", " ").replace("-", " ")
        words = re.findall(r"[a-z]{3,}", text)
        stopwords = {"the", "and", "for", "with", "from", "that", "this", "are"}
        return [w for w in words if w not in stopwords]

    @staticmethod
    def _extract_path_words(path: str) -> list[str]:
        """Extract meaningful words from API paths."""
        segments = path.strip("/").split("/")
        return [
            seg.lower().replace("_", " ") for seg in segments if not seg.startswith("{") and seg not in ("api", "v1")
        ]


# ---------------------------------------------------------------------------
# Fleet Management
# ---------------------------------------------------------------------------


class OllamaFleet:
    """Lightweight fleet manager for known-good Ollama servers."""

    def __init__(self):
        self._configs: list[dict] = []

    def discover_and_start(self) -> list[dict]:
        """Discover servers, provision models, return configs."""
        servers = self._discover()
        self._configs = self._provision(servers)
        logger.info("Fleet ready: %d servers", len(self._configs))
        for config in self._configs:
            label = config["base_url"].replace("http://", "").split(":")[0]
            logger.info(
                "  %s -> %s (num_ctx=%d)",
                label,
                config["model"],
                config["num_ctx"],
            )
        return list(self._configs)

    def _discover(self) -> list[str]:
        """Find reachable Ollama servers."""
        candidates = ["localhost", "192.168.1.86", "192.168.1.225"]
        explicit = os.environ.get("OLLAMA_SERVERS", "")
        if explicit:
            candidates.extend(host.strip() for host in explicit.split(",") if host.strip())
        found = [host for host in candidates if self._check_server(host)]
        logger.info("Discovered %d Ollama servers: %s", len(found), found)
        return found

    @staticmethod
    def _check_server(host: str) -> bool:
        """Check if an Ollama server is reachable."""
        import urllib.request

        try:
            url = f"http://{host}:{OLLAMA_PORT}/api/tags"
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def _provision(self, servers: list[str]) -> list[dict]:
        """Get the best available model and optimal num_ctx on each server."""
        configs = []
        for host in servers:
            model = self._get_best_model(host)
            if model:
                num_ctx = self._estimate_num_ctx(host, model)
                config: dict = {
                    "backend": "ollama",
                    "base_url": f"http://{host}:{OLLAMA_PORT}/v1",
                    "model": model,
                    "api_key": "ollama",
                    "num_ctx": num_ctx,
                    "kv_cache_type": KV_CACHE_TYPE,
                }
                if re.search(MOE_PATTERN, model):
                    config["num_gpu"] = MOE_NUM_GPU
                    logger.info(
                        "[%s] MoE model detected (%s) -> num_gpu=%d, kv_cache_type=%s",
                        host,
                        model,
                        MOE_NUM_GPU,
                        KV_CACHE_TYPE,
                    )
                configs.append(config)
        return configs

    @staticmethod
    def _get_best_model(host: str) -> str | None:
        """Find the best loaded model on a server."""
        import urllib.request

        try:
            url = f"http://{host}:{OLLAMA_PORT}/api/tags"
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
            models = data.get("models", [])
            preferred_prefixes = ["mistral", "qwen2.5", "llama3"]
            for prefix in preferred_prefixes:
                for model in models:
                    if model.get("name", "").startswith(prefix):
                        return model["name"]
            return models[0]["name"] if models else None
        except Exception:
            return None

    @staticmethod
    def _query_vram_usage(host: str) -> dict | None:
        """Query Ollama /api/ps for running model VRAM usage."""
        import urllib.request

        try:
            url = f"http://{host}:{OLLAMA_PORT}/api/ps"
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
            running = data.get("models", [])
            if not running:
                return None
            entry = running[0]
            return {
                "size": entry.get("size", 0),
                "size_vram": entry.get("size_vram", 0),
            }
        except Exception:
            return None

    @classmethod
    def _estimate_num_ctx(cls, host: str, model: str) -> int:
        """Estimate optimal num_ctx based on GPU VRAM headroom."""
        vram_info = cls._query_vram_usage(host)
        if not vram_info:
            logger.info("[%s] No VRAM info available, using default num_ctx=%d", host, OLLAMA_NUM_CTX_DEFAULT)
            return OLLAMA_NUM_CTX_DEFAULT
        model_bytes = vram_info["size"]
        vram_bytes = vram_info["size_vram"]
        gib = 1024**3
        if vram_bytes < model_bytes * 0.9:
            logger.info(
                "[%s] Model partially offloaded (%.1f/%.1f GiB in VRAM) -> num_ctx=%d",
                host,
                vram_bytes / gib,
                model_bytes / gib,
                OLLAMA_NUM_CTX_DEFAULT,
            )
            return OLLAMA_NUM_CTX_DEFAULT
        vram_gib = vram_bytes / gib
        total_gib = cls._infer_total_vram_gib(vram_gib)
        headroom = total_gib - vram_gib - GPU_OVERHEAD_GIB
        max_tokens = int(max(0, headroom) * gib / KV_BYTES_PER_TOKEN_7B)
        num_ctx = cls._clamp_power_of_two(max_tokens)
        logger.info(
            "[%s] VRAM: %.1f/%.0f GiB, headroom: %.1f GiB -> num_ctx=%d",
            host,
            vram_gib,
            total_gib,
            headroom,
            num_ctx,
        )
        return num_ctx

    @staticmethod
    def _infer_total_vram_gib(used_gib: float) -> float:
        """Infer total GPU VRAM from known common GPU sizes."""
        for size in COMMON_GPU_VRAM_GIB:
            if size >= used_gib * 1.05:
                return float(size)
        return float(COMMON_GPU_VRAM_GIB[-1])

    @staticmethod
    def _clamp_power_of_two(max_tokens: int) -> int:
        """Round down to nearest power of 2, clamped to safe range."""
        if max_tokens < 2048:
            return OLLAMA_NUM_CTX_DEFAULT
        power = 1
        while power * 2 <= max_tokens:
            power *= 2
        return min(power, OLLAMA_NUM_CTX_MAX)


# ---------------------------------------------------------------------------
# AI Client
# ---------------------------------------------------------------------------


class AiClient:
    """OpenAI-compatible client with retry logic and JSON extraction."""

    def __init__(self, config: dict):
        self.config = config
        self._client = OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
        )
        self.model = config["model"]
        self.num_ctx = config.get("num_ctx", OLLAMA_NUM_CTX_DEFAULT)
        self.num_gpu: int | None = config.get("num_gpu")
        self.kv_cache_type: str | None = config.get("kv_cache_type")
        self.label = config["base_url"].replace("http://", "").split(":")[0]

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Call the AI backend with retries."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                kwargs: dict = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "timeout": OLLAMA_TIMEOUT,
                    "extra_body": {"options": self._build_options()},
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                response = self._client.chat.completions.create(**kwargs)
                text = response.choices[0].message.content or ""
                if text.strip():
                    return text.strip()
                logger.warning(
                    "[%s] Empty response (attempt %d/%d)",
                    self.label,
                    attempt,
                    MAX_RETRIES,
                )
            except Exception as exc:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "[%s] AI call failed (attempt %d/%d): %s -- retry %.1fs",
                    self.label,
                    attempt,
                    MAX_RETRIES,
                    str(exc)[:120],
                    delay,
                )
                time.sleep(delay)
        return ""

    def _build_options(self) -> dict:
        """Build Ollama options dict for extra_body."""
        options: dict = {"num_ctx": self.num_ctx}
        if self.kv_cache_type:
            options["kv_cache_type"] = self.kv_cache_type
        if self.num_gpu is not None:
            options["num_gpu"] = self.num_gpu
        return options

    def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> dict | list | None:
        """Call AI and parse JSON from the response."""
        text = self.call(system_prompt, user_prompt, json_mode=json_mode)
        if not text:
            return None
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> dict | list | None:
        """Extract JSON from text, handling markdown code fences."""
        fence = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        for pattern in (r"\[.*\]", r"\{.*\}"):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        logger.warning("Failed to parse JSON from AI response (%d chars)", len(text))
        return None


# ---------------------------------------------------------------------------
# Fleet Work Queue Runner
# ---------------------------------------------------------------------------


class FleetRunner:
    """Shared queue + ThreadPoolExecutor pattern for fleet work distribution."""

    def __init__(self, fleet_configs: list[dict], pass_name: str):
        self.fleet_configs = fleet_configs
        self.pass_name = pass_name

    def run_all(
        self,
        work_items: list,
        process_func,
    ) -> list:
        """Distribute work_items across fleet, calling process_func for each."""
        work_queue: queue.Queue = queue.Queue()
        for item in work_items:
            work_queue.put(item)

        all_results: list = []
        results_lock = threading.Lock()
        progress = {"done": 0, "total": len(work_items)}

        def worker(config: dict, worker_id: int) -> None:
            client = AiClient(config)
            while True:
                try:
                    item = work_queue.get_nowait()
                except queue.Empty:
                    break
                result = process_func(client, item)
                with results_lock:
                    if isinstance(result, list):
                        all_results.extend(result)
                    else:
                        all_results.append(result)
                    progress["done"] += 1
                    if progress["done"] % 5 == 0 or progress["done"] == progress["total"]:
                        logger.info(
                            "  %s [%d/%d] (worker-%d on %s)",
                            self.pass_name,
                            progress["done"],
                            progress["total"],
                            worker_id,
                            client.label,
                        )

        with ThreadPoolExecutor(max_workers=len(self.fleet_configs)) as executor:
            futures = [executor.submit(worker, config, idx) for idx, config in enumerate(self.fleet_configs)]
            for future in futures:
                future.result()

        return all_results


# ---------------------------------------------------------------------------
# Pass 1: Theme-Based Consolidation (Full Context)
# ---------------------------------------------------------------------------


CONSOLIDATION_SYSTEM = """You are an expert software feature analyst. You will receive community feature ideas for the Juniper Mist Cloud platform grouped by theme.

Your job: Group similar ideas into distinct, SPECIFIC, buildable feature clusters. Each cluster = one concrete thing an engineer could build using the Mist REST API.

For each cluster, return:
1. "name": A SPECIFIC, actionable feature name that describes exactly what is built.
   GOOD examples: "Bulk Device Firmware Scheduler", "Site-Level SLE Trend Exporter", "WLAN Configuration Cloner"
   BAD examples (NEVER use these patterns): "Features", "Monitoring Features", "Wireless Features", "Security Features", "Device Management Features"
2. "description": 2-3 sentences. What does it DO? What Mist API endpoints would it use? Who benefits?
3. "idea_titles": Exact list of original idea titles merged into this cluster
4. "idea_count": Number of ideas in this cluster
5. "primary_theme": The dominant theme
6. "total_demand": Sum of demand_signal values for all ideas in the cluster
7. "has_foundational": true if ANY idea was marked foundational
8. "buildable_via_api": true if this can be built by calling the Mist REST API. false if it requires Juniper to change their cloud platform, hardware, firmware behavior, or portal UI.

Critical rules:
- NAMING: Every name MUST contain a verb or action noun (Exporter, Scheduler, Cloner, Reporter, Auditor, Migrator, Monitor). Generic category names are FORBIDDEN.
- NAMING: If you cannot think of a specific name, the ideas are too diverse -- split into smaller clusters.
- BUILDABILITY: MistHelper is a Python CLI that calls the Mist REST API. It CANNOT change AP antenna behavior, fix firmware bugs, modify the Mist dashboard UI, or change how Mist cloud processes data. Mark these as buildable_via_api=false.
- Merge near-duplicates aggressively. "AP firmware upgrade" and "Schedule firmware updates" = same cluster.
- Each idea title belongs to exactly ONE cluster.
- Consider the full description and comments to understand what users actually want.

Return ONLY a valid JSON array:
[{"name": "...", "description": "...", "idea_titles": [...], "idea_count": N, "primary_theme": "...", "total_demand": N, "has_foundational": bool, "buildable_via_api": bool}]"""


class Consolidator:
    """Pass 1: Group ideas into feature clusters with full context."""

    def __init__(self, fleet_configs: list[dict]):
        self.fleet_configs = fleet_configs

    def consolidate(self, ideas: list[dict]) -> list[dict]:
        """Group ideas by theme, send batches to fleet, return clusters."""
        theme_groups = self._group_by_primary_theme(ideas)
        logger.info(
            "Pass 1: %d ideas across %d themes",
            len(ideas),
            len(theme_groups),
        )

        work_items = self._build_smart_batches(theme_groups)
        logger.info("Pass 1: %d batches to process", len(work_items))

        runner = FleetRunner(self.fleet_configs, "Pass 1")
        all_clusters = runner.run_all(work_items, self._process_one_batch)

        logger.info("Pass 1: %d feature clusters produced", len(all_clusters))
        return all_clusters

    @staticmethod
    def _group_by_primary_theme(ideas: list[dict]) -> dict[str, list[dict]]:
        """Group ideas by their first theme."""
        groups: dict[str, list[dict]] = {}
        for idea in ideas:
            themes = idea.get("themes", [])
            theme = themes[0] if themes else "uncategorized"
            groups.setdefault(theme, []).append(idea)
        return groups

    @staticmethod
    def _build_smart_batches(groups: dict[str, list[dict]]) -> list[dict]:
        """Build batches, merging tiny themes to reduce batch count."""
        work_items: list[dict] = []
        small_theme_pool: list[dict] = []
        small_theme_names: list[str] = []

        for theme in sorted(groups, key=lambda t: -len(groups[t])):
            ideas = groups[theme]
            if len(ideas) >= MIN_THEME_SIZE_FOR_OWN_BATCH:
                for start in range(0, len(ideas), CONSOLIDATION_BATCH_SIZE):
                    batch = ideas[start : start + CONSOLIDATION_BATCH_SIZE]
                    work_items.append({"theme": theme, "ideas": batch})
            else:
                small_theme_pool.extend(ideas)
                small_theme_names.append(theme)
                if len(small_theme_pool) >= CONSOLIDATION_BATCH_SIZE:
                    work_items.append(
                        {
                            "theme": "cross-theme",
                            "ideas": small_theme_pool[:CONSOLIDATION_BATCH_SIZE],
                        }
                    )
                    small_theme_pool = small_theme_pool[CONSOLIDATION_BATCH_SIZE:]
                    small_theme_names = []

        if small_theme_pool:
            work_items.append(
                {
                    "theme": "cross-theme",
                    "ideas": small_theme_pool,
                }
            )

        return work_items

    @staticmethod
    def _process_one_batch(client: AiClient, item: dict) -> list[dict]:
        """Send one batch to AI with FULL context (no truncation)."""
        theme = item["theme"]  # Theme label used in prompt + cluster metadata.
        ideas = item["ideas"]  # Idea dicts pulled from the upstream pool.
        user_prompt = Consolidator._build_idea_prompt(theme, ideas)  # Prompt assembly extracted.
        result = client.call_json(CONSOLIDATION_SYSTEM, user_prompt)  # Single AI call returns parsed JSON.
        result = Consolidator._normalize_ai_response(result, theme, ideas)  # Coerce to list[dict].
        valid_clusters = Consolidator._validate_ai_clusters(result, theme, ideas)  # Filter+enrich.
        if not valid_clusters:  # Empty result -> emit a single fallback cluster.
            return [Consolidator._make_fallback_cluster(theme, ideas)]  # Single-element list.
        return valid_clusters  # Normal path: forward the AI-derived clusters.

    @staticmethod
    def _build_idea_block(idea: dict) -> str:
        """Render a single idea dict into the TITLE / DESCRIPTION / COMMENTS block."""
        title = idea.get("source_title", "Unknown")  # Plain-text title with a sane default.
        description = idea.get("source_description", "")  # Body text; empty when missing.
        comments = idea.get("source_comments", [])  # Optional list of top comments.
        demand = idea.get("demand_signal", 0)  # Numeric demand score forwarded to the AI.
        foundational = idea.get("is_foundational", False)  # Bool flag marks foundational ideas.
        block = f"TITLE: {title}\nDESCRIPTION: {description}"  # Start with the two required lines.
        if comments:  # Append the top-3 comments line only when comments are present.
            top_comments = comments[:3]  # Cap at three so prompts stay reasonable.
            block += "\nTOP COMMENTS: " + " | ".join(str(c) for c in top_comments)
        block += f"\nDEMAND_SIGNAL: {demand}"  # Demand score always appended on its own line.
        if foundational:  # Optional tag appended when the idea is flagged foundational.
            block += " [FOUNDATIONAL]"
        return block  # Return the assembled multi-line block.

    @staticmethod
    def _build_idea_prompt(theme: str, ideas: list[dict]) -> str:
        """Render the per-theme prompt body fed to the consolidation AI call."""
        idea_blocks = [Consolidator._build_idea_block(idea) for idea in ideas]  # One block per idea.
        return (
            f"Theme: {theme}\n"  # Theme header.
            f"Number of ideas: {len(ideas)}\n"  # Idea count helps the AI scope output.
            f"{'=' * 40}\n\n"  # Separator line.
            + "\n---\n".join(idea_blocks)  # Idea blocks joined by triple-dash markers.
        )

    @staticmethod
    def _normalize_ai_response(result: object, theme: str, ideas: list[dict]) -> list:
        """Coerce arbitrary AI return shapes into a list[dict] for downstream filtering."""
        if isinstance(result, list):  # Common case: already a list of dicts.
            return result
        if isinstance(result, dict):  # AI returned one cluster -> wrap in a list.
            return [result]
        # Unrecognized shape -> fall back to a single best-effort cluster.
        return [Consolidator._make_fallback_cluster(theme, ideas)]

    @staticmethod
    def _validate_ai_clusters(result: list, theme: str, ideas: list[dict]) -> list[dict]:
        """Drop non-dict entries and enrich valid clusters with theme metadata."""
        valid_clusters: list[dict] = []  # Accumulator for the enriched cluster dicts.
        for cluster in result:  # Iterate exactly once over the AI return.
            if not isinstance(cluster, dict):  # Skip malformed entries with a warning.
                logger.warning("Pass 1: Skipping non-dict item in response for theme=%s", theme)
                continue
            Consolidator._enrich_cluster(cluster, theme, ideas)  # Mutate in place.
            valid_clusters.append(cluster)  # Keep the enriched cluster.
        return valid_clusters  # Caller decides whether to fall back when empty.

    @staticmethod
    def _enrich_cluster(cluster: dict, theme: str, ideas: list[dict]) -> None:
        """Add theme/idea-derived metadata to an AI-produced cluster in place."""
        cluster["source_theme"] = theme  # Tag the cluster with its originating theme.
        if "idea_titles" not in cluster:  # Default to all idea titles when AI omits the field.
            cluster["idea_titles"] = [i.get("source_title", "") for i in ideas]
        if "idea_count" not in cluster:  # Derive count from the titles list when missing.
            cluster["idea_count"] = len(cluster.get("idea_titles", []))
        if "total_demand" not in cluster:  # Sum demand signals when AI omits the field.
            cluster["total_demand"] = sum(i.get("demand_signal", 0) for i in ideas)

    @staticmethod
    def _make_fallback_cluster(theme: str, ideas: list[dict]) -> dict:
        """Build the single fallback cluster used when AI returns nothing useful."""
        first_title = ideas[0].get("source_title", theme) if ideas else theme  # Defensive default.
        return {
            "name": first_title,  # Pick the first idea's title as the cluster name.
            "description": f"Collection of {len(ideas)} {theme} feature requests",  # Generic blurb.
            "idea_titles": [i.get("source_title", "") for i in ideas],  # Forward all titles.
            "idea_count": len(ideas),  # Count of underlying ideas.
            "primary_theme": theme,  # Forward the originating theme.
            "source_theme": theme,  # Mirror the source theme tag for consistency.
            "total_demand": sum(i.get("demand_signal", 0) for i in ideas),  # Total demand summed.
            "has_foundational": any(i.get("is_foundational") for i in ideas),  # Bool union.
            "buildable_via_api": True,  # Default optimistic flag for the downstream filter.
        }


# ---------------------------------------------------------------------------
# Pass 1b: Cross-Theme Deduplication
# ---------------------------------------------------------------------------


CROSS_THEME_SYSTEM = """You are merging feature clusters that were independently created from different themes. Many clusters from different themes describe the SAME feature.

For example:
- "Device Inventory Export" (theme: inventory) and "Export Device List to CSV" (theme: device_management) are the SAME feature.
- "AP Channel Utilization Report" (theme: monitoring) and "Radio Frequency Analytics" (theme: RF) overlap significantly.

Your job: Identify clusters that should be merged and produce a consolidated list.

For each OUTPUT cluster:
1. "name": The MOST SPECIFIC, actionable name from the merged set. Must contain a verb or action noun.
   FORBIDDEN patterns: "Features", "X Features", any name that is just a category label.
   If merging would create a vague name, keep the most specific sub-cluster name instead.
2. "description": Merged description covering all merged clusters
3. "merged_from": List of original cluster names that were merged
4. "idea_titles": Combined list of all idea titles from merged clusters
5. "idea_count": Total ideas across all merged clusters
6. "primary_theme": The most relevant theme
7. "total_demand": Sum of demand across merged clusters
8. "has_foundational": true if any merged cluster was foundational
9. "buildable_via_api": true if buildable via Mist REST API. false if it requires platform/hardware/firmware changes by Juniper.

Rules:
- If two clusters overlap > 70%, merge them.
- If clusters are truly distinct, keep them separate.
- Err on the side of merging — fewer, richer clusters are better than many thin ones.
- The output list should be SHORTER than the input list.
- NEVER create a merged cluster with a generic name. The merged name must be as specific as the best input name.

Return ONLY valid JSON array of cluster objects."""


class CrossThemeConsolidator:
    """Pass 1b: Merge similar clusters across different themes."""

    def __init__(self, fleet_configs: list[dict]):
        self.fleet_configs = fleet_configs

    def deduplicate(self, clusters: list[dict]) -> list[dict]:
        """Send clusters in batches to AI for cross-theme dedup."""
        if len(clusters) <= CROSS_THEME_BATCH_SIZE:
            return self._dedup_batch(clusters)

        batches = self._build_batches(clusters)
        logger.info(
            "Pass 1b: %d clusters in %d batches for cross-theme dedup",
            len(clusters),
            len(batches),
        )

        runner = FleetRunner(self.fleet_configs, "Pass 1b")
        round1_results = runner.run_all(batches, self._process_batch)

        if len(round1_results) > CROSS_THEME_BATCH_SIZE:
            logger.info(
                "Pass 1b round 2: merging %d clusters from round 1",
                len(round1_results),
            )
            batches2 = self._build_batches(round1_results)
            round2_results = runner.run_all(batches2, self._process_batch)
            logger.info("Pass 1b: %d -> %d clusters after 2 rounds", len(clusters), len(round2_results))
            return round2_results

        logger.info("Pass 1b: %d -> %d clusters after dedup", len(clusters), len(round1_results))
        return round1_results

    @staticmethod
    def _build_batches(clusters: list[dict]) -> list[list[dict]]:
        """Split clusters into batches for processing."""
        return [clusters[i : i + CROSS_THEME_BATCH_SIZE] for i in range(0, len(clusters), CROSS_THEME_BATCH_SIZE)]

    def _dedup_batch(self, clusters: list[dict]) -> list[dict]:
        """Run a single batch through one AI call."""
        if not self.fleet_configs:
            return clusters
        client = AiClient(self.fleet_configs[0])
        return self._process_batch(client, clusters)

    @staticmethod
    def _process_batch(client: AiClient, batch: list[dict]) -> list[dict]:
        """Process one batch of clusters for cross-theme merging."""
        summaries = []
        for idx, cluster in enumerate(batch):
            summary = (
                f"[{idx}] NAME: {cluster.get('name', '?')}\n"
                f"    THEME: {cluster.get('primary_theme', cluster.get('source_theme', '?'))}\n"
                f"    DESC: {cluster.get('description', '')}\n"
                f"    IDEAS: {cluster.get('idea_count', 1)} | DEMAND: {cluster.get('total_demand', 0)}\n"
                f"    FOUNDATIONAL: {cluster.get('has_foundational', False)}"
            )
            summaries.append(summary)

        user_prompt = f"Total clusters to review: {len(batch)}\n" f"{'='*40}\n\n" + "\n---\n".join(summaries)

        result = client.call_json(CROSS_THEME_SYSTEM, user_prompt)
        if not isinstance(result, list):
            logger.warning("Pass 1b: Non-list response, returning original batch")
            return batch

        valid_clusters = [c for c in result if isinstance(c, dict)]
        if not valid_clusters:
            logger.warning("Pass 1b: No valid dict items in response, returning batch")
            return batch

        for cluster in valid_clusters:
            if "idea_count" not in cluster:
                merged_originals = cluster.get("merged_from", [])
                original_counts = [b.get("idea_count", 1) for b in batch if b.get("name") in merged_originals]
                cluster["idea_count"] = sum(original_counts) or 1

            if "idea_titles" not in cluster:
                merged_names = cluster.get("merged_from", [])
                all_titles = []
                for b_cluster in batch:
                    if b_cluster.get("name") in merged_names:
                        all_titles.extend(b_cluster.get("idea_titles", []))
                cluster["idea_titles"] = all_titles or ["Unknown"]

        return valid_clusters


# ---------------------------------------------------------------------------
# Pass 2: Feasibility Scoring (with real API endpoint data)
# ---------------------------------------------------------------------------


SCORING_SYSTEM = """You are a senior software engineer estimating the buildability of features for MistHelper, a Python CLI tool that wraps the Juniper Mist REST API.

IMPORTANT CONTEXT: MistHelper can ONLY automate operations via the Mist REST API. It CANNOT:
- Change AP hardware behavior (antenna tilt, power modes)
- Fix firmware bugs or change firmware behavior
- Modify the Mist cloud dashboard UI
- Change how Mist cloud processes or stores data internally
- Add new API endpoints that don't exist yet

Score this feature cluster:

1. "api_feasibility" (0-10): Can the Mist API provide the data needed?
   - 10: Endpoint exists, returns exactly what's needed
   - 7-9: Endpoints exist but need combining or post-processing
   - 4-6: Partial API support, some data available
   - 1-3: Minimal API support, workarounds needed
   - 0: No API support, or requires platform changes (not API-automatable)

2. "effort": "S" (< 1 day), "M" (1-3 days), "L" (1-2 weeks), "XL" (> 2 weeks)

3. "foundational_value" (0-10): Does building this enable OTHER features?

4. "user_impact" (0-10): Value to network operations engineers (NOC)?

5. "buildable_via_api" (true/false): Can MistHelper build this by calling Mist REST API?
   - true: All required data and actions are available via API
   - false: Requires Juniper to change platform, hardware, firmware, or cloud UI
   Examples of NOT buildable: "AP antenna down-tilt", "Fix OVA deployment", "Preserve router ID on fabric update", "Radio shutdown on ethernet failure"

6. "justification": 2-3 sentences. Reference specific API endpoints if applicable.

RELEVANT API ENDPOINTS (for this feature's domain):
{api_endpoints}

Return ONLY valid JSON:
{{"api_feasibility": N, "effort": "S|M|L|XL", "foundational_value": N, "user_impact": N, "buildable_via_api": true/false, "justification": "..."}}"""


class FeasibilityScorer:
    """Pass 2: Score each cluster with real API endpoint context."""

    def __init__(self, fleet_configs: list[dict], api_index: dict):
        self.fleet_configs = fleet_configs
        self.api_index = api_index

    def score(self, clusters: list[dict]) -> list[dict]:
        """Score each cluster using the fleet."""
        logger.info("Pass 2: Scoring %d clusters", len(clusters))

        work_items = [(idx, cluster) for idx, cluster in enumerate(clusters)]
        runner = FleetRunner(self.fleet_configs, "Pass 2")
        raw_results = runner.run_all(work_items, self._score_one)

        results_by_idx: dict[int, dict] = {}
        for result in raw_results:
            if isinstance(result, dict) and "_idx" in result:
                results_by_idx[result.pop("_idx")] = result

        scored = []
        for idx, cluster in enumerate(clusters):
            merged = cluster.copy()
            if idx in results_by_idx:
                merged.update(results_by_idx[idx])
            else:
                merged.update(self._default_scores())
            scored.append(merged)

        logger.info("Pass 2: Scored %d clusters", len(scored))
        return scored

    def _score_one(self, client: AiClient, item: tuple[int, dict]) -> dict:
        """Score a single cluster with relevant API endpoints in context."""
        idx, cluster = item
        relevant_endpoints = self._find_relevant_endpoints(cluster)
        endpoint_text = self._format_endpoints(relevant_endpoints)

        system_prompt = SCORING_SYSTEM.replace("{api_endpoints}", endpoint_text)

        user_prompt = (
            f"Feature: {cluster.get('name', 'Unknown')}\n"
            f"Description: {cluster.get('description', 'N/A')}\n"
            f"Ideas merged: {cluster.get('idea_count', 1)}\n"
            f"Community demand signal: {cluster.get('total_demand', 0)}\n"
            f"Theme: {cluster.get('primary_theme', cluster.get('source_theme', 'N/A'))}\n"
            f"Foundational: {cluster.get('has_foundational', False)}\n"
        )

        result = client.call_json(system_prompt, user_prompt)
        scores = self._validate_scores(result) if isinstance(result, dict) else self._default_scores()
        scores["_idx"] = idx
        return scores

    def _find_relevant_endpoints(self, cluster: dict) -> list[dict]:
        """Find API endpoints relevant to this cluster's domain."""
        keywords: set[str] = set()
        for field in ("name", "description", "primary_theme", "source_theme"):
            text = cluster.get(field, "")
            if text:
                keywords.update(ApiCoverageFilter._extract_words(text))

        matched_endpoints: list[dict] = []
        for category, endpoints in self.api_index.items():
            category_words = set(ApiCoverageFilter._extract_words(category))
            if keywords & category_words:
                for endpoint in endpoints[:5]:
                    matched_endpoints.append(
                        {
                            "category": category,
                            "method": endpoint.get("method", ""),
                            "path": endpoint.get("path", ""),
                            "summary": endpoint.get("summary", ""),
                        }
                    )
            if len(matched_endpoints) >= 15:
                break
        return matched_endpoints

    @staticmethod
    def _format_endpoints(endpoints: list[dict]) -> str:
        """Format endpoints for the AI prompt."""
        if not endpoints:
            return "(No directly matching endpoints found)"
        lines = []
        for ep in endpoints:
            lines.append(f"  {ep['method']} {ep['path']} — {ep['summary']} [{ep['category']}]")
        return "\n".join(lines)

    @staticmethod
    def _validate_scores(scores: dict) -> dict:
        """Clamp scores to valid ranges."""
        validated = {}
        for field in ("api_feasibility", "foundational_value", "user_impact"):
            value = scores.get(field, 5)
            try:
                value = max(0, min(10, int(value)))
            except (TypeError, ValueError):
                value = 5
            validated[field] = value

        effort = str(scores.get("effort", "M")).upper()
        validated["effort"] = effort if effort in EFFORT_MAP else "M"
        validated["justification"] = str(scores.get("justification", ""))[:500]

        buildable = scores.get("buildable_via_api", True)
        if isinstance(buildable, str):
            validated["buildable_via_api"] = buildable.lower() not in ("false", "no", "0")
        else:
            validated["buildable_via_api"] = bool(buildable)

        return validated

    @staticmethod
    def _default_scores() -> dict:
        """Default scores when AI scoring fails."""
        return {
            "api_feasibility": 5,
            "effort": "M",
            "foundational_value": 5,
            "user_impact": 5,
            "buildable_via_api": True,
            "justification": "Default scores -- AI scoring failed",
        }


# ---------------------------------------------------------------------------
# Pass 3: Stack Ranking (Ollama Fleet)
# ---------------------------------------------------------------------------


RANKING_SYSTEM = """You rank features for MistHelper (Python CLI for Juniper Mist REST API). Return ONLY valid JSON.

CRITICAL FILTERS (apply BEFORE scoring):
- If buildable_via_api is false or "False", give score 0. MistHelper cannot build platform/hardware/firmware changes.
- If the feature name is vague (just a category like "Features", "Monitoring Features", "Security Features"), give score 0.
- If MistHelper ALREADY HAS this feature (see existing operations below), give score 0.

EXISTING MISTHELPER OPERATIONS (already built -- score 0 for duplicates):
- Firmware upgrades (AP, Switch, SSR) with scheduling and template-based targeting
- Device inventory export (all types: AP, switch, gateway)
- Site/org listing and data extraction
- WebSocket real-time commands for APs, switches, gateways
- Packet captures (site-level and org-level, including switch port captures)
- Device events, stats, and license reporting
- Template management (WLAN, RF, network, device profiles)
- Webhook management
- SLE metrics extraction
- Alarm reporting
- Client data extraction (wireless, wired, WAN)
- WLAN configuration export
- RF template management
- AP reboots (site-wide, specific APs, by model)
- Virtual Chassis conversion operations
- SSH command runner (bulk device command execution)

Scoring formula for REMAINING features:
- Buildability (40%): api_feasibility / effort_numeric
- Impact (40%): user_impact * demand (capped at 50)
- Strategic (20%): foundational_value

Return a JSON object: {"ranked": [{"name": "exact name", "score": 0-100, "reason": "short"}]}
Sort best to worst. Use EXACT feature names from input. No text outside JSON."""


class StackRanker:
    """Pass 3: Use Ollama fleet to rank clusters and pick top N."""

    def __init__(self, fleet_configs: list[dict], top_n: int = TOP_N):
        self.fleet_configs = fleet_configs
        self.top_n = top_n

    def rank(self, scored_clusters: list[dict]) -> list[dict]:
        """Rank clusters using fleet AI ranking with local fallback."""
        logger.info("Pass 3: Ranking %d clusters via Ollama fleet", len(scored_clusters))

        chunks = self._chunk_clusters(scored_clusters, chunk_size=12)
        work_items = list(enumerate(chunks))

        runner = FleetRunner(self.fleet_configs, "Pass 3")
        chunk_results = runner.run_all(work_items, self._rank_one_chunk)

        all_ranked: list[dict] = []
        for result in chunk_results:
            if isinstance(result, dict) and "ranked" in result:
                all_ranked.extend(result["ranked"])

        if not all_ranked:
            logger.warning("Pass 3: No AI results, using local scoring")
            return self._local_rank(scored_clusters)[: self.top_n]

        all_ranked.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        seen_names: dict[str, int] = {}
        deduped: list[dict] = []
        for feature in all_ranked:
            raw_name = feature.get("name", "").strip()
            cleaned_name = self._clean_feature_name(raw_name)
            feature["name"] = cleaned_name
            normalized = cleaned_name.lower()
            if normalized not in seen_names:
                seen_names[normalized] = len(deduped)
                deduped.append(feature)
        all_ranked = deduped

        if len(all_ranked) < self.top_n:
            ranked_names = {r.get("name") for r in all_ranked}
            supplement = self._local_rank(
                [c for c in scored_clusters if c.get("name") not in ranked_names],
            )
            all_ranked.extend(supplement)

        for idx, feature in enumerate(all_ranked[: self.top_n]):
            feature["rank"] = idx + 1

        return all_ranked[: self.top_n]

    @staticmethod
    def _clean_feature_name(name: str) -> str:
        """Remove artifacts from AI-generated feature names."""
        cleaned = re.sub(r"\s*\(continued\)", "", name, flags=re.IGNORECASE)
        mixed_match = re.match(r"Mixed\([^)]*\)\s*(.*)", cleaned)
        if mixed_match:
            suffix = mixed_match.group(1).strip()
            cleaned = suffix if suffix else cleaned
        cleaned = re.sub(r"Mixed_remainder\([^)]*\)\s*", "", cleaned)
        return cleaned.strip() or name

    def _rank_one_chunk(self, client: AiClient, item: tuple[int, list[dict]]) -> dict:
        """Rank one chunk of clusters via fleet AI."""
        chunk_idx, clusters = item
        summaries = self._build_summaries(clusters)

        user_prompt = f"Rank these {len(clusters)} features best-to-worst:\n\n" + "\n".join(summaries)

        result = client.call_json(RANKING_SYSTEM, user_prompt, json_mode=True)
        if isinstance(result, dict) and "ranked" in result:
            result = result["ranked"]
        if not isinstance(result, list):
            logger.warning("Pass 3 chunk %d: Non-list AI response, using local", chunk_idx)
            return {"ranked": self._local_rank(clusters)}

        ranked = self._match_ai_results(result, clusters)
        if len(ranked) < len(clusters) // 2:
            logger.info("Pass 3 chunk %d: AI matched %d/%d, supplementing", chunk_idx, len(ranked), len(clusters))
            ranked_names = {r.get("name") for r in ranked}
            supplement = self._local_rank(
                [c for c in clusters if c.get("name") not in ranked_names],
            )
            ranked.extend(supplement)

        return {"ranked": ranked}

    @staticmethod
    def _build_summaries(clusters: list[dict]) -> list[str]:
        """Build one-line summaries for the AI prompt."""
        summaries = []
        for idx, cluster in enumerate(clusters):
            effort_num = EFFORT_MAP.get(cluster.get("effort", "M"), 2)
            line = (
                f"[{idx}] {cluster.get('name', '?')} "
                f"| ideas={cluster.get('idea_count', 1)} "
                f"| demand={cluster.get('total_demand', 0)} "
                f"| api={cluster.get('api_feasibility', 5)} "
                f"| effort={cluster.get('effort', 'M')}({effort_num}) "
                f"| impact={cluster.get('user_impact', 5)} "
                f"| foundational={cluster.get('foundational_value', 5)} "
                f"| desc: {cluster.get('description', '')[:100]}"
            )
            summaries.append(line)
        return summaries

    @staticmethod
    def _match_ai_results(result: list, clusters: list[dict]) -> list[dict]:
        """Match AI-ranked names back to the original cluster data."""
        ranked = []
        for entry in result:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "")
            matched = StackRanker._find_cluster(name, clusters)
            if matched:
                matched["final_score"] = entry.get("score", 0)
                matched["rank_justification"] = entry.get("reason", entry.get("justification", ""))
                ranked.append(matched)
        return ranked

    @staticmethod
    def _find_cluster(name: str, clusters: list[dict]) -> dict | None:
        """Find a cluster by name (exact then substring match)."""
        name_lower = name.lower().strip()
        for cluster in clusters:
            if cluster.get("name", "").lower().strip() == name_lower:
                return cluster.copy()
        for cluster in clusters:
            cluster_name = cluster.get("name", "").lower()
            if name_lower in cluster_name or cluster_name in name_lower:
                return cluster.copy()
        return None

    @staticmethod
    def _local_rank(clusters: list[dict]) -> list[dict]:
        """Rank clusters using a deterministic local formula."""
        for cluster in clusters:
            if not cluster.get("buildable_via_api", True):
                cluster["final_score"] = 0.0
                continue

            api_f = cluster.get("api_feasibility", 5)
            effort_num = EFFORT_MAP.get(cluster.get("effort", "M"), 2)
            user_imp = cluster.get("user_impact", 5)
            demand = cluster.get("total_demand", cluster.get("idea_count", 1))
            foundational = cluster.get("foundational_value", 5)

            buildability = api_f * (1.0 / effort_num) * 10
            impact = user_imp * min(demand, 50) / 50.0 * 10
            score = (buildability * 0.4) + (impact * 0.4) + (foundational * 0.2)
            cluster["final_score"] = round(score, 2)

        clusters.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        for idx, cluster in enumerate(clusters):
            cluster["rank"] = idx + 1
        return clusters

    @staticmethod
    def _chunk_clusters(clusters: list[dict], chunk_size: int = 12) -> list[list[dict]]:
        """Split clusters into fleet-distributable chunks."""
        return [clusters[i : i + chunk_size] for i in range(0, len(clusters), chunk_size)]


# ---------------------------------------------------------------------------
# Pass 4: Dependency Ordering
# ---------------------------------------------------------------------------


class DependencyOrderer:
    """Pass 4: Order the top N features for optimal build sequence."""

    def order(self, ranked: list[dict]) -> list[dict]:
        """Reorder: foundational features first, then by composite score."""
        logger.info("Pass 4: Ordering %d features by dependencies", len(ranked))

        foundational = [
            feature
            for feature in ranked
            if feature.get("foundational_value", 0) >= 7 or feature.get("has_foundational", False)
        ]
        standard = [feature for feature in ranked if feature not in foundational]

        foundational.sort(
            key=lambda x: (
                -x.get("foundational_value", 0),
                -x.get("final_score", 0),
            ),
        )
        standard.sort(key=lambda x: x.get("rank", 999))

        ordered = foundational + standard
        for idx, feature in enumerate(ordered):
            feature["build_order"] = idx + 1
            feature["build_phase"] = self._assign_phase(idx, len(ordered))

        logger.info(
            "Pass 4: %d foundational (build first), %d standard",
            len(foundational),
            len(standard),
        )
        return ordered

    @staticmethod
    def _assign_phase(index: int, total: int) -> str:
        """Assign a build phase label."""
        fraction = index / max(total, 1)
        if fraction < 0.15:
            return "Phase 1: Foundation"
        if fraction < 0.40:
            return "Phase 2: Core"
        if fraction < 0.70:
            return "Phase 3: Enhancement"
        return "Phase 4: Polish"


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


class ReportGenerator:
    """Generate final output files in markdown, JSON, and CSV."""

    def generate_all(self, features: list[dict], stats: dict) -> None:
        """Generate all three report formats."""
        self._generate_markdown(features, stats)
        self._generate_json(features, stats)
        self._generate_csv(features)

    def _generate_markdown(self, features: list[dict], stats: dict) -> None:
        """Generate comprehensive markdown report."""
        path = OUTPUT_DIR / "mist_ideas_top100.md"
        lines = self._build_header(stats, len(features))
        lines.extend(self._build_phase_tables(features))
        lines.extend(self._build_detail_sections(features))

        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        logger.info("Markdown report: %s (%d KB)", path, path.stat().st_size // 1024)

    @staticmethod
    def _build_header(stats: dict, feature_count: int) -> list[str]:
        """Build markdown header section."""
        return [
            "# MistHelper Feature Roadmap: Top 100 Buildable Features",
            "",
            "## Executive Summary",
            "",
            f"- **Source ideas analyzed**: {stats.get('total_ideas', 0):,}",
            f"- **After MistHelper-centric filter**: {stats.get('after_prefilter', 0):,}",
            f"- **Feature clusters formed**: {stats.get('clusters_formed', 0):,}",
            f"- **After cross-theme dedup**: {stats.get('clusters_deduped', 'N/A')}",
            f"- **Top features selected**: {feature_count}",
            f"- **Foundational features**: {stats.get('foundational_count', 0)}",
            "",
            "## Build Phases",
            "",
        ]

    @staticmethod
    def _build_phase_tables(features: list[dict]) -> list[str]:
        """Build phase-grouped summary tables."""
        lines: list[str] = []
        current_phase = ""
        for feature in features:
            phase = feature.get("build_phase", "")
            if phase != current_phase:
                current_phase = phase
                lines.append(f"### {phase}")
                lines.append("")
                lines.append("| # | Feature | Ideas | Demand | API | Effort | Impact | Score |")
                lines.append("| - | - | - | - | - | - | - | - |")

            lines.append(
                f"| {feature.get('build_order', '?')} "
                f"| {feature.get('name', 'Unknown')} "
                f"| {feature.get('idea_count', 1)} "
                f"| {feature.get('total_demand', 0)} "
                f"| {feature.get('api_feasibility', '?')}/10 "
                f"| {feature.get('effort', '?')} "
                f"| {feature.get('user_impact', '?')}/10 "
                f"| {feature.get('final_score', 0):.1f} |"
            )
        lines.append("")
        return lines

    @staticmethod
    def _build_detail_sections(features: list[dict]) -> list[str]:
        """Build per-feature detail sections."""
        lines = ["## Feature Details", ""]
        for feature in features:
            lines.append(f"### {feature.get('build_order', '?')}. {feature.get('name', 'Unknown')}")
            lines.append("")
            lines.append(f"**Description**: {feature.get('description', 'N/A')}")
            lines.append("")
            lines.append(f"- **API Feasibility**: {feature.get('api_feasibility', '?')}/10")
            lines.append(f"- **Effort**: {feature.get('effort', '?')}")
            lines.append(f"- **User Impact**: {feature.get('user_impact', '?')}/10")
            lines.append(f"- **Foundational Value**: {feature.get('foundational_value', '?')}/10")
            lines.append(f"- **Ideas Merged**: {feature.get('idea_count', 1)}")
            lines.append(f"- **Community Demand**: {feature.get('total_demand', 0)}")
            theme = feature.get("primary_theme", feature.get("source_theme", "N/A"))
            lines.append(f"- **Theme**: {theme}")

            justification = feature.get("justification", feature.get("rank_justification", ""))
            if justification:
                lines.append(f"- **Rationale**: {justification}")

            merged = feature.get("merged_from", [])
            if merged:
                lines.append(f"- **Merged from**: {', '.join(str(m) for m in merged)}")

            titles = feature.get("idea_titles", [])
            if titles:
                shown = titles[:8]
                lines.append(f"- **Source Ideas**: {', '.join(str(t) for t in shown)}")
                if len(titles) > 8:
                    lines.append(f"  _(and {len(titles) - 8} more)_")
            lines.append("")
        return lines

    @staticmethod
    def _generate_json(features: list[dict], stats: dict) -> None:
        """Generate JSON sidecar."""
        path = OUTPUT_DIR / "mist_ideas_top100.json"
        output = {"metadata": stats, "features": features}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2, default=str)
        logger.info("JSON report: %s (%d KB)", path, path.stat().st_size // 1024)

    @staticmethod
    def _generate_csv(features: list[dict]) -> None:
        """Generate CSV export."""
        path = OUTPUT_DIR / "mist_ideas_top100.csv"
        fieldnames = [
            "build_order",
            "build_phase",
            "name",
            "description",
            "idea_count",
            "total_demand",
            "api_feasibility",
            "effort",
            "user_impact",
            "foundational_value",
            "final_score",
            "primary_theme",
            "justification",
        ]
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for feature in features:
                row = {k: feature.get(k, "") for k in fieldnames}
                if not row.get("primary_theme"):
                    row["primary_theme"] = feature.get("source_theme", "")
                if not row.get("justification"):
                    row["justification"] = feature.get("rank_justification", "")
                writer.writerow(row)
        logger.info("CSV report: %s", path)


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------


class DistillationPipeline:
    """Orchestrate the full 6-stage distillation pipeline."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats: dict = {}

    def run(self, start_pass: int = 0) -> list[dict]:
        """Execute the pipeline from the given pass number."""
        loader = CacheLoader()
        ideas = loader.load_all()
        api_index = loader.load_api_index()
        self.stats["total_ideas"] = len(ideas)

        filtered = self._run_prefilter(ideas, api_index, start_pass)
        clusters = self._run_pass1(filtered, start_pass)
        deduped = self._run_pass1b(clusters, start_pass)
        scored = self._run_pass2(deduped, api_index, start_pass)
        ranked = self._run_pass3(scored, start_pass)
        ordered = self._run_pass4(ranked)
        self._generate_reports(ordered)
        return ordered

    def _run_prefilter(self, ideas: list[dict], api_index: dict, start: int) -> list[dict]:
        """Pre-filter: MistHelper-centric API coverage + demand signal."""
        cache_path = OUTPUT_DIR / "mist_ideas_filtered.json"
        if start > 0 and cache_path.exists():
            logger.info("Pre-filter: Loading cached results")
            with open(cache_path, encoding="utf-8") as handle:
                filtered = json.load(handle)
            self.stats["after_prefilter"] = len(filtered)
            return filtered

        logger.info("=" * 60)
        logger.info("PRE-FILTER: MistHelper-Centric API Coverage + Demand Signal")
        logger.info("=" * 60)

        api_filter = ApiCoverageFilter(api_index)
        filtered = api_filter.filter_and_score(ideas)
        self.stats["after_prefilter"] = len(filtered)

        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump(filtered, handle, indent=2, default=str)
        logger.info("Saved: %s", cache_path)
        return filtered

    def _run_pass1(self, filtered: list[dict], start: int) -> list[dict]:
        """Pass 1: Theme-based consolidation."""
        cache_path = OUTPUT_DIR / "mist_ideas_clusters.json"
        if start > 1 and cache_path.exists():
            logger.info("Pass 1: Loading cached clusters")
            with open(cache_path, encoding="utf-8") as handle:
                clusters = json.load(handle)
            self.stats["clusters_formed"] = len(clusters)
            return clusters

        logger.info("=" * 60)
        logger.info("PASS 1: Theme-Based Consolidation (Full Context)")
        logger.info("=" * 60)

        fleet_configs = self._get_fleet_configs()
        consolidator = Consolidator(fleet_configs)
        clusters = consolidator.consolidate(filtered)
        self.stats["clusters_formed"] = len(clusters)

        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump(clusters, handle, indent=2, default=str)
        logger.info("Saved: %s (%d clusters)", cache_path, len(clusters))
        return clusters

    def _run_pass1b(self, clusters: list[dict], start: int) -> list[dict]:
        """Pass 1b: Cross-theme deduplication."""
        cache_path = OUTPUT_DIR / "mist_ideas_clusters_deduped.json"
        if start > 1 and cache_path.exists():
            logger.info("Pass 1b: Loading cached deduped clusters")
            with open(cache_path, encoding="utf-8") as handle:
                deduped = json.load(handle)
            self.stats["clusters_deduped"] = len(deduped)
            return deduped

        logger.info("=" * 60)
        logger.info("PASS 1b: Cross-Theme Deduplication")
        logger.info("=" * 60)

        fleet_configs = self._get_fleet_configs()
        deduper = CrossThemeConsolidator(fleet_configs)
        deduped = deduper.deduplicate(clusters)
        self.stats["clusters_deduped"] = len(deduped)

        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump(deduped, handle, indent=2, default=str)
        logger.info("Saved: %s (%d clusters)", cache_path, len(deduped))
        return deduped

    def _run_pass2(self, clusters: list[dict], api_index: dict, start: int) -> list[dict]:
        """Pass 2: Feasibility scoring."""
        cache_path = OUTPUT_DIR / "mist_ideas_scored.json"
        if start > 2 and cache_path.exists():
            logger.info("Pass 2: Loading cached scores")
            with open(cache_path, encoding="utf-8") as handle:
                return json.load(handle)

        logger.info("=" * 60)
        logger.info("PASS 2: Feasibility Scoring (with API endpoint data)")
        logger.info("=" * 60)

        fleet_configs = self._get_fleet_configs()
        scorer = FeasibilityScorer(fleet_configs, api_index)
        scored = scorer.score(clusters)

        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump(scored, handle, indent=2, default=str)
        logger.info("Saved: %s", cache_path)
        return scored

    def _run_pass3(self, scored: list[dict], start: int) -> list[dict]:
        """Pass 3: Stack ranking."""
        cache_path = OUTPUT_DIR / "mist_ideas_ranked.json"
        if start > 3 and cache_path.exists():
            logger.info("Pass 3: Loading cached rankings")
            with open(cache_path, encoding="utf-8") as handle:
                return json.load(handle)

        logger.info("=" * 60)
        logger.info("PASS 3: Stack Ranking (Top %d)", TOP_N)
        logger.info("=" * 60)

        fleet_configs = self._get_fleet_configs()
        ranker = StackRanker(fleet_configs, top_n=TOP_N)
        ranked = ranker.rank(scored)

        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump(ranked, handle, indent=2, default=str)
        logger.info("Saved: %s", cache_path)
        return ranked

    @staticmethod
    def _run_pass4(ranked: list[dict]) -> list[dict]:
        """Pass 4: Dependency ordering."""
        logger.info("=" * 60)
        logger.info("PASS 4: Dependency Ordering")
        logger.info("=" * 60)
        return DependencyOrderer().order(ranked)

    def _generate_reports(self, features: list[dict]) -> None:
        """Generate all output reports."""
        logger.info("=" * 60)
        logger.info("GENERATING REPORTS")
        logger.info("=" * 60)

        self.stats["foundational_count"] = sum(
            1 for f in features if f.get("foundational_value", 0) >= 7 or f.get("has_foundational")
        )
        ReportGenerator().generate_all(features, self.stats)

    def _get_fleet_configs(self) -> list[dict]:
        """Get Ollama fleet backend configs."""
        fleet = OllamaFleet()
        configs = fleet.discover_and_start()
        if not configs:
            logger.error("No Ollama servers found. Set OLLAMA_SERVERS or start local Ollama.")
            sys.exit(1)
        return configs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Distill 2,400+ Mist ideas to top 100 buildable features",
    )
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    parser.add_argument(
        "--pass",
        type=int,
        default=0,
        dest="start_pass",
        help="Resume from pass N (0=prefilter, 1=consolidation, 2=scoring, 3=ranking)",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger.info("Mist Ideas Distiller v2 starting (quality mode)")
    logger.info("Cache: %s | Output: %s", CACHE_DIR, OUTPUT_DIR)

    pipeline = DistillationPipeline(
        verbose=args.verbose,
    )
    features = pipeline.run(start_pass=args.start_pass)
    logger.info(
        "Done! %d features in build order -> data/mist_ideas_top100.*",
        len(features),
    )
