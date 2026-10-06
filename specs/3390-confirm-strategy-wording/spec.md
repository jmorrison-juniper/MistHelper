# Confirmation strategy wording

## Problem

The confirmation pages can name a strategy that the cloud does not send.
This occurs when a plan uses the per-device upgrade call.

## Requirements

1. State that the cloud applies no strategy when every child uses the per-device call.
2. Name each group without a strategy when a plan mixes call types.
3. Use the same plain-language strategy names on both confirmation pages.
4. Keep upgrade requests and execution behavior unchanged.

## Verification

Contract tests render both pages and verify normal, mixed, and all-per-device plans.
