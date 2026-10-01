### Remove deprecated SLE operations

- **Removed**: Menu 263 no longer offers `getSiteSleSummary` or `getSiteSleClassifierDetails`.
  The catalog and supplemental primary-key metadata also exclude both operations. Issue #3335.
- **Changed**: Menu 263 offers 15 operations.
  `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend` remain offered with unchanged SDK resolution and primary-key strategies.
  The SDK constraint `mistapi>=0.64.0,<0.65` remains unchanged.
  This change requires no schema or data migration.
  Existing stored records, unrelated keys, upsert behavior, and SLE refusal behavior remain unchanged.
  Issue #3699 records the separate existing trend-object output defect. This metadata removal does not repair it. Issue #3335.
