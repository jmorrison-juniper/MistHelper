# Implementation Plan: Source-grounded Mist API skill

**Branch**: `docs/2393-mist-api-skill` | **Date**: 2026-09-16 | **Spec**: `specs/2393-mist-api-skill/spec.md`

**Input**: Feature specification from `specs/2393-mist-api-skill/spec.md`

## Summary

Update the existing repository Mist API skill so it uses repository sources and the installed SDK.
Do not create a duplicate skill.
Add SpecKit records, a release-note fragment, and verification evidence for the claims.

## Technical Context

**Language/Version**: Markdown documentation with Python 3.13 used only for verification commands.

**Primary Dependencies**: Installed `mistapi` version `0.64.0`, the local OpenAPI files, and repository documentation.

**Storage**: Git-tracked Markdown files only.

**Testing**: STE linter, Markdown link checks, and repository quality gates.

**Target Platform**: Windows development worktree.

**Project Type**: Documentation and skill guidance.

**Performance Goals**: The skill must guide a reader to the smallest source file needed for an answer.

**Constraints**: Do not edit vendor OpenAPI files or generated endpoint pages.

**Scale/Scope**: One skill entry point, five reference guides, three SpecKit files, and one release-note fragment.

## Constitution Check

The change is documentation-only.
No Python implementation changes are planned.
The plan obeys the issue-first rule because issue #2393 owns the branch.
The plan obeys the one-term rule because it improves the existing Mist API skill.

## Project Structure

### Documentation for this feature

```text
specs/2393-mist-api-skill/
├── spec.md
├── plan.md
└── tasks.md
```

### Source files for this feature

```text
.github/skills/managing-mist-api/
├── SKILL.md
└── references/
    ├── source-authority.md
    ├── endpoint-catalog.md
    ├── request-lifecycle.md
    ├── domain-workflows.md
    └── verification.md

changelog.d/
└── issue-2393-mist-api-skill.md
```

**Structure Decision**: Improve the existing `managing-mist-api` skill because the repository must use one skill per concept.

## Files added or changed

| File | Action | Reason |
| - | - | - |
| `.github/skills/managing-mist-api/SKILL.md` | Add or update | Provide the skill entry point. |
| `.github/skills/managing-mist-api/references/source-authority.md` | Add or update | Define the source hierarchy and conflict rules. |
| `.github/skills/managing-mist-api/references/endpoint-catalog.md` | Add or update | Route categories and source files. |
| `.github/skills/managing-mist-api/references/request-lifecycle.md` | Add or update | Define safe request and result handling. |
| `.github/skills/managing-mist-api/references/domain-workflows.md` | Add or update | Give bounded API workflows. |
| `.github/skills/managing-mist-api/references/verification.md` | Add or update | Define offline checks and acceptance scenarios. |
| `specs/2393-mist-api-skill/spec.md` | Add | Record the user need and acceptance criteria. |
| `specs/2393-mist-api-skill/plan.md` | Add | Record the implementation plan. |
| `specs/2393-mist-api-skill/tasks.md` | Add | Record dependency-ordered work. |
| `changelog.d/issue-2393-mist-api-skill.md` | Add | Record the user-visible documentation change. |

## Verified claims

| Claim | Evidence command | Result |
| - | - | - |
| The installed SDK version is `0.64.0`. | `python -c "import mistapi; print(mistapi.__version__)"` | `0.64.0` |
| `listOrgSites` exists in `mistapi.api.v1.orgs.sites`. | `hasattr()` plus `inspect.signature()` | The function exists with `org_id`, `limit`, and `page`. |
| `getSiteInfo` exists in `mistapi.api.v1.sites.sites`. | `hasattr()` plus `inspect.signature()` | The function exists with `site_id`. |
| `getSite` is absent from `mistapi.api.v1.sites.sites`. | `hasattr()` | The result is `False`. |
| `listSites` is absent from `mistapi.api.v1.sites.sites`. | `hasattr()` | The result is `False`. |
| `getOrgAoscxRegisterCmd` exists in `mistapi.api.v1.orgs.aoscx`. | `hasattr()` plus `inspect.signature()` | The function exists with `org_id`. |
| `mistapi.api.v1.orgs.aos` is absent. | `importlib.import_module()` | The import raises `ModuleNotFoundError`. |
| The primary OpenAPI source contains `listOrgSites`. | Structural JSON scan | It maps to `GET /api/v1/orgs/{org_id}/sites`. |
| The primary OpenAPI source contains `getSiteInfo`. | Structural JSON scan | It maps to `GET /api/v1/sites/{site_id}`. |
| The primary OpenAPI source contains `getOrgAoscxRegisterCmd`. | Structural JSON scan | It maps to `GET /api/v1/orgs/{org_id}/aoscx/register_cmd`. |
| The installer optimize path is a GET operation. | Structural JSON scan | `/api/v1/installer/sites/{site_name}/optimize` has `GET`. |
| The self path exists. | Structural JSON scan | `/api/v1/self` has `DELETE`, `GET`, and `PUT`. |
| The organization path exists. | Structural JSON scan | `/api/v1/orgs/{org_id}` has `DELETE`, `GET`, and `PUT`. |
| The site path exists. | Structural JSON scan | `/api/v1/sites/{site_id}` has `DELETE`, `GET`, and `PUT`. |

Total verified endpoint and SDK claims: 14.

## Complexity Tracking

No constitution violation is required.
