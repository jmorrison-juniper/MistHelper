# Remote Evidence Checklist: SpecKit Task Audit Link and Legend Classification

**Purpose**: Confirm that each remote claim in the record has a path, a ref, a blob SHA, a result, and a line.

**Created**: 2026-11-26

**Feature**: [research.md](../research.md)

## Remote Checks

- [x] The remote table in `research.md` holds 48 rows. The `remote_checks` array in the status file holds 48 entries.
- [x] Each row names a path, a ref, a blob SHA or `none`, a result, and a line or zero.
- [x] Each code claim cites a remote path and a line. No claim uses a local path as proof.
- [x] The local `.venv` copy is local-only evidence. No remote row cites it.
- [x] Each commit in the record exists on GitHub (research R2 and R3).
- [x] The three unpublished upstream commits return HTTP 422, so they are absent from GitHub.

## Runs and Logs

- [x] Each CI claim names the run ID, the job ID, the head commit, and the step.
- [x] The result of `gh run view 42589635262 --log-failed` is recorded as empty for the SpecKit job, because that job passed.
- [x] Each second-mode claim names the run ID, the job ID, and the failing step.

## Upstream Evidence

- [x] Each upstream claim names the repository, the commit, the path, and the API URL form.
- [x] No web page was fetched. Every upstream fact came from the GitHub API.

## Security

- [x] No token value appears in the record.
- [x] Each account reference names the variable only.

## Unverified Items

- [x] Each unverified item in `research.md` names its reason (U1 to U6).
