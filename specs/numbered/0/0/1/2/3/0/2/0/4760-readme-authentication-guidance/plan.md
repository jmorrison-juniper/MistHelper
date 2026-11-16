# Implementation Plan: README Authentication Guidance

**Branch**: `jmorrison-juniper-readme-authentication-guidance` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/3/0/2/0/4760-readme-authentication-guidance/spec.md`.

## Summary

Correct only the README authentication guidance. State that operators can use an API token or interactive email and password sign-in, which can prompt for a two-factor code. Explain that token requests send the token to Mist over HTTPS. Add one release-note fragment for issue #4760.

## Technical Context

**Language/Version**: Python 3.15 or newer. No runtime code changes.

**Primary Dependencies**: Existing `mistapi` SDK behavior. No dependency changes.

**Storage**: None.

**Testing**: README review, STE lint, local Markdown-link guard, changelog-fragment guard, and specs structure guard.

**Target Platform**: Windows, macOS, and Linux operator documentation.

**Project Type**: Command-line tool documentation.

**Performance Goals**: None. This change does not alter runtime behavior.

**Constraints**: Edit only the README authentication guidance and one issue-specific release fragment. Preserve all WAN and Menu 164 text and all other README content. Do not edit the API-page candidate for issue #4759.

**Scale/Scope**: The README authentication paragraphs in Who, Where, and Step 2, one release fragment, and the managed Spec Kit record for issue #4760.

## Constitution Check

- **Managed records**: The feature uses the eight-level base-5 route for issue 4760.
- **Release fragment**: The change adds one uniquely named file under `changelog.d/`. The folder has existing growth, so this issue does not add a shared index or edit the aggregate changelog. Future release coordination continues to move merged fragments into the release record.
- **Runtime safety**: No runtime code, cloud operation, database, or product output changes.
- **Mist transport**: This issue adds no Mist request. Existing token and interactive authentication behavior is documented from current source and SDK usage.
- **Commit form**: Use `docs: correct README authentication guidance`.
- **Other holds**: Preserve the WAN guide and description, the Menu 164 paragraph, and the separate API-page candidate.

The constitution checks pass for this documentation-only scope.

## Project Structure

### Documentation

```text
README.md
changelog.d/issue-4760-readme-authentication-guidance.md
specs/numbered/0/0/1/2/3/0/2/0/4760-readme-authentication-guidance/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    checklists/requirements.md
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
No source changes.
```

**Structure Decision**: Keep product changes in the existing README and release-fragment folders. Keep the issue specification and supporting records in the managed numeric route. The README change is limited to authentication guidance.

## Complexity Tracking

No code complexity exception is required.
