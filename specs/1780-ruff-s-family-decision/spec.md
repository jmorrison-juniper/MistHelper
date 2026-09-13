# Feature Specification: Ruff S Family Decision

**Feature Branch**: `docs/1778-1780-specs` (specification only. The implementation needs its own branch.)

**GitHub Issue**: [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780) - "chore: decide whether ruff should select the S rule family that duplicates bandit"

**Created**: 2026-08-05

**Status**: Specification. The team has not made the decision yet.

**Input**: The root ruff configuration does not select the `S` family, so every `# noqa: S...` annotation does nothing. Three options exist. Gather the data, choose one option, record the reason, and apply the choice.

---

## Background

The root `pyproject.toml` file holds this select list.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G"]
```

The `S` family holds the flake8-bandit rules. The list does not hold it. A `# noqa: S105` annotation therefore changes nothing in a ruff run.

Issue [#1719](https://github.com/jmorrison-juniper/MistHelper/issues/1719) removed every annotation that this absence made useless. That issue left the design question open on purpose, because the answer needs a team decision.

Issue #1780 states the question. Should ruff select `S` at all?

### The three options

| Option | Description |
| - | - |
| 1 | Add `S` to the ruff select list and keep bandit. |
| 2 | Keep the select list as it is. This is the current state. |
| 3 | Select `S` in ruff and drop bandit. |

### Measured baseline

A maintainer measured every option on 2026-08-05 with ruff 0.16.0 and bandit 1.9.4. The document [research.md](research.md) holds the full output. The table below holds the numbers that drive the decision.

| Measurement | Value |
| - | - |
| Ruff `S` results across the repository | 13,566 |
| Ruff `S101` results in the test tree | 13,440 |
| Ruff `S` results outside the test tree | 121 |
| Results on a line that already holds a `# nosec` comment | 62 |
| Production results that bandit does not report | 10 |
| Bandit results in tracked files today | 0 |
| Existing `# nosec` comments in the repository | 117 |
| Files that hold a `# nosec` comment | 51 |
| Ruff `S` rules | 73 |
| Bandit rules | 75 |
| Bandit rules with no ruff equivalent | 4 |
| Python files that ruff excludes and bandit reads | 111 |

### The finding that issue #1780 does not state

The measurement produced one fact that changes the risk of Option 1 and Option 3.

A `# noqa: S...` annotation is **latent**, not inert. It hides nothing while `S` stays out of the select list. It starts to hide a result the moment somebody adds `S`.

The proof sits at `mist-ops-platform/src/shared/config/settings.py` line 41.

```python
    api_host: str = "0.0.0.0"  # noqa: S104
```

A run of `ruff check --select S` on that file reports one result at line 27 and no result at line 41. The same run with `--ignore-noqa` reports both. Bandit reports line 41 as a MEDIUM `B104`.

Warning: If a person selects the ruff `S` family before issue [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778) deletes that annotation, the MEDIUM result becomes invisible to ruff and stays invisible to CI. Issue #1778 must land first.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the decision without asking the author (Priority: P1)

A new maintainer wonders why a `# noqa: S101` annotation appears in a pull request review but never fires. The maintainer opens the decision record. The record states the choice, the reason, and the measured data behind it. The maintainer needs no further conversation.

**Why this priority**: The question returns every time somebody reads a suppression comment. A written decision ends the loop. This story delivers value even if the team keeps the current state.

**Independent Test**: A reviewer opens the decision record and finds the chosen option, the date, the reason, and a link to the measured data.

**Acceptance Scenarios**:

1. **Given** the decision record, **When** a reviewer reads it, **Then** the record names one of the three options.
2. **Given** the decision record, **When** a reviewer reads it, **Then** the record states the reason and links to the measurement that supports it.
3. **Given** the decision record, **When** a reviewer reads it, **Then** the record names the date and the tool versions that produced the measurement.
4. **Given** the decision record, **When** a reviewer reads it, **Then** the record states what would change the decision later.

---

### User Story 2 - Write the correct suppression comment on the first try (Priority: P1)

A developer adds a subprocess call and sees a security result. The developer opens the suppression contract. The contract states which comment form works. The developer writes one comment and the gate turns green.

**Why this priority**: A wrong suppression comment wastes a CI cycle and a review cycle. The contract removes the guess.

**Independent Test**: A reviewer reads `specs/1032-bandit-severity-gate/contracts/suppression-comment.md` and finds a statement about the ruff `S` family.

**Acceptance Scenarios**:

1. **Given** the updated suppression contract, **When** a developer reads it, **Then** the contract states which comment form suppresses a security result.
2. **Given** the updated suppression contract, **When** a developer reads it, **Then** the contract states whether a `# noqa: S...` annotation does anything.
3. **Given** the updated suppression contract, **When** a developer reads it, **Then** the contract names the tool that owns each security rule.
4. **Given** a security result on one line, **When** a developer applies the contract, **Then** the developer writes one comment and not two.

---

### User Story 3 - Stop a latent annotation from entering the code (Priority: P2)

A reviewer reads a pull request that adds `# noqa: S603`. A gate rejects the annotation, because the `S` family stays out of the select list. The annotation never reaches `main`.

**Why this priority**: This story protects the decision over time. Issue #1719 removed the annotations once. Without a gate, they return.

**Independent Test**: A reviewer adds a `# noqa: S101` annotation to a tracked file and confirms that a gate reports it.

**Acceptance Scenarios**:

1. **Given** a pull request that adds a `# noqa: S...` annotation, **When** CI runs the lint gate, **Then** the gate reports the line and names the file.
2. **Given** the current code base, **When** CI runs the lint gate, **Then** the gate reports zero latent annotations.
3. **Given** a person who removes the `S` family from the select list later, **When** CI runs the lint gate, **Then** the gate reports every annotation that turns latent.

---

### Edge Cases

- A person selects `S` without an ignore rule for the test tree. The gate then reports 13,440 `S101` results and can never turn green.
- A person selects `S` and clears the results with `--fix`. Ruff can add a `# noqa` comment automatically, so the repository gains thousands of annotations in one command. A reviewer cannot read that diff.
- A person drops bandit and does not remove the `mist-ops-platform` entry from the ruff exclude list. The subtree then holds 111 Python files with no security scan and no visible warning.
- A person drops bandit and loses `B613`, which detects a Trojan Source attack. No other gate in this repository detects that attack.
- A person selects `S` before issue #1778 lands. The latent annotation at `settings.py` line 41 then hides a MEDIUM result for good.
- A future ruff release adds the four missing bandit rules. The gap analysis then needs a new measurement, and Option 3 becomes cheaper.
- A future bandit release adds a rule. The team must triage the new result. The team must not restore a severity filter, per issue #889.

---

## Requirements *(mandatory)*

### Decision requirements

- **FR-001**: The team MUST choose one of the three options and MUST record the choice in the repository.
- **FR-002**: The decision record MUST state the reason for the choice.
- **FR-003**: The decision record MUST link to the measured data in [research.md](research.md).
- **FR-004**: The decision record MUST name the tool versions and the date of the measurement.
- **FR-005**: The decision record MUST state what evidence would change the decision later.
- **FR-006**: The decision record MUST state which tool owns each security rule, or MUST state that the two tools overlap and MUST name the overlap.

### Contract requirements

- **FR-007**: The file `specs/1032-bandit-severity-gate/contracts/suppression-comment.md` MUST state which comment form suppresses a security result.
- **FR-008**: The suppression contract MUST state whether a `# noqa: S...` annotation has any effect.
- **FR-009**: If the team keeps the `S` family out of the select list, the contract MUST state that a `# noqa: S...` annotation is latent and MUST state the consequence.

### Guard requirements

- **FR-010**: If the team keeps the `S` family out of the select list, a gate MUST report any new `# noqa: S...` annotation.
- **FR-011**: The guard MUST report the file and the line number, so that a developer can find the annotation without a search.
- **FR-012**: The guard MUST report zero results against the current code base at the time it lands.

### Coordination requirements

- **FR-013**: This work MUST NOT add `S` to the select list before issue #1778 deletes the latent annotation at `mist-ops-platform/src/shared/config/settings.py` line 41.
- **FR-014**: The pull request MUST reference issue #1719, which raised this question, and issue #1778, which holds the ordering risk.
- **FR-015**: If the team chooses Option 1 or Option 3, the work MUST run `ruff check --select S --ignore-noqa` first and MUST triage every result that a latent annotation currently hides.

### Quality requirements

- **FR-016**: Every changed file MUST keep every CI gate green.
- **FR-017**: All prose and all commit text MUST follow the writing guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-018**: The decision MUST NOT reduce security coverage without a written statement of what it gives up.

### Key Entities

- **Rule family**: A group of ruff rules with a shared prefix. The `S` family holds the flake8-bandit rules.
- **Latent annotation**: A `# noqa` comment for a rule that no configuration selects today. It starts to hide a result the moment somebody selects that rule.
- **Suppression contract**: The document that states which comment form hides a security result.
- **Decision record**: The document that states the chosen option, the reason, and the measured data.

---

## Non-Goals

- **NG-001**: This work does not correct the 10 production results that [research.md](research.md) section R4 lists. Those need their own issue.
- **NG-002**: This work does not change the bandit configuration, the bandit targets, or the bandit exclude list.
- **NG-003**: This work does not remove any tree from the ruff exclude list.
- **NG-004**: This work does not correct the gitignore defect in issue #1778. It records the ordering only.
- **NG-005**: This work does not add a new security tool such as Semgrep.
- **NG-006**: This work does not change the CodeQL workflow.
- **NG-007**: This work does not select any other ruff rule family.

---

## Success Criteria *(mandatory)*

- **SC-001**: The repository holds one document that names the chosen option and the reason.
- **SC-002**: A reader finds the decision within two minutes and needs no conversation with the author.
- **SC-003**: The suppression contract states which comment form works, and a reader needs no second document.
- **SC-004**: The repository holds zero latent `# noqa: S...` annotations at the time the work lands.
- **SC-005**: A gate reports any new latent annotation and names the file and the line.
- **SC-006**: Every CI gate that was green before the change stays green.
- **SC-007**: The bandit gate keeps its current result count of zero in tracked files.
- **SC-008**: The pull request states the ordering against issue #1778.
- **SC-009**: If the team chooses Option 1 or Option 3, the ruff `S` gate reports zero results on the branch.
- **SC-010**: If the team chooses Option 3, the pull request names every tree that loses its security scan and names every bandit rule that the repository gives up.

---

## Assumptions

- The team accepts a measured recommendation. [research.md](research.md) recommends Option 2 with two named corrections.
- The tool versions stay pinned in `requirements-dev.txt`, so the measurement holds until Dependabot raises an update.
- The `mist-ops-platform`, `web_portal`, and `src/maps` trees stay in the repository and stay in the ruff exclude list.
- The test suite keeps its `assert` statements. Pytest needs them, so `S101` in the test tree can never be a real result.
- CodeQL stays in place and covers a different rule set, so it does not replace either tool.
