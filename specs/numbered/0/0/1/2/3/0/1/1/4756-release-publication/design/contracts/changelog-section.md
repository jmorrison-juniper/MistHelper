# Contract: CHANGELOG Release Section

This contract defines the one section that the release adds to `CHANGELOG.md`. The rules apply to the section only. No other line changes (FR-014).

## Location

- The file is `CHANGELOG.md` at the repository root (RC-06).
- The section starts after the blank line that follows the `## [Unreleased]` heading at line 13 (RC-09).
- The section ends before the heading of the previous release, `26.09.28.19.49`, at line 15 (RC-10).
- The Unreleased heading stays. Its section stays empty (FR-003).

## Section Heading

- The heading is level two.
- The heading text is the release stamp inside square brackets, then a space, a hyphen, a space, and the UTC date in the form `YYYY-MM-DD`.
- The heading form copies the form of the previous release heading (RC-10).

## Introduction

The introduction holds three lines.

1. The first sentence names the count of collected fragments. It uses the form of line 17 (RC-13): "This release collects" followed by the count, then "release-note fragments from" and the folder name in code format.
2. The second sentence names the previous GitHub release in code format. It uses the form of line 18 (RC-13), and the value is `v26.11.21.06.27`.
3. A blank line separates the introduction from the entry sentence. The entry sentence is "Each heading below names one change. Each bullet starts with its change type." (RC-14).

## Entries

- Each collected fragment gives one entry.
- Entries appear in ordinal order of the fragment file name.
- Each entry begins with one level-three heading. The heading text is the fragment heading text.
- If the fragment heading uses another level, the heading changes only its count of number signs to three.
- The body lines after the heading keep their text, except for the link rule.
- A blank line separates each entry from the next.

## Link Rule

- Every relative link in the section resolves from the repository root (TEST-2, RC-37).
- A link that starts with a folder step from the fragment folder loses that step.
- The link text and any anchor stay unchanged.

## Count Rule

- The count in the introduction equals the number of level-three entries.
- The count equals the number of fragments that the same release pull request deletes from `changelog.d/`.
- TEST-4 writes both counts to `test-artifacts\release-4756\reconcile.txt`.

## Verbatim Rule

- For each fragment, its body lines appear in the section in the same order.
- The only permitted differences are the heading level and the link rule.
- TEST-4 proves this rule by comparing each fragment with its entry.

## Forbidden Changes

- No line outside the section changes (FR-014).
- The Unreleased heading and its following blank line keep their bytes.
- No second release section is added for an earlier release.
