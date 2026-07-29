# Phase 0 Research: Bandit Severity Gate Hardening

**Feature**: `1032-bandit-severity-gate` | **Branch**: `security/889-bandit-ll` | **Date**: 2026-07-28

This document records every decision that the plan depends on. The implementer measured each fact on commit `fb604b4` with bandit 1.9.4. The Technical Context in [plan.md](plan.md) holds no open clarification.

---

## R1 - Group the work by rule, not by file

**Decision**: Order the tasks by bandit rule. Inside a rule, order by file.

**Rationale**: One rule shares one reasoning pattern. A reviewer who accepts the pattern for B105 accepts all 11 findings in one read. A file-ordered pull request would force the reviewer to re-derive the same reasoning in 21 places. The rule order also produces a clean exit measurement, because the count for one rule must reach zero before the next group starts.

**Alternatives considered**:

- *Order by file*: Rejected. `starlink_dashboard.py` alone holds 4 different rules. The reviewer would switch reasoning 4 times inside one file.
- *One pull request per file*: Rejected. 21 pull requests for 54 comment lines costs more review time than it saves.

---

## R2 - Suppress the B105 findings instead of renaming the constants

**Decision**: Add a `# nosec B105` comment with a stated reason. Do not rename the constants.

**Rationale**: Bandit B105 fires on the **name** of a variable, not on the value. The rule matches a name that holds `token`, `secret`, `pass`, or `pwd`. All 11 findings are module-level constants. The measured values are a prompt sentinel such as `"q"` and `"CREATE"`, a CSS alpha value such as `"0.2"`, an attribute name such as `"_api_token"`, a Vault path prefix, and a null-byte delimiter. None is a credential. No defect exists, so no fix exists.

A rename such as `CANCEL_TOKEN` to `CANCEL_SENTINEL` would remove the finding at the root, which requirement FR-008 ranks above a suppression. The plan still rejects the rename for three reasons. The rename spreads churn to every call site of a public constant. The rename makes `_TOKEN_ATTR` less accurate, because that constant genuinely names a token attribute. The specification already set the default decision for B105 to a suppression and named `src/ssh/config/env_loader.py` line 67 as the model.

**Alternatives considered**:

- *Rename every constant*: Rejected for the reasons above. Record the option in the pull request so a reviewer can ask for it on a specific constant.
- *Add `B105` to a bandit skip list in `pyproject.toml`*: Rejected. A global skip would hide a future real credential. It also changes the `[tool.bandit]` scope, which the specification lists as a non-goal.

---

## R3 - `# nosec` placement on a multi-line statement

**Decision**: Place the comment on the clearest line inside the statement. Prefer the line that bandit reports.

**Rationale**: The implementer probed the behavior with a synthetic file and bandit 1.9.4. A comment on the reported first line suppressed the finding. A comment on an inner argument line also suppressed the finding. A control case with no comment still reported. Bandit therefore matches a `# nosec` comment against the whole line range of the statement.

Six of the nine B603 findings sit on a `subprocess.run(` call that spans several lines. This result frees the implementer from crowding a long argument onto the opening line.

**Second measured result**: One comment suppresses several rules when the rule identifiers appear space separated, as in `# nosec B603 B607`. Three statements carry both B603 and B607: `starlink_dashboard.py` line 34, `starlink_dashboard.py` line 171, and `tools/compliance_analyzer/engine.py` line 229. Each needs one comment, not two. The repository already uses this form at two places with `# nosec B605 B607`.

---

## R4 - The existing `# noqa: S...` annotations suppress nothing

**Decision**: Treat every `# noqa: S101`, `# noqa: S603`, and similar annotation as inert. Add a real `# nosec` comment on the same line.

**Rationale**: The root `ruff` configuration selects `["E", "F", "W", "I", "UP", "B", "G"]`. The `S` set, which is `flake8-bandit`, is absent. The `mist-ops-platform` configuration also omits `S`. An `S` annotation therefore silences no `ruff` rule. Bandit reads `# nosec` only and ignores `# noqa` completely.

Two in-scope lines carry this trap. `src/gateway/_wan2_variable_device.py` line 371 carries `# noqa: S101`. `src/utils/zscaler_probe.py` line 184 carries `# noqa: S603 - args are validated above`. Both still report to bandit today.

**Consequence**: The implementer must not read an `S` annotation as a completed triage. The implementer must also leave the annotation in place, because removing it is a separate cleanup that this scope does not cover.

---

## R5 - Split B101 by runtime duty, then pick the exception type

**Decision**: Classify each of the 18 asserts as type narrowing or as a runtime guard. Suppress the narrowing cases. Convert the runtime cases to an explicit `raise`.

**Rationale**: Requirement FR-009 and requirement FR-010 already draw this line. The Python interpreter removes every `assert` under the `-O` flag. A statement that only satisfies `mypy` loses nothing. A statement that validates an input loses the protection.

**Measured classification**:

| Class | Count | Evidence |
| - | - | - |
| Type narrowing | 11 | Each line already carries a comment such as `# WHY: mypy narrowing` or `# Guarded by _polyglot_db_layer_available`. An earlier guard proves the value. |
| Runtime guard | 7 | 5 sit inside the `_rule_*` validators of `src/maps/plotly_map_templates.py`. 2 sit in the `__post_init__` of `SiteAutoUpgradeConfig`. |

**Exception type for the conversions**:

- `plotly_map_templates.py`: use `ValueError`. The rules check content, such as a missing placeholder or a short CSS string. `ValueError` states a bad value.
- `site_auto_upgrade.py`: use `TypeError`. Both asserts call `isinstance`. `TypeError` states a wrong type.

**Verified safety of the type change**: A repository-wide search of `tests/` for `AssertionError` returned 15 matches in 8 files. None of those files tests the five modules in scope. The `validate_template` tests in `tests/maps/test_plotly_map_templates.py` assert the success path only, such as `assert mgr.validate_template() is True`. No test depends on `AssertionError` from these modules.

**Docstring dependency**: The `validate_template` docstring declares `Raises: AssertionError`. The conversion must update that line to `ValueError`. The `pydocstyle` gate and the `interrogate` gate read the docstring.

**Alternatives considered**:

- *Convert all 18 asserts*: Rejected. A narrowing assert has no runtime duty, so a conversion would add 11 dead branches. Each dead branch would also lower the coverage score.
- *Suppress all 18 asserts*: Rejected. It would leave `validate_template` as a silent no-op under `-O`, which is the exact defect that the gate exists to catch.

---

## R6 - Decide each B110 finding at its own call site

**Decision**: Narrow the exception type and add a debug log for 5 findings. Suppress 2 findings with a stated reason.

**Rationale**: A silent `except` block hides a fault. Requirement FR-011 sets the default to narrow and log. Two sites need the escalation that the same requirement allows.

- `src/utils/logger_utils.py` line 113 sits inside a logging filter. A log call from the logging path can re-enter the same filter and can recurse without end. The existing comment already states that the block must never crash the logger. This site takes a suppression and keeps the broad `except`.
- `src/utils/zscaler_probe.py` line 371 closes a socket in a cleanup path. The line already carries `# pragma: no cover - best-effort cleanup`. The specification names a best-effort cleanup as a valid escalation. This site takes a suppression.

**Overlap with issue #1709 - resolved**: Issue #1709 asks the same question about the broad `except` blocks in `MistHelper.py`. The measurement shows that **none** of the 7 B110 findings sit in `MistHelper.py`. The files are `mist-ops-platform/src/api/routes/health.py`, `src/auth/interactive/login_orchestrator.py`, `src/export/site_insights/device_metric_operation.py`, `src/firmware/firmware_manager.py`, `src/utils/logger_utils.py`, and `src/utils/zscaler_probe.py`. The line-level conflict that the specification feared does not exist. The implementer still reads the current scope of #1709 before the first edit, because that scope may grow.

**Complexity impact**: A narrowed exception type replaces one clause with another clause. It adds no branch, so the `radon` score stays flat. A `logging.debug` call adds one statement inside a block that the tests already miss, so the coverage impact is 5 statements against an 80 percent threshold on `src/`.

---

## R7 - Resolve the B607 executables with `shutil.which`

**Decision**: Resolve the executable and pass the resolved path. Fall back to a suppression only when the resolution is not practical.

**Rationale**: Requirement FR-013 sets the default. All 3 B607 findings name a partial path: `"uv"` twice in `starlink_dashboard.py` and `"git"` once in `tools/compliance_analyzer/engine.py`. A partial path lets a directory earlier on `PATH` supply a different program.

All 3 findings sit **outside** `src/`. The `mypy`, `pylint`, `radon`, `vulture`, and coverage gates read `src/` only, so this change faces `ruff`, `black`, and `bandit` alone. That makes it the lowest-risk code change in the whole feature.

`src/site/address_audit/ui_geocoder.py` already imports `shutil` for a `PATH` lookup of the Edge executable, so the repository already holds the pattern.

**Action logging**: The resolution is a meaningful action under Principle VII. Each resolution logs before the lookup and logs the resolved path after the lookup. The log must never print an argument that could hold a secret.

**Alternatives considered**:

- *Suppress all 3*: Rejected. The resolution is small, and the gate risk is the lowest of any code change in this feature.
- *Hardcode an absolute path*: Rejected. The path differs across Linux, Windows, and the container.

---

## R8 - Keep the empty-string default in `EmailAdapter.__init__`

**Decision**: Add a `# nosec B107` comment with a stated reason. Do not change the signature.

**Rationale**: The finding is `password: str = ""` in `mist-ops-platform/src/shared/services/notification.py`. The empty string is a "not provided" sentinel, not a credential. The repository already documents the identical pattern at `src/ssh/config/env_loader.py` line 67 with the comment `# nosec B105 - empty password is a sentinel for "not provided"`.

Requirement FR-014 permits this outcome when the value is shown not to be a secret. The specification's own escalation note for B107 allows a suppression for a documented placeholder.

**Blocking check**: The implementer must confirm that no caller passes a literal credential into this parameter. If a caller does, the decision flips to the default in the specification. The value then moves to the environment and the team rotates the credential.

**Alternatives considered**:

- *Change the default to `None`*: Rejected for now. It changes the annotation to `str | None` and forces a `None` check in `send`. That is a behavior change with no security benefit, because `""` and `None` both mean "no authentication".

---

## R9 - Change `.github/workflows/ci.yml` last

**Decision**: Make the workflow edit the final change in the branch.

**Rationale**: The removal of `-ll` makes every remaining LOW finding fail the build. An early flip would turn every intermediate push red and would hide a real regression inside expected noise. The clean measurement after Group D proves that the flip is safe.

---

## R10 - Map each file to the gates that read it

**Decision**: Sequence the groups by gate exposure. Start with the files that the fewest gates read.

**Measured exposure**:

| Path | ruff, black, bandit | mypy, radon, vulture, coverage | pylint |
| - | - | - | - |
| `src/` | Yes | Yes | Yes, except `src/maps`, `src/ssh`, and `src/ui` |
| `starlink_dashboard.py` | Yes | No | No |
| `tools/` | Yes | No | No |
| `mist-ops-platform/` | Yes | No | No |

**Consequence**: 24 of the 54 findings sit outside `src/`. Group A holds 13 of them, which is why Group A runs first. The 5 asserts in `src/maps/plotly_map_templates.py` skip `pylint` but still face `mypy`, `radon`, `vulture`, and coverage.

---

## R11 - Do not pin the bandit version in this scope

**Decision**: Record the gap. Open a separate issue if the team wants the pin.

**Rationale**: The workflow runs `pip install 'bandit[toml]'` with no constraint. The specification lists a stable version as an assumption, but nothing enforces it. A new bandit release can add a rule and can fail the stricter gate with no code change. The risk grows once `-ll` is gone, because a new LOW rule then breaks the build.

This plan does not add the pin, because no requirement asks for it and because a pin invites version drift that nobody reviews. The stricter gate makes the risk visible, which is the correct first outcome.

---

## R12 - Standardize the suppression comment format

**Decision**: Use `# nosec RULE - reason.` with an ASCII hyphen and a single space on each side.

**Rationale**: A survey of the existing comments found several forms. The most common form is a bare `# nosec B101`, which appears 24 times. Other forms use ` - `, ` -- `, and an em dash. Requirement FR-007 forbids a bare suppression for any comment that this work adds. Principle V requires ASCII, so the em dash is out.

The specification states that the existing 79 suppression comments stay valid and that this work does not review them. The new format applies to added comments only.

The full format rules live in [contracts/suppression-comment.md](contracts/suppression-comment.md).

---

## R13 - Handle a line that grows past the line-length limit

**Decision**: Shorten the reason first. Move the comment to another line of the same statement second. Add `# noqa: E501` last.

**Rationale**: Many target lines already carry a long `# WHY:` comment. Adding a `# nosec` reason can push the line past 120 characters, or past 99 characters inside `mist-ops-platform`. The `ruff` gate then fails on E501.

Result R3 gives the second option real power. A `# nosec` comment works on any line of a multi-line statement, so a crowded opening line can hand the comment to a shorter inner line.

The repository already uses `# noqa: E501` in about 166 places, so the last option follows house convention. It stays last, because a shorter reason reads better than a longer line.

---

## Open questions

None. Every fact in this document comes from a measurement on commit `fb604b4`.
