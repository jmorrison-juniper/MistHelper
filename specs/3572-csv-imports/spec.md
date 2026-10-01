# Feature Specification: Import PSKs, user MACs, and assets from CSV

**Feature Branch**: `feat/3572-csv-imports`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 292 import PSKs, user MACs, and assets from CSV. MistHelper is CSV-native, but every CSV flows out of the tool and none flows in. Mist offers import endpoints for pre-shared keys, user MAC entries, and assets, and no operation calls them. An operator who migrates a PSK list types each key in the UI. The operation asks for the import type (org PSKs, org user MACs, org assets, site PSKs, site assets), reads the file data/import_<type>.csv, validates the columns against the OpenAPI schema, prints a preview of the first ten rows and the total, asks the operator to type IMPORT and the row count, sends the import, and writes CsvImportLog.csv with the result."

## User Scenarios and Testing

### User Story 1 - Preview and validate a CSV import (Priority: P1)

An operator selects one import type and MistHelper reads the matching file under `data/`. The tool validates the required columns before it can send a request. The operator sees the first ten rows and the total row count.

**Why this priority**: A bad import can create incorrect Mist cloud records. The operator must see the scope and any schema defect before the destructive step.

**Independent Test**: Provide a CSV without a required column. Verify that validation stops before the client sends a request and that the message names the missing column.

**Acceptance Scenarios**:

1. **Given** `data/import_org_psks.csv` is missing `passphrase`, **When** the operator selects org PSKs, **Then** the operation stops before any request and prints a message that names `passphrase`.
2. **Given** `data/import_site_assets.csv` has 12 valid rows, **When** the operator selects site assets, **Then** the preview prints the first 10 rows and the total row count of 12.
3. **Given** the input file does not exist, **When** the operator selects that import type, **Then** the operation stops and names the expected file path under `data/`.

---

### User Story 2 - Confirm and send a destructive import (Priority: P1)

After validation, the operator must type `IMPORT <row_count>` before MistHelper sends data to Mist. The operation supports dry run mode, which performs all validation and preview steps but sends no request.

**Why this priority**: The import endpoints create or update Mist records. A typed row count prevents accidental execution and confirms that the operator reviewed the preview.

**Independent Test**: Run the operation with a valid CSV and the wrong confirmation phrase. Verify that no request is sent. Run it with dry run mode and verify that no request is sent.

**Acceptance Scenarios**:

1. **Given** a valid CSV has 3 rows, **When** the operator types `IMPORT 2`, **Then** the operation stops and sends no request.
2. **Given** a valid CSV has 3 rows, **When** the operator types `IMPORT 3`, **Then** the operation sends one import request.
3. **Given** dry run mode is enabled, **When** the operator types `IMPORT 3`, **Then** the operation writes a dry run result and sends no request.

---

### User Story 3 - Protect PSK passphrases and write the run log (Priority: P1)

PSK imports include a `passphrase` column. MistHelper must never write that value to a log line or to the import result log. The result log states the import type, row count, and result only.

**Why this priority**: A PSK passphrase is a secret. A log file with passphrases could expose a wireless network.

**Independent Test**: Import a PSK CSV with a unique passphrase and capture log records. Verify that the passphrase does not appear and that the log states only the row count.

**Acceptance Scenarios**:

1. **Given** a PSK CSV contains `secret-psk-value`, **When** validation, preview, and request logging run, **Then** no log record contains `secret-psk-value`.
2. **Given** an import completes, **When** MistHelper writes `CsvImportLog.csv`, **Then** the row includes the import type, row count, and result summary.
3. **Given** dry run mode completes, **When** MistHelper writes `CsvImportLog.csv`, **Then** the row states `dry_run` and no request status.

---

### User Story 4 - Build request bodies that match the OpenAPI shape (Priority: P2)

MistHelper uses the installed `mistapi` file-upload functions where the OpenAPI file declares multipart CSV uploads. Each supported import type has one test that verifies the request shape.

**Why this priority**: The Mist SDK also exposes JSON-body functions for the same paths. The operation must choose the file upload path and keep the request shape consistent.

**Independent Test**: Stub the SDK functions and verify that each import type sends the expected scope identifier and CSV file path.

**Acceptance Scenarios**:

1. **Given** org PSKs, org user MACs, and org assets imports, **When** the request sends, **Then** the client passes `org_id` and the CSV file path to the matching `importOrg*File` function.
2. **Given** site PSKs and site assets imports, **When** the request sends, **Then** the client passes `site_id` and the CSV file path to the matching `importSite*File` function.
3. **Given** the OpenAPI schema changes to JSON-only, **When** a future maintainer updates the client, **Then** the tests must show the new request shape before merge.

## Requirements

### Functional Requirements

- **FR-001**: The operation must offer exactly these import types: org PSKs, org user MACs, org assets, site PSKs, and site assets.
- **FR-002**: The operation must read only `data/import_<type>.csv`, where `<type>` is one of `org_psks`, `org_user_macs`, `org_assets`, `site_psks`, or `site_assets`.
- **FR-003**: The operation must validate required columns before it sends a request.
- **FR-004**: A missing required column must stop the operation and name the missing column.
- **FR-005**: The operation must print a preview of the first ten rows and the total row count.
- **FR-006**: The operation must mask secret fields in the preview and in logs.
- **FR-007**: The operation must send no request until the operator types `IMPORT <row_count>`.
- **FR-008**: The operation must support dry run mode that sends no request.
- **FR-009**: The operation must write `CsvImportLog.csv` under `data/` with the import type, row count, and result.
- **FR-010**: The operation must expose `CsvImportOperation.run()` as the menu handler for deferred menu wiring.
- **FR-011**: The wiring manifest must describe menu 292 as destructive and deferred to the integration pull request.
- **FR-012**: The release note fragment must exist under `changelog.d/issue-3572-csv-imports.md`.

### Key Entities

- **Import type**: The selected API operation, required columns, input file name, scope type, and SDK file function.
- **Import batch**: The parsed CSV rows, input file path, row count, and validation outcome.
- **Import result**: The selected type, row count, dry run flag, request status, and result summary.

## Safety and Review

Menu 292 is destructive because each endpoint creates or updates records in the Mist cloud. The integration pull request must register it as `destructive`, require the `IMPORT <row_count>` typed phrase, and state that a human review is required before merge.
