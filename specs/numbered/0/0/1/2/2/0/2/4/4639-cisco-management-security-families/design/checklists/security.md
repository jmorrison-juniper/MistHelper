# Security Checklist: Review management and security configuration families

**Purpose**: Check the security controls of the management review before implementation.
**Created**: 2026-11-26
**Feature**: `design/contracts/secret-redaction.md`, `design/contracts/management-review.md`, and `spec.md`

## Secret Handling

- [x] SEC001 Secret values are omitted from review output. Control: the omission rule and FR-006. Test: TM-03.
- [x] SEC002 Secret values never reach a log line. Control: log counts only and the logging rule. Test: TM-16.
- [x] SEC003 One-way hashes and reversible type 7 values are never decoded, reconstructed, or displayed. Control: FR-007 and the omission rule. Test: TM-04.
- [x] SEC004 The field register names every verified secret field and its treatment. Checked in `design/contracts/secret-redaction.md`.
- [x] SEC005 The review never echoes a source token. Control: display-only observations hold the allow-listed phrase only. Test: TM-02.

## Device Command Safety

- [x] SEC006 The review generates no device command. Control: FR-005. Test: TM-07.
- [x] SEC007 The review never writes the raw command property of the gateway template. Control: D-6 and research row R59.
- [x] SEC008 Organization-scope settings are never written by this issue. Control: D-8 and research row R51.

## Input and Output Safety

- [x] SEC009 Input passes the existing source validation before review. Control: the existing `SourceConfiguration.read` method (research row R30 shows the source kind check).
- [x] SEC010 Banner bodies are not classified, so banner text never becomes a family observation. Control: `IOSDnsConverter.banner_delimiter`. Test: DNS banner tests (research rows R27, R31).
- [x] SEC011 A mapped value passes its value rule before it leaves the review. Control: the mapping entry value rule and TM-14.

## Network and Test Safety

- [x] SEC012 The review opens no network socket. Control: FR-012. Test: TM-15.
- [x] SEC013 Test fixtures use synthetic values only. Control: `design/contracts/secret-redaction.md`, Test Rules.
- [x] SEC014 No security finding is suppressed. Control: the row for security findings in `plan.md`.

## Residual Risk

- [x] SEC015 A reviewer cannot confirm a secret value from the review. Explained: D-4 accepts this risk. The reviewer checks the source file.
- [x] SEC016 A secret value in a copied log or export cannot be removed. Explained: the warning in `design/contracts/secret-redaction.md` states this risk. Mitigation: the log and export rules.
