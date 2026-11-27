# Security Checklist: Site read refusal

**Purpose**: Check the security properties of the refusal path and of the T008 test.

**Created**: 2026-11-26

**Feature**: [Specification](../../spec.md)

## Response content

- [x] The refusal body holds no transport exception text. The contract test raises `private-transport-detail` and asserts the exact envelope (contract lines 39 and 59).
- [x] The refusal body holds no token, no session value, and no submitted option value (the envelope constant, RC-37).
- [x] The refusal body names the cloud read in plain words and gives one recovery step.

## Logging

- [x] Each new handler logs the exception class name only (`org_upgrade.py` lines 1148, 1228, and 1351).
- [x] The record names no credential value and quotes no environment variable value.
- [ ] Explained: the mistapi logger writes the exception text at `mistapi\__api_request.py` lines 226 and 251. The record does not verify whether that text carries a secret (U-4). The T008 test does not read or print that text.

## Transport

- [x] The reads call mistapi functions only (RC-66, RC-68). The repair adds no direct HTTP call.
- [x] The repair adds no credential handling and no session write on a refusal (`org_upgrade.py` lines 1232 to 1234 follow the try block).

## Test design

- [x] The contract tests use local fake readers and the in-memory store. They call no live Mist API.
- [x] The T008 test patches the transport of the local session only. It starts no container and calls no live API.
