# Site Packet Capture (Menu 09) - Specification

## Summary
This operation triggers a site-scoped packet capture via PacketCaptureManager.start_site_packet_capture and delivers PCAP files (binary) for diagnostic use. The menu provides options for capture duration, filters (BPF), target devices or SSIDs, and optional remote retrieval to local storage or container volume.

## Purpose
Enable NOC engineers to capture network traffic at a Mist site for troubleshooting connectivity, application behavior, and security analysis. Capture artifacts are PCAP files intended for offline analysis with standard tools (tcpdump, wireshark, tshark).

## Stakeholders
- NOC Engineers (primary users)
- Platform SRE (access, storage policy)
- Security team (when captures include sensitive data)
- Product owner for MistHelper

## Acceptance Criteria
Pass
- Operation starts and completes a site packet capture via PacketCaptureManager.start_site_packet_capture with requested parameters
- One or more PCAP files are produced and retrievable to the configured output path
- Metadata record (see recommendation) is created when requested
- Capture honors duration and BPF filter; errors surfaced with actionable messages

Fail
- No PCAP generated or file corrupted
- Capture runs beyond configured timeout or ignores filters
- Unauthorized capture attempts succeed

## API function(s) used
- PacketCaptureManager.start_site_packet_capture (primary)
- File retrieval utilities in PacketCaptureManager or DataExporter (optional)

## SQL export relevance and recommendation
sql_export_relevant: false — PCAP files are binary artifacts and do not map naturally to row-oriented SQL export. However, we recommend storing a small metadata record per capture in SQLite for indexing and audit: fields: capture_id (uuid), site_id, start_ts, end_ts, duration_sec, filter, device_ids, file_path, size_bytes, user, status, sha256. This enables searches without storing binary data inside the DB.

## Primary key strategy suggestion
Use a natural composite key: primary_key = [capture_id] where capture_id is a UUID generated at capture creation. Indexes: site_id, start_ts, status.

## Risks and Assumptions
- Assumes PacketCaptureManager has network privileges and destination storage access
- Captures may include sensitive payloads; ensure compliance with retention and masking policies
- Large captures can exhaust disk; implement size/duration limits and rotation
- Network impact during capture is assumed minimal but should be communicated to stakeholders
