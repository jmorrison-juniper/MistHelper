# MSP Info Guidance (Menu 56)

**Summary**

This menu operation surfaces Managed Service Provider (MSP) guidance and organization-level configuration recommendations for a selected org. It calls OrgConfigExporter.msp to collect, normalize, and present human-friendly guidance for MSP-run customers.

**Purpose**

Provide NOC and MSP engineers with a single-command export of MSP-relevant configuration guidance, best-practices, and remediation notes (readable text/CSV) to aid audits and onboarding.

**Stakeholders**

- NOC Engineers
- MSP Operations
- Compliance/Audit teams
- Product owner (MistHelper)

**Acceptance Criteria**

1. Running the menu triggers OrgConfigExporter.msp for the chosen org_id and returns non-empty guidance entries when applicable.
2. Output is human-readable (plain text and optional CSV) with clear headings and remediation steps.
3. No PII or secrets are output.
4. Exit code 0 and user-facing success message when guidance exists; graceful message when none exists.

**API function(s)**

- OrgConfigExporter.msp(org_id: str, options: dict) -> List[dict]
  - Expected fields per item: {"category","issue_summary","recommendation","confidence","reference_links"}
  - Behavior: idempotent, read-only; rate-limit aware; returns empty list if no guidance.

**SQL export relevance & recommendation**

- sql_export_relevant: false
- Recommendation: Do NOT write to SQLite by default. Export as human-readable text/CSV. If downstream analytics required, add optional CSV-to-SQL ingest step behind a flag.

**Primary key suggestion (if relevant)**

- Not applicable for primary menu output (advice items are transient). If persisted, use composite natural key: [org_id, category, issue_summary_hash].

**Spec dir**: specs/103-audit-menu-56-msp-info-guidance