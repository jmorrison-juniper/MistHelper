# Implementation Plan: Configure the multi-site write gate

**Issue**: #3203 | **Spec**: [spec.md](spec.md)

## Technical Context

- Python 3.13 and Flask. The change adds no dependency.
- Production starts through `wsgi_capture.py`, which loads `.env` before the
  application factory reads the environment.
- The routes already enforce the Flask key `ORG_UPGRADE_WRITES_ENABLED`.

## Design

1. Add one strict reader for a Boolean environment value to `app/config.py`.
2. Store the decision in a frozen `WriteSettings` group.
3. Copy the decision into the existing Flask configuration key.
4. Name the setting in the closed-gate warning.
5. Document the setting in `deploy/.env.example`.

## Constitution Check

- Safety first: the default and every unknown value keep the gate closed.
- No wrapper and no compatibility path: the environment reader supplies the
  existing route gate directly.
- Tests: unit tests prove parsing and the default. Both states of the
  confirmation page have a contract test.

## Risks

- A deployment administrator can enable a destructive operation. The setting
  requires the exact value `true`, and the deployment example states the risk.
- The setting takes effect at process startup. A deployment must restart the
  portal after it changes `.env`.
