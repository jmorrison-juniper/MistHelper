# Research: Ruff S Family Decision

**Feature**: `1780-ruff-s-family-decision` | **Date**: 2026-08-05

**GitHub Issue**: [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780)

**Purpose**: Issue #1780 asks the team to choose between three options. This document holds the measured data that the choice needs. Every number here comes from a command that a maintainer ran on 2026-08-05. No number here is an estimate.

**Tool versions**: ruff 0.16.0, bandit 1.9.4, Python 3.13. Both versions come from `requirements-dev.txt`.

---

## R1: What does ruff report today?

**Command**:

```powershell
.venv\Scripts\python.exe -m ruff check --select S --statistics .
```

**Output**:

```text
13440   S101    assert
   39   S106    hardcoded-password-func-arg
   25   S108    hardcoded-temp-file
   22   S105    hardcoded-password-string
   13   S603    subprocess-without-shell-equals-true
   10   S110    try-except-pass
    3   S310    suspicious-url-open-usage
    3   S607    start-process-with-partial-path
    3   S608    hardcoded-sql-expression
    2   S104    hardcoded-bind-all-interfaces
    2   S113    request-without-timeout
    2   S605    start-process-with-a-shell
    1   S112    try-except-continue
    1   S606    start-process-with-no-shell
Found 13566 errors.
```

**Finding**: The `S` family reports 13,566 results across the repository. One rule produces 99.1 percent of them. `S101` fires on every `assert` statement, and the test suite holds 13,440 of them.

---

## R2: Where do the results sit?

**Commands**:

```powershell
.venv\Scripts\python.exe -m ruff check --select S --statistics --exclude tests .
.venv\Scripts\python.exe -m ruff check --select S --statistics src
```

**Output without the test tree**:

```text
81      S101    assert
 9      S105    hardcoded-password-string
 8      S110    try-except-pass
 8      S603    subprocess-without-shell-equals-true
 3      S310    suspicious-url-open-usage
 3      S608    hardcoded-sql-expression
 2      S113    request-without-timeout
 2      S605    start-process-with-a-shell
 2      S607    start-process-with-partial-path
 1      S104    hardcoded-bind-all-interfaces
 1      S112    try-except-continue
 1      S606    start-process-with-no-shell
Found 121 errors.
```

**Output for the `src/` tree only**: 62 results.

**Finding**: The test tree holds 13,445 of the 13,566 results. The production code holds 121. Any option that selects `S` must ignore `S101` in the test tree, or the gate can never turn green.

---

## R3: How many results need a second suppression comment?

A maintainer read the source line for each of the 121 non-test results and searched it for the text `# nosec`.

| Group | Count |
| - | - |
| The line already holds a `# nosec` comment | 62 |
| The line holds no `# nosec` comment | 59 |
| Total | 121 |
| Distinct files | 42 |

**Finding**: 62 lines already carry a bandit suppression. Ruff reads `# noqa` and does not read `# nosec`. Each of those 62 lines therefore needs a second annotation on the same line. The result reads `# noqa: S603  # nosec B603`. Issue [#1719](https://github.com/jmorrison-juniper/MistHelper/issues/1719) removed that exact confusion.

The repository holds 117 `# nosec` comments across 51 tracked Python files today.

---

## R4: Where do the 59 unsuppressed results sit?

| Location | Count | Why bandit stays quiet |
| - | - | - |
| `tools/test_quality_analyzer/fixtures/` | 42 | The `[tool.bandit]` table lists the path in `exclude_dirs`. The files hold deliberately bad code that the analyzer reads as test material. |
| `specs/010-endpoint-usage-audit/_validate_report.py` | 7 | The `[tool.bandit]` table lists `specs` in `exclude_dirs`. |
| Production code | 10 | See the table below. |

**The 10 production results that bandit does not report**:

```text
MistHelper.py:917                              S310  with urllib.request.urlopen(
src/analytics/site_analytics_configurator.py:11 S105  _CONFIRM_TOKEN: str = "CONFIGURE"
src/db/__init__.py:45                          S105  arango_password: str = "misthelper"
src/db/__init__.py:48                          S105  redis_password: str = "misthelper"
src/refactors/sqlite_database_writer.py:248    S101  assert (
src/ssh/shell_execution/shell_executor.py:157  S101  assert (
src/utils/logger_utils.py:113                  S110  except Exception:
src/utils/zscaler_catalogue.py:679             S310  req = urllib.request.Request(url, ...)
src/utils/zscaler_probe.py:184                 S603  completed = subprocess.run(
src/utils/zscaler_probe.py:371                 S110  except Exception:
```

**Caution**: The search read the reported line only. Bandit accepts a `# nosec` comment on any line of a multi line statement. Some of these 10 results may already hold a suppression on an adjacent line. The implementer must read each statement before treating it as a new result.

**Finding**: Two results look like real value. `src/db/__init__.py` lines 45 and 48 hold a default password of `misthelper` in an annotated assignment. Bandit does not report an annotated assignment under `B105`. Ruff does. That is one measured case where ruff finds a default credential that bandit misses.

---

## R5: What does bandit report today?

**Command**:

```powershell
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1780.json" -q
```

| Measurement | Count |
| - | - |
| Raw results on Windows | 43 |
| Results under `tools/test_quality_analyzer/fixtures/` | 42 |
| Results that remain | 1 |
| Results in files that git tracks | 0 |

The one remaining result is `mist-ops-platform/src/shared/config/settings.py` line 41, `B104`, MEDIUM. Git does not track that file. Issue [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778) owns it.

A Windows scan does not apply the `exclude_dirs` entry for the analyzer fixtures, because the configured path uses a forward slash and a Windows scan reports a backslash. CI runs on Linux and applies the entry.

**Finding**: The bandit gate is clean. Issue [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889) delivered that state. Any option that adds a second tool starts from 121 new results against a gate that reports zero today.

---

## R6: Do the two tools read the same files?

**Ruff excludes** (root `pyproject.toml`, `[tool.ruff] extend-exclude`):

```text
mist-ops-platform, web_portal, scripts, src/maps
```

**Bandit excludes** (root `pyproject.toml`, `[tool.bandit] exclude_dirs`):

```text
tests, .venv, node_modules, scripts, specs, tools/test_quality_analyzer/fixtures
```

| Tree | Ruff reads it | Bandit reads it |
| - | - | - |
| `src/` except `src/maps` | Yes | Yes |
| `src/maps` | No | Yes |
| `mist-ops-platform` | No | Yes |
| `web_portal` | No | Yes |
| `tests` | Yes | No |
| `specs` | Yes | No |
| `tools/test_quality_analyzer/fixtures` | Yes | No |
| `scripts` | No | No |

**Finding**: The two coverage sets differ in both directions. Option 3 in issue #1780 asks the team to drop bandit. That option would leave `src/maps`, `mist-ops-platform`, and `web_portal` with no security scan at all. The three trees hold 111 Python files.

The `mist-ops-platform` subtree holds its own `pyproject.toml` with a separate ruff configuration. That configuration selects `E`, `W`, `F`, `I`, `N`, `UP`, `B`, `A`, `C4`, `SIM`, `TCH`, `RUF`, and `PLR`. It does not select `S` either. The root `extend-exclude` entry means a repository wide ruff run never reads the subtree, so the subtree configuration has no effect in CI.

---

## R7: How large is the rule gap?

**Commands**:

```powershell
.venv\Scripts\python.exe -m ruff rule --all --output-format json
```

The maintainer compared the ruff `S` codes against the bandit rule identifiers from `bandit.core.extension_loader`.

| Measurement | Count |
| - | - |
| Ruff `S` rules | 73 |
| Bandit rules (42 plugin tests plus 33 blacklist entries) | 75 |
| Bandit rules with no ruff equivalent | 4 |
| Ruff rules with no bandit equivalent | 2 |

**The 4 bandit rules that ruff does not implement**:

| Rule | Name |
| - | - |
| B613 | `trojansource` |
| B614 | `pytorch_load` |
| B615 | `huggingface_unsafe_download` |
| B703 | `django_mark_safe` |

**Finding**: The rule gap is small in count but not small in value. `B613` detects a Trojan Source attack, which uses a bidirectional Unicode control character to make source code read one way and run another way. No other gate in this repository detects that attack. Three of the four gaps cover frameworks that this project does not use, which are PyTorch, Hugging Face, and Django.

The two ruff rules with no bandit number are `S320` and `S410`. Bandit removed both rules in an earlier release, so the gap is a version difference and not a capability difference.

---

## R8: What is the runtime cost?

| Tool | Scope | Observed wall time |
| - | - | - |
| Ruff | Whole repository | Under 1 second |
| Bandit | Whole repository | About 10 seconds |

Both jobs sit in the fast group of the CI workflow, which the workflow comment records as 8 to 11 seconds. Neither tool sets the total workflow time. The slow group holds pytest, pylint, and black.

**Finding**: The speed argument in issue #1780 is correct but small. The workflow saves about 10 seconds if it drops bandit. That saving does not change the developer experience, because the two jobs run in parallel.

---

## R9: The latent annotation problem

This finding does not appear in issue #1780. It changes the risk of every option that selects `S`.

**Commands**:

```powershell
.venv\Scripts\python.exe -m ruff check --select S mist-ops-platform/src/shared/config/settings.py
.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa mist-ops-platform/src/shared/config/settings.py
```

**Output without `--ignore-noqa`**: one result, `S105` at line 27.

**Output with `--ignore-noqa`**: two results, `S105` at line 27 and `S104` at line 41.

Line 41 reads as follows.

```python
    api_host: str = "0.0.0.0"  # noqa: S104
```

**Finding**: A `# noqa: S...` annotation is not inert. It is latent. It hides nothing while `S` stays out of the select list. It starts to hide a result the moment somebody adds `S`. Bandit reports that same line as a MEDIUM `B104`.

Warning: If the team selects the ruff `S` family before issue #1778 deletes this annotation, the MEDIUM result becomes invisible to ruff and stays invisible to CI, because git does not track the file. Issue #1778 must land first.

Issue #1719 removed every other annotation of this kind. This one stayed out of scope, because a person cannot commit an edit to an untracked file.

---

## R10: What would each option cost?

The counts below come from R1 through R9. Each count is a measurement, not an estimate.

### Option 1: Add `S` to the ruff select list and keep bandit

| Item | Count or effect |
| - | - |
| New ruff results to clear | 13,566 |
| Results the team must ignore by rule and path | 13,440 `S101` results in `tests/` |
| Lines that need a second annotation next to an existing `# nosec` | 62 |
| Production results with no current suppression | 10 |
| Security coverage lost | None |
| New security coverage gained | The 10 results in R4, which include 2 default passwords |
| Suppression comment forms in the repository | 2 |

### Option 2: Keep the select list as it is

| Item | Count or effect |
| - | - |
| New ruff results to clear | 0 |
| Lines that need a second annotation | 0 |
| Security coverage lost | None |
| New security coverage gained | None |
| Suppression comment forms in the repository | 1 |
| Latent `# noqa: S...` annotations that stay latent | 1, at `settings.py` line 41 |

### Option 3: Select `S` in ruff and drop bandit

| Item | Count or effect |
| - | - |
| New ruff results to clear | 13,566 |
| Lines that lose their suppression and need a new one | 117 `# nosec` comments across 51 files |
| Trees that lose every security scan | `src/maps`, `mist-ops-platform`, `web_portal` |
| Python files in those trees | 111 |
| Bandit rules lost | 4, including `B613` Trojan Source detection |
| CI time saved | About 10 seconds, in a parallel job |
| Suppression comment forms in the repository | 1 |

---

## Recommendation

The data supports **Option 2 with two named corrections**. The plan states the reasoning. The corrections are as follows.

1. Adopt a rule that forbids a `# noqa: S...` annotation while `S` stays out of the select list. A `RUF100` check can enforce the rule. The annotation is latent, not harmless.
2. Open a separate issue for the 10 production results in R4. Two of them are default passwords in `src/db/__init__.py`. Bandit misses them because of an annotated assignment. Correct them under the bandit gate that already exists, and do not add a second tool to find them.

Option 3 fails on the coverage data alone. It would leave 111 Python files with no security scan and would lose Trojan Source detection.

Option 1 delivers 10 new results for a cost of 62 double suppressions, one new ignore block for 13,440 test asserts, and a second suppression comment form. The same 10 results cost far less through a single bandit pass, because bandit already reads 8 of those 10 files.
