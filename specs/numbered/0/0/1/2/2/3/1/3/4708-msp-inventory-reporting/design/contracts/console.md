# Console Contract

The batch summary reports successful organizations and skipped or failed organizations.
If any organization is excluded, the batch status says `partial`.
If every organization succeeds, the batch status says `complete`.

A missing-ID record produces an operator warning with its progress position, organization name, and missing-ID cause.
Runner exceptions retain their existing operator error.

Complete combined-report headings retain `All Orgs`.
Each partial combined-report heading states `Partial` and gives successful and skipped or failed counts.
The model, firmware, and version-per-model reports share this coverage label.
At least two successes remain necessary for combined reports.

Exporter calls retain their filenames, API identifiers, field ordering, and successful organization rows.
Empty successful results count as successful organizations.
