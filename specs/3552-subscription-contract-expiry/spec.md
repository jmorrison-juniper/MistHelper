# Feature Specification: Subscription Contract Expiry

**Feature Branch**: `3552-subscription-contract-expiry`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 271 subscription and contract expiry report. Menus 42, 43, and 204 export raw licenses, license usage, and JSI contracts, but no operation scores them. An operator learns that a subscription expired or that usage exceeds entitlement only when the Mist UI shows the warning. Mist gives a 30-day grace period and can set the organization to read-only after 90 days. SubscriptionExpiry.csv: one row per subscription type with entitled, usage, status (Active, Expired, Exceeded, Inactive), end date, days remaining, and a band (expired, 0-30 days, 31-90 days, more than 90 days). ContractExpiry.csv: one row per device with serial, model, contract status, contract state (Supported, Unsupported), end date, and a bucket (Expired, 0-3 months, 0-12 months, more than 12 months). A console summary prints the counts per band."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score subscription expiry and entitlement risk (Priority: P1)

An operator runs menu 271 to get one subscription expiry report for the selected organization. The report shows each subscription type, its entitlement, its current usage, its state, its end date, the days that remain, and the risk band. The operator can see expired subscriptions, subscriptions inside the 30-day grace period, subscriptions inside the 90-day read-only risk window, and subscriptions with usage above entitlement before the Mist UI is the only warning source.

**Why this priority**: Subscription expiry and over-use can cause service limits and can make an organization read-only after the grace period. This is the main risk that the feature must show.

**Independent Test**: Use source data that includes active, expired, exceeded, and inactive subscription records. Run menu 271 and verify that SubscriptionExpiry.csv has one row per subscription type and that each row has correct entitled, usage, status, end date, days remaining, and band values.

**Acceptance Scenarios**:

1. **Given** a subscription type with usage less than or equal to entitlement and an end date more than 90 days in the future, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains that subscription type with status "Active", the correct days remaining, and band "more than 90 days".
2. **Given** a subscription type with an end date 1 to 30 days in the future, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains that subscription type with band "0-30 days".
3. **Given** a subscription type with an end date 31 to 90 days in the future, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains that subscription type with band "31-90 days".
4. **Given** a subscription type with an end date before the report date, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains this data:
   - status "Expired"
   - days remaining `0`
   - band "expired"
5. **Given** a subscription type where usage is greater than entitlement, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains that subscription type with status "Exceeded".
6. **Given** a subscription type that is present but not active for use, **When** the operator runs menu 271, **Then** SubscriptionExpiry.csv contains that subscription type with status "Inactive".

---

### User Story 2 - Score device contract expiry risk (Priority: P2)

An operator runs menu 271 to get one contract expiry report for devices. The report shows each device serial, model, contract status, supported state, end date, and expiry bucket. The operator can see unsupported devices and devices with contracts that expire soon.

**Why this priority**: Device support status affects renewal work and support readiness. Operators need device-level evidence, not only raw contract exports.

**Independent Test**: Use source data that includes supported, unsupported, expired, near-expiry, and long-term device contracts. Run menu 271 and verify that ContractExpiry.csv has one row per device with correct serial, model, contract status, contract state, end date, and bucket values.

**Acceptance Scenarios**:

1. **Given** a device contract with an end date before the report date, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains the device with bucket "Expired".
2. **Given** a device contract with an end date from today through 3 months in the future, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains the device with bucket "0-3 months".
3. **Given** a device contract with an end date more than 3 months and not more than 12 months in the future, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains the device with bucket "0-12 months".
4. **Given** a device contract with an end date more than 12 months in the future, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains the device with bucket "more than 12 months".
5. **Given** a device that has support coverage, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains that device with contract state "Supported".
6. **Given** a device that has no valid support coverage, **When** the operator runs menu 271, **Then** ContractExpiry.csv contains that device with contract state "Unsupported".

---

### User Story 3 - Summarize expiry risk in the console (Priority: P3)

An operator runs menu 271 and sees a console summary with counts for each subscription band and each contract bucket. The operator can quickly decide whether renewal work is urgent without opening the CSV files.

**Why this priority**: The console summary gives fast awareness. The CSV files remain the detailed audit record.

**Independent Test**: Use source data with known counts in every subscription band and contract bucket. Run menu 271 and verify that the console summary count for each band and bucket matches the exported CSV rows.

**Acceptance Scenarios**:

1. **Given** subscription records in all four subscription bands, **When** the operator runs menu 271, **Then** the console summary prints the count for "expired", "0-30 days", "31-90 days", and "more than 90 days".
2. **Given** device contract records in all four contract buckets, **When** the operator runs menu 271, **Then** the console summary prints the count for "Expired", "0-3 months", "0-12 months", and "more than 12 months".
3. **Given** the generated CSV files, **When** the console summary is reviewed, **Then** each summary count equals the number of rows in the related CSV file for the same band or bucket.

### Edge Cases

- If a source export has no subscription records, the subscription report must still finish and show zero counts for all subscription bands.
- If a source export has no contract records, the contract report must still finish and show zero counts for all contract buckets.
- If a subscription or contract has no end date, the report must not invent an expiry date. The row must clearly show that the end date is missing and must not be counted as expired.
- If entitlement or usage is missing for a subscription type, the row must still be exported with the available values and a status that does not hide the missing data.
- If a device record has a missing model or serial, the row must still be exported with a clear missing value marker for the absent field.
- If the same subscription type or device appears more than once in the source data, the report must use one clear row per required output grain: one row per subscription type in SubscriptionExpiry.csv and one row per device in ContractExpiry.csv.
- If the report date is the same as the end date, the item must be treated as within the nearest current-risk band, not as more than 90 days or more than 12 months.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide menu 271 as the subscription and contract expiry report.
- **FR-002**: The system MUST use the available raw license, license usage, and JSI contract information to produce scored expiry reports.
- **FR-003**: The system MUST create SubscriptionExpiry.csv each time the operator runs menu 271.
- **FR-004**: SubscriptionExpiry.csv MUST contain exactly one row per subscription type.
- **FR-005**: Each SubscriptionExpiry.csv row MUST include subscription type, entitled, usage, status, end date, days remaining, and band.
- **FR-006**: Subscription status MUST be one of "Active", "Expired", "Exceeded", or "Inactive".
- **FR-007**: The subscription band MUST be one of "expired", "0-30 days", "31-90 days", or "more than 90 days" when an end date is available.
- **FR-008**: A subscription with an end date before the report date MUST be assigned band "expired".
- **FR-009**: A subscription with an end date 0 to 30 days from the report date MUST be assigned band "0-30 days".
- **FR-010**: A subscription with an end date 31 to 90 days from the report date MUST be assigned band "31-90 days".
- **FR-011**: A subscription with an end date more than 90 days from the report date MUST be assigned band "more than 90 days".
- **FR-012**: A subscription with usage greater than entitlement MUST be marked with status "Exceeded".
- **FR-013**: A subscription with an expired end date MUST be marked with status "Expired" unless the source data gives a more severe status that must be preserved.
- **FR-014**: The subscription report MUST show the 30-day grace-period risk and the 90-day read-only risk through the subscription bands.
- **FR-015**: The system MUST create ContractExpiry.csv each time the operator runs menu 271.
- **FR-016**: ContractExpiry.csv MUST contain exactly one row per device.
- **FR-017**: Each ContractExpiry.csv row MUST include serial, model, contract status, contract state, end date, and bucket.
- **FR-018**: Contract state MUST be one of "Supported" or "Unsupported".
- **FR-019**: The contract bucket MUST be one of "Expired", "0-3 months", "0-12 months", or "more than 12 months" when an end date is available.
- **FR-020**: A device contract with an end date before the report date MUST be assigned bucket "Expired".
- **FR-021**: A device contract with an end date from the report date through 3 months in the future MUST be assigned bucket "0-3 months".
- **FR-022**: A device contract with an end date more than 3 months and not more than 12 months in the future MUST be assigned bucket "0-12 months".
- **FR-023**: A device contract with an end date more than 12 months in the future MUST be assigned bucket "more than 12 months".
- **FR-024**: The system MUST print a console summary with counts for each subscription band.
- **FR-025**: The system MUST print a console summary with counts for each contract bucket.
- **FR-026**: Console summary counts MUST match the generated CSV rows for the same band or bucket.
- **FR-027**: The report MUST finish without failure when subscription data is empty and MUST show zero subscription counts.
- **FR-028**: The report MUST finish without failure when contract data is empty and MUST show zero contract counts.
- **FR-029**: Rows with missing end dates MUST remain visible in the correct CSV file and MUST clearly show that the end date is missing.
- **FR-030**: Rows with missing entitlement, usage, serial, or model values MUST remain visible in the correct CSV file and MUST clearly show which value is missing.
- **FR-031**: The report MUST NOT depend on the Mist UI warning before it can show expired, grace-period, read-only-risk, exceeded-entitlement, unsupported, or near-expiry risk.

### Key Entities

- **Subscription Expiry Row**: One scored subscription type. Key attributes are subscription type, entitled count, usage count, status, end date, days remaining, and expiry band.
- **Contract Expiry Row**: One scored device contract. Key attributes are serial, model, contract status, contract state, end date, and expiry bucket.
- **Console Summary**: A count set that shows the number of subscription rows in each band and the number of contract rows in each bucket.
- **Report Date**: The date used to calculate days remaining, subscription bands, and contract buckets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In test data with known subscription states, 100% of subscription types appear once in SubscriptionExpiry.csv with the expected entitled, usage, status, end date, days remaining, and band values.
- **SC-002**: In test data with known contract states, 100% of devices appear once in ContractExpiry.csv with the expected serial, model, contract status, contract state, end date, and bucket values.
- **SC-003**: For test data that covers every subscription band and contract bucket, console summary counts match the CSV row counts for the same band or bucket with 100% accuracy.
- **SC-004**: An operator can identify expired subscriptions, subscriptions in the 0-30 day grace period, subscriptions in the 31-90 day read-only risk window, and exceeded-entitlement subscriptions from the report output without opening the Mist UI.
- **SC-005**: An operator can identify unsupported devices, expired contracts, contracts expiring within 3 months, contracts expiring within 12 months, and contracts expiring after 12 months from the report output.
- **SC-006**: The report completes and produces both required CSV files and the console summary for empty subscription or contract data sets.

## Assumptions

- Operators already have access to the raw data that menus 42, 43, and 204 export.
- The report is for one selected organization at a time.
- Calendar-day calculations use the date when the operator runs menu 271.
- The term "0-3 months" includes contracts that expire today and contracts that expire through 3 calendar months from the report date.
- The term "0-12 months" means more than 3 months and not more than 12 calendar months from the report date, because the 0-3 month bucket is more urgent.
- Rows with missing end dates are exported with a clear missing value marker and are excluded from dated expiry bands or buckets unless the source data already marks them expired or unsupported.
- The feature reports status and risk. It does not change subscription entitlement, device contracts, or organization state.
