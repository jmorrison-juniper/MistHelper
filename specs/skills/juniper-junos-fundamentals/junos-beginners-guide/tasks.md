# Tasks: Day One: Beginner's Guide to Learning Junos skill package

**Input**: Design documents from `specs/skills/juniper-junos-fundamentals/junos-beginners-guide/`

## Phase 1: Setup

- [x] T001 [FR-001] Create the artifact directory for `junos-beginners-guide`.
- [x] T002 [FR-002] Read the installed SpecKit templates before rendering artifacts.

## Phase 2: Core generation

- [x] T003 [FR-001] Write `spec.md`, `plan.md`, `tasks.md`, and `checklists/requirements.md`.
- [x] T004 [FR-003] Write source hash and source metadata into `.spec-context.json`.
- [x] T005 [FR-004] Run the cross-artifact analysis after task generation.
- [x] T006 [FR-005] Record the companion extension inventory in `analysis.md`.

## Dependencies

Phase 1 must finish before Phase 2.

## Implementation Strategy

Generate one package first, validate it, then repeat the same harness for each document.
