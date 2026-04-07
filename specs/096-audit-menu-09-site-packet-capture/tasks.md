- TC-001: Write spec and plan
  - Description: Produce spec_md and plan_md artifacts and create spec directory specs/096-audit-menu-09-site-packet-capture
  - Dependencies: none

- TC-002: Add menu metadata entry
  - Description: Add JSON/YAML menu metadata pointing to function_ref PacketCaptureManager.start_site_packet_capture
  - Dependencies: TC-001

- TC-003: Implement parameter validation
  - Description: Implement CLI prompts and validation for duration, BPF filter, target devices/SSID, output path, and optional metadata toggle
  - Dependencies: TC-002

- TC-004: Implement capture orchestration
  - Description: Call PacketCaptureManager.start_site_packet_capture, poll status, handle errors, and collect PCAP file paths
  - Dependencies: TC-003

- TC-005: Implement metadata persistence (optional toggle)
  - Description: Create SQLite insertion logic for minimal metadata record (capture_id, site_id, timestamps, filter, file_path, size, sha256, status)
  - Dependencies: TC-004

- TC-006: Implement file retrieval and storage handling
  - Description: Ensure PCAP retrieval to local path or configured volume, implement rotation and size checks
  - Dependencies: TC-004

- TC-007: Add unit tests
  - Description: Tests for validation, metadata serialization, and error handling (use mocks for PacketCaptureManager)
  - Dependencies: TC-003, TC-005

- TC-008: Add integration smoke test
  - Description: End-to-end smoke test that performs a short capture (or uses a mocked small PCAP) and verifies metadata and file integrity
  - Dependencies: TC-004, TC-006, TC-007

- TC-009: Documentation and README update
  - Description: Add usage notes, security/retention guidance, and example commands
  - Dependencies: TC-004, TC-005

- TC-010: CI and release
  - Description: Wire tests into CI, update changelog, create PR
  - Dependencies: TC-007, TC-008, TC-009

Each task should be created as a todo/issue with the listed ID, description, and dependencies for tracking and assignment.