# Phase 1 Data Model: Bandit Severity Gate Hardening

**Feature**: `1032-bandit-severity-gate` | **Branch**: `security/889-bandit-ll` | **Date**: 2026-07-28

This feature stores no data at runtime. The "data" of this feature is the triage record. This document defines the record, then lists all 54 rows.

---

## 1. Entities

### 1.1 BanditFinding

One entry in the bandit JSON report.

| Field | Type | Source | Note |
| - | - | - | - |
| `test_id` | string | `results[].test_id` | The rule identifier, such as `B101`. |
| `test_name` | string | `results[].test_name` | The rule name, such as `assert_used`. |
| `filename` | string | `results[].filename` | A Windows scan returns a backslash path. Normalize it before any comparison. |
| `line_number` | integer | `results[].line_number` | The first line of the flagged statement. |
| `issue_severity` | string | `results[].issue_severity` | Every in-scope finding measures `LOW`. |
| `issue_confidence` | string | `results[].issue_confidence` | Not used for any decision. |

**Validation rules**:

- A finding is in scope only when `git ls-files` lists the normalized path.
- A finding is in scope only when the normalized path does not start with `tools/test_quality_analyzer/fixtures/`.
- The in-scope count must equal 54 at commit `fb604b4`. A different count means that the branch moved. The implementer must then re-derive the ledger before any edit.

### 1.2 TriageDecision

The recorded outcome for one finding. Requirement FR-008 sets the preference order.

| Value | Meaning | Rank |
| - | - | - |
| `FIX` | The code changes so that the flagged defect disappears. | 1, most preferred |
| `REFACTOR` | The code changes so that the flagged pattern disappears. | 2 |
| `SUPPRESS` | The code keeps the pattern and gains a `# nosec` comment with a verified reason. | 3, least preferred |

**Validation rules**:

- Every one of the 54 findings holds exactly one decision. Requirement FR-006 forbids an empty decision.
- A `SUPPRESS` decision requires a non-empty `evidence` value. A blank evidence value fails review.
- A `SUPPRESS` decision is invalid when the value under review is a real credential. Requirement FR-014 forces a `FIX` in that case.

### 1.3 SuppressionComment

The source comment that hides one finding. See [contracts/suppression-comment.md](contracts/suppression-comment.md) for the exact format.

| Field | Type | Rule |
| - | - | - |
| `rule_ids` | list of string | At least one identifier. Several identifiers appear space separated. |
| `reason` | string | One sentence. It states why the finding is safe at this call site. |
| `line` | integer | Any line inside the flagged statement. Research decision R3 proves the range behavior. |

**Validation rules**:

- The comment uses ASCII only. Principle V forbids an em dash.
- The comment must not exceed the line length for its tree. The limit is 120 characters at the root and 99 characters inside `mist-ops-platform`.
- A bare `# nosec` with no rule identifier fails requirement FR-007.
- A `# nosec` with a rule identifier and no reason fails requirement FR-007.

### 1.4 TriageLedgerRow

One row joins a `BanditFinding` to its `TriageDecision`. Section 3 holds the complete ledger.

| Field | Purpose |
| - | - |
| `id` | A stable number from 1 to 54. It survives a line-number shift. |
| `rule` | The bandit rule identifier. |
| `path` | The repository-relative path. |
| `line_at_baseline` | The line number at commit `fb604b4`. It is a starting hint, not an address. |
| `anchor` | A symbol name or a literal value. The implementer searches for this text, not for the line number. |
| `group` | The work group from A to E. |
| `default_decision` | The decision that the plan proposes. |

**Why the ledger carries an anchor**: Group D2 converts 7 asserts into multi-line `if` blocks. Each conversion pushes every later line in that file down. A ledger that stores only a line number goes stale after the first edit in a file. The implementer must therefore locate each finding by its anchor text.

### 1.5 MeasurementSnapshot

The scan result at one point in the work. The implementer captures one snapshot after each group.

| Field | Value at baseline |
| - | - |
| `commit` | `fb604b4` |
| `bandit_version` | `1.9.4` |
| `raw_count` | 105 |
| `tracked_count` | 96 |
| `in_scope_count` | 54 |
| `count_above_low` | 0 |

---

## 2. Finding lifecycle

Each finding moves through four states. A group advances all of its findings together.

```text
OPEN  ->  DECIDED  ->  APPLIED  ->  VERIFIED
```

| State | Entry condition | Exit condition |
| - | - | - |
| `OPEN` | The measurement lists the finding. | The implementer records a decision and, for a `SUPPRESS`, records the evidence. |
| `DECIDED` | The ledger row holds a decision. | The implementer edits the source. |
| `APPLIED` | The source holds the comment or the new code. | A fresh scan no longer reports the finding. |
| `VERIFIED` | The scan reports zero findings for that rule, and the other rule counts did not change. | The group closes. |

**Rule**: A group must reach `VERIFIED` before the next group starts. Group E starts only after every finding reaches `VERIFIED`.

---

## 3. The triage ledger

The line numbers below come from commit `fb604b4`. Locate each finding by its anchor.

### Group A - The subprocess family (17 findings)

| # | Rule | Path | Line | Anchor | Default decision |
| - | - | - | - | - | - |
| 1 | B404 | `src/site/address_audit/ui_geocoder.py` | 48 | `import subprocess` | SUPPRESS. Name the seam and the runner, in the style of `MistHelper.py` line 47. |
| 2 | B404 | `src/utils/zscaler_probe.py` | 29 | `import subprocess` | SUPPRESS. Same style. |
| 3 | B404 | `starlink_dashboard.py` | 18 | `import subprocess` | SUPPRESS. Same style. |
| 4 | B404 | `tools/compliance_analyzer/engine.py` | 8 | `import subprocess` | SUPPRESS. Same style. |
| 5 | B603 | `src/site/address_audit/ui_geocoder.py` | 625 | `proc = subprocess.Popen(` | SUPPRESS. State the source of each argument. |
| 6 | B603 | `src/utils/zscaler_probe.py` | 184 | `completed = subprocess.run(` | SUPPRESS. The line already carries an inert `# noqa: S603`. See research decision R4. |
| 7 | B603, B607 | `starlink_dashboard.py` | 34 | `["uv", "--version"]` | FIX for B607 with `shutil.which`. SUPPRESS for B603. One combined comment. |
| 8 | B603 | `starlink_dashboard.py` | 47 | `[sys.executable, "-m", "pip", "install", "uv"]` | SUPPRESS. Every argument is a literal or `sys.executable`. |
| 9 | B603 | `starlink_dashboard.py` | 98 | `["uv", "pip", "install"] + packages` | SUPPRESS. State that `packages` comes from a module constant. |
| 10 | B603 | `starlink_dashboard.py` | 105 | `[sys.executable, "-m", ...]` | SUPPRESS. Same reason as row 8. |
| 11 | B603, B607 | `starlink_dashboard.py` | 171 | PyQt6 install through `uv` | FIX for B607 with `shutil.which`. SUPPRESS for B603. One combined comment. |
| 12 | B603 | `starlink_dashboard.py` | 178 | PyQt6 install through `sys.executable` | SUPPRESS. Same reason as row 8. |
| 13 | B603, B607 | `tools/compliance_analyzer/engine.py` | 229 | `["git", "check-ignore", ...]` | FIX for B607 with `shutil.which`. SUPPRESS for B603. One combined comment. |
| 14 | B606 | `starlink_dashboard.py` | 191 | `os.execv(sys.executable, ...)` | SUPPRESS. The target is `sys.executable` and the arguments are `sys.argv`. |

Rows 7, 11, and 13 each hold two findings. The group therefore holds 17 findings on 14 statements.

### Group B - The credential-string family (12 findings)

| # | Rule | Path | Line | Anchor | Default decision |
| - | - | - | - | - | - |
| 15 | B105 | `mist-ops-platform/src/shared/mist/session.py` | 24 | `VAULT_SECRET_PREFIX` | SUPPRESS. The value is a Vault path prefix, not a secret. Limit 99 characters. |
| 16 | B105 | `src/db/redis_writer.py` | 46 | `ALREADY_EXISTS_TOKEN` | SUPPRESS. The value is an error-message fragment used for matching. |
| 17 | B105 | `src/gateway/wan_probe_device_override_manager.py` | 30 | `APPLY_CONFIRM_TOKEN` | SUPPRESS. The value is the typed confirmation word `APPLY`. |
| 18 | B105 | `src/gateway/wan_probe_device_override_manager.py` | 31 | `CANCEL_TOKEN` | SUPPRESS. The value is the prompt cancel keyword `cancel`. |
| 19 | B105 | `src/maps/_flask_viewer.py` | 42 | `_TOKEN_ATTR` | SUPPRESS. The value is an attribute name, not a token value. |
| 20 | B105 | `src/maps/plotly_map_figure_builder.py` | 38 | `_FILL_ALPHA_TOKEN` | SUPPRESS. The value is the CSS alpha string `0.2`. |
| 21 | B105 | `src/maps/plotly_map_figure_builder.py` | 39 | `_BORDER_ALPHA_TOKEN` | SUPPRESS. The value is the CSS alpha string `0.8`. |
| 22 | B105 | `src/maps/plotly_map_figure_builder.py` | 40 | `_LABEL_BG_ALPHA_TOKEN` | SUPPRESS. The value is the CSS alpha string `0.9`. |
| 23 | B105 | `src/wan_vpn_builder.py` | 38 | `CANCEL_TOKEN` | SUPPRESS. The value is the prompt sentinel `q`. |
| 24 | B105 | `src/wan_vpn_builder.py` | 39 | `CONFIRM_TOKEN` | SUPPRESS. The value is the typed confirmation word `CREATE`. |
| 25 | B105 | `tools/ste_linter/parsing/wordcount.py` | 15 | `_PROTECTED_TOKEN` | SUPPRESS. The value is a null-byte delimiter that survives a whitespace split. |
| 26 | B107 | `mist-ops-platform/src/shared/services/notification.py` | 22 | `password: str = ""` in `EmailAdapter.__init__` | SUPPRESS. The empty string is a "not provided" sentinel. Confirm that no caller passes a literal credential. Limit 99 characters. |

### Group C - Silent exception handling (7 findings)

| # | Rule | Path | Line | Anchor | Default decision |
| - | - | - | - | - | - |
| 27 | B110 | `mist-ops-platform/src/api/routes/health.py` | 208 | `pass  # Redis unavailable` | FIX. Narrow the exception type and log at debug. Limit 99 characters. |
| 28 | B110 | `mist-ops-platform/src/api/routes/health.py` | 217 | `pass  # Worker unavailable` | FIX. Narrow the exception type and log at debug. Limit 99 characters. |
| 29 | B110 | `src/auth/interactive/login_orchestrator.py` | 233 | `configure_session_timeout(apisession)` | FIX. Narrow the exception type and log at debug. |
| 30 | B110 | `src/export/site_insights/device_metric_operation.py` | 163 | `pass  # WHY: Degrade gracefully` | FIX. Narrow the exception type and log at debug. |
| 31 | B110 | `src/firmware/firmware_manager.py` | 2326 | `_display_ssr_inventory_stats` | FIX. Narrow the exception type and log at debug. |
| 32 | B110 | `src/utils/logger_utils.py` | 113 | `record.args = ()` | SUPPRESS. A log call inside the logging filter risks recursion. See Complexity Tracking in the plan. |
| 33 | B110 | `src/utils/zscaler_probe.py` | 371 | `conn.close()` cleanup | SUPPRESS. The block is a best-effort cleanup that the specification names as a valid escalation. |

### Group D1 - Assert statements that only narrow a type (11 findings)

Requirement FR-010 permits a suppression. Each comment must name the guard that already proves the value.

| # | Rule | Path | Line | Anchor | Default decision |
| - | - | - | - | - | - |
| 34 | B101 | `src/export/data_exporter.py` | 62 | `assert configure_db_logging is not None` | SUPPRESS. `_polyglot_db_layer_available` already guards it. |
| 35 | B101 | `src/export/data_exporter.py` | 63 | `assert DatabaseConfig is not None` | SUPPRESS. Same guard. |
| 36 | B101 | `src/export/data_exporter.py` | 64 | `assert DatabaseRouter is not None` | SUPPRESS. Same guard. |
| 37 | B101 | `src/export/data_exporter.py` | 162 | `assert DataExporter._router is not None` | SUPPRESS. The caller checks `_should_skip_polyglot` first. |
| 38 | B101 | `src/export/data_exporter.py` | 183 | `assert api_function_name is not None` | SUPPRESS. The caller already validated the value. |
| 39 | B101 | `src/firmware/firmware_manager.py` | 2963 | `assert prepared is not None` | SUPPRESS. The early return above proves the value. |
| 40 | B101 | `src/firmware/firmware_manager.py` | 2991 | `assert org_and_sites is not None` | SUPPRESS. Same pattern. |
| 41 | B101 | `src/firmware/firmware_manager.py` | 2996 | `assert config_and_version is not None` | SUPPRESS. Same pattern. |
| 42 | B101 | `src/firmware/firmware_manager.py` | 3011 | `assert selected_sites is not None` | SUPPRESS. Same pattern. |
| 43 | B101 | `src/firmware/site_auto_upgrade.py` | 88 | `assert isinstance(resolved, SiteAutoUpgradeConfig)` | SUPPRESS. The `"config" in cfg` branch already proves the shape. |
| 44 | B101 | `src/gateway/_wan2_variable_device.py` | 371 | `assert self._pool_fn is not None` | SUPPRESS. The line carries an inert `# noqa: S101`. See research decision R4. |

### Group D2 - Assert statements that guard runtime behavior (7 findings)

Requirement FR-009 demands an explicit check that raises. Python removes an `assert` under the `-O` flag.

| # | Rule | Path | Line | Anchor | Default decision |
| - | - | - | - | - | - |
| 45 | B101 | `src/firmware/site_auto_upgrade.py` | 54 | `assert isinstance(self.org_id, str)` | FIX. Raise `TypeError` inside `SiteAutoUpgradeConfig.__post_init__`. |
| 46 | B101 | `src/firmware/site_auto_upgrade.py` | 55 | `assert isinstance(self.dry_run, bool)` | FIX. Raise `TypeError`. |
| 47 | B101 | `src/maps/plotly_map_templates.py` | 187 | `_rule_css_length` | FIX. Raise `ValueError`. |
| 48 | B101 | `src/maps/plotly_map_templates.py` | 191 | `_rule_html_entry` | FIX. Raise `ValueError`. |
| 49 | B101 | `src/maps/plotly_map_templates.py` | 196 | `_rule_html_style` | FIX. Raise `ValueError`. |
| 50 | B101 | `src/maps/plotly_map_templates.py` | 200 | `_rule_meta_shape`, the `isinstance` check | FIX. Raise `TypeError`. |
| 51 | B101 | `src/maps/plotly_map_templates.py` | 201 | `_rule_meta_shape`, the title-key check | FIX. Raise `ValueError`. |

**Linked edit**: The `validate_template` docstring declares `Raises: AssertionError`. Rows 47 to 51 change that behavior, so the docstring changes with them.

### Group E - The gate change

| # | Target | Anchor | Decision |
| - | - | - | - |
| 52 | `.github/workflows/ci.yml` | `run: bandit -c pyproject.toml -r . -ll` | Remove `-ll`. Keep `-c pyproject.toml` and `-r .`. |
| 53 | `.github/workflows/ci.yml` | `# -ll gates on MEDIUM+ severity ...` | Replace the comment. State that the gate fails on any severity. |

Rows 52 and 53 are work items, not bandit findings. The finding count stays 54.

---

## 4. Ledger totals

| Group | Findings | Default FIX | Default SUPPRESS |
| - | - | - | - |
| A - subprocess family | 17 | 3 | 14 |
| B - credential strings | 12 | 0 | 12 |
| C - silent exceptions | 7 | 5 | 2 |
| D1 - type narrowing | 11 | 0 | 11 |
| D2 - runtime guards | 7 | 7 | 0 |
| **Total** | **54** | **15** | **39** |

A reviewer may move any row from `SUPPRESS` to `FIX`. Requirement FR-008 ranks a fix above a suppression, so a move in that direction never needs a justification. A move in the other direction needs one.
