# Implementation Plan: Source back-reference settings slice

## Scope

This plan delivers the settings sub-slice of issue #1703. It moves low-risk source reads away from `MistHelper`.

The branch does not edit `MistHelper.py`. The root alias remains because another agent owns that file.

## Technical Context

- Python 3.13.
- Existing packages under `src`, `tests`, `specs`, and `changelog.d`.
- Existing quality gates in `pyproject.toml` and GitHub Actions.

## Changes

1. Add `src.config.runtime_settings` for the page limit, CSV freshness, API retry settings, and small runtime flags.
2. Add `src.api.api_usage_cache` for the shared rate-limit cache.
3. Extend `src.refactors.fast_mode_constants` with retry and fallback thread settings.
4. Update startup publishing in `src.refactors.main_entrypoint`.
5. Move direct settings reads in the API helpers, gateway helpers, and upgrade portal helpers.
6. Update focused tests so they patch the new source modules.

## Risk Controls

- Keep all root-facing late imports that still protect cycles.
- Run targeted tests before the full gate.
- Run import checks for each changed source module group.
- Prove that `MistHelper.py` does not appear in the diff.

## Out of Scope

- Do not remove `sys.modules["MistHelper"]`.
- Do not refactor capture dependency objects.
- Do not move exporter class imports.
- Do not finish all 376 text references.
