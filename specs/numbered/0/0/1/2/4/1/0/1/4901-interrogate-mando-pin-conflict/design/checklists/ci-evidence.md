# CI Evidence Checklist: Interrogate Gate Failure on PR #4888

**Purpose**: Check that each CI fact in the record has a source.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Failure Identity

- [x] Run ID 45064243269 and job ID 137336719025 are recorded (research R1).
- [x] The check name `Interrogate (docstring coverage)` matches the job name in `ci.yml` (RV-09).
- [x] The failed step `Run pip install -r requirements-dev.txt` comes from the job summary (research R1).
- [x] Head `e86098cdc2b189d217805b3b4060ef609cbc37af` and test-merge commit `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` are both explained (analysis A-5).

## Failure Cause

- [x] The exact error lines appear with their timestamps (research R1).
- [x] The line `radon 6.0.1 depends on mando<0.8 and >=0.6` appears in the job log.
- [x] The job log holds zero `RESULT:` lines, so the docstring command never started (research R1).
- [x] The pin in the failing head reads `mando==0.8.2` (RV-05).

## Baseline and Scope

- [x] Main run 45774119357 has conclusion success. Its job 139753527432 prints `RESULT: PASSED (minimum: 90.0%, actual: 99.7%)` (research R3).
- [x] Twenty-six of 28 failed jobs print the resolver message. Two fail in aggregator steps (research R2).
- [x] Two Native Windows runs, 45064235051 and 45064235097, print the same resolver message (research R1).
- [x] Branch protection lists `Interrogate (docstring coverage)` among 15 required contexts (research R3).

## Limits

- [x] This session did not rerun the CI workflow. The result of the fix is pending T-REMOTE-CI.
- [x] The docstring value on the fix head is unverified until T-REMOTE-CI (research Unverified, U-2).
- [x] The mapping of issue #4894 to its job is unverified (research Unverified, U-5).
