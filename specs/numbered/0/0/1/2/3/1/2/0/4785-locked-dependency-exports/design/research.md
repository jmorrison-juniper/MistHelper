# Research: Locked Dependency Exports

## Decision: Use the tracked lock as the version source

Generate `requirements.txt` and `requirements-dev.txt` from `uv.lock`.

**Rationale**: The repository guard compares both files with locked UV exports. Direct edits can remove platform markers or publish versions that the lock does not contain.

**Alternatives considered**:

- Edit `requirements.txt` by hand. Rejected because the export guard detects drift.
- Change project limits to permit Gunicorn 27. Rejected because this issue does not assess that compatibility change.

## Decision: Upgrade only compatible package versions

Upgrade `markdown-it-py`, `openai`, and `simplejson` through UV. Keep Gunicorn below version 27.

**Rationale**: The selected package upgrades fit the existing project limits. The declared Gunicorn limit excludes version 27.

**Alternatives considered**:

- Keep the requested Gunicorn 27 pin. Rejected because it conflicts with `pyproject.toml`.
- Remove platform markers from exports. Rejected because the lock defines those markers for supported platforms.

## Decision: Regenerate both exports

Regenerate the runtime and development requirements files after the lock update.

**Rationale**: The development export includes runtime packages. A runtime package update makes both exports stale.

**Alternatives considered**:

- Regenerate only the runtime export. Rejected because the dependency export guard checks both files.
