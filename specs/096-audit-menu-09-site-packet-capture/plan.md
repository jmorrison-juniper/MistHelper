# Plan for Site Packet Capture Operation

## High-level approach
1. Add menu entry mapping to PacketCaptureManager.start_site_packet_capture with parameter validation.
2. Implement orchestration logic to: validate inputs, invoke API, poll for completion, retrieve PCAP(s), and write metadata record.
3. Provide options for local download, container volume placement, or leaving files on remote storage with metadata pointer.
4. Add unit and integration tests for parameter handling, error cases, and metadata persistence.

## Deliverables
- Menu metadata and wiring to function_ref
- Parameter validation and CLI prompts for duration, BPF filter, targets, output path
- Capture orchestration code with progress logging and error handling
- Metadata SQLite insertion module (optional toggle)
- Unit tests and an integration smoke test that simulates capture flow (using small-duration captures or mocks)
- README snippet describing usage and security considerations

## Milestones
- M1: Spec and plan (this artifact) — complete
- M2: Implement orchestration and metadata insertion (code) — estimated 1 day
- M3: Tests and CI integration — estimated 0.5 day
- M4: Documentation and release notes — estimated 0.25 day

## People and roles
- Single engineer: implementer, tester, and documenter. Responsible for code changes, test creation, and PR.

## Verification plan
Manual checks
- Start a 10-second capture with a narrow BPF on a test site, retrieve PCAP, open in tshark/wireshark
- Validate metadata record fields and file checksum

Automated tests to add later
- Unit tests for parameter validation and metadata serialization
- Integration test that invokes capture with a mocked PacketCaptureManager returning a small pcap blob
- CI check that metadata insertion works and no regressions occur

Note: Stop before implementation. Proceed only after reviews of spec and plan are accepted.