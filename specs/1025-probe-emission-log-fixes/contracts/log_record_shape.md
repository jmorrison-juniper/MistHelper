# Contract: Log Record Shape & Count

**Feature**: `1025-probe-emission-log-fixes`
**Scope**: Menu 206 (`manage_org_synthetic_probes`) WARNING log records
**Related FRs**: FR-001, FR-002, FR-004, FR-009, FR-010, FR-013

This document is the machine-checkable contract that the two new
regression tests (`test_cenr_warning_dedup`, `test_country_code_warning_dedup`)
assert against. The contract is written from the operator's perspective:
what will appear in `data/script.log` after this feature ships, and what
tests will fail CI if that ever regresses.

---

## 1. CENR missing-observation WARNING

### Emission site
Load-time, immediately after `_load_probe_sources()` returns and the
missing-host set has been computed. Before any per-site iteration begins.

### Log level
`logging.WARNING` (unchanged from today; see R5).

### Count guarantee
For a run touching `N` sites and `M` unique catalogue hosts absent from
CENR:

| Before | After (contract) |
|--------|------------------|
| `N × M` WARNINGs | `<= M` WARNINGs |

`M == 0` (fully-populated CENR) MUST emit zero WARNINGs.

### Message content (FR-013)
The emitted message MUST contain, in string form (case-preserving):
1. The literal token `CENR` (grep anchor operators may have wired into
   dashboards).
2. Every missing hostname (either enumerated inline or in a sorted
   collection — the exact format is chosen at implementation time but
   MUST be greppable to the *individual* host name).
3. A phrase indicating that the catalogue default URL is being used
   (so operators know behavior is fallback, not failure).

### Machine-checkable assertions (test contract)
```python
# tests/unit/org/test_org_synthetic_probes_manager.py

def test_cenr_warning_dedup_ge_1_missing(caplog):
    """FR-001, FR-002, FR-009, SC-001. Fixture: ~315 sites, 7 missing hosts."""
    with caplog.at_level(logging.WARNING):
        manage_org_synthetic_probes(fake_session, org_id)
    cenr_warnings = [r for r in caplog.records
                     if "CENR" in r.getMessage() and r.levelno == logging.WARNING]
    # FR-001: at most M WARNINGs, not N x M
    assert len(cenr_warnings) <= 7, (
        f"CENR WARNING count {len(cenr_warnings)} exceeded unique-missing-host "
        f"cap 7; per-site duplication may have regressed."
    )
    # FR-013: every unique missing host is grep-visible somewhere in the batch
    combined = " ".join(r.getMessage() for r in cenr_warnings)
    for host in EXPECTED_MISSING_HOSTS:
        assert host in combined, f"missing-host name {host!r} absent from log"


def test_cenr_warning_zero_when_fully_populated(caplog):
    """FR-001 zero-emission case. Fixture: CENR observations for every host."""
    with caplog.at_level(logging.WARNING):
        manage_org_synthetic_probes(fake_session_fully_populated, org_id)
    cenr_warnings = [r for r in caplog.records if "CENR" in r.getMessage()]
    assert len(cenr_warnings) == 0
```

---

## 2. Unmapped-country-code WARNING

### Emission site
Load-time, after the site list is loaded and its `country_code` set has
been computed. Before per-site region resolution begins.

### Log level
`logging.WARNING` (unchanged from today; see R5).

### Count guarantee
For a run touching `N` sites whose country codes cover `K` unique unmapped
values:

| Before | After (contract) |
|--------|------------------|
| Up to `N` WARNINGs | `<= K` WARNINGs |

`K == 0` (all codes mapped or in intentional-gap set) MUST emit zero
WARNINGs of this type.

### Message content (FR-013)
The emitted message MUST contain:
1. The literal token `country_code` (grep anchor).
2. Every unmapped code (either enumerated inline or in a sorted
   collection).
3. The default region that will be used as fallback (so operators can
   reason about the resulting classification).

### Machine-checkable assertions (test contract)
```python
def test_unmapped_country_warning_dedup(caplog):
    """FR-004, FR-010, SC-002. Fixture: sites with codes NOT in map/gap set."""
    with caplog.at_level(logging.WARNING):
        manage_org_synthetic_probes(fake_session_with_unmapped, org_id)
    country_warnings = [r for r in caplog.records
                        if "country_code" in r.getMessage()
                        and r.levelno == logging.WARNING]
    unique_unmapped = compute_unique_unmapped_codes(fake_session_with_unmapped)
    assert len(country_warnings) <= len(unique_unmapped), (
        f"country_code WARNING count {len(country_warnings)} exceeded "
        f"unique-code cap {len(unique_unmapped)}; per-site duplication regressed."
    )


def test_latam_caribbean_no_warnings(caplog):
    """FR-005, SC-002, SC-003. Fixture: sites in PA/BS/HT/DO/GT/CU/CR/HN."""
    with caplog.at_level(logging.WARNING):
        manage_org_synthetic_probes(fake_session_latam, org_id)
    country_warnings = [r for r in caplog.records if "country_code" in r.getMessage()]
    assert country_warnings == [], (
        "LATAM/Caribbean codes should now be mapped; no unmapped WARNINGs expected."
    )
```

---

## 3. Non-goals (out of scope for this contract)

- The exact wording, punctuation, or word order of the WARNING messages
  is NOT pinned by this contract — only the grep-anchor tokens and the
  count bound. Implementers may tune wording for readability.
- INFO / DEBUG log records are NOT constrained. Implementations may emit
  additional diagnostic detail at lower levels.
- Log records emitted by other modules called during
  `manage_org_synthetic_probes` (e.g. `mistapi`, `TelemetryEmitter`) are
  NOT constrained by this contract.
- Non-WARNING records containing the words `CENR` or `country_code` (e.g.
  DEBUG traces) are excluded from the counts above via the `levelno`
  filter.
