# Feature Specification: Grade Python user text in the STE linter

**Feature Branch**: `feat/1684-ste-grade-strings`

**Created**: 2026-09-13

**Status**: Draft

**Input**: GitHub issue #1684 asks the STE linter to grade logging calls and user-facing string literals.

## Background

The Python parser now grades only docstrings and comments. The parser states that code is never graded. That misses the text an operator reads in logs, prompts, and printed output.

This feature adds a second Python source surface. The parser reads selected string literal arguments. It keeps the old docstring and comment behavior.

The new categories default off. A repository-wide trial would grade many old operational strings at once. That would lower the repository score for text that this issue does not repair. Operators can enable the two categories in `[tool.ste_linter]`, or with command-line flags.

## User Scenarios and Testing

### User Story 1 - Grade logging message text (Priority: P1)

A maintainer enables logging string grading. The linter reads the message text in `logging.debug`, `logging.info`, `logging.warning`, `logging.error`, `logging.critical`, and `logging.exception` calls.

**Why this priority**: Operators read logs during an incident. Those messages must obey the writing policy.

**Independent Test**: Parse synthetic Python source with logging calls. Confirm that each message creates a span with kind `logging` and the call line.

**Acceptance Scenarios**:

1. **Given** a Python file with `logging.info("The devices have been fetched.")`, **When** logging string grading is enabled, **Then** the linter reports the message at that line.
2. **Given** a lazy log call with `%s`, **When** the parser extracts the message, **Then** the placeholder is absent from the graded text.

---

### User Story 2 - Grade user-facing prompt and print text (Priority: P1)

A maintainer enables user-facing string grading. The linter reads string literal text passed to `print(...)` and `safe_input(...)`.

**Why this priority**: A NOC engineer reads prompts and printed text before an action. The prompt must be short and clear.

**Independent Test**: Parse synthetic Python source with `print` and `safe_input`. Confirm that each text creates a `user-facing` span.

**Acceptance Scenarios**:

1. **Given** a Python file with `print("The task has been completed.")`, **When** user-facing grading is enabled, **Then** the linter grades the printed sentence.
2. **Given** a `safe_input("Enter the site name: ")` call, **When** user-facing grading is enabled, **Then** the linter grades the prompt text.

---

### User Story 3 - Keep code tokens out of the grade (Priority: P2)

A maintainer grades source that uses templates, identifiers, and quoted code tokens. The linter grades only the prose around those tokens.

**Why this priority**: STE says to never change a quoted string or an identifier. The linter must not tell a maintainer to change one.

**Independent Test**: Parse synthetic source with f-strings, format placeholders, identifiers, empty strings, and non-ASCII prose.

**Acceptance Scenarios**:

1. **Given** an f-string with an expression, **When** the parser extracts text, **Then** the expression name is absent from the span.
2. **Given** a message that holds only `device_id`, **When** the parser extracts text, **Then** no span is created.
3. **Given** a non-ASCII sentence, **When** the parser extracts text, **Then** the prose remains in the span.

## Edge Cases

- An empty string creates no span.
- A multi-line implicit concatenation creates one span at the first literal line.
- A lazy logging call removes `%s` and `%d` placeholders before grading.
- An f-string grades only its constant text.
- A quoted code token is removed before grading.
- A string that holds only an identifier creates no span.

## Requirements

### Functional Requirements

- **FR-001**: The parser MUST preserve docstring and comment extraction.
- **FR-002**: The parser MUST extract configured `logging.*` message literals when logging string grading is enabled.
- **FR-003**: The parser MUST extract configured user-facing call literals when user-facing grading is enabled.
- **FR-004**: The parser MUST remove format placeholders before it creates a prose span.
- **FR-005**: The parser MUST skip empty strings, identifiers, and quoted code tokens.
- **FR-006**: The configuration MUST let an operator enable or disable each new category.
- **FR-007**: The command line MUST let an operator opt in to each new category without editing the config file.
- **FR-008**: The tests MUST cover an f-string, lazy `%s` logging, implicit concatenation, an empty string, non-ASCII text, and an identifier-only string.

### Key Entities

- **Python string span**: A `ProseSpan` from a Python call argument. It holds the cleaned text, the source line, and a kind.
- **String grading configuration**: The switches and call-name lists that decide which Python calls add string spans.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A targeted pytest module proves all requested string extraction cases.
- **SC-002**: The full quality gates pass locally before the commit.
- **SC-003**: A self-run of the STE linter with both new flags shows string spans affect the report.
- **SC-004**: The repository score stays stable by default, because the new categories are opt in.

## Assumptions

- The first literal argument of a logging call is the message template.
- `print(...)` can grade each literal positional argument.
- `safe_input(...)` grades the prompt positional argument or the `prompt` keyword.
- A dotted call matches by its full dotted name or by its final name.
