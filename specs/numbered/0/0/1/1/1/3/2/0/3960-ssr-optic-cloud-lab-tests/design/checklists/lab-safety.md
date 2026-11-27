# Lab Safety Checklist: SSR optic and Mist cloud path lab tests

**Purpose**: Give the owner a safety check for each owner-only lab step

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Before any lab step

- [ ] The owner names the lab SSR and its release.
- [ ] The owner uses a lab SSR. The owner does not use a production router.
- [ ] The owner keeps each credential out of the issue, the runbook, and the record.

## Before H-6

Caution: H-6 stops Mist management of the lab router until the block rule is removed.

- [ ] The baseline from H-5 is recorded.
- [ ] The owner types the confirmation phrase from D-8 with the lab router name.
- [ ] The owner has a plan to remove the block rule before the block starts.

## After each output

- [ ] The sanitization checklist in contracts/lab-output-record.md passes.
- [ ] The release string is recorded.
- [ ] The command text is unchanged.

## After H-6

- [ ] The block rule is removed.
- [ ] Running `show mist detail` again shows Connection as up.
