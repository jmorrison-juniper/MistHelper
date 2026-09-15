# Implementation Plan: Performance monitoring modules

**Branch**: `feat/2533-perf-monitoring` | **Date**: 2026-09-15 | **Spec**: `specs/2533-perf-monitoring/spec.md`

**Input**: Feature specification from `specs/2533-perf-monitoring/spec.md`

## Summary

Add the shared performance monitoring package that issue #2533 requests. Keep the recorder off by default. Use a level gate, spans, a bounded sink, and a deny-by-default privacy policy.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Standard library only. No new dependency is required.

**Storage**: Bounded JSON Lines output under `data/performance/`.

**Testing**: pytest, pytest-cov, ruff, black, mypy, pydocstyle, and bandit.

**Target Platform**: Windows development, Linux container runtime.

**Project Type**: Python library code inside the existing CLI project.

**Performance Goals**: The disabled path must remain close to a null context manager cost.

**Constraints**: Monitoring must not store secrets, personal data, raw paths, URLs, SQL text, IP addresses, MAC addresses, UUIDs, or tokens.

**Scale/Scope**: This slice adds the shared modules and tests. Later slices can add hooks from issue #2482.

## Constitution Check

- The new performance package holds five modules after `clock.py` moves into `recorder.py`.
- The code keeps monitoring behind an explicit level setting.
- The sink writes only bounded records and never raises into the measured operation.
- The privacy policy uses deny-by-default label handling.
- Existing `src/utils` already exceeds five children. This feature does not add another direct child there beyond the existing package.

## Project Structure

### Documentation (this feature)

```text
specs/2533-perf-monitoring/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
src/utils/performance/
├── __init__.py
├── event.py
├── privacy.py
├── recorder.py
└── sink.py

tests/unit/utils/performance/
└── test_privacy_filter_storage.py
```

**Structure Decision**: Keep the feature in `src/utils/performance/` because issue #2533 requires that import path. Keep all behavior inside classes in that package.

## Design

### `src/utils/performance/event.py`

`PerformanceEvent` stores the bounded event contract. `EventSource` reduces a raw source path to a safe source area before JSON output.

### `src/utils/performance/privacy.py`

`PerformancePrivacyPolicy` owns the deny patterns, allowed dimension keys, allowed dimension values, count buckets, status families, and source label scrubber.

### `src/utils/performance/recorder.py`

`RecorderSettings` holds the level, sample rate, queue bound, byte bound, and CPU clock flag. `Recorder` gates families before span allocation. `Span` reads wall and CPU clocks once at start and once at exit. `NullSpan` is the disabled path.

### `src/utils/performance/sink.py`

`BoundedSink` bounds retained records by count and byte estimate. It flushes JSON Lines on request. It opens its circuit after repeated write failures.

## Privacy Design

The privacy policy denies by default. It drops unknown label keys. It permits only fixed values for known label keys. It redacts text that looks like a secret, personal data, a raw path, a URL, SQL text, an IP address, a MAC address, a UUID, or a token.

## Validation Plan

Run these gates before the commit.

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pydocstyle src/
python -m bandit -q -c pyproject.toml -r src/
python -m pytest tests/test_performance_monitoring.py tests/test_performance_memory.py tests/unit/utils/performance/test_privacy_filter_storage.py -v
python -m pytest tests/test_performance_monitoring.py tests/test_performance_memory.py tests/unit/utils/performance/test_privacy_filter_storage.py --cov=src/utils/performance --cov-report=term-missing
```
