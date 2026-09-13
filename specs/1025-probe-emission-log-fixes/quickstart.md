# Quickstart: Validating the 1025 Log-Quality Fixes

**Feature**: `1025-probe-emission-log-fixes`
**Audience**: Operators triaging a menu 206 run + CI reviewers checking
that the fix landed as specified.

This is a runnable validation guide. It does NOT include implementation
code — for that, see the module diff after `/speckit.implement` runs.
See the contracts under `contracts/` for the assertion details.

---

## Prerequisites

- Python 3.13+ virtualenv provisioned per `AGENTS.md` bootstrap
  instructions.
- `pytest`, `pytest-cov` installed (already in `pyproject.toml`).
- Working directory: repository root.
- Feature branch `1025-probe-emission-log-fixes` checked out on top of
  merged `1024-vpn-icmp-reachability` (1025 depends on the 1024 code
  paths being present).

---

## 1. Unit-test validation (fast; runs in CI)

### 1a. Run only the new/extended tests for 1025

```bash
pytest tests/unit/org/test_org_synthetic_probes_manager.py \
       tests/unit/org/test_country_region_coverage.py \
       -v
```

**Expected outcome**: All tests PASS. Runtime under 5 s wall-clock on the
reference dev machine (SC-007).

Tests that MUST be present and passing:
- `test_cenr_warning_dedup_ge_1_missing` — FR-001, FR-002, SC-001
  (verifies CENR WARNING count `<= |unique_missing_hosts|`).
- `test_cenr_warning_zero_when_fully_populated` — zero-emission case.
- `test_unmapped_country_warning_dedup` — FR-004, FR-010, SC-002
  (verifies country WARNING count `<= |unique_unmapped_codes|`).
- `test_latam_caribbean_no_warnings` — FR-005, SC-002, SC-003 (verifies
  PA/BS/HT/DO/GT/CU/CR/HN now map cleanly).
- `test_latam_caribbean_region_resolution` — SC-003 (verifies resolved
  region for each covered site is `"americas"`).
- `test_probe_payload_byte_stability_smoke` — INV-1 / FR-011 / SC-004.
- `test_iso_cover_1_disjoint` through `test_iso_cover_4_region_values` —
  coverage regression suite (FR-008, SC-005).

### 1b. Run only the coverage regression test in isolation

```bash
pytest tests/unit/org/test_country_region_coverage.py -v
```

Useful when the coverage suite fires on a change to
`_COUNTRY_CODE_TO_REGION` or `_COUNTRY_CODE_INTENTIONAL_GAPS` — the
diagnostic names the missing / double-declared code.

### 1c. Full org-scoped unit test suite

```bash
pytest tests/unit/org/ -v
```

Should be entirely green. Any pre-existing tests from spec 1024 must
continue to pass — 1025 is additive.

---

## 2. Contract-driven validation (referenced from `contracts/`)

Each contract file under `specs/1025-probe-emission-log-fixes/contracts/`
carries its own test-code snippet. To confirm a contract holds, run its
associated tests (see the linked test names in each contract's §3).

- `contracts/log_record_shape.md` §3 → CENR + country-code dedup tests.
- `contracts/iso_coverage_invariant.md` §3 → four `test_iso_cover_*`
  tests.
- `contracts/byte_stability_invariant.md` §3 →
  `test_probe_payload_byte_stability_smoke`.

Do not paste the contract test code into implementation modules — it is
illustrative of the assertion shape, not the test file itself.

---

## 3. Live-run validation (manual smoke against a real org)

Only after unit tests pass. This is the operator-facing acceptance
check for SC-001 / SC-002 / SC-006.

### 3a. Confirm the pre-change baseline (optional, for comparison)

Skip if you have already captured the baseline count during 1024 or
during 1025's specification work.

```bash
git stash             # temporarily hide 1025 changes if applied
python MistHelper.py  # log in, run menu 206 against target org
grep -c "no observation for" data/script.log
grep -c "country_code" data/script.log
git stash pop         # re-apply 1025 changes
```

Record the two counts.

### 3b. Run menu 206 with 1025 applied

```bash
python MistHelper.py
# menu -> 206 manage_org_synthetic_probes
# provide VLAN list at prompt
# answer merge/swap when asked
# answer y at the final confirmation
```

After the run completes, inspect the log:

```bash
grep -c "CENR" data/script.log            # missing-observation WARNINGs
grep -c "country_code" data/script.log    # unmapped-code WARNINGs
tail -100 data/script.log                 # visual sanity check
```

**Expected outcomes**:
- CENR WARNING count on the current run's slice of the log is `<= 7` on
  the ~315-site reference org (SC-001; a >99% reduction from ~1,261).
- country_code WARNING count is `0` when the site set contains only
  codes that are in `_COUNTRY_CODE_TO_REGION` (SC-002); `<= K` when it
  contains `K` unique unmapped codes.
- No probe was skipped, no probe URL changed for non-VPN targets. This
  is the operational restatement of INV-1 / FR-011.

### 3c. Diff the emitted probe collection against baseline (optional but
recommended when a merge is imminent)

If a byte-stability baseline is available for the target org from
before 1025, dump the org-side probe collection after the run and diff:

```bash
# assumes you have a baseline probes.json captured pre-1025
python scripts/dump_org_synthetic_probes.py \
       --org-id <ORG_UUID> \
       --output data/1025_after_probes.json
diff -u data/pre_1025_baseline_probes.json data/1025_after_probes.json
```

Expected: empty diff for all `zcc-` non-VPN probes.

---

## 4. CI validation

The GitHub Actions pipeline runs the full `pytest` suite plus `ruff`,
`black`, `mypy`, and `interrogate` (docstring coverage) on every push.
The 1025 changes are expected to be green out of the box on these:

```bash
ruff check src/org/org_synthetic_probes_manager.py
black --check src/org/org_synthetic_probes_manager.py
mypy src/org/org_synthetic_probes_manager.py
interrogate -v src/org/org_synthetic_probes_manager.py
pytest tests/unit/org/ --cov=src.org.org_synthetic_probes_manager
```

Docstring coverage target: `>= 90 %` (per project-level `DOCS.md`).

---

## 5. Rollback

If a post-merge issue surfaces:

```bash
git revert <merge_commit_sha>
git push origin main
```

Rollback is safe because 1025 changes are additive (extra dict entries,
new frozenset, moved WARNING) and preserve INV-1 by construction — no
data migration or setting reshape is involved.

---

## 6. Success signals in one line each

- `pytest tests/unit/org/test_country_region_coverage.py` → PASS.
- `pytest tests/unit/org/test_org_synthetic_probes_manager.py` → PASS.
- `grep -c "CENR" data/script.log` after a real run → single-digit.
- `grep -c "country_code" data/script.log` after a real run against
  LATAM/Caribbean sites → 0.
- Diff of emitted non-VPN probes vs. baseline → empty.
