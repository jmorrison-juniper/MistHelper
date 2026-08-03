"""Cache and resume helpers for the SSID Template Consolidation manager.

Holds the Phase 1 org-data cache, the per-phase result files used by
resume support, and the small set of pure helpers that operate on those
JSON payloads. Split out of the parent module so the coordinator stays
under the compliance length / block budgets while the cache surface
remains re-exported for the existing test suite.
"""

# WHY: cluster class delegates almost every attribute back to the parent manager
# via _ClusterBase.__getattr__, so pylint's "too-few-public-methods" and
# "protected-access" alarms do not fit this proxy pattern. Import-outside-toplevel
# is also intentional in sibling clusters to break cycles.
# pylint: disable=protected-access,import-outside-toplevel,too-few-public-methods

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import json  # WHY: cache is JSON-encoded on disk
import logging  # WHY: emit cache/resume telemetry alongside other phases
import os  # WHY: file existence + path composition on Windows/POSIX
from datetime import datetime  # WHY: ISO timestamps for cache freshness math
from typing import TYPE_CHECKING, Any  # WHY: broad typing for opaque payloads

from ._ssid_template_cluster import _ClusterBase  # WHY: shared parent-proxy wrapper

if TYPE_CHECKING:  # WHY: only pulled in by type checkers to avoid import cycle
    from collections.abc import Callable  # WHY: precise callable type for safe_input fn

    SafeInputFn = Callable[..., str]  # WHY: EOF-safe input reader signature


# ---------------------------------------------------------------------------
# Pure module-level helpers (imported by tests)
# ---------------------------------------------------------------------------


def _cache_age_minutes(collected_at: str) -> float:  # WHY: pure helper reused by cache freshness logging
    """Return age of cache in minutes from ISO timestamp."""
    collected_time = datetime.fromisoformat(collected_at)  # WHY: parse ISO-8601 back to aware dt
    age_delta = datetime.now(tz=collected_time.tzinfo) - collected_time  # WHY: preserve tz semantics
    return age_delta.total_seconds() / 60.0  # WHY: analyzer scores age in minutes


def _check_prerequisite_for_all(phase_number: int) -> bool:  # WHY: run-all short-circuit for phase 1
    """Check prerequisite for run-all-phases mode (phase > 1)."""
    return phase_number <= 1  # WHY: only phase 1 has no upstream artefacts


def _check_cache_exists(cache_file: str) -> bool:  # WHY: gate downstream phases on phase-1 artefact
    """Check if Phase 1 cache file exists."""
    if not os.path.exists(cache_file):  # WHY: guard first-run before phase 1 completes
        logging.warning("Phase 1 cache not found. Run Phase 1 first.")  # WHY: teach operator the fix
        return False  # WHY: signal caller to abort the current phase
    return True  # WHY: cache present, downstream phase may proceed


def _handle_completed_resume(  # WHY: UX branch when prior run finished all rows
    phase: int,
    completed_count: int,
    total: int,
    safe_input_fn: SafeInputFn,
) -> tuple[bool, list[dict[str, Any]]]:
    """Handle resume when phase is already complete."""
    logging.warning(
        "Phase %d already completed (%d/%d). Re-running will overwrite.", phase, completed_count, total
    )  # WHY: warn
    choice: str = safe_input_fn(  # WHY: ask before re-running a completed phase
        "Re-run from scratch? (y/N): ",
        context="ssid_consolidation_resume",
    )
    if choice.strip().lower() in ("y", "yes"):  # WHY: explicit opt-in to re-run
        return False, []  # WHY: caller treats this as a fresh start
    return True, []  # WHY: preserve existing artefacts, no new results to seed


def _handle_partial_resume(  # WHY: UX branch when prior run stopped mid-phase
    phase: int,
    completed_count: int,
    total: int,
    prior_results: list[dict[str, Any]],
    safe_input_fn: SafeInputFn,
) -> tuple[bool, list[dict[str, Any]]]:
    """Handle resume when phase is partially complete."""
    logging.warning(
        "Phase %d partially completed (%d/%d).", phase, completed_count, total
    )  # WHY: report progress to operator
    choice: str = safe_input_fn(  # WHY: default (Y) is resume — matches operator intent
        "Resume from last checkpoint? (Y/n): ",
        context="ssid_consolidation_resume",
    )
    if choice.strip().lower() in ("n", "no"):  # WHY: explicit opt-out restarts from scratch
        return False, []  # WHY: caller discards prior rows and restarts
    return True, prior_results  # WHY: seed caller with completed rows so we skip them


# ---------------------------------------------------------------------------
# Cluster class wrapping parent cache/resume methods
# ---------------------------------------------------------------------------


class _SsidTemplateCacheCluster(_ClusterBase):  # WHY: proxy cluster grouping cache/resume methods on parent
    """Owns cache read/write, phase-result JSON I/O, and resume prompts."""

    def _check_prerequisite(self, phase: int) -> bool:  # WHY: enforce artefact chain across phases
        """Verify that the prior phase's output exists."""
        if phase <= 1:  # WHY: phase 1 has no upstream artefacts to require
            return True  # WHY: unconditional pass for the first phase
        parent = self._mm  # WHY: proxy alias for readability + W0212 avoidance
        if phase == 2:  # WHY: phase 2 depends solely on the audit cache
            return _check_cache_exists(parent.CACHE_FILE)  # WHY: reuse shared cache-existence guard
        prior_file = parent.PHASE_RESULT_FILES.get(phase - 1)  # WHY: chain phases via results file
        if prior_file and not os.path.exists(prior_file):  # WHY: prior artefact absent blocks this phase
            logging.warning("Phase %d results not found. Run Phase %d first.", phase - 1, phase - 1)  # WHY: teach fix
            return False  # WHY: signal caller to abort
        return True  # WHY: prior artefact present, proceed

    def _load_cache(self) -> dict[str, Any] | None:  # WHY: return typed cache or None on miss/corruption
        """Load Phase 1 cache if it exists and is fresh."""
        parent = self._mm  # WHY: proxy alias — keeps helper focused
        if not os.path.exists(parent.CACHE_FILE):  # WHY: no cache yet, force fetch
            return None  # WHY: caller must repopulate from live API
        try:  # WHY: tolerate corrupt/unreadable cache without failing startup
            with open(parent.CACHE_FILE, encoding="utf-8") as file_handle:  # WHY: utf-8 for portability
                cached: dict[str, Any] = json.load(file_handle)  # WHY: decode JSON payload once
            self._log_cache_age(cached, parent.CACHE_FRESHNESS_MINUTES)  # WHY: age telemetry only
            return cached  # WHY: return regardless of age — caller may still consent to reuse
        except (json.JSONDecodeError, OSError) as error:  # WHY: JSON or disk errors are recoverable
            logging.warning("Failed to load cache: %s", error)  # WHY: corrupt/missing cache is recoverable
            return None  # WHY: treat as cache-miss and let caller repopulate

    @staticmethod
    def _log_cache_age(cached: dict[str, Any], freshness_minutes: int) -> None:  # WHY: static — no self needed
        """Emit an info-level line comparing cache age to the freshness budget."""
        collected_at = cached.get("collected_at", "")  # WHY: older caches may lack timestamp
        if not collected_at:  # WHY: nothing to compare against, skip logging
            return  # WHY: no timestamp → nothing to log
        age_minutes = _cache_age_minutes(collected_at)  # WHY: reuse shared helper for age math
        if age_minutes <= freshness_minutes:  # WHY: distinguish fresh vs stale in logs
            logging.info("Cache is fresh (%.1f minutes old)", age_minutes)  # WHY: fresh branch telemetry
        else:
            logging.info("Cache is stale (%.1f minutes old)", age_minutes)  # WHY: stale branch telemetry

    def _save_cache(self, data: dict[str, Any]) -> None:  # WHY: persists Phase-1 cache to disk
        """Write cache JSON with collection timestamp."""
        parent = self._mm  # WHY: bind parent state used across attribute writes
        data["collected_at"] = datetime.now().isoformat()  # WHY: stamp for freshness math
        data["target_ssid"] = parent.target_ssid  # WHY: preserve SSID scope in payload
        data["org_id"] = parent.org_id  # WHY: preserve org scope in payload
        try:  # WHY: tolerate disk/permission errors without failing pipeline
            with open(parent.CACHE_FILE, "w", encoding="utf-8") as file_handle:  # WHY: overwrite prior cache
                json.dump(data, file_handle, indent=2, default=str)  # WHY: pretty for grep
            logging.info("Cache saved to %s", parent.CACHE_FILE)  # WHY: confirm write path in logs
        except OSError as error:  # WHY: disk full/perm error path
            logging.error("Failed to save cache: %s", error)  # WHY: disk full/perm errors are recoverable

    def _save_phase_results(self, phase: int, results: list[dict[str, Any]]) -> None:  # WHY: resume artefact writer
        """Write phase results JSON for resume support."""
        parent = self._mm  # WHY: bind parent state used across attribute writes
        result_file = parent.PHASE_RESULT_FILES.get(phase)  # WHY: phase 1 has no results file
        if not result_file:  # WHY: no-op for phases without a persistent artefact
            return  # WHY: nothing to persist for this phase
        payload = {  # WHY: standardized resume envelope shared with _load_phase_results
            "phase": phase,
            "target_ssid": parent.target_ssid,
            "started_at": datetime.now().isoformat(),
            "total": len(results),
            "results": results,
        }
        try:  # WHY: tolerate disk/permission errors without failing pipeline
            with open(result_file, "w", encoding="utf-8") as file_handle:  # WHY: overwrite prior results
                json.dump(payload, file_handle, indent=2, default=str)  # WHY: pretty for grep
            logging.info("Phase %d results saved to %s", phase, result_file)  # WHY: confirm write path in logs
        except OSError as error:  # WHY: disk full/perm error path
            logging.error("Failed to save phase %d results: %s", phase, error)  # WHY: recoverable disk error

    def _load_phase_results(self, phase: int) -> dict[str, Any] | None:
        """Load phase results JSON if it exists."""
        parent = self._mm  # WHY: bind parent state
        result_file = parent.PHASE_RESULT_FILES.get(phase)  # WHY: phase 1 has no results file
        if not result_file or not os.path.exists(result_file):  # WHY: nothing to resume from
            return None
        try:
            with open(result_file, encoding="utf-8") as file_handle:
                loaded: dict[str, Any] = json.load(file_handle)
            return loaded
        except (json.JSONDecodeError, OSError) as error:
            logging.warning("Failed to load phase %d results: %s", phase, error)
            return None

    def _offer_resume(
        self,
        phase: int,  # WHY: the prior results load from disk below, so no caller supplies them.
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Detect partial run and offer to resume or restart."""
        parent = self._mm  # WHY: proxy alias — reused thrice below
        existing = self._load_phase_results(phase)  # WHY: no prior run means nothing to resume
        if not existing:
            return False, []
        prior_results: list[dict[str, Any]] = existing.get("results", [])
        completed_count = sum(1 for row in prior_results if row.get("status") not in ("pending", "failed"))
        total = existing.get("total", 0)
        if completed_count >= total:  # WHY: fully complete → different UX than partial
            return _handle_completed_resume(phase, completed_count, total, parent.safe_input_fn)
        return _handle_partial_resume(phase, completed_count, total, prior_results, parent.safe_input_fn)
